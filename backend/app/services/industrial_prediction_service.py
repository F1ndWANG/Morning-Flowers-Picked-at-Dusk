from backend.app.core.catalog import CATEGORY_CONFIG
from backend.app.services.text_feature_utils import clamp, saturation


SURFACE_INTENT_PRIORS = {
  "search": {
    "intent": 0.92,
    "conversion": 0.82,
    "exploration": 0.42,
  },
  "feed": {
    "intent": 0.62,
    "conversion": 0.58,
    "exploration": 0.78,
  },
  "video": {
    "intent": 0.52,
    "conversion": 0.48,
    "exploration": 0.88,
  },
  "mall": {
    "intent": 0.84,
    "conversion": 0.86,
    "exploration": 0.46,
  },
}

CATEGORY_VALUE_PRIORS = {
  "beauty": {
    "ctr": 0.68,
    "cvr": 0.74,
  },
  "appliance": {
    "ctr": 0.58,
    "cvr": 0.70,
  },
  "education": {
    "ctr": 0.56,
    "cvr": 0.64,
  },
  "sports": {
    "ctr": 0.66,
    "cvr": 0.62,
  },
}


def _safe_average(values: list[float]) -> float:
  return sum(values) / max(1, len(values))


def _surface_prior(campaign: dict) -> dict:
  return SURFACE_INTENT_PRIORS.get(campaign.get("platform"), SURFACE_INTENT_PRIORS["feed"])


def _category_prior(campaign: dict) -> dict:
  return CATEGORY_VALUE_PRIORS.get(campaign.get("category"), CATEGORY_VALUE_PRIORS["beauty"])


def _build_cross_features(signals: dict, advanced: dict, alignment: dict, campaign: dict, case_context: dict) -> dict:
  surface_prior = _surface_prior(campaign)
  category_prior = _category_prior(campaign)
  modality_stats = case_context.get("modalityStats", {})

  memorization_cross = _safe_average(
    [
      signals["brandSignal"] * signals["highlightSignal"],
      signals["trustSignal"] * signals["priceSignal"],
      signals["ctaSignal"] * surface_prior["conversion"],
      advanced["brandConsistency"] * category_prior["cvr"],
    ]
  )
  generalization_cross = _safe_average(
    [
      advanced["hookStrength"] * surface_prior["exploration"],
      advanced["platformIntentFit"] * signals["audienceSignal"],
      alignment["overallAlignment"] * signals["caseAlignmentSignal"],
      advanced["emotionalIntensity"] * category_prior["ctr"],
    ]
  )
  fm_interaction_score = _safe_average(
    [
      advanced["sellingPointDensity"] * advanced["trustDepth"],
      advanced["readability"] * signals["claritySignal"],
      advanced["imageCopyConsistency"] * alignment["imageCopyAlignment"],
      signals["assetSignal"] * alignment.get("multimodalGrounding", alignment["overallAlignment"]),
    ]
  )
  dcn_cross_score = clamp(
    memorization_cross * 0.34
    + generalization_cross * 0.34
    + fm_interaction_score * 0.24
    + saturation(modality_stats.get("totalAssetCount", 0), 3) * 0.08,
    0,
    1,
  )

  return {
    "memorizationCross": clamp(memorization_cross, 0, 1),
    "generalizationCross": clamp(generalization_cross, 0, 1),
    "fmInteractionScore": clamp(fm_interaction_score, 0, 1),
    "dcnCrossScore": dcn_cross_score,
  }


def _build_multitask_signals(signals: dict, advanced: dict, alignment: dict, campaign: dict) -> dict:
  surface_prior = _surface_prior(campaign)
  category_prior = _category_prior(campaign)

  click_task_score = clamp(
    advanced["hookStrength"] * 0.28
    + advanced["emotionalIntensity"] * 0.18
    + signals["urgencySignal"] * 0.16
    + signals["claritySignal"] * 0.15
    + surface_prior["exploration"] * 0.13
    + category_prior["ctr"] * 0.10,
    0,
    1,
  )
  conversion_task_score = clamp(
    advanced["trustDepth"] * 0.25
    + advanced["sellingPointDensity"] * 0.20
    + signals["priceSignal"] * 0.14
    + signals["ctaSignal"] * 0.14
    + alignment["overallAlignment"] * 0.12
    + surface_prior["conversion"] * 0.10
    + category_prior["cvr"] * 0.05,
    0,
    1,
  )
  task_balance = 1 - abs(click_task_score - conversion_task_score)
  multitask_consistency = clamp(
    task_balance * 0.48
    + min(click_task_score, conversion_task_score) * 0.34
    + (1 - advanced["conversionFriction"]) * 0.18,
    0,
    1,
  )

  return {
    "clickTaskScore": click_task_score,
    "conversionTaskScore": conversion_task_score,
    "multitaskConsistency": multitask_consistency,
  }


def build_industrial_prediction_signals(
  creative: dict,
  campaign: dict,
  case_context: dict,
  signals: dict,
  advanced: dict,
  alignment: dict,
) -> dict:
  cross_features = _build_cross_features(signals, advanced, alignment, campaign, case_context)
  multitask = _build_multitask_signals(signals, advanced, alignment, campaign)
  surface_prior = _surface_prior(campaign)

  user_interest_proxy = clamp(
    signals["audienceSignal"] * 0.26
    + signals["caseAlignmentSignal"] * 0.22
    + signals["multimodalAlignmentSignal"] * 0.20
    + advanced["platformIntentFit"] * 0.18
    + surface_prior["intent"] * 0.14,
    0,
    1,
  )
  calibration_factor = clamp(
    0.92
    + cross_features["dcnCrossScore"] * 0.10
    + multitask["multitaskConsistency"] * 0.08
    + user_interest_proxy * 0.06
    - advanced["riskCueDensity"] * 0.08
    - advanced["conversionFriction"] * 0.06,
    0.82,
    1.18,
  )

  return {
    **cross_features,
    **multitask,
    "surfaceIntentScore": surface_prior["intent"],
    "surfaceConversionScore": surface_prior["conversion"],
    "userInterestProxy": user_interest_proxy,
    "calibrationFactor": calibration_factor,
    "servingArchitecture": "wide-deep-dcn-esmm-proxy",
  }


def attach_esmm_outputs(metrics: dict, industrial: dict) -> dict:
  ctr = metrics["ctr"]
  cvr = metrics["cvr"]
  ctcvr = ctr * cvr
  post_click_cvr = clamp(cvr, 0.001, 0.95)
  esmm_consistency = clamp(
    industrial["multitaskConsistency"] * 0.55
    + industrial["calibrationFactor"] * 0.25
    + (1 - abs(industrial["clickTaskScore"] - industrial["conversionTaskScore"])) * 0.20,
    0,
    1,
  )
  return {
    **metrics,
    "ctcvr": ctcvr,
    "postClickCvr": post_click_cvr,
    "esmmConsistency": esmm_consistency,
  }
