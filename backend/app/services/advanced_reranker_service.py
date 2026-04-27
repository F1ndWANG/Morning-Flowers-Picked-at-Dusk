from backend.app.services.model_runtime_service import get_objective_weights
from backend.app.services.text_feature_utils import clamp, jaccard_text


def _creative_text(creative: dict) -> str:
  return " ".join(
    [
      creative.get("title", ""),
      creative.get("description", ""),
      creative.get("imageLine", ""),
      " ".join(creative.get("sellingPoints", [])),
    ]
  )


def creative_similarity(a: dict, b: dict) -> float:
  text_similarity = jaccard_text(_creative_text(a), _creative_text(b))
  angle_similarity = 1.0 if a.get("angle") and a.get("angle") == b.get("angle") else 0.0
  visual_similarity = 1.0 if a.get("visual") and a.get("visual") == b.get("visual") else 0.0
  title_similarity = jaccard_text(a.get("title", ""), b.get("title", ""))
  return clamp(text_similarity * 0.52 + title_similarity * 0.18 + angle_similarity * 0.18 + visual_similarity * 0.12, 0, 1)


def _safe_max(values: list[float]) -> float:
  return max(max(values), 1e-9)


def _dominates(a: dict, b: dict) -> bool:
  objectives = [
    a["metrics"]["ctr"] >= b["metrics"]["ctr"],
    a["metrics"]["cvr"] >= b["metrics"]["cvr"],
    a["metrics"].get("riskAdjustedEcpm", a["metrics"]["ecpm"]) >= b["metrics"].get("riskAdjustedEcpm", b["metrics"]["ecpm"]),
    a["metrics"].get("confidence", 0) >= b["metrics"].get("confidence", 0),
    a.get("alignment", {}).get("overallAlignment", 0) >= b.get("alignment", {}).get("overallAlignment", 0),
  ]
  strictly_better = [
    a["metrics"]["ctr"] > b["metrics"]["ctr"],
    a["metrics"]["cvr"] > b["metrics"]["cvr"],
    a["metrics"].get("riskAdjustedEcpm", a["metrics"]["ecpm"]) > b["metrics"].get("riskAdjustedEcpm", b["metrics"]["ecpm"]),
    a.get("alignment", {}).get("overallAlignment", 0) > b.get("alignment", {}).get("overallAlignment", 0),
  ]
  return all(objectives) and any(strictly_better)


def _pareto_bonus(candidate: dict, candidates: list[dict]) -> float:
  dominated_by = sum(1 for other in candidates if other.get("id") != candidate.get("id") and _dominates(other, candidate))
  dominates = sum(1 for other in candidates if other.get("id") != candidate.get("id") and _dominates(candidate, other))
  return clamp(0.055 + dominates * 0.012 - dominated_by * 0.018, 0, 0.09)


def _build_base_rank_items(candidates: list[dict], objective: str, diversity_weight: float) -> list[dict]:
  weights = get_objective_weights()[objective]
  max_ctr = _safe_max([item["metrics"]["ctr"] for item in candidates])
  max_cvr = _safe_max([item["metrics"]["cvr"] for item in candidates])
  max_ecpm = _safe_max([item["metrics"]["ecpm"] for item in candidates])
  max_risk_adjusted_ecpm = _safe_max([
    item["metrics"].get("riskAdjustedEcpm", item["metrics"]["ecpm"]) for item in candidates
  ])

  ranked = []
  for creative in candidates:
    metrics = creative["metrics"]
    features = creative.get("advancedFeatures", {})
    industrial = creative.get("industrialFeatures", {})
    alignment = creative.get("alignment", {})
    compliance = creative.get("compliance", {})

    ctr_component = (metrics["ctr"] / max_ctr) * weights["ctr"]
    cvr_component = (metrics["cvr"] / max_cvr) * weights["cvr"]
    ecpm_component = (metrics["ecpm"] / max_ecpm) * weights["ecpm"]
    risk_adjusted_component = (
      metrics.get("riskAdjustedEcpm", metrics["ecpm"]) / max_risk_adjusted_ecpm
    ) * 0.10
    quality_component = features.get("commercialQuality", 0.5) * 0.09
    alignment_component = alignment.get("overallAlignment", 0.3) * 0.08
    industrial_component = (
      industrial.get("dcnCrossScore", 0.5) * 0.045
      + industrial.get("multitaskConsistency", 0.5) * 0.045
      + industrial.get("userInterestProxy", 0.5) * 0.035
    )
    diversity_component = creative.get("diversity", 0.22) * diversity_weight
    pareto_component = _pareto_bonus(creative, candidates)
    risk_penalty = (
      features.get("conversionFriction", 0) * 0.035
      + features.get("riskCueDensity", 0) * 0.055
      + max(0, 0.70 - metrics.get("confidence", 0.70)) * 0.055
    )
    quality_factor = compliance.get("scoreFactor", 1)
    confidence_factor = 0.90 + metrics.get("confidence", 0.8) * 0.10
    base_score = (
      ctr_component
      + cvr_component
      + ecpm_component
      + risk_adjusted_component
      + quality_component
      + alignment_component
      + industrial_component
      + diversity_component
      + pareto_component
      - risk_penalty
    ) * quality_factor * confidence_factor

    ranked.append(
      {
        **creative,
        "score": base_score,
        "rankingBreakdown": {
          "ctrComponent": ctr_component,
          "cvrComponent": cvr_component,
          "ecpmComponent": ecpm_component,
          "riskAdjustedComponent": risk_adjusted_component,
          "qualityComponent": quality_component,
          "alignmentComponent": alignment_component,
          "industrialComponent": industrial_component,
          "diversityComponent": diversity_component,
          "paretoComponent": pareto_component,
          "riskPenalty": risk_penalty,
          "qualityFactor": quality_factor,
          "confidenceFactor": confidence_factor,
          "noveltyPenalty": 0,
          "maxSelectedSimilarity": 0,
          "baseScore": base_score,
          "finalScore": base_score,
        },
      }
    )
  return ranked


def rerank_creatives(candidates: list[dict], objective: str, diversity_weight: float) -> list[dict]:
  remaining = _build_base_rank_items(candidates, objective, diversity_weight)
  selected: list[dict] = []

  while remaining:
    best_index = 0
    best_candidate = remaining[0]
    best_score = float("-inf")

    for index, candidate in enumerate(remaining):
      max_similarity = max((creative_similarity(candidate, item) for item in selected), default=0.0)
      novelty_penalty = max_similarity * max(diversity_weight, 0.04) * 0.58
      final_score = candidate["rankingBreakdown"]["baseScore"] - novelty_penalty
      if final_score > best_score:
        best_score = final_score
        best_index = index
        best_candidate = {
          **candidate,
          "score": final_score,
          "rankingBreakdown": {
            **candidate["rankingBreakdown"],
            "noveltyPenalty": novelty_penalty,
            "maxSelectedSimilarity": max_similarity,
            "finalScore": final_score,
          },
        }

    selected.append(best_candidate)
    remaining.pop(best_index)

  return [{**creative, "rank": index + 1} for index, creative in enumerate(selected)]
