import { simulateTraffic } from "./simulation.js";
import { formatInteger, formatLift, formatPercent, objectiveText, platformText, strategyText } from "../utils/format.js";

export function buildReport(form, strategies, activeStrategy, integrationInfo) {
  const baseline = strategies.baseline.winner;
  const winner = activeStrategy.winner;
  const baselineSim = simulateTraffic(baseline, form);
  const winnerSim = simulateTraffic(winner, form);

  return [
    "# AIGC 广告创意生成与优选项目报告",
    "",
    "## 1. 项目目标",
    `针对 ${form.productName} 在 ${platformText(form.platform)} 渠道的投放需求，使用 LLM 生成多版本创意池，再通过 CTR/CVR/eCPM 预估与多目标排序选出更优广告。`,
    "",
    "## 2. 当前配置",
    `- 商品：${form.brandName} ${form.productName}`,
    `- 类目：${form.category}`,
    `- 人群：${form.audience}`,
    `- 目标：${objectiveText(form.objective)}`,
    `- 实验模式：${strategyText(form.experimentMode)}`,
    `- 文本生成模式：${form.textGenerationMode}`,
    `- 图片生成模式：${form.imageGenerationMode}`,
    `- 卖点：${form.highlights.join("、")}`,
    "",
    "## 3. 方法设计",
    "- 生成层：支持模板生成与真实 LLM API，两种模式都输出标题、描述、卖点和图片文案。",
    "- 评估层：基于可解释特征预测 CTR、CVR、eCPM。",
    "- 优选层：按目标做多目标加权排序，并加入多样性约束与质量门控。",
    "- 视觉层：支持图片 Prompt 生成，并预留文生图 API 接口位。",
    "",
    "## 4. 实验结果",
    `- Baseline CTR：${formatPercent(baseline.metrics.ctr)} / CVR：${formatPercent(baseline.metrics.cvr)} / eCPM：${baseline.metrics.ecpm.toFixed(1)}`,
    `- Winner CTR：${formatPercent(winner.metrics.ctr)} / CVR：${formatPercent(winner.metrics.cvr)} / eCPM：${winner.metrics.ecpm.toFixed(1)}`,
    `- CTR 提升：${formatLift(winner.metrics.ctr, baseline.metrics.ctr)}`,
    `- CVR 提升：${formatLift(winner.metrics.cvr, baseline.metrics.cvr)}`,
    `- eCPM 提升：${formatLift(winner.metrics.ecpm, baseline.metrics.ecpm)}`,
    `- 创意覆盖率：${(activeStrategy.metrics.coverageRate * 100).toFixed(0)}%`,
    `- 平均多样性：${activeStrategy.metrics.averageDiversity.toFixed(2)}`,
    "",
    "## 5. 在线模拟",
    `- 曝光量：${formatInteger(winnerSim.impressions)}`,
    `- Baseline 点击 / 转化：${baselineSim.clicks} / ${baselineSim.conversions}`,
    `- Winner 点击 / 转化：${winnerSim.clicks} / ${winnerSim.conversions}`,
    `- Baseline GMV：${baselineSim.grossMerchandise.toFixed(0)} 元`,
    `- Winner GMV：${winnerSim.grossMerchandise.toFixed(0)} 元`,
    `- Winner ROI：${winnerSim.roi.toFixed(2)}`,
    "",
    "## 6. API 接入位",
    `- 文本大模型：${integrationInfo.textGeneration.note}`,
    `- 文生图接口：${integrationInfo.imageGeneration.note}`,
    "",
    "## 7. Top1 创意",
    `- 标题：${winner.title}`,
    `- 描述：${winner.description}`,
    `- 图片文案：${winner.imageLine}`,
    `- 主要卖点：${winner.sellingPoints.join("、")}`,
    `- 图片 Prompt：${winner.imagePrompt ?? "未生成"}`,
    `- 入选原因：${winner.reasons.join("；")}`
  ].join("\n");
}
