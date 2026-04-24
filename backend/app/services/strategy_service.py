import re

from backend.app.core.catalog import CATEGORY_CONFIG
from backend.app.services.advanced_reranker_service import creative_similarity, rerank_creatives
from backend.app.services.compliance_service import attach_compliance
from backend.app.services.diagnosis_service import build_creative_diagnosis
from backend.app.services.scoring_service import enrich_creatives


def _tokenize(text: str) -> set[str]:
  return {item.strip().lower() for item in re.split(r"[\s,\n.;:!?，。；：！？]+", text) if item.strip()}


def _creative_text(creative: dict) -> str:
  return f"{creative['title']} {creative['description']} {creative['imageLine']} {' '.join(creative['sellingPoints'])}"


def _jaccard(a: set[str], b: set[str]) -> float:
  union = a | b
  return len(a & b) / len(union) if union else 0


def _creative_similarity(a: dict, b: dict) -> float:
  return creative_similarity(a, b)


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


def attach_diagnosis(creatives: list[dict], campaign: dict, case_context: dict) -> list[dict]:
  return [
    {
      **creative,
      "diagnosis": build_creative_diagnosis(creative, campaign, case_context),
    }
    for creative in creatives
  ]


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
  predictive_only = attach_diagnosis(predictive_only, campaign, case_context)
  full_ranked = attach_diagnosis(full_ranked, campaign, case_context)
  diversified = attach_diagnosis(diversified, campaign, case_context)
  baseline_with_diagnosis = attach_diagnosis([baseline], campaign, case_context)[0]
  llm_only_winner = {**diversified[0], "rank": 1, "score": 0}
  angle_count = len(CATEGORY_CONFIG[campaign["category"]]["angles"])

  return {
    "baseline": _build_strategy_payload(
      "baseline",
      "Baseline Only",
      "Only output the baseline template creative without expansion or rerank.",
      baseline_with_diagnosis,
      [baseline_with_diagnosis],
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
