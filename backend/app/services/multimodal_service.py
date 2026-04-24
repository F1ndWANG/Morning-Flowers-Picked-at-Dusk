import json
import re

from backend.app.core.catalog import CATEGORY_CONFIG
from backend.app.core.settings import get_settings
from backend.app.services.asset_service import build_asset_preview, normalize_case_assets
from backend.app.services.provider_client import post_json, post_multipart


FALLBACK_HIGHLIGHTS = ["Clear benefit", "Scenario fit", "Reason to buy"]
FALLBACK_AUDIENCE = "Potential users interested in this product category"


def _extract_first_json_object(text: str) -> dict:
  start = text.find("{")
  if start < 0:
    raise ValueError("No JSON object found in case understanding response.")

  depth = 0
  in_string = False
  escape = False
  for index in range(start, len(text)):
    char = text[index]
    if in_string:
      if escape:
        escape = False
      elif char == "\\":
        escape = True
      elif char == "\"":
        in_string = False
      continue

    if char == "\"":
      in_string = True
    elif char == "{":
      depth += 1
    elif char == "}":
      depth -= 1
      if depth == 0:
        return json.loads(text[start:index + 1])

  raise ValueError("No complete JSON object found in case understanding response.")


def _pick_category(text: str, default_category: str) -> str:
  lowered = text.lower()
  category_keywords = {
    "beauty": ["serum", "skincare", "repair", "brightening", "sensitive skin", "essence"],
    "appliance": ["coffee", "capsule", "kitchen", "appliance", "espresso", "machine"],
    "education": ["course", "training", "interview", "resume", "bootcamp", "learning"],
    "sports": ["running", "sport", "fitness", "outdoor", "training", "shoe"],
  }
  for category, keywords in category_keywords.items():
    if any(keyword in lowered for keyword in keywords):
      return category
  return default_category


def _extract_highlights(text: str, fallback: list[str]) -> list[str]:
  chunks = [item.strip() for item in re.split(r"[,\n.;!?，。；！？]", text) if item.strip()]
  scored = []
  for chunk in chunks:
    score = 0
    if re.search(r"\d", chunk):
      score += 2
    if len(chunk) >= 10:
      score += 1
    if re.search(r"(support|repair|improve|reduce|boost|lightweight|suitable|upgrade|clear)", chunk, re.I):
      score += 2
    scored.append((score, chunk))
  highlights = [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:5]]
  return highlights or fallback or FALLBACK_HIGHLIGHTS


def _build_modality_stats(normalized_assets: list[dict], analyses: list[dict]) -> dict:
  image_count = sum(1 for asset in normalized_assets if asset["kind"] == "image")
  audio_count = sum(1 for asset in normalized_assets if asset["kind"] == "audio")
  text_count = sum(1 for asset in normalized_assets if asset["kind"] == "text" and asset.get("text"))
  transcript_count = sum(1 for item in analyses if item.get("transcript"))
  return {
    "totalAssetCount": len(normalized_assets),
    "imageAssetCount": image_count,
    "audioAssetCount": audio_count,
    "textAssetCount": text_count,
    "transcriptCount": transcript_count,
    "hasImageAsset": image_count > 0,
    "hasAudioAsset": audio_count > 0,
  }


def _build_context_fields(form: dict, normalized_assets: list[dict], analyses: list[dict]) -> tuple[list[str], str]:
  text_assets = [asset.get("text", "") for asset in normalized_assets if asset["kind"] == "text" and asset.get("text")]
  analysis_summaries = [item.get("summary", "") for item in analyses if item.get("summary")]
  transcript_text = " ".join(item.get("transcript", "") for item in analyses if item.get("transcript"))
  case_parts = [form.get("caseText", ""), *text_assets, *analysis_summaries, transcript_text]
  case_text = " ".join(part.strip() for part in case_parts if part and part.strip()).strip()
  case_signals = [item.get("signal") for item in analyses if item.get("signal")]
  return case_signals, case_text


def _base_case_context(form: dict, normalized_assets: list[dict], analyses: list[dict], parsed: dict | None = None) -> dict:
  parsed = parsed or {}
  case_signals, case_text = _build_context_fields(form, normalized_assets, analyses)
  product_name = parsed.get("productName") or form.get("productName") or (normalized_assets[0]["name"].split(".")[0] if normalized_assets else "Case Product")
  brand_name = parsed.get("brandName") or form.get("brandName") or "Case Brand"
  category = parsed.get("category") or _pick_category(case_text, form.get("category", "beauty"))
  highlights = _extract_highlights(" ".join(parsed.get("highlights", []) or [case_text]), form.get("highlights") or [])
  modality_stats = _build_modality_stats(normalized_assets, analyses)

  return {
    "productName": product_name,
    "brandName": brand_name,
    "category": category,
    "price": parsed.get("price") or form.get("price") or 199,
    "audience": parsed.get("audience") or form.get("audience") or FALLBACK_AUDIENCE,
    "objective": form.get("objective", "balanced"),
    "platform": form.get("platform", "feed"),
    "tone": form.get("tone", "premium"),
    "highlights": highlights[:5],
    "caseSummary": parsed.get("caseSummary") or case_text or "No detailed case description was provided.",
    "assetAnalyses": analyses,
    "assetPreviews": [build_asset_preview(asset) for asset in normalized_assets],
    "caseSignals": case_signals,
    "transcriptText": " ".join(item.get("transcript", "") for item in analyses if item.get("transcript")).strip(),
    "modalityStats": modality_stats,
    "assetSummary": " | ".join(item.get("summary", "") for item in analyses if item.get("summary")),
  }


