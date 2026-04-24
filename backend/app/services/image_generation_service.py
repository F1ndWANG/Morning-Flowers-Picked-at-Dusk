import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path

from backend.app.core.catalog import PLATFORM_LABELS
from backend.app.core.settings import get_settings
from backend.app.services.provider_client import post_json


PROMPT_VERSION = "structured-ad-prompt-v2"
IMAGE_CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "runtime" / "image_cache.json"
PROMPT_DIMENSION_LABELS = {
  "subject": "Subject",
  "environment": "Environment",
  "medium": "Medium",
  "composition": "Composition",
  "lighting": "Lighting",
  "style": "Style",
  "emotion": "Emotion",
  "atmosphere": "Atmosphere",
}


def _utc_now() -> str:
  return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _build_cache_key(prompt: str, settings) -> str:
  raw = "\n".join([settings.image_provider, settings.image_api_base, settings.image_model, settings.image_size, prompt])
  return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_image_cache() -> dict:
  if not IMAGE_CACHE_PATH.exists():
    return {}
  try:
    return json.loads(IMAGE_CACHE_PATH.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return {}


def _save_image_cache(cache: dict) -> None:
  IMAGE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
  temp_path = IMAGE_CACHE_PATH.with_suffix(".tmp")
  temp_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
  temp_path.replace(IMAGE_CACHE_PATH)


def _build_subject(creative: dict, campaign: dict) -> str:
  return (
    f"The hero subject is {campaign['brandName']} {campaign['productName']}, shown as the absolute visual focus. "
    f"The product should appear premium, physically accurate, highly recognizable, and directly support the key claim: {creative['title']}."
  )


def _build_environment(campaign: dict, case_context: dict) -> str:
  case_summary = case_context.get("caseSummary") or campaign.get("caseSummary", "")
  category_defaults = {
    "beauty": "a clean skincare studio scene with elegant reflective surfaces and refined cosmetic context",
    "appliance": "a modern lifestyle scene with practical product usage context and premium home texture",
    "education": "a focused workspace scene with modern desk elements and aspirational learning context",
    "sports": "an energetic performance scene with outdoor or training-ground context",
  }
  default_environment = category_defaults.get(campaign["category"], "a polished commercial advertising environment")
  return (
    f"{default_environment}. "
    f"Integrate the campaign background subtly: {case_summary}"
  )


def _build_medium(campaign: dict) -> str:
  platform_label = PLATFORM_LABELS.get(campaign["platform"], campaign["platform"])
  return (
    f"a polished commercial advertising poster tailored for the {platform_label} surface, "
    f"optimized for digital ad delivery with readable headline placement and strong first-screen impact."
  )


def _build_composition(creative: dict, campaign: dict) -> str:
  return (
    "keep a strong visual hierarchy with the product in the primary focal zone, "
    "balanced negative space for headline and copy, and a premium poster layout. "
    f"Reserve clean copy space for the headline '{creative['title']}' and the supporting line '{creative['imageLine']}'."
  )


def _build_lighting(campaign: dict) -> str:
  tone_defaults = {
    "premium": "soft cinematic key light with refined highlights, controlled reflections, and luxurious contrast",
    "direct": "clean bright commercial lighting with crisp edges and high product readability",
    "playful": "lively bright lighting with soft glow and energetic color separation",
    "warm": "warm directional light with soft golden spill and inviting commercial warmth",
  }
  return f"{tone_defaults.get(campaign['tone'], 'clean premium commercial studio lighting')}."


def _build_style(creative: dict, campaign: dict) -> str:
  return (
    f"{creative['visual']}, premium advertising photography, high detail, sharp texture fidelity, "
    f"{campaign['tone']} brand tone, strong commercial finish, no clutter, no amateur design."
  )


def _build_emotion(campaign: dict) -> str:
  emotion_defaults = {
    "balanced": "trustworthy, desirable, and conversion-friendly",
    "ctr": "attention-grabbing, curiosity-driven, and energetic",
    "cvr": "credible, reassuring, and purchase-oriented",
    "ecpm": "commercially strong, polished, and broadly appealing",
  }
  return f"{emotion_defaults.get(campaign['objective'], 'premium and persuasive')}."


def _build_atmosphere(campaign: dict, creative: dict) -> str:
  selling_points = ", ".join(creative["sellingPoints"])
  return (
    "immersive, premium, intentional, and ad-ready. "
    f"Make the viewer feel the value of these selling points: {selling_points}. "
    "The final image should feel like a real launch campaign asset, not a casual illustration."
  )


def _compose_prompt_dimensions(creative: dict, campaign: dict, case_context: dict) -> dict:
  return {
    "subject": _build_subject(creative, campaign),
    "environment": _build_environment(campaign, case_context),
    "medium": _build_medium(campaign),
    "composition": _build_composition(creative, campaign),
    "lighting": _build_lighting(campaign),
    "style": _build_style(creative, campaign),
    "emotion": _build_emotion(campaign),
    "atmosphere": _build_atmosphere(campaign, creative),
  }


def build_image_prompt(creative: dict, campaign: dict, case_context: dict) -> str:
  dimensions = _compose_prompt_dimensions(creative, campaign, case_context)
  dimension_lines = [
    f"{PROMPT_DIMENSION_LABELS[key]}: {value}"
    for key, value in dimensions.items()
  ]
  return "\n".join(
    [
      f"Prompt framework: {PROMPT_VERSION}",
      "Generate a high-quality advertising image using these controlled dimensions:",
      *dimension_lines,
      "Additional constraints: readable ad-copy layout, strong product fidelity, premium commercial quality, clean background control, no extra distorted objects, no low-detail rendering.",
    ]
  )


def attach_image_prompts(creatives: list[dict], campaign: dict, case_context: dict) -> list[dict]:
  attached = []
  for creative in creatives:
    prompt_dimensions = _compose_prompt_dimensions(creative, campaign, case_context)
    attached.append(
      {
        **creative,
        "imagePrompt": build_image_prompt(creative, campaign, case_context),
        "imagePromptDimensions": prompt_dimensions,
        "imageMeta": {
          "assetState": "prompt-only",
          "imageSource": "prompt-template",
          "apiMarked": True,
          "apiRequiredEnv": "AIGCSAR_IMAGE_API_KEY",
          "promptVersion": PROMPT_VERSION,
          "promptFramework": list(prompt_dimensions.keys()),
        },
      }
    )
  return attached


def _build_image_payload(prompt: str, settings) -> dict:
  payload = {
    "model": settings.image_model,
    "prompt": prompt,
    "image_size": settings.image_size,
  }

  if settings.image_model == "Kwai-Kolors/Kolors":
    payload["batch_size"] = 1
    payload["num_inference_steps"] = 28
    payload["guidance_scale"] = 8

  if settings.image_model == "Qwen/Qwen-Image":
    payload["num_inference_steps"] = 50
    payload["guidance_scale"] = 4

  return payload


def _extract_image_url(response: dict) -> str:
  images = response.get("images") or response.get("data") or []
  if not images:
    raise ValueError("No image data found in provider response.")

  first = images[0]
  if isinstance(first, str):
    return first
  if "url" in first and first["url"]:
    return first["url"]
  if "b64_json" in first and first["b64_json"]:
    return f"data:image/png;base64,{first['b64_json']}"
  raise ValueError("Provider response does not contain a usable image URL or base64 payload.")


def _truncate(text: str, limit: int) -> str:
  value = str(text or "").replace("\n", " ").strip()
  return value if len(value) <= limit else f"{value[:limit - 1]}…"


def _build_placeholder_image_data_url(creative: dict, campaign: dict, index: int) -> str:
  title = html.escape(_truncate(creative.get("title", "Ad Creative"), 28))
  subtitle = html.escape(_truncate(creative.get("imageLine", creative.get("description", "")), 34))
  brand = html.escape(_truncate(f"{campaign.get('brandName', '')} {campaign.get('productName', '')}", 28))
  point_a = html.escape(_truncate((creative.get("sellingPoints") or [""])[0], 20))
  point_b = html.escape(_truncate((creative.get("sellingPoints") or ["", ""])[1] if len(creative.get("sellingPoints") or []) > 1 else "", 20))
  palette = creative.get("palette") or ["#176b63", "#bf6b2c", "#f4f7f6"]
  primary = html.escape(str(palette[0]))
  accent = html.escape(str(palette[1] if len(palette) > 1 else "#bf6b2c"))
  bg = html.escape(str(palette[2] if len(palette) > 2 else "#f4f7f6"))
  svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="52%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="{primary}" stop-opacity="0.18"/>
    </linearGradient>
    <radialGradient id="orb" cx="68%" cy="28%" r="46%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.34"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="24" stdDeviation="24" flood-color="#17201f" flood-opacity="0.18"/>
    </filter>
  </defs>
  <rect width="1024" height="1024" rx="64" fill="url(#bg)"/>
  <rect width="1024" height="1024" rx="64" fill="url(#orb)"/>
  <circle cx="760" cy="220" r="168" fill="{accent}" opacity="0.16"/>
  <circle cx="806" cy="278" r="94" fill="{primary}" opacity="0.16"/>
  <rect x="86" y="94" width="852" height="836" rx="42" fill="#fffefa" opacity="0.78" filter="url(#shadow)"/>
  <text x="128" y="164" font-family="Arial, Microsoft YaHei, sans-serif" font-size="28" fill="{accent}" font-weight="700" letter-spacing="4">CREATIVE #{index + 1:02d}</text>
  <text x="128" y="238" font-family="Arial, Microsoft YaHei, sans-serif" font-size="46" fill="#17201f" font-weight="800">{brand}</text>
  <foreignObject x="128" y="286" width="768" height="210">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial,'Microsoft YaHei',sans-serif;font-size:62px;font-weight:900;line-height:1.12;color:#17201f;">{title}</div>
  </foreignObject>
  <rect x="128" y="538" width="348" height="56" rx="28" fill="{primary}" opacity="0.12"/>
  <text x="154" y="575" font-family="Arial, Microsoft YaHei, sans-serif" font-size="26" fill="{primary}" font-weight="700">{point_a}</text>
  <rect x="500" y="538" width="348" height="56" rx="28" fill="{accent}" opacity="0.12"/>
  <text x="526" y="575" font-family="Arial, Microsoft YaHei, sans-serif" font-size="26" fill="{accent}" font-weight="700">{point_b}</text>
  <foreignObject x="128" y="650" width="768" height="122">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial,'Microsoft YaHei',sans-serif;font-size:34px;line-height:1.35;color:#60706d;">{subtitle}</div>
  </foreignObject>
  <rect x="128" y="820" width="250" height="68" rx="34" fill="{primary}"/>
  <text x="172" y="864" font-family="Arial, Microsoft YaHei, sans-serif" font-size="28" fill="#ffffff" font-weight="800">立即查看</text>
</svg>"""
  encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
  return f"data:image/svg+xml;base64,{encoded}"


def _attach_placeholder_images(creatives: list[dict], campaign: dict, state: str, source: str) -> list[dict]:
  attached = []
  for index, creative in enumerate(creatives):
    attached.append(
      {
        **creative,
        "imageAssetUrl": _build_placeholder_image_data_url(creative, campaign, index),
        "imageMeta": {
          **creative.get("imageMeta", {}),
          "assetState": state,
          "imageSource": source,
          "apiMarked": True,
          "promptVersion": PROMPT_VERSION,
          "promptFramework": list(creative.get("imagePromptDimensions", {}).keys()),
        },
      }
    )
  return attached


def _build_api_generated_creative(creative: dict, image_url: str, settings, source: str = "image-api") -> dict:
  return {
    **creative,
    "imageAssetUrl": image_url,
    "imageMeta": {
      "assetState": "generated" if source == "image-api" else "cache-hit",
      "imageSource": source,
      "provider": settings.image_provider,
      "model": settings.image_model,
      "apiMarked": True,
      "promptVersion": PROMPT_VERSION,
      "promptFramework": list(creative.get("imagePromptDimensions", {}).keys()),
    },
  }


def _build_fallback_creative(creative: dict, campaign: dict, index: int, settings, error: Exception) -> dict:
  return {
    **creative,
    "imageAssetUrl": _build_placeholder_image_data_url(creative, campaign, index),
    "imageMeta": {
      "assetState": "api-error-local-fallback",
      "imageSource": "local-svg-placeholder",
      "provider": settings.image_provider,
      "model": settings.image_model,
      "apiMarked": True,
      "promptVersion": PROMPT_VERSION,
      "promptFramework": list(creative.get("imagePromptDimensions", {}).keys()),
      "error": str(error),
    },
  }


def _generate_single_image(index: int, creative: dict, campaign: dict, settings, cache: dict) -> tuple[int, dict, dict]:
  cache_key = _build_cache_key(creative["imagePrompt"], settings)
  cached = cache.get(cache_key) if settings.image_cache_enabled else None
  if cached and cached.get("imageAssetUrl"):
    return index, _build_api_generated_creative(creative, cached["imageAssetUrl"], settings, "image-cache"), {
      "status": "cache-hit",
      "cacheKey": cache_key,
    }

  try:
    payload = _build_image_payload(creative["imagePrompt"], settings)
    response = post_json(
      f"{settings.image_api_base.rstrip('/')}/images/generations",
      payload,
      settings.image_api_key,
      timeout=settings.image_timeout_seconds,
    )
    image_url = _extract_image_url(response)
    return index, _build_api_generated_creative(creative, image_url, settings), {
      "status": "api-success",
      "cacheKey": cache_key,
      "imageAssetUrl": image_url,
    }
  except Exception as error:  # noqa: BLE001
    return index, _build_fallback_creative(creative, campaign, index, settings, error), {
      "status": "fallback",
      "error": f"{creative.get('id', index)}: {error}",
      "cacheKey": cache_key,
    }


def maybe_generate_image_assets(creatives: list[dict], campaign: dict, case_context: dict) -> tuple[list[dict], dict]:
  settings = get_settings()
  requested_mode = campaign.get("imageGenerationMode", "mock")
  prepared = attach_image_prompts(creatives, campaign, case_context)

  if requested_mode != "api":
    prepared = _attach_placeholder_images(prepared, campaign, "generated-local", "local-svg-placeholder")
    return prepared, {
      "mode": "mock",
      "requestedMode": requested_mode,
      "provider": "local-svg-placeholder",
      "configured": False,
      "usedApi": False,
      "apiMarked": True,
      "requestedCount": len(prepared),
      "generatedCount": len(prepared),
      "fallbackCount": len(prepared),
      "note": "Image API is disabled, so every creative received an independent local SVG ad image.",
    }

  if not settings.image_api_key:
    prepared = _attach_placeholder_images(prepared, campaign, "generated-local", "local-svg-placeholder")
    return prepared, {
      "mode": "mock-fallback",
      "requestedMode": requested_mode,
      "provider": settings.image_provider,
      "configured": False,
      "usedApi": False,
      "apiMarked": True,
      "model": settings.image_model,
      "requestedCount": len(prepared),
      "generatedCount": len(prepared),
      "fallbackCount": len(prepared),
      "note": "Image API mode was selected but AIGCSAR_IMAGE_API_KEY is missing, so every creative received an independent local SVG ad image.",
    }

  generated = [None] * len(prepared)
  errors = []
  cache_hits = 0
  cache_updates = {}
  cache = _load_image_cache() if settings.image_cache_enabled else {}

  with ThreadPoolExecutor(max_workers=min(settings.image_concurrency, len(prepared))) as executor:
    futures = [
      executor.submit(_generate_single_image, index, creative, campaign, settings, cache)
      for index, creative in enumerate(prepared)
    ]
    for future in as_completed(futures):
      index, creative_result, trace = future.result()
      generated[index] = creative_result
      if trace["status"] == "cache-hit":
        cache_hits += 1
      elif trace["status"] == "api-success" and settings.image_cache_enabled:
        cache_updates[trace["cacheKey"]] = {
          "imageAssetUrl": trace["imageAssetUrl"],
          "provider": settings.image_provider,
          "model": settings.image_model,
          "imageSize": settings.image_size,
          "createdAt": _utc_now(),
        }
      elif trace["status"] == "fallback":
        errors.append(trace["error"])

  if cache_updates:
    cache.update(cache_updates)
    _save_image_cache(cache)

  api_success_count = sum(1 for item in generated if item.get("imageMeta", {}).get("imageSource") == "image-api")
  cache_success_count = sum(1 for item in generated if item.get("imageMeta", {}).get("imageSource") == "image-cache")
  fallback_count = len(generated) - api_success_count - cache_success_count
  return generated, {
    "mode": "api" if api_success_count + cache_success_count == len(generated) else "api-partial-fallback",
    "requestedMode": requested_mode,
    "provider": settings.image_provider,
    "configured": True,
    "usedApi": api_success_count > 0,
    "apiMarked": True,
    "model": settings.image_model,
    "timeoutSeconds": settings.image_timeout_seconds,
    "concurrency": settings.image_concurrency,
    "cacheEnabled": settings.image_cache_enabled,
    "requestedCount": len(generated),
    "generatedCount": len(generated),
    "apiSuccessCount": api_success_count,
    "cacheHitCount": cache_hits,
    "fallbackCount": fallback_count,
    "note": (
      f"Generated image assets for {len(generated)} creatives with concurrency={settings.image_concurrency}. "
      f"API success: {api_success_count}, cache hit: {cache_hits}, local fallback: {fallback_count}."
    ),
    "errors": errors[:3],
  }
