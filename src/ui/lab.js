import { STRATEGY_ORDER } from "../config/catalog.js";
import { simulateTraffic } from "../core/simulation.js";
import { formatInteger, formatLift, formatPercent } from "../utils/format.js";

export function renderStrategyCards(dom, form, strategies) {
  const baselineWinner = strategies.baseline.winner;
  dom.strategyGrid.innerHTML = "";

  STRATEGY_ORDER.forEach((key) => {
    const strategy = strategies[key];
    const winner = strategy.winner;
    const card = document.createElement("article");
    card.className = `strategy-card${form.experimentMode === key ? " active" : ""}`;
    card.innerHTML = `
      <div class="strategy-head">
        <div>
          <span>${strategy.description}</span>
          <strong>${strategy.label}</strong>
        </div>
        <span>${key === "baseline" ? "Control" : "Experiment"}</span>
      </div>
      <div class="strategy-metrics">
        <div class="strategy-metric"><small>CTR</small><strong>${formatPercent(winner.metrics.ctr)}</strong></div>
        <div class="strategy-metric"><small>CVR</small><strong>${formatPercent(winner.metrics.cvr)}</strong></div>
        <div class="strategy-metric"><small>eCPM</small><strong>${winner.metrics.ecpm.toFixed(1)}</strong></div>
        <div class="strategy-metric"><small>Coverage</small><strong>${(strategy.metrics.coverageRate * 100).toFixed(0)}%</strong></div>
        <div class="strategy-metric"><small>Avg Diversity</small><strong>${strategy.metrics.averageDiversity.toFixed(2)}</strong></div>
        <div class="strategy-metric"><small>vs Baseline</small><strong>${key === "baseline" ? "0.0%" : formatLift(winner.metrics.ctr, baselineWinner.metrics.ctr)}</strong></div>
      </div>
    `;
    dom.strategyGrid.appendChild(card);
  });
}

export function renderSimulationBoard(dom, form, strategies) {
  dom.simulationBoard.innerHTML = "";
  const active = strategies[form.experimentMode];
  const baseline = strategies.baseline.winner;
  const baselineSim = simulateTraffic(baseline, form);
  const activeSim = simulateTraffic(active.winner, form);

  const card = document.createElement("article");
  card.className = "sim-card";
  card.innerHTML = `
    <span>Online Traffic Simulation</span>
    <strong>${active.label}</strong>
    <div class="sim-card-grid">
      <div><small>曝光量</small><strong>${formatInteger(activeSim.impressions)}</strong></div>
      <div><small>Baseline 点击</small><strong>${baselineSim.clicks}</strong></div>
      <div><small>Baseline 转化</small><strong>${baselineSim.conversions}</strong></div>
      <div><small>Winner 点击</small><strong>${activeSim.clicks}</strong></div>
      <div><small>Winner 转化</small><strong>${activeSim.conversions}</strong></div>
      <div><small>Baseline GMV</small><strong>${baselineSim.grossMerchandise.toFixed(0)}</strong></div>
      <div><small>Winner GMV</small><strong>${activeSim.grossMerchandise.toFixed(0)}</strong></div>
      <div><small>增量 GMV</small><strong>${(activeSim.grossMerchandise - baselineSim.grossMerchandise).toFixed(0)}</strong></div>
      <div><small>Winner ROI</small><strong>${activeSim.roi.toFixed(2)}</strong></div>
    </div>
  `;
  dom.simulationBoard.appendChild(card);
}
