import re

from backend.app.services.text_feature_utils import clamp, overlap_ratio, saturation, token_list


CTA_PATTERN = re.compile(
  r"(buy now|shop now|learn more|start now|try now|click|discover|get yours|join now|立即|马上|领取|查看|下单|购买|报名|体验|试用|了解)",
  re.I,
)
TRUST_PATTERN = re.compile(
  r"(clinically|tested|trusted|professional|certified|verified|review|真实|认证|实验|测试|专业|口碑|成分|报告|保障|安全|温和)",
  re.I,
)
URGENCY_PATTERN = re.compile(
  r"(now|limited|today|instant|launch|save|unlock|限时|首发|马上|立即|新品|抢先|专享)",
  re.I,
)
EMOTION_PATTERN = re.compile(
  r"(治愈|安心|轻松|愉悦|高级|自由|松弛|专注|自信|惊喜|舒适|warm|calm|premium|confident|relaxed)",
  re.I,
)
RISK_PATTERN = re.compile(
  r"(最|第一|100%|永久|根治|治愈疾病|绝对|神效|guaranteed|no\.?1|best ever)",
  re.I,
)


def _creative_text(creative: dict) -> str:
  return " ".join(
    [
      creative.get("title", ""),
      creative.get("description", ""),
      creative.get("imageLine", ""),
      " ".join(creative.get("sellingPoints", [])),
    ]
  )


def extract_advanced_features(creative: dict, campaign: dict, case_context: dict) -> dict:
  title = creative.get("title", "")
  description = creative.get("description", "")
  selling_points = creative.get("sellingPoints", [])
  image_line = creative.get("imageLine", "")
  text = _creative_text(creative)
  tokens = token_list(text)
  unique_ratio = len(set(tokens)) / max(1, len(tokens))

  title_len = len(title)
  description_len = len(description)
  point_count = len([item for item in selling_points if item])
  highlight_hits = sum(1 for item in campaign.get("highlights", []) if item and item.lower() in text.lower())

  number_count = len(re.findall(r"\d+", text))
  cta_count = len(CTA_PATTERN.findall(text))
  trust_count = len(TRUST_PATTERN.findall(text))
  urgency_count = len(URGENCY_PATTERN.findall(text))
  emotion_count = len(EMOTION_PATTERN.findall(text))
  risk_count = len(RISK_PATTERN.findall(text))

  hook_strength = clamp(
    0.25
    + saturation(number_count, 2) * 0.22
    + saturation(urgency_count, 1.5) * 0.20
    + saturation(cta_count, 1.5) * 0.20
    + (0.18 if 8 <= title_len <= 32 else 0),
    0,
    1,
  )
  selling_point_density = clamp((point_count + highlight_hits) / 6, 0, 1)
  trust_depth = clamp(0.28 + saturation(trust_count, 2) * 0.50 + saturation(highlight_hits, 3) * 0.22, 0, 1)
  emotional_intensity = clamp(0.25 + saturation(emotion_count, 2) * 0.45 + saturation(urgency_count, 2) * 0.20, 0, 1)
  readability = clamp(
    0.25
    + (0.28 if 10 <= title_len <= 32 else 0.10)
    + (0.28 if 38 <= description_len <= 160 else 0.12)
    + unique_ratio * 0.19,
    0,
    1,
  )
  brand_consistency = 1.0 if campaign.get("brandName") and campaign["brandName"].lower() in text.lower() else 0.45
  audience_fit = overlap_ratio(campaign.get("audience", ""), text)
  case_fit = max(
    overlap_ratio(campaign.get("caseSummary", ""), text),
    overlap_ratio(case_context.get("caseSummary", ""), text),
    overlap_ratio(case_context.get("assetSummary", ""), text),
  )
  image_copy_consistency = max(
    overlap_ratio(title, image_line),
    overlap_ratio(" ".join(selling_points), image_line),
    overlap_ratio(image_line, text),
  )
  conversion_friction = clamp(
    0.18
    + (0.22 if not cta_count else 0)
    + (0.18 if trust_depth < 0.45 else 0)
    + (0.16 if selling_point_density < 0.35 else 0)
    + (0.16 if risk_count > 0 else 0)
    + (0.10 if readability < 0.55 else 0),
    0,
    1,
  )
  platform_intent_fit = clamp(0.55 + audience_fit * 0.20 + case_fit * 0.18 + selling_point_density * 0.12, 0, 1)
  commercial_quality = clamp(
    hook_strength * 0.18
    + selling_point_density * 0.18
    + trust_depth * 0.18
    + readability * 0.16
    + brand_consistency * 0.12
    + image_copy_consistency * 0.10
    + (1 - conversion_friction) * 0.08,
    0,
    1,
  )

  return {
    "hookStrength": hook_strength,
    "sellingPointDensity": selling_point_density,
    "trustDepth": trust_depth,
    "emotionalIntensity": emotional_intensity,
    "readability": readability,
    "brandConsistency": brand_consistency,
    "audienceFit": audience_fit,
    "caseFit": case_fit,
    "imageCopyConsistency": image_copy_consistency,
    "platformIntentFit": platform_intent_fit,
    "conversionFriction": conversion_friction,
    "riskCueDensity": clamp(risk_count / 3, 0, 1),
    "commercialQuality": commercial_quality,
  }
