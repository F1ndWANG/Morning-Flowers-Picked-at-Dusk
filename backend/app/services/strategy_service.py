import re

from backend.app.core.catalog import CATEGORY_CONFIG
from backend.app.services.compliance_service import attach_compliance
from backend.app.services.model_runtime_service import get_objective_weights
from backend.app.services.scoring_service import enrich_creatives


def _tokenize(text: str) -> set[str]:
  return {item.strip().lower() for item in re.split(r"[\s,\n.;:!?，。；：！？]+", text) if item.strip()}


def _creative_text(creative: dict) -> str:
  return f"{creative['title']} {creative['description']} {creative['imageLine']} {' '.join(creative['sellingPoints'])}"


def _jaccard(a: set[str], b: set[str]) -> float:
  union = a | b
  return len(a & b) / len(union) if union else 0


def _creative_similarity(a: dict, b: dict) -> float:
  text_similarity = _jaccard(_tokenize(_creative_text(a)), _tokenize(_creative_text(b)))
  angle_similarity = 1.0 if a.get("angle") and a.get("angle") == b.get("angle") else 0.0
  visual_similarity = 1.0 if a.get("visual") and a.get("visual") == b.get("visual") else 0.0
  return min(1.0, text_similarity * 0.70 + angle_similarity * 0.18 + visual_similarity * 0.12)


def apply_diversity_penalty(candidates: list[dict]) -> list[dict]:
  diversified = []
  for creative in candidates:
    max_similarity = 0.0
    for other in candidates:
      if other["id"] == creative["id"]:
        continue
      max_similarity = max(max_similarity, _creative_similarity(creative, other))
    diversified.append({**creative, "diversity": max(0.18, 1 - max_similarity)})
  return diversified


def _build_base_rank_items(candidates: list[dict], objective: str, diversity_weight: float) -> list[dict]:
  weights = get_objective_weights()[objective]
  max_ctr = max(item["metrics"]["ctr"] for item in candidates)
  max_cvr = max(item["metrics"]["cvr"] for item in candidates)
  max_ecpm = max(item["metrics"]["ecpm"] for item in candidates)
  max_risk_adjusted_ecpm = max(item["metrics"].get("riskAdjustedEcpm", item["metrics"]["ecpm"]) for item in candidates)

  ranked = []
  for creative in candidates:
    ctr_component = (creative["metrics"]["ctr"] / max_ctr) * weights["ctr"]
    cvr_component = (creative["metrics"]["cvr"] / max_cvr) * weights["cvr"]
    ecpm_component = (creative["metrics"]["ecpm"] / max_ecpm) * weights["ecpm"]
    risk_adjusted_component = (
      creative["metrics"].get("riskAdjustedEcpm", creative["metrics"]["ecpm"]) / max_risk_adjusted_ecpm
    ) * 0.08
    diversity_component = creative.get("diversity", 0.22) * diversity_weight
    quality_factor = creative["compliance"]["scoreFactor"]
    confidence_factor = 0.92 + creative["metrics"].get("confidence", 0.8) * 0.08
    base_score = (
      ctr_component
      + cvr_component
      + ecpm_component
      + risk_adjusted_component
      + diversity_component
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
          "diversityComponent": diversity_component,
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
      max_similarity = max((_creative_similarity(candidate, item) for item in selected), default=0.0)
      novelty_penalty = max_similarity * diversity_weight * 0.45
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


def _build_strategy_payload(key: str, label: str, description: str, winner: dict, creatives: list[dict], angle_count: int) -> dict:
  coverage_angles = len({item["angle"] for item in creatives}) if creatives else 1
  coverage_rate = coverage_angles / max(1, angle_count)
  average_diversity = sum(item.get("diversity", 0.22) for item in creatives) / max(1, len(creatives))
  average_confidence = sum(item.get("metrics", {}).get("confidence", 0) for item in creatives) / max(1, len(creatives))
  return {
    "key": key,
    "label": label,
    "description": description,
    "winner": winner,
    "creatives": creatives,
    "metrics": {
      "coverageAngles": coverage_angles,
      "coverageRate": coverage_rate,
      "creativeCoverage": len(creatives),
      "averageDiversity": average_diversity,
      "averageConfidence": average_confidence,
    },
  }


def build_strategies(campaign: dict, baseline: dict, drafts: list[dict], case_context: dict) -> dict:
  enriched = enrich_creatives(drafts, campaign, case_context)
  with_compliance = attach_compliance(enriched, campaign)
  diversified = apply_diversity_penalty(with_compliance)
  predictive_only = rerank_creatives([{**item, "diversity": 0.22} for item in diversified], campaign["objective"], 0)
  full_ranked = rerank_creatives(diversified, campaign["objective"], campaign["diversityWeight"])
  llm_only_winner = {**diversified[0], "rank": 1, "score": 0}
  angle_count = len(CATEGORY_CONFIG[campaign["category"]]["angles"])

  return {
    "baseline": _build_strategy_payload(
      "baseline",
      "Baseline Only",
      "Only output the baseline template creative without expansion or rerank.",
      baseline,
      [baseline],
      angle_count,
    ),
    "llm-only": _build_strategy_payload(
      "llm-only",
      "LLM Only",
      "Generate creatives only, without predictive ranking.",
      llm_only_winner,
      diversified,
      angle_count,
    ),
    "predictive-only": _build_strategy_payload(
      "predictive-only",
      "Generate + Predict",
      "Generate multiple creatives and rank them by CTR, CVR, and eCPM prediction.",
      predictive_only[0],
      predictive_only,
      angle_count,
    ),
    "full": _build_strategy_payload(
      "full",
      "Full Pipeline",
      "Generation, prediction, compliance gating, confidence scoring, and MMR diversity-aware rerank.",
      full_ranked[0],
      full_ranked,
      angle_count,
    ),
  }
