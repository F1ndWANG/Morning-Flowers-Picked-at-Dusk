import { CATEGORY_CONFIG } from "../config/catalog.js";
import { jaccardSimilarity, tokenize } from "../utils/text.js";

export function scoreCreative(creative, form, seed) {
  const text = `${creative.title} ${creative.description} ${creative.imageLine}`;
  const titleLength = creative.title.length;
  const hasNumber = /\d/.test(text) ? 1 : 0;
  const hasBrand = text.includes(form.brandName) ? 1 : 0;
  const audienceHit = form.audience
    .split(/[、，,\s]/)
    .filter(Boolean)
    .some((token) => text.includes(token));
  const highlightsHit = form.highlights.filter((item) => text.includes(item)).length;
  const clarity = titleLength >= 12 && titleLength <= 24 ? 1 : 0.65;
  const trustWords = /(专业|真实|可用|改善|体验|精选|系统|案例|修护|高压|冲刺)/.test(text) ? 1 : 0.55;
  const urgency = /(立即|马上|限时|现在|抢先|领取)/.test(text) ? 1 : 0.58;
  const angleFit = /(成分|功效|效率|成绩|性能)/.test(creative.angle) ? 1 : 0.76;
  const platformFit = CATEGORY_CONFIG[form.category].platformFit[form.platform];
  const bidFactor = CATEGORY_CONFIG[form.category].bidFactor;

  const contributions = {
    数字利益点: hasNumber * 0.004,
    人群相关性: audienceHit ? 0.003 : 0,
    标题清晰度: clarity * 0.006,
    紧迫感: urgency * 0.0025,
    卖点命中: highlightsHit * 0.0018,
    品牌信任: hasBrand * 0.003,
    信任词命中: trustWords * 0.004,
    角度匹配: angleFit * 0.0026,
    渠道适配: (platformFit - 1) * 0.01
  };

  const ctr =
    0.018 +
    contributions.数字利益点 +
    contributions.人群相关性 +
    contributions.标题清晰度 +
    contributions.紧迫感 +
    contributions.卖点命中 +
    contributions.角度匹配 +
    contributions.渠道适配 +
    seed * 0.01;

  const cvr =
    0.012 +
    contributions.品牌信任 +
    contributions.信任词命中 +
    Math.min(creative.sellingPoints.length, 3) * 0.0015 +
    highlightsHit * 0.0012 +
    platformFit * 0.0018 +
    seed * 0.006;

  const ecpm = ctr * (1.8 + cvr * 80) * bidFactor * 1000;
  const reasons = [];
  if (hasNumber) reasons.push("包含数字化利益点，点击意愿更强");
  if (audienceHit) reasons.push("文案命中目标人群表达");
  if (trustWords === 1) reasons.push("带有信任型措辞，利于转化");
  if (clarity === 1) reasons.push("标题长度适中，首屏理解更快");
  if (platformFit > 1.05) reasons.push("与当前投放渠道适配度更高");
  reasons.push(`主打 ${creative.angle} 角度，扩大创意覆盖。`);

  return {
    metrics: {
      ctr,
      cvr,
      ecpm,
      clarity,
      trustWords,
      urgency
    },
    contributions,
    reasons
  };
}

export function enrichCreatives(drafts, form) {
  return drafts.map((draft, index) => {
    const scoring = scoreCreative(draft, form, (index + 1) / 100);
    return {
      ...draft,
      metrics: scoring.metrics,
      contributions: scoring.contributions,
      reasons: scoring.reasons,
      score: 0
    };
  });
}

export function applyDiversityPenalty(candidates) {
  return candidates.map((creative, _, list) => {
    const baseTokens = tokenize(`${creative.title} ${creative.description} ${creative.imageLine}`);
    const similarities = list
      .filter((item) => item.id !== creative.id)
      .map((item) => tokenize(`${item.title} ${item.description} ${item.imageLine}`))
      .map((tokens) => jaccardSimilarity(baseTokens, tokens));

    return {
      ...creative,
      diversity: Math.max(0.18, 1 - Math.max(...similarities, 0))
    };
  });
}

export function rerankCreatives(candidates, objective, diversityWeight) {
  const objectiveWeights = {
    balanced: { ctr: 0.38, cvr: 0.32, ecpm: 0.22 },
    ctr: { ctr: 0.56, cvr: 0.16, ecpm: 0.16 },
    cvr: { ctr: 0.18, cvr: 0.48, ecpm: 0.22 },
    ecpm: { ctr: 0.22, cvr: 0.22, ecpm: 0.44 }
  };
  const weights = objectiveWeights[objective];
  const maxCtr = Math.max(...candidates.map((item) => item.metrics.ctr));
  const maxCvr = Math.max(...candidates.map((item) => item.metrics.cvr));
  const maxEcpm = Math.max(...candidates.map((item) => item.metrics.ecpm));

  return [...candidates]
    .map((creative) => {
      const normalizedCtr = creative.metrics.ctr / maxCtr;
      const normalizedCvr = creative.metrics.cvr / maxCvr;
      const normalizedEcpm = creative.metrics.ecpm / maxEcpm;
      const qualityFactor = creative.compliance?.scoreFactor ?? 1;
      const ctrComponent = normalizedCtr * weights.ctr;
      const cvrComponent = normalizedCvr * weights.cvr;
      const ecpmComponent = normalizedEcpm * weights.ecpm;
      const diversityComponent = creative.diversity * diversityWeight;
      const score = (ctrComponent + cvrComponent + ecpmComponent + diversityComponent) * qualityFactor;

      return {
        ...creative,
        score,
        rankingBreakdown: {
          ctrComponent,
          cvrComponent,
          ecpmComponent,
          diversityComponent,
          qualityFactor,
          finalScore: score
        }
      };
    })
    .sort((a, b) => b.score - a.score)
    .map((creative, index) => ({ ...creative, rank: index + 1 }));
}
