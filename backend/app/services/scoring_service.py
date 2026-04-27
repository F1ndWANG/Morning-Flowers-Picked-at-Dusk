import re

from backend.app.core.catalog import CATEGORY_CONFIG, PLATFORM_LABELS
from backend.app.services.creative_feature_extractor import extract_advanced_features
from backend.app.services.industrial_prediction_service import attach_esmm_outputs, build_industrial_prediction_signals
from backend.app.services.model_runtime_service import get_model_runtime, get_surface_weights
from backend.app.services.multimodal_alignment_service import evaluate_multimodal_alignment
from backend.app.services.predictor_service import predict_metric


def _clamp(value: float, lower: float, upper: float) -> float:
  return max(lower, min(upper, value))


def _tokenize(text: str) -> set[str]:
  return {token.strip().lower() for token in re.split(r"[\s,\n.;:!?，。；：！？]+", text) if token.strip()}


def _overlap_ratio(source: str, target: str) -> float:
  source_tokens = _tokenize(source)
  target_tokens = _tokenize(target)
  if not source_tokens or not target_tokens:
    return 0
  return len(source_tokens & target_tokens) / len(source_tokens)


def _count_cta_hits(text: str) -> int:
  return len(re.findall(r"(buy now|shop now|learn more|start now|try now|click|discover|get yours|join now)", text, re.I))


def _build_signals(creative: dict, campaign: dict, case_context: dict) -> dict:
  text = " ".join(
    [
      creative["title"],
      creative["description"],
      creative["imageLine"],
      " ".join(creative["sellingPoints"]),
    ]
  )
  highlight_hits = sum(1 for item in campaign["highlights"] if item and item.lower() in text.lower())
  title_length = len(creative["title"])
  description_length = len(creative["description"])
  modality_stats = case_context.get("modalityStats", {})
  asset_summary = " ".join(
    [
      case_context.get("assetSummary", ""),
      case_context.get("transcriptText", ""),
      " ".join(case_context.get("caseSignals", [])),
    ]
  )

  brand_signal = 1.0 if campaign["brandName"] and campaign["brandName"].lower() in text.lower() else 0.35
  audience_signal = _overlap_ratio(campaign["audience"], text)
  highlight_signal = highlight_hits / max(1, min(3, len(campaign["highlights"])))
  clarity_signal = 1.0 if 10 <= title_length <= 28 else 0.62
  urgency_signal = 1.0 if re.search(r"(now|limited|today|instant|launch|save|unlock)", text, re.I) else 0.42
  trust_signal = 1.0 if re.search(r"(clinically|tested|trusted|professional|certified|verified|real reviews)", text, re.I) else 0.48
  number_signal = 1.0 if re.search(r"\d", text) else 0.4
  price_signal = 1.0 if re.search(r"(\$|discount|coupon|trial|offer|value|bundle)", text, re.I) else 0.45
  case_alignment_signal = max(
    _overlap_ratio(campaign["caseSummary"], text),
    _overlap_ratio(asset_summary, text),
  )
  surface_signal = CATEGORY_CONFIG[campaign["category"]]["platformFit"][campaign["platform"]] - 0.85

  cta_signal = _clamp(0.35 + _count_cta_hits(text) * 0.28, 0.35, 1.0)
  readability_signal = 1.0 if 36 <= description_length <= 140 and title_length <= 28 else 0.68
  asset_signal = _clamp(
    0.35
    + modality_stats.get("imageAssetCount", 0) * 0.22
    + modality_stats.get("audioAssetCount", 0) * 0.18
    + modality_stats.get("textAssetCount", 0) * 0.12
    + modality_stats.get("transcriptCount", 0) * 0.10,
    0.35,
    1.0,
  )
  multimodal_alignment_signal = max(
    _overlap_ratio(case_context.get("transcriptText", ""), text),
    _overlap_ratio(case_context.get("assetSummary", ""), text),
  )

  return {
    "numberSignal": number_signal,
    "brandSignal": brand_signal,
    "audienceSignal": audience_signal,
    "highlightSignal": highlight_signal,
    "claritySignal": clarity_signal,
    "urgencySignal": urgency_signal,
    "trustSignal": trust_signal,
    "surfaceSignal": surface_signal,
    "caseAlignmentSignal": case_alignment_signal,
    "priceSignal": price_signal,
    "ctaSignal": cta_signal,
    "readabilitySignal": readability_signal,
    "assetSignal": asset_signal,
    "multimodalAlignmentSignal": multimodal_alignment_signal,
  }


