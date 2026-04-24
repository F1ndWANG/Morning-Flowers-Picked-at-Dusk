from backend.app.services.text_feature_utils import clamp, overlap_ratio


def evaluate_multimodal_alignment(creative: dict, campaign: dict, case_context: dict) -> dict:
  selling_points = " ".join(creative.get("sellingPoints", []))
  creative_text = " ".join(
    [
      creative.get("title", ""),
      creative.get("description", ""),
      creative.get("imageLine", ""),
      selling_points,
    ]
  )
  context_text = " ".join(
    [
      campaign.get("caseSummary", ""),
      case_context.get("caseSummary", ""),
      case_context.get("assetSummary", ""),
      case_context.get("transcriptText", ""),
      " ".join(case_context.get("caseSignals", [])),
    ]
  )
  image_prompt_text = " ".join(
    [
      creative.get("imagePrompt", ""),
      creative.get("imageLine", ""),
      " ".join(str(value) for value in creative.get("imagePromptDimensions", {}).values()),
    ]
  )

  selling_point_coverage = overlap_ratio(" ".join(campaign.get("highlights", [])), creative_text)
  case_semantic_alignment = max(overlap_ratio(context_text, creative_text), overlap_ratio(creative_text, context_text))
  audience_alignment = overlap_ratio(campaign.get("audience", ""), creative_text)
  image_copy_alignment = max(overlap_ratio(creative_text, image_prompt_text), overlap_ratio(selling_points, image_prompt_text))
  prompt_dimensions = creative.get("imagePromptDimensions", {})
  visual_prompt_completeness = len([value for value in prompt_dimensions.values() if value]) / 8 if prompt_dimensions else 0.35
  multimodal_grounding = max(
    overlap_ratio(case_context.get("assetSummary", ""), creative_text),
    overlap_ratio(case_context.get("transcriptText", ""), creative_text),
  )

  overall = clamp(
    selling_point_coverage * 0.24
    + case_semantic_alignment * 0.22
    + audience_alignment * 0.14
    + image_copy_alignment * 0.18
    + visual_prompt_completeness * 0.12
    + multimodal_grounding * 0.10,
    0,
    1,
  )

  return {
    "sellingPointCoverage": selling_point_coverage,
    "caseSemanticAlignment": case_semantic_alignment,
    "audienceAlignment": audience_alignment,
    "imageCopyAlignment": image_copy_alignment,
    "visualPromptCompleteness": visual_prompt_completeness,
    "multimodalGrounding": multimodal_grounding,
    "overallAlignment": overall,
  }
