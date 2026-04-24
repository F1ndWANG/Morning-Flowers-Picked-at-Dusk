from backend.app.core.settings import get_integration_catalog
from backend.app.services.compliance_service import evaluate_compliance
from backend.app.services.generator_service import build_baseline, generate_creative_drafts, merge_campaign
from backend.app.services.image_generation_service import attach_image_prompts, maybe_generate_image_assets
from backend.app.services.llm_service import generate_text_creatives
from backend.app.services.multimodal_service import analyze_case_inputs
from backend.app.services.prompt_service import build_prompt_bundle
from backend.app.services.report_service import build_report
from backend.app.services.scoring_service import build_prediction_runtime, build_surface_predictions, score_creative
from backend.app.services.strategy_service import build_strategies


def run_pipeline(form: dict) -> dict:
  integration_info = get_integration_catalog()
  case_context, multimodal_trace = analyze_case_inputs(form)
  campaign = merge_campaign(form, case_context)
  prediction_runtime = build_prediction_runtime()

  baseline = build_baseline(campaign)
  baseline_scoring = score_creative(baseline, campaign, case_context, 0.01)
  baseline = {
    **baseline,
    "metrics": baseline_scoring["metrics"],
    "metricIntervals": baseline_scoring["metricIntervals"],
    "features": baseline_scoring["features"],
    "advancedFeatures": baseline_scoring["advancedFeatures"],
    "alignment": baseline_scoring["alignment"],
    "contributions": baseline_scoring["contributions"],
    "reasons": baseline_scoring["reasons"],
    "diversity": 0.22,
    "score": 0,
  }
  baseline["compliance"] = evaluate_compliance(baseline, campaign)
  baseline = attach_image_prompts([baseline], campaign, case_context)[0]

  template_drafts = generate_creative_drafts(campaign, case_context)
  drafts, text_trace = generate_text_creatives(campaign, case_context, template_drafts)
  strategies = build_strategies(campaign, baseline, drafts, case_context)
  active_strategy = strategies[campaign["experimentMode"]]

  if campaign["experimentMode"] == "baseline":
    baseline_winner = active_strategy["winner"]
    ranked_creatives = [
      {
        **baseline_winner,
        "surfacePredictions": build_surface_predictions(baseline_winner, campaign),
      }
    ]
    image_trace = {
      "mode": "baseline-prompt-only",
      "requestedMode": campaign["imageGenerationMode"],
      "provider": "prompt-template",
      "configured": False,
      "usedApi": False,
      "apiMarked": True,
      "note": "当前展示的是基础模板创意，只生成图片 Prompt。",
    }
  else:
    ranked_creatives, image_trace = maybe_generate_image_assets(active_strategy["creatives"], campaign, case_context)
    ranked_creatives = [
      {
        **creative,
        "surfacePredictions": build_surface_predictions(creative, campaign),
      }
      for creative in ranked_creatives
    ]
    active_strategy = {**active_strategy, "creatives": ranked_creatives, "winner": ranked_creatives[0]}
    strategies[campaign["experimentMode"]] = active_strategy

  surface_predictions = active_strategy["winner"].get("surfacePredictions") or build_surface_predictions(active_strategy["winner"], campaign)
  prompts = build_prompt_bundle(campaign, case_context, active_strategy["winner"])

  integration_info["multimodalUnderstanding"].update(multimodal_trace)
  integration_info["textGeneration"].update(text_trace)
  integration_info["imageGeneration"].update(image_trace)

  report = build_report(
    campaign,
    case_context,
    strategies,
    active_strategy,
    integration_info,
    surface_predictions,
  )

  return {
    "campaign": campaign,
    "case_context": case_context,
    "baseline": baseline,
    "strategies": strategies,
    "active_strategy": active_strategy,
    "ranked_creatives": ranked_creatives,
    "prompts": prompts,
    "report": report,
    "integration_info": integration_info,
    "surface_predictions": surface_predictions,
    "prediction_runtime": prediction_runtime,
  }
