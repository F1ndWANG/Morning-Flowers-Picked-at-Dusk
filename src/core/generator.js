import { CATEGORY_CONFIG, TONE_CONFIG } from "../config/catalog.js";
import { platformText } from "../utils/format.js";
import { scoreCreative } from "./scoring.js";

export function buildBaseline(form) {
  const firstHighlight = form.highlights[0] || "高品质体验";
  const title = `${form.brandName}${form.productName}`;
  const description = `主打 ${firstHighlight}，面向 ${form.audience}，在 ${platformText(form.platform)} 渠道中突出核心利益点与基础转化入口。`;
  const creative = {
    id: "baseline",
    rank: 0,
    angle: "基础模板",
    channel: platformText(form.platform),
    title,
    description,
    imageLine: `${form.productName}\n${firstHighlight}`,
    sellingPoints: form.highlights.slice(0, 3),
    visual: "标准棚拍素材",
    palette: ["#61574f", "#8f7f6b", "#dbc8af"],
    generationMeta: {
      textSource: "baseline-template",
      apiMarked: false
    }
  };
  const scoring = scoreCreative(creative, form, 0.08);
  return {
    ...creative,
    metrics: scoring.metrics,
    contributions: scoring.contributions,
    reasons: scoring.reasons,
    diversity: 0.22,
    score: 0
  };
}

export function generateCreativeDrafts(form) {
  const categoryConfig = CATEGORY_CONFIG[form.category];
  const toneConfig = TONE_CONFIG[form.tone];
  const highlights = form.highlights.length ? form.highlights : ["体验升级", "高效解决需求", "真实口碑背书"];
  const drafts = [];

  for (let index = 0; index < form.creativeCount; index += 1) {
    const angle = categoryConfig.angles[index % categoryConfig.angles.length];
    const hook = categoryConfig.hooks[index % categoryConfig.hooks.length];
    const channel = categoryConfig.channels[index % categoryConfig.channels.length];
    const lead = toneConfig.prefixes[index % toneConfig.prefixes.length];
    const benefitA = highlights[index % highlights.length];
    const benefitB = highlights[(index + 1) % highlights.length];
    const benefitC = highlights[(index + 2) % highlights.length];
    const visual = categoryConfig.visuals[index % categoryConfig.visuals.length];
    const cta = categoryConfig.cta[index % categoryConfig.cta.length];
    const descriptor = toneConfig.suffixes[index % toneConfig.suffixes.length];
    const priceText = form.price >= 999 ? `到手 ${form.price} 元档` : `${form.price} 元轻决策`;

    const titleOptions = [
      `${lead} ${form.productName}，${hook}`,
      `${hook} 不靠堆料，${benefitA} 才是关键`,
      `${form.brandName}${form.productName}，${benefitA} + ${benefitB}`,
      `${priceText}，把 ${benefitA} 讲明白`
    ];

    const descOptions = [
      `面向 ${form.audience}，这版创意围绕 ${benefitA}、${benefitB} 和 ${benefitC} 展开，${descriptor}。`,
      `先用 ${hook} 抓住注意力，再用 ${benefitA} 和 ${priceText} 解释性价比，最后用 ${cta} 收口。`,
      `从 ${angle} 角度切入，突出 ${benefitA}，强化 ${benefitB} 的体感，并用 ${benefitC} 降低决策阻力。`
    ];

    drafts.push({
      id: `creative-${index + 1}`,
      rawIndex: index,
      angle,
      channel,
      title: titleOptions[(index + form.productName.length) % titleOptions.length],
      description: descOptions[(index + form.brandName.length) % descOptions.length],
      imageLine: `${hook}\n${benefitA}`,
      sellingPoints: [benefitA, benefitB, benefitC],
      visual,
      palette: toneConfig.colorSet,
      generationMeta: {
        textSource: "mock-template",
        textProvider: "local-template-engine",
        apiMarked: true,
        apiRequiredEnv: "AIGCSAR_LLM_API_KEY"
      }
    });
  }

  return drafts;
}
