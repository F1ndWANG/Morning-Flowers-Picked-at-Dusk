def _add_if(items: list[str], condition: bool, text: str) -> None:
  if condition:
    items.append(text)


def build_creative_diagnosis(creative: dict, campaign: dict, case_context: dict) -> dict:
  metrics = creative.get("metrics", {})
  features = creative.get("advancedFeatures", {})
  industrial = creative.get("industrialFeatures", {})
  alignment = creative.get("alignment", {})
  compliance = creative.get("compliance", {})
  breakdown = creative.get("rankingBreakdown", {})

  strengths: list[str] = []
  risks: list[str] = []
  recommendations: list[str] = []

  _add_if(strengths, features.get("hookStrength", 0) >= 0.68, "标题钩子强，具备较好的点击触发能力。")
  _add_if(strengths, features.get("sellingPointDensity", 0) >= 0.55, "核心卖点覆盖充分，信息密度较高。")
  _add_if(strengths, features.get("trustDepth", 0) >= 0.62, "文案包含信任背书，有利于转化。")
  _add_if(strengths, alignment.get("overallAlignment", 0) >= 0.35, "创意与任务上下文/素材信息保持一致。")
  _add_if(strengths, industrial.get("dcnCrossScore", 0) >= 0.52, "交叉特征表现较好，具备 Wide&Deep/DCN 类精排加分信号。")
  _add_if(strengths, industrial.get("multitaskConsistency", 0) >= 0.58, "点击与转化任务一致性较高，符合 ESMM/MMoE 多任务排序偏好。")
  _add_if(strengths, metrics.get("riskAdjustedEcpm", 0) >= metrics.get("ecpm", 0) * 0.75, "风险调整收益保持稳定。")

  _add_if(risks, features.get("conversionFriction", 0) >= 0.55, "转化阻力偏高，可能缺少明确行动理由或信任信息。")
  _add_if(risks, features.get("riskCueDensity", 0) > 0, "存在夸大或绝对化表达风险，需要合规复核。")
  _add_if(risks, alignment.get("imageCopyAlignment", 0) < 0.18, "图片文案与标题/卖点一致性不足。")
  _add_if(risks, industrial.get("multitaskConsistency", 1) < 0.42, "CTR 点击信号不能有效转化为 CVR 信号，需要增强信任和购买理由。")
  _add_if(risks, metrics.get("confidence", 1) < 0.68, "预测置信度偏低，建议补充更明确的商品或素材信息。")
  _add_if(risks, compliance.get("scoreFactor", 1) < 0.92, "合规分降低了最终排序得分。")

  _add_if(recommendations, features.get("hookStrength", 0) < 0.55, "增强标题钩子：加入数字、场景痛点或明确收益。")
  _add_if(recommendations, features.get("sellingPointDensity", 0) < 0.45, "补充 2-3 个具体卖点，避免只写抽象形容词。")
  _add_if(recommendations, features.get("trustDepth", 0) < 0.50, "增加成分、认证、实验、用户反馈等信任证据。")
  _add_if(recommendations, alignment.get("overallAlignment", 0) < 0.28, "让标题、描述、图片文案统一围绕同一个核心卖点。")
  _add_if(recommendations, industrial.get("dcnCrossScore", 0) < 0.45, "增强品牌+卖点、场景+人群、CTA+优惠等组合表达，提高交叉特征分。")
  _add_if(recommendations, industrial.get("multitaskConsistency", 0) < 0.50, "让标题负责吸引点击，描述和卖点补足信任/价格/行动理由，提升多任务一致性。")
  _add_if(recommendations, features.get("conversionFriction", 0) >= 0.55, "加入更清晰的 CTA 或购买理由，降低决策成本。")
  _add_if(recommendations, breakdown.get("noveltyPenalty", 0) > 0.03, "该方案与已选高分方案相似，可尝试更换场景或卖点角度。")

  if not strengths:
    strengths.append("该方案具备基础投放可用性，但尚无明显突出优势。")
  if not risks:
    risks.append("未发现明显高风险项。")
  if not recommendations:
    recommendations.append("当前方案较均衡，可优先用于小流量验证。")

  health_score = max(0, min(1, (
    features.get("commercialQuality", 0.5) * 0.32
    + alignment.get("overallAlignment", 0.3) * 0.18
    + industrial.get("multitaskConsistency", 0.5) * 0.18
    + industrial.get("dcnCrossScore", 0.5) * 0.12
    + metrics.get("confidence", 0.6) * 0.10
    + compliance.get("scoreFactor", 0.9) * 0.10
  )))
  if health_score >= 0.76:
    level = "strong"
  elif health_score >= 0.58:
    level = "stable"
  else:
    level = "needs_work"

  return {
    "level": level,
    "healthScore": health_score,
    "strengths": strengths[:4],
    "risks": risks[:4],
    "recommendations": recommendations[:4],
  }
