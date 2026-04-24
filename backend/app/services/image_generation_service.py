from backend.app.core.catalog import PLATFORM_LABELS
from backend.app.core.settings import get_settings
from backend.app.services.provider_client import post_json


PROMPT_VERSION = "structured-ad-prompt-v2"
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


def maybe_generate_image_assets(creatives: list[dict], campaign: dict, case_context: dict) -> tuple[list[dict], dict]:
  settings = get_settings()
  requested_mode = campaign.get("imageGenerationMode", "mock")
  prepared = attach_image_prompts(creatives, campaign, case_context)

  if requested_mode != "api":
    return prepared, {
      "mode": "mock",
      "requestedMode": requested_mode,
      "provider": "prompt-only",
      "configured": False,
      "usedApi": False,
      "apiMarked": True,
      "note": "The system is currently returning only an image prompt. Configure AIGCSAR_IMAGE_API_KEY to generate a real sample image.",
    }

  if not settings.image_api_key:
    return prepared, {
      "mode": "mock-fallback",
      "requestedMode": requested_mode,
      "provider": settings.image_provider,
      "configured": False,
      "usedApi": False,
      "apiMarked": True,
      "model": settings.image_model,
      "note": "Image API mode was selected but AIGCSAR_IMAGE_API_KEY is missing, so the system returned only an image prompt.",
    }

  try:
    winner = prepared[0]
    payload = _build_image_payload(winner["imagePrompt"], settings)
    response = post_json(
      f"{settings.image_api_base.rstrip('/')}/images/generations",
      payload,
      settings.image_api_key,
      timeout=180,
    )
    image_url = _extract_image_url(response)
    prepared[0] = {
      **winner,
      "imageAssetUrl": image_url,
        "imageMeta": {
          "assetState": "generated",
          "imageSource": "image-api",
          "provider": settings.image_provider,
          "model": settings.image_model,
          "apiMarked": True,
          "promptVersion": PROMPT_VERSION,
          "promptFramework": list(winner.get("imagePromptDimensions", {}).keys()),
        },
      }
    return prepared, {
      "mode": "api",
      "requestedMode": requested_mode,
      "provider": settings.image_provider,
      "configured": True,
      "usedApi": True,
      "apiMarked": True,
      "model": settings.image_model,
      "note": "Sample image generation succeeded through the real image API.",
    }
  except Exception as error:  # noqa: BLE001
    return prepared, {
      "mode": "api-error-fallback",
      "requestedMode": requested_mode,
      "provider": settings.image_provider,
      "configured": True,
      "usedApi": False,
      "apiMarked": True,
      "model": settings.image_model,
      "note": f"Image generation failed and the system fell back to prompt-only output. Error: {error}",
    }
