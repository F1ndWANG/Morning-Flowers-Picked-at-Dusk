import { formatPercent, objectiveText, strategyText } from "../utils/format.js";

export function renderQualityPanel(dom, form, activeStrategy) {
  const winner = activeStrategy.winner;
  const compliance = winner.compliance ?? {
    riskLevel: "低",
    scoreFactor: 1,
    issues: [],
    passes: []
  };

  dom.qualityList.innerHTML = "";
  const summary = document.createElement("div");
  summary.className = "quality-summary";
  summary.innerHTML = `
    <div class="quality-metric">
      <small>风险等级</small>
      <strong>${compliance.riskLevel}</strong>
    </div>
    <div class="quality-metric">
      <small>质量因子</small>
      <strong>${compliance.scoreFactor.toFixed(2)}</strong>
    </div>
    <div class="quality-metric">
      <small>实验策略</small>
      <strong>${strategyText(form.experimentMode)}</strong>
    </div>
    <div class="quality-metric">
      <small>投放目标</small>
      <strong>${objectiveText(form.objective)}</strong>
    </div>
  `;
  dom.qualityList.appendChild(summary);

  const items = [
    ...compliance.passes.map((text) => ({ type: "pass", text })),
    ...compliance.issues.map((item) => ({ type: "issue", text: item.message }))
  ];
  if (items.length === 0) {
    items.push({ type: "pass", text: "当前文案未命中明显风险规则。" });
  }

  const detailList = document.createElement("div");
  detailList.className = "quality-detail-list";
  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = `quality-item ${item.type}`;
    node.textContent = item.text;
    detailList.appendChild(node);
  });
  dom.qualityList.appendChild(detailList);
}

export function renderHistoryPanel(dom, history) {
  dom.historyList.innerHTML = "";

  if (history.length === 0) {
    const empty = document.createElement("div");
    empty.className = "history-empty";
    empty.textContent = "还没有实验记录。点击“生成并优选创意”后会自动保存最近实验。";
    dom.historyList.appendChild(empty);
    return;
  }

  history.forEach((record) => {
    const item = document.createElement("article");
    item.className = "history-item";
    item.innerHTML = `
      <div class="history-head">
        <strong>${record.brandName} ${record.productName}</strong>
        <span>${record.createdAt}</span>
      </div>
      <p class="history-title">${record.winnerTitle}</p>
      <div class="history-metrics">
        <span>${strategyText(record.experimentMode)}</span>
        <span>CTR ${formatPercent(record.ctr)}</span>
        <span>CVR ${formatPercent(record.cvr)}</span>
        <span>eCPM ${record.ecpm.toFixed(1)}</span>
        <span>风险 ${record.riskLevel}</span>
      </div>
    `;
    dom.historyList.appendChild(item);
  });
}