def _estimate_confidence(case_context: dict, signals: dict, advanced_features: dict | None = None, alignment: dict | None = None) -> float:
  advanced_features = advanced_features or {}
  alignment = alignment or {}
  modality_stats = case_context.get("modalityStats", {})
  confidence = 0.58
  confidence += min(len(case_context.get("caseSummary", "")) / 240, 0.12)
  confidence += min(modality_stats.get("totalAssetCount", 0) * 0.05, 0.15)
  confidence += min(modality_stats.get("transcriptCount", 0) * 0.04, 0.08)
  confidence += signals["caseAlignmentSignal"] * 0.08
  confidence += signals["highlightSignal"] * 0.05
  confidence += advanced_features.get("commercialQuality", 0) * 0.04
  confidence += alignment.get("overallAlignment", 0) * 0.05
  confidence -= advanced_features.get("conversionFriction", 0) * 0.04
  return _clamp(confidence, 0.55, 0.96)


def _build_metric_intervals(ctr: float, cvr: float, ecpm: float, confidence: float) -> dict:
  relative_margin = _clamp((1 - confidence) * 0.55 + 0.04, 0.05, 0.30)
  ctr_margin = ctr * relative_margin
  cvr_margin = cvr * (relative_margin + 0.03)
  ecpm_margin = ecpm * (relative_margin + 0.06)
  return {
    "ctr": {
      "lower": _clamp(ctr - ctr_margin, 0.001, 1),
      "upper": _clamp(ctr + ctr_margin, 0.001, 1),
    },
    "cvr": {
      "lower": _clamp(cvr - cvr_margin, 0.001, 1),
      "upper": _clamp(cvr + cvr_margin, 0.001, 1),
    },
    "ecpm": {
      "lower": max(0, ecpm - ecpm_margin),
      "upper": max(0, ecpm + ecpm_margin),
    },
  }


def _build_reason_list(signals: dict, campaign: dict, case_context: dict) -> list[str]:
  reasons: list[str] = []
  if signals["highlightSignal"] >= 0.66:
    reasons.append("Core selling points are strongly expressed in the creative.")
  if signals["audienceSignal"] >= 0.25:
    reasons.append("Audience wording is aligned with the target segment.")
  if signals["caseAlignmentSignal"] >= 0.2:
    reasons.append("The creative stays close to the original case and campaign context.")
  if signals["brandSignal"] >= 1:
    reasons.append("Brand exposure is explicit, which helps trust and conversion.")
  if signals["claritySignal"] >= 1 and signals["readabilitySignal"] >= 1:
    reasons.append("The title and description are concise enough for quick comprehension.")
  if signals["multimodalAlignmentSignal"] >= 0.18:
    reasons.append("The copy reflects the uploaded assets or transcript cues instead of ignoring them.")
  if case_context.get("modalityStats", {}).get("totalAssetCount", 0) > 0 and signals["assetSignal"] >= 0.7:
    reasons.append("Uploaded assets added extra context, which improves cold-start confidence.")
  reasons.append(f"The current copy is better aligned with the {PLATFORM_LABELS.get(campaign['platform'], campaign['platform'])} surface.")
  return reasons


