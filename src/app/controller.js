import { createApiClient } from "./apiClient.js";
import { populateForm, readForm, readPayload } from "../ui/dom.js";


function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
}


function formatConfidence(value) {
  return Number(value || 0).toFixed(2);
}


function formatScore(value) {
  return Number(value || 0).toFixed(3);
}


function formatRange(interval, formatter, fallbackValue) {
  if (!interval) {
    return `${formatter(fallbackValue)} - ${formatter(fallbackValue)}`;
  }
  return `${formatter(interval.lower)} - ${formatter(interval.upper)}`;
}


function setText(node, text) {
  if (node) {
    node.textContent = text;
  }
}


function setHtml(node, html) {
  if (node) {
    node.innerHTML = html;
  }
}


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function setStatus(dom, text, isError = false) {
  if (!dom.statusText) {
    return;
  }
  dom.statusText.textContent = text;
  dom.statusText.classList.toggle("warning", isError);
}


function renderSelectOptions(select, options, selectedValue) {
  if (!select) {
    return;
  }

  select.innerHTML = "";
  Object.entries(options).forEach(([key, value]) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = value.label ?? value;
    option.selected = key === selectedValue;
    select.appendChild(option);
  });
}


function renderCatalog(dom, catalog, currentValues) {
  renderSelectOptions(dom.category, catalog.categories, currentValues.category);
  renderSelectOptions(dom.objective, catalog.objectives, currentValues.objective);
  renderSelectOptions(dom.platform, catalog.platforms, currentValues.platform);
  renderSelectOptions(dom.tone, catalog.tones, currentValues.tone);
}


function getCreatives(result) {
  const creatives = result.active_strategy?.creatives || result.ranked_creatives || [];
  if (creatives.length > 0) {
    return creatives;
  }
  return result.active_strategy?.winner ? [result.active_strategy.winner] : [result.baseline].filter(Boolean);
}


function getCreativeKey(creative, index) {
  return creative.id || `creative-${creative.rank || index + 1}`;
}


function renderCreativeQueue(dom, creatives, activeKey) {
  setText(dom.creativeCount, `${creatives.length} 套方案`);

  if (!dom.creativeList) {
    return;
  }

  dom.creativeList.innerHTML = creatives
    .map((creative, index) => {
      const key = getCreativeKey(creative, index);
      const isActive = key === activeKey;
      const metrics = creative.metrics || {};
      return `
        <button class="creative-option ${isActive ? "active" : ""}" type="button" data-creative-key="${escapeHtml(key)}">
          <div class="creative-option-head">
            <span>#${creative.rank || index + 1}</span>
            <strong>${escapeHtml(creative.title || "未命名方案")}</strong>
          </div>
          <p>${escapeHtml(creative.description || "暂无描述")}</p>
          <div class="creative-option-metrics">
            <span>Score <b>${formatScore(creative.score)}</b></span>
            <span>CTR <b>${formatPercent(metrics.ctr || 0)}</b></span>
            <span>CVR <b>${formatPercent(metrics.cvr || 0)}</b></span>
            <span>eCPM <b>${Number(metrics.ecpm || 0).toFixed(1)}</b></span>
          </div>
        </button>
      `;
    })
    .join("");
}


