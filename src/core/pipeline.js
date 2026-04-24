import { evaluateCompliance } from "./compliance.js";
import { buildBaseline, generateCreativeDrafts } from "./generator.js";
import { buildPromptBundle } from "./prompt.js";
import { buildReport } from "./report.js";
import { buildStrategies } from "./strategies.js";

function attachImagePrompts(creatives, form) {
  return creatives.map((creative) => ({
    ...creative,
    imagePrompt: `为商品 ${form.brandName} ${form.productName} 生成广告画面，主标题为“${creative.title}”，画面文案为“${creative.imageLine}”，卖点包含 ${creative.sellingPoints.join("、")}，留出 CTA 区域。`,
    imageMeta: {
      assetState: "prompt-only",
      imageSource: "mock-image-prompt",
      apiMarked: true,
      apiRequiredEnv: "AIGCSAR_IMAGE_API_KEY"
    }
  }));
}

function buildLocalIntegrationInfo(form) {
  return {
    textGeneration: {
      mode: form.textGenerationMode === "api" ? "mock-fallback" : "mock",
      requestedMode: form.textGenerationMode,
      provider: "local-template-engine",
      configured: false,
      usedApi: false,
      apiMarked: true,
      requiredEnv: ["AIGCSAR_LLM_API_KEY", "AIGCSAR_LLM_MODEL", "AIGCSAR_LLM_API_BASE"],
      note:
        form.textGenerationMode === "api"
          ? "前端本地模式不调用真实 LLM API。请切换到 Backend API 并配置 AIGCSAR_LLM_API_KEY。"
          : "当前使用本地模板生成文本。"
    },
    imageGeneration: {
      mode: form.imageGenerationMode === "api" ? "mock-fallback" : "mock",
      requestedMode: form.imageGenerationMode,
      provider: "prompt-only",
      configured: false,
      usedApi: false,
      apiMarked: true,
      requiredEnv: ["AIGCSAR_IMAGE_API_KEY", "AIGCSAR_IMAGE_MODEL", "AIGCSAR_IMAGE_API_BASE"],
      note:
        form.imageGenerationMode === "api"
          ? "前端本地模式不调用真实文生图 API。请切换到 Backend API 并配置 AIGCSAR_IMAGE_API_KEY。"
          : "当前只生成图片 Prompt。"
    }
  };
}

export function runPipeline(form) {
  const integrationInfo = buildLocalIntegrationInfo(form);
  const baseline = {
    ...buildBaseline(form)
  };
  baseline.compliance = evaluateCompliance(baseline, form);
  const [baselineWithImage] = attachImagePrompts([baseline], form);

  const drafts = generateCreativeDrafts(form);
  const strategies = buildStrategies(form, baselineWithImage, drafts);
  strategies["llm-only"].creatives = attachImagePrompts(strategies["llm-only"].creatives, form);
  strategies["predictive-only"].creatives = attachImagePrompts(strategies["predictive-only"].creatives, form);
  strategies.full.creatives = attachImagePrompts(strategies.full.creatives, form);

  strategies["llm-only"].winner = strategies["llm-only"].creatives[0];
  strategies["predictive-only"].winner = strategies["predictive-only"].creatives[0];
  strategies.full.winner = strategies.full.creatives[0];
  const activeStrategy = strategies[form.experimentMode];
  const rankedCreatives = form.experimentMode === "baseline" ? [baselineWithImage] : activeStrategy.creatives;
  const prompts = buildPromptBundle(form, activeStrategy.winner);
  const report = buildReport(form, strategies, activeStrategy, integrationInfo);

  return {
    baseline: baselineWithImage,
    drafts,
    strategies,
    activeStrategy,
    rankedCreatives,
    prompts,
    report,
    integrationInfo
  };
}
