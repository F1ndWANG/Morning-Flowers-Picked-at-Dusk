const RISK_RULES = [
  {
    key: "absolute_claim",
    label: "绝对化表述",
    pattern: /(最强|第一|顶级|永久|100%|绝对|稳赚|保过|包过)/,
    penalty: 0.12,
    message: "包含绝对化或结果承诺词，存在审核风险。"
  },
  {
    key: "medical_claim",
    label: "医疗宣称",
    pattern: /(治疗|治愈|药用|医美级|医疗级|处方|根治)/,
    penalty: 0.16,
    message: "包含偏医疗或功效过强的表述，需要人工复核。"
  },
  {
    key: "finance_claim",
    label: "收益承诺",
    pattern: /(稳赚|保本|躺赚|稳赚不赔)/,
    penalty: 0.18,
    message: "包含收益承诺，可能触发金融类风控。"
  }
];

export function evaluateCompliance(creative, form) {
  const text = `${creative.title} ${creative.description} ${creative.imageLine}`;
  const issues = [];

  RISK_RULES.forEach((rule) => {
    if (rule.pattern.test(text)) {
      issues.push({
        key: rule.key,
        label: rule.label,
        penalty: rule.penalty,
        message: rule.message
      });
    }
  });

  if (creative.title.length > 28) {
    issues.push({
      key: "length",
      label: "标题过长",
      penalty: 0.06,
      message: "标题长度偏长，可能影响首屏阅读效率。"
    });
  }

  if (!text.includes(form.brandName)) {
    issues.push({
      key: "brand_visibility",
      label: "品牌露出不足",
      penalty: 0.04,
      message: "品牌词未充分露出，可记忆性和可信度偏弱。"
    });
  }

  const riskPenalty = issues.reduce((sum, issue) => sum + issue.penalty, 0);
  const scoreFactor = Math.max(0.55, 1 - riskPenalty);
  const riskLevel = riskPenalty >= 0.25 ? "高" : riskPenalty >= 0.12 ? "中" : "低";

  const passes = [
    text.includes(form.brandName) ? "品牌露出清晰" : null,
    /\d/.test(text) ? "利益点带数字支撑" : null,
    issues.length === 0 ? "未命中高风险规则" : null,
    creative.sellingPoints.length >= 3 ? "卖点结构完整" : null
  ].filter(Boolean);

  return {
    riskPenalty,
    scoreFactor,
    riskLevel,
    issues,
    passes
  };
}

export function attachCompliance(candidates, form) {
  return candidates.map((candidate) => ({
    ...candidate,
    compliance: evaluateCompliance(candidate, form)
  }));
}
