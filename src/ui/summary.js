import { CATEGORY_CONFIG } from "../config/catalog.js";
import { formatLift, formatPercent, strategyText } from "../utils/format.js";
import { buildMetricBars, renderReasonList } from "./metrics.js";

export function renderSummary(dom, form, baseline, activeStrategy, rankedCreatives) {
  const topCreative = activeStrategy.winner;
  const coverageAngles = new Set(rankedCreatives.map((item) => item.angle)).size;
  const coverage = coverageAngles / CATEGORY_CONFIG[form.category].angles.length;

  dom.topCtr.textContent = formatPercent(topCreative.metrics.ctr);
  dom.topCvr.textContent = formatPercent(topCreative.metrics.cvr);
  dom.topEcpm.textContent = topCreative.metrics.ecpm.toFixed(1);
  dom.ctrLift.textContent = `相对 Baseline ${formatLift(topCreative.metrics.ctr, baseline.metrics.ctr)}`;
  dom.cvrLift.textContent = `相对 Baseline ${formatLift(topCreative.metrics.cvr, baseline.metrics.cvr)}`;
  dom.ecpmLift.textContent = `相对 Baseline ${formatLift(topCreative.metrics.ecpm, baseline.metrics.ecpm)}`;
  dom.diversityScore.textContent = (topCreative.diversity ?? 0.22).toFixed(2);
  dom.coverageText.textContent = `覆盖 ${coverageAngles} 个创意角度`;
  dom.heroCandidates.textContent = String(Math.max(rankedCreatives.length, 1)).padStart(2, "0");
  dom.heroStrategy.textContent = strategyText(form.experimentMode);
  dom.heroCoverage.textContent = `${(coverage * 100).toFixed(0)}%`;

  dom.baselineName.textContent = baseline.title;
  dom.winnerName.textContent = topCreative.title;
  dom.baselineCopy.textContent = baseline.description;
  dom.winnerCopy.textContent = topCreative.description;

  buildMetricBars({ ...baseline.metrics, diversity: 0.22 }, dom.baselineBars);
  buildMetricBars({ ...topCreative.metrics, diversity: topCreative.diversity ?? 0.22 }, dom.winnerBars);

  renderReasonList(dom.winnerReasons, topCreative.reasons.slice(0, 6), (text) => `<span>${text}</span>`);
  const topFeatures = Object.entries(topCreative.contributions)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
  renderReasonList(
    dom.featureBreakdown,
    topFeatures,
    ([name, value]) => `<span>${name}</span><strong>+${(value * 100).toFixed(2)}bp</strong>`
  );
}