def _describe_image_asset_with_api(asset: dict) -> dict:
  settings = get_settings()
  payload = {
    "model": settings.vision_model,
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Identify the product, the visual style, the strongest selling point, and the best advertising angle in one short summary.",
          },
          {"type": "image_url", "image_url": {"url": asset["dataUrl"]}},
        ],
      }
    ],
  }
  response = post_json(f"{settings.llm_api_base.rstrip('/')}/chat/completions", payload, settings.llm_api_key)
  content = response["choices"][0]["message"]["content"]
  return {
    "assetId": asset["id"],
    "kind": "image",
    "summary": content.strip(),
    "signal": "image-understanding",
  }


def _transcribe_audio_with_api(asset: dict) -> dict:
  settings = get_settings()
  response = post_multipart(
    f"{settings.llm_api_base.rstrip('/')}/audio/transcriptions",
    {"model": settings.audio_model},
    [
      {
        "field": "file",
        "filename": asset["name"],
        "content_type": asset["mimeType"] or "audio/mpeg",
        "content": asset["binary"],
      }
    ],
    settings.llm_api_key,
  )
  transcript = response.get("text", "").strip()
  return {
    "assetId": asset["id"],
    "kind": "audio",
    "summary": transcript or f"Uploaded audio asset: {asset['name']}",
    "signal": "audio-transcription",
    "transcript": transcript,
  }


def _mock_analyze_asset(asset: dict) -> dict:
  if asset["kind"] == "image":
    return {
      "assetId": asset["id"],
      "kind": "image",
      "summary": f"Image asset {asset['name']} is available and can be used to infer product appearance and ad style.",
      "signal": "image-mock-summary",
    }
  if asset["kind"] == "audio":
    return {
      "assetId": asset["id"],
      "kind": "audio",
      "summary": f"Audio asset {asset['name']} is available and likely contains spoken selling points or audience cues.",
      "signal": "audio-mock-summary",
      "transcript": asset["name"],
    }
  return {
    "assetId": asset["id"],
    "kind": "text",
    "summary": (asset.get("text", "") or "")[:160] or f"Text asset {asset['name']}",
    "signal": "text-case",
  }


def _extract_context_with_api(form: dict, analyses: list[dict], normalized_assets: list[dict]) -> dict:
  settings = get_settings()
  joined_analyses = "\n".join(f"- {item['kind']}: {item['summary']}" for item in analyses)
  category_labels = ", ".join(f"{key}:{value['label']}" for key, value in CATEGORY_CONFIG.items())
  payload = {
    "model": settings.llm_model,
    "messages": [
      {
        "role": "system",
        "content": (
          "You are an advertising case understanding assistant. "
          "Return one JSON object only with fields: productName, brandName, category, audience, price, highlights, caseSummary. "
          "category must be chosen from the provided category list and highlights must be a string array."
        ),
      },
      {
        "role": "user",
        "content": (
          f"User text:\n{form.get('caseText', '')}\n\n"
          f"Asset analyses:\n{joined_analyses}\n\n"
          f"Structured hints: product={form.get('productName', '')}, brand={form.get('brandName', '')}, audience={form.get('audience', '')}\n"
          f"Categories: {category_labels}"
        ),
      },
    ],
    "temperature": 0.2,
  }
  response = post_json(f"{settings.llm_api_base.rstrip('/')}/chat/completions", payload, settings.llm_api_key)
  content = response["choices"][0]["message"]["content"]
  parsed = _extract_first_json_object(content)
  return _base_case_context(form, normalized_assets, analyses, parsed)


def analyze_case_inputs(form: dict) -> tuple[dict, dict]:
  normalized_assets = normalize_case_assets(form.get("caseAssets", []))
  settings = get_settings()
  case_understanding_mode = form.get("caseUnderstandingMode", "api")
  use_api = case_understanding_mode == "api" and bool(settings.llm_api_key)

  analyses: list[dict] = []
  for asset in normalized_assets:
    if use_api and asset["kind"] == "image" and asset.get("dataUrl"):
      analyses.append(_describe_image_asset_with_api(asset))
    elif use_api and asset["kind"] == "audio" and asset.get("binary"):
      analyses.append(_transcribe_audio_with_api(asset))
    else:
      analyses.append(_mock_analyze_asset(asset))

  if use_api:
    case_context = _extract_context_with_api(form, analyses, normalized_assets)
    trace = {
      "mode": "api",
      "provider": settings.llm_provider,
      "usedApi": True,
      "configured": True,
      "requestedMode": case_understanding_mode,
      "note": "Case understanding used the multimodal API path.",
    }
  else:
    case_context = _base_case_context(form, normalized_assets, analyses)
    trace = {
      "mode": "mock",
      "provider": "local-case-understanding",
      "usedApi": False,
      "configured": bool(settings.llm_api_key),
      "requestedMode": case_understanding_mode,
      "note": "Case understanding used the local parser and mock asset analysis.",
    }

  return case_context, trace
