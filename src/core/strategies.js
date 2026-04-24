import { attachCompliance } from "./compliance.js";
import { applyDiversityPenalty, enrichCreatives, rerankCreatives } from "./scoring.js";

function buildStrategyPayload(key, label, description, winner, creatives, angleCount) {
  const coverageAngles = new Set(creatives.map((creative) => creative.angle)).size || 1;
  const averageDiversity = creatives.length
    ? creatives.reduce((sum, item) => sum + (item.diversity ?? 0.22), 0) / creatives.length
    : 0.22;

  return {
    key,
    label,
    description,
    winner,
    creatives,
    metrics: {
      coverageAngles,
      coverageRate: angleCount ? coverageAngles / angleCount : 0,
      averageDiversity
    }
  };
}

export function buildStrategies(form, baseline, drafts) {
  const enriched = enrichCreatives(drafts, form);
  const complianceChecked = attachCompliance(enriched, form);
  const diversified = applyDiversityPenalty(complianceChecked);
  const angleCount = new Set(diversified.map((item) => item.angle)).size || 1;

  const llmOnlyWinner = {
    ...diversified[0],
    rank: 1,
    score: 0
  };

  const predictiveOnlyList = rerankCreatives(
    diversified.map((item) => ({ ...item, diversity: 0.22 })),
    form.objective,
    0
  );

  const fullPipelineList = rerankCreatives(diversified, form.objective, form.diversityWeight);

  return {
    baseline: buildStrategyPayload("baseline", "Baseline Only", "单模板广告，不做生成与排序。", baseline, [baseline], angleCount),
    "llm-only": buildStrategyPayload("llm-only", "LLM Only", "只生成，不做效果预估和 rerank。", llmOnlyWinner, diversified, angleCount),
    "predictive-only": buildStrategyPayload(
      "predictive-only",
      "Generate + Predict",
      "生成候选后仅按预估分排序，不加多样性约束。",
      predictiveOnlyList[0],
      predictiveOnlyList,
      angleCount
    ),
    full: buildStrategyPayload(
      "full",
      "Full Pipeline",
      "生成 + 预估 + 多样性 rerank。",
      fullPipelineList[0],
      fullPipelineList,
      angleCount
    )
  };
}