def score_creative(creative: dict, campaign: dict, case_context: dict, seed: float = 0) -> dict:
  signals = _build_signals(creative, campaign, case_context)
  advanced_features = extract_advanced_features(creative, campaign, case_context)
  alignment = evaluate_multimodal_alignment(creative, campaign, case_context)
  industrial_features = build_industrial_prediction_signals(
    creative,
    campaign,
    case_context,
    signals,
    advanced_features,
    alignment,
  )
  ctr, ctr_contributions = predict_metric("ctr", signals, seed * 0.0025)
  cvr, cvr_contributions = predict_metric("cvr", signals, seed * 0.0016)

  ctr_multiplier = _clamp(
    0.88
    + advanced_features["hookStrength"] * 0.13
    + advanced_features["emotionalIntensity"] * 0.05
    + advanced_features["platformIntentFit"] * 0.06
    + alignment["overallAlignment"] * 0.05
    - advanced_features["riskCueDensity"] * 0.04,
    0.86,
    1.18,
  )
  cvr_multiplier = _clamp(
    0.86
    + advanced_features["trustDepth"] * 0.11
    + advanced_features["sellingPointDensity"] * 0.08
    + advanced_features["readability"] * 0.05
    + alignment["imageCopyAlignment"] * 0.05
    - advanced_features["conversionFriction"] * 0.10,
    0.82,
    1.20,
  )
  ctr = _clamp(ctr * ctr_multiplier, 0.001, 1)
  cvr = _clamp(cvr * cvr_multiplier, 0.001, 1)
  industrial_ctr_multiplier = _clamp(
    0.88
    + industrial_features["dcnCrossScore"] * 0.14
    + industrial_features["memorizationCross"] * 0.07
    + industrial_features["userInterestProxy"] * 0.07
    + industrial_features["surfaceIntentScore"] * 0.04
    - advanced_features["riskCueDensity"] * 0.05,
    0.86,
    1.22,
  )
  industrial_cvr_multiplier = _clamp(
    0.87
    + industrial_features["fmInteractionScore"] * 0.10
    + industrial_features["multitaskConsistency"] * 0.12
    + industrial_features["conversionTaskScore"] * 0.07
    + industrial_features["surfaceConversionScore"] * 0.04
    - advanced_features["conversionFriction"] * 0.08,
    0.84,
    1.24,
  )
  ctr = _clamp(ctr * industrial_ctr_multiplier * industrial_features["calibrationFactor"], 0.001, 1)
  cvr = _clamp(cvr * industrial_cvr_multiplier * industrial_features["calibrationFactor"], 0.001, 1)

  bid_factor = CATEGORY_CONFIG[campaign["category"]]["bidFactor"]
  surface_factor = get_surface_weights().get(campaign["platform"], 1.0)
  ecpm = ctr * (1.4 + cvr * 100) * bid_factor * surface_factor * 1000
  confidence = _estimate_confidence(case_context, signals, advanced_features, alignment)
  confidence = _clamp(
    confidence
    + industrial_features["multitaskConsistency"] * 0.035
    + industrial_features["dcnCrossScore"] * 0.025
    - advanced_features["conversionFriction"] * 0.025,
    0.55,
    0.98,
  )
  intervals = _build_metric_intervals(ctr, cvr, ecpm, confidence)
  metrics = attach_esmm_outputs(
    {
      "ctr": ctr,
      "cvr": cvr,
      "ecpm": ecpm,
      "clarity": signals["claritySignal"],
      "trust": signals["trustSignal"],
      "caseAlignment": signals["caseAlignmentSignal"],
      "confidence": confidence,
      "riskAdjustedEcpm": ecpm * confidence,
    },
    industrial_features,
  )

  contributions = {
    "ctr": {key: ctr_contributions.get(key, 0) for key in signals},
    "cvr": {key: cvr_contributions.get(key, 0) for key in signals},
  }

  return {
    "metrics": metrics,
    "metricIntervals": intervals,
    "features": signals,
    "advancedFeatures": advanced_features,
    "industrialFeatures": industrial_features,
    "alignment": alignment,
    "contributions": contributions,
    "reasons": _build_reason_list(signals, campaign, case_context),
  }


def enrich_creatives(creatives: list[dict], campaign: dict, case_context: dict) -> list[dict]:
  enriched = []
  for index, creative in enumerate(creatives):
    scoring = score_creative(creative, campaign, case_context, seed=(index + 1) / 100)
    enriched.append(
      {
        **creative,
        "metrics": scoring["metrics"],
        "features": scoring["features"],
        "advancedFeatures": scoring["advancedFeatures"],
        "industrialFeatures": scoring["industrialFeatures"],
        "alignment": scoring["alignment"],
        "contributions": scoring["contributions"],
        "metricIntervals": scoring["metricIntervals"],
        "reasons": scoring["reasons"],
        "score": 0,
      }
    )
  return enriched


def build_surface_predictions(winner: dict, campaign: dict) -> dict:
  predictions = {}
  current_fit = CATEGORY_CONFIG[campaign["category"]]["platformFit"][campaign["platform"]]
  confidence = winner["metrics"].get("confidence", 0.8)
  for surface, label in PLATFORM_LABELS.items():
    fit = CATEGORY_CONFIG[campaign["category"]]["platformFit"][surface]
    surface_ctr = winner["metrics"]["ctr"] * (fit / current_fit)
    surface_cvr = winner["metrics"]["cvr"] * (0.96 + (fit - 1) * 0.6)
    surface_ecpm = surface_ctr * (1.4 + surface_cvr * 100) * CATEGORY_CONFIG[campaign["category"]]["bidFactor"] * 1000
    predictions[surface] = {
      "label": label,
      "fit": fit,
      "ctr": _clamp(surface_ctr, 0.004, 0.2),
      "cvr": _clamp(surface_cvr, 0.003, 0.12),
      "ctcvr": _clamp(surface_ctr, 0.004, 0.2) * _clamp(surface_cvr, 0.003, 0.12),
      "ecpm": surface_ecpm,
      "confidence": confidence,
      "riskAdjustedEcpm": surface_ecpm * confidence,
      "isCurrent": surface == campaign["platform"],
    }
  return predictions


def build_prediction_runtime() -> dict:
  return get_model_runtime()