function renderCreativeDetail(dom, result, winner) {
  const caseContext = result.case_context ?? {};
  const multimodalInfo = result.integration_info?.multimodalUnderstanding ?? {};
  const assetCount = caseContext.modalityStats?.totalAssetCount ?? 0;
  const transcriptText = (caseContext.transcriptText || "").trim();
  const metrics = winner.metrics || {};

  setText(dom.winnerName, winner.title || "等待生成");
  setText(dom.winnerCopy, winner.description || "点击生成后展示广告描述。");
  setText(dom.winnerImageLine, winner.imageLine || "暂无图片文案。");
  setText(dom.selectedScore, formatScore(winner.score));
  setText(dom.activeRank, `当前 #${winner.rank || 1}`);
  setText(dom.topCtr, formatPercent(metrics.ctr || 0));
  setText(dom.topCvr, formatPercent(metrics.cvr || 0));
  setText(dom.topEcpm, Number(metrics.ecpm || 0).toFixed(1));
  setText(dom.topConfidence, formatConfidence(metrics.confidence));
  setText(dom.ctrInterval, formatRange(winner.metricIntervals?.ctr, formatPercent, metrics.ctr || 0));
  setText(dom.cvrInterval, formatRange(winner.metricIntervals?.cvr, formatPercent, metrics.cvr || 0));
  setText(
    dom.ecpmInterval,
    formatRange(winner.metricIntervals?.ecpm, (value) => Number(value || 0).toFixed(1), metrics.ecpm || 0)
  );
  setText(dom.riskAdjustedEcpm, Number(metrics.riskAdjustedEcpm || 0).toFixed(1));
  setText(dom.ctrLift, "点击率预估");
  setText(dom.cvrLift, "转化率预估");
  setText(dom.ecpmLift, "收益效率预估");
  setText(dom.confidenceHint, assetCount > 0 ? "已融合素材信息" : "基于文本与结构化字段");

  setHtml(
    dom.winnerSellingPoints,
    (winner.sellingPoints || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")
  );

  setText(dom.caseInsightSummary, caseContext.caseSummary || "暂无案例摘要。");
  setText(dom.caseInsightAssets, String(assetCount));
  setText(dom.caseInsightTranscript, transcriptText ? "已提取" : "无");
  setText(dom.caseInsightMode, multimodalInfo.mode === "api" ? "API" : "本地");
  setHtml(
    dom.selectionReasons,
    (winner.reasons || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")
  );
  if (winner.imageAssetUrl && dom.sampleImage) {
    dom.sampleImage.src = winner.imageAssetUrl;
    dom.sampleImage.classList.add("visible");
    setText(dom.sampleImageHint, "当前方案的广告图由后端图片生成接口返回。");
  } else {
    if (dom.sampleImage) {
      dom.sampleImage.removeAttribute("src");
      dom.sampleImage.classList.remove("visible");
    }
    setText(dom.sampleImageHint, winner.imageLine || "图片接口未返回图片，当前显示图片文案。");
  }
}


function renderSurfaces(dom, surfaces) {
  if (!dom.surfaceGrid) {
    return;
  }

  const surfaceOrder = ["search", "feed", "video", "mall"];
  const surfaceNames = {
    search: "搜索广告",
    feed: "信息流广告",
    video: "视频推荐",
    mall: "商城推荐",
  };

  dom.surfaceGrid.innerHTML = surfaceOrder
    .filter((key) => surfaces[key])
    .map((key) => {
      const item = surfaces[key];
      return `
        <article class="surface-card ${item.isCurrent ? "active" : ""}">
          <div class="surface-head">
            <span>${key.toUpperCase()}</span>
            <strong>${surfaceNames[key] ?? item.label}</strong>
          </div>
          <div class="surface-metrics">
            <div><small>CTR</small><strong>${formatPercent(item.ctr)}</strong></div>
            <div><small>CVR</small><strong>${formatPercent(item.cvr)}</strong></div>
            <div><small>eCPM</small><strong>${item.ecpm.toFixed(1)}</strong></div>
            <div><small>Confidence</small><strong>${formatConfidence(item.confidence)}</strong></div>
          </div>
        </article>
      `;
    })
    .join("");
}


function renderResult(dom, result, activeKey = null) {
  const creatives = getCreatives(result);
  const fallbackKey = getCreativeKey(creatives[0], 0);
  const selectedKey = activeKey || fallbackKey;
  const selectedIndex = Math.max(0, creatives.findIndex((creative, index) => getCreativeKey(creative, index) === selectedKey));
  const selectedCreative = creatives[selectedIndex] || creatives[0];
  const resolvedKey = getCreativeKey(selectedCreative, selectedIndex);

  renderCreativeQueue(dom, creatives, resolvedKey);
  renderCreativeDetail(dom, result, selectedCreative);
  renderSurfaces(dom, selectedCreative.surfacePredictions || result.surface_predictions || {});

  return resolvedKey;
}


export function createController(dom) {
  const apiClient = createApiClient();
  const state = {
    catalog: null,
    samples: {},
    lastResult: null,
    activeCreativeKey: null,
    retryTimer: null,
  };

  function stopRetryLoop() {
    if (state.retryTimer) {
      clearTimeout(state.retryTimer);
      state.retryTimer = null;
    }
  }

  function scheduleRetry() {
    if (state.retryTimer) {
      return;
    }
    state.retryTimer = window.setTimeout(async () => {
      state.retryTimer = null;
      const connected = await hydrateRuntime({ silent: true });
      if (connected && !state.lastResult) {
        await runPrediction();
      }
    }, 3000);
  }

  async function hydrateRuntime(options = {}) {
    const { silent = false } = options;
    setText(dom.runtimeHint, apiClient.baseUrl);
    setText(dom.runtimeMode, "Backend API");

    try {
      await apiClient.checkHealth();
      setText(dom.runtimeBackend, "Connected");
      stopRetryLoop();

      const [catalogResponse, sampleResponse] = await Promise.all([
        apiClient.getCatalog(),
        apiClient.getSamples(),
      ]);

      state.catalog = catalogResponse;
      state.samples = sampleResponse.samples ?? {};
      renderCatalog(dom, state.catalog, readForm(dom));

      if (!silent) {
        setStatus(dom, "后端连接成功，可以开始生成广告与预测效果。");
      }
      return true;
    } catch (error) {
      setText(dom.runtimeBackend, "Offline");
      if (!silent) {
        setStatus(dom, `后端暂不可用：${error.message}`, true);
      }
      scheduleRetry();
      return false;
    }
  }

  async function useSample(sampleKey) {
    const sample = state.samples[sampleKey];
    if (!sample) {
      return;
    }
    populateForm(dom, sample);
    await runPrediction();
  }

  async function runPrediction() {
    if (dom.generateBtn) {
      dom.generateBtn.disabled = true;
    }

    try {
      setStatus(dom, "正在生成广告标题、描述、卖点、图片文案，并进行搜广推效果预测...");
      const payload = await readPayload(dom);
      const result = await apiClient.runPipeline(payload);
      state.lastResult = result;
      setText(dom.runtimeBackend, "Connected");
      stopRetryLoop();

      state.activeCreativeKey = renderResult(dom, result);
      setStatus(dom, "生成完成，已返回多套候选创意、广告图与搜广推预测结果，可点击候选卡片切换方案。");
    } catch (error) {
      setStatus(dom, `生成失败：${error.message}`, true);
    } finally {
      if (dom.generateBtn) {
        dom.generateBtn.disabled = false;
      }
    }
  }

  function bindEvents() {
    dom.generateBtn?.addEventListener("click", () => {
      void runPrediction();
    });
    dom.sampleSkincare?.addEventListener("click", () => {
      void useSample("skincare");
    });
    dom.sampleCoffee?.addEventListener("click", () => {
      void useSample("coffee");
    });
    dom.sampleCourse?.addEventListener("click", () => {
      void useSample("course");
    });
    dom.creativeList?.addEventListener("click", (event) => {
      const option = event.target.closest("[data-creative-key]");
      if (!option || !state.lastResult) {
        return;
      }
      state.activeCreativeKey = renderResult(dom, state.lastResult, option.dataset.creativeKey);
    });
  }

  return {
    bindEvents,
    hydrateRuntime,
    runPrediction,
  };
}
