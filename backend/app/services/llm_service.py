import json
import re

from backend.app.core.catalog import CATEGORY_CONFIG
from backend.app.core.settings import get_settings
from backend.app.services.provider_client import post_json


def _extract_json_array(text: str) -> list[dict]:
  match = re.search(r"\[[\s\S]*\]", text)
  if not match:
    raise ValueError("No JSON array found in model response.")
  payload = json.loads(match.group(0))
  if not isinstance(payload, list):
    raise ValueError("Model response is not a JSON array.")
  return payload


def _build_messages(campaign: dict, case_context: dict) -> list[dict]:
  category = CATEGORY_CONFIG[campaign["category"]]
  highlights = "、".join(campaign["highlights"])
  analyses = "\n".join(f"- {item['kind']}: {item['summary']}" for item in case_context.get("assetAnalyses", [])) or "- 无额外素材分析"
  return [
    {
      "role": "system",
      "content": (
        "你是广告创意生成助手。"
        "请严格只返回 JSON 数组，不要输出任何解释。"
        "数组中的每个对象必须包含 title、description、selling_points、image_copy、angle、visual_style 字段。"
        "selling_points 必须是长度为 3 的字符串数组。"
      ),
    },
    {
      "role": "user",
      "content": (
        f"案例总结：{campaign['caseSummary']}\n"
        f"素材理解：\n{analyses}\n"
        f"商品：{campaign['brandName']} {campaign['productName']}\n"
        f"类目：{category['label']}\n"
        f"价格：{campaign['price']} 元\n"
        f"受众：{campaign['audience']}\n"
        f"渠道：{campaign['platform']}\n"
        f"风格：{campaign['tone']}\n"
        f"卖点：{highlights}\n"
        f"可选角度：{'、'.join(category['angles'])}\n"
        f"可选视觉：{'、'.join(category['visuals'])}\n"
        f"请生成 {campaign['creativeCount']} 组适合搜广推场景的广告创意，覆盖不同角度。"
      ),
    },
  ]


def _normalize_drafts(campaign: dict, fallback_drafts: list[dict], items: list[dict]) -> list[dict]:
  category = CATEGORY_CONFIG[campaign["category"]]
  creatives: list[dict] = []
  for index in range(campaign["creativeCount"]):
    item = items[index] if index < len(items) else {}
    fallback = fallback_drafts[index]
    selling_points = item.get("selling_points") or fallback["sellingPoints"]
    if len(selling_points) < 3:
      selling_points = (selling_points + fallback["sellingPoints"])[:3]

    creatives.append(
      {
        **fallback,
        "title": item.get("title") or fallback["title"],
        "description": item.get("description") or fallback["description"],
        "imageLine": item.get("image_copy") or fallback["imageLine"],
        "sellingPoints": selling_points[:3],
        "angle": item.get("angle") or fallback["angle"] or category["angles"][index % len(category["angles"])],
        "visual": item.get("visual_style") or fallback["visual"],
        "generationMeta": {
          "textSource": "llm-api",
          "provider": get_settings().llm_provider,
          "model": get_settings().llm_model,
          "apiMarked": True,
        },
      }
    )
  return creatives


def _fallback_response(fallback_drafts: list[dict], requested_mode: str, note: str, mode: str) -> tuple[list[dict], dict]:
  drafts = []
  for draft in fallback_drafts:
    drafts.append(
      {
        **draft,
        "generationMeta": {
          **draft.get("generationMeta", {}),
          "textSource": "mock-template",
          "provider": "local-template-engine",
          "apiMarked": True,
          "apiRequiredEnv": "AIGCSAR_LLM_API_KEY",
        },
      }
    )
  settings = get_settings()
  return drafts, {
    "mode": mode,
    "requestedMode": requested_mode,
    "provider": "local-template-engine" if mode == "mock" else settings.llm_provider,
    "configured": bool(settings.llm_api_key),
    "usedApi": False,
    "apiMarked": True,
    "model": settings.llm_model,
    "note": note,
  }


def generate_text_creatives(campaign: dict, case_context: dict, fallback_drafts: list[dict]) -> tuple[list[dict], dict]:
  settings = get_settings()
  requested_mode = campaign.get("textGenerationMode", "mock")

  if requested_mode != "api":
    return _fallback_response(
      fallback_drafts,
      requested_mode,
      "Text generation is using the local template engine. Switch to API mode to call MiniMax.",
      "mock",
    )

  if not settings.llm_api_key:
    return _fallback_response(
      fallback_drafts,
      requested_mode,
      "API mode was selected but AIGCSAR_LLM_API_KEY is missing, so the system fell back to templates.",
      "mock-fallback",
    )

  payload = {
    "model": settings.llm_model,
    "messages": _build_messages(campaign, case_context),
    "temperature": 0.8,
  }

  try:
    response = post_json(f"{settings.llm_api_base.rstrip('/')}/chat/completions", payload, settings.llm_api_key)
    content = response["choices"][0]["message"]["content"]
    drafts = _normalize_drafts(campaign, fallback_drafts, _extract_json_array(content))
    return drafts, {
      "mode": "api",
      "requestedMode": requested_mode,
      "provider": settings.llm_provider,
      "configured": True,
      "usedApi": True,
      "apiMarked": True,
      "model": settings.llm_model,
      "note": "Text creatives were generated through the real MiniMax API.",
    }
  except Exception as error:  # noqa: BLE001
    return _fallback_response(
      fallback_drafts,
      requested_mode,
      f"MiniMax text generation failed and the system fell back to templates. Error: {error}",
      "api-error-fallback",
    )
