function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}


function splitHighlights(value) {
  return String(value || "")
    .split(/[\n,，、/]/)
    .map((item) => item.trim())
    .filter(Boolean);
}


export function getDomElements() {
  return {
    caseText: document.querySelector("#case-text"),
    caseImage: document.querySelector("#case-image"),
    caseAudio: document.querySelector("#case-audio"),
    caseUnderstandingMode: document.querySelector("#case-understanding-mode"),
    productName: document.querySelector("#product-name"),
    brandName: document.querySelector("#brand-name"),
    category: document.querySelector("#category"),
    price: document.querySelector("#price"),
    audience: document.querySelector("#audience"),
    objective: document.querySelector("#objective"),
    platform: document.querySelector("#platform"),
    tone: document.querySelector("#tone"),
    textGenerationMode: document.querySelector("#text-generation-mode"),
    imageGenerationMode: document.querySelector("#image-generation-mode"),
    imageGenerationCount: document.querySelector("#image-generation-count"),
    highlights: document.querySelector("#highlights"),
    generateBtn: document.querySelector("#generate-btn"),
    sampleSkincare: document.querySelector("#sample-skincare"),
    sampleCoffee: document.querySelector("#sample-coffee"),
    sampleCourse: document.querySelector("#sample-course"),
    runtimeBackend: document.querySelector("#runtime-backend"),
    runtimeMode: document.querySelector("#runtime-mode"),
    runtimeHint: document.querySelector("#runtime-hint"),
    statusText: document.querySelector("#status-text"),
    winnerName: document.querySelector("#winner-name"),
    winnerCopy: document.querySelector("#winner-copy"),
    winnerSellingPoints: document.querySelector("#winner-selling-points"),
    winnerImageLine: document.querySelector("#winner-image-line"),
    creativeList: document.querySelector("#creative-list"),
    creativeCount: document.querySelector("#creative-count"),
    activeRank: document.querySelector("#active-rank"),
    selectedScore: document.querySelector("#selected-score"),
    topCtr: document.querySelector("#top-ctr"),
    topCvr: document.querySelector("#top-cvr"),
    topEcpm: document.querySelector("#top-ecpm"),
    topConfidence: document.querySelector("#top-confidence"),
    ctrInterval: document.querySelector("#ctr-interval"),
    cvrInterval: document.querySelector("#cvr-interval"),
    ecpmInterval: document.querySelector("#ecpm-interval"),
    riskAdjustedEcpm: document.querySelector("#risk-adjusted-ecpm"),
    ctrLift: document.querySelector("#ctr-lift"),
    cvrLift: document.querySelector("#cvr-lift"),
    ecpmLift: document.querySelector("#ecpm-lift"),
    confidenceHint: document.querySelector("#confidence-hint"),
    sampleImage: document.querySelector("#sample-image"),
    sampleImageHint: document.querySelector("#sample-image-hint"),
    surfaceGrid: document.querySelector("#surface-grid"),
    caseInsightSummary: document.querySelector("#case-insight-summary"),
    caseInsightAssets: document.querySelector("#case-insight-assets"),
    caseInsightTranscript: document.querySelector("#case-insight-transcript"),
    caseInsightMode: document.querySelector("#case-insight-mode"),
    selectionReasons: document.querySelector("#selection-reasons"),
    qualitySignals: document.querySelector("#quality-signals"),
    diagnosisStrengths: document.querySelector("#diagnosis-strengths"),
    diagnosisRisks: document.querySelector("#diagnosis-risks"),
    diagnosisRecommendations: document.querySelector("#diagnosis-recommendations"),
    imagePromptDimensions: document.querySelector("#image-prompt-dimensions"),
    imagePromptPreview: document.querySelector("#image-prompt-preview"),
  };
}


export function readForm(dom) {
  return {
    caseText: dom.caseText?.value?.trim() || "",
    caseUnderstandingMode: dom.caseUnderstandingMode?.value || "api",
    productName: dom.productName?.value?.trim() || "",
    brandName: dom.brandName?.value?.trim() || "",
    category: dom.category?.value || "beauty",
    price: Math.max(0, Number(dom.price?.value) || 0),
    audience: dom.audience?.value?.trim() || "",
    objective: dom.objective?.value || "balanced",
    platform: dom.platform?.value || "feed",
    tone: dom.tone?.value || "premium",
    creativeCount: 9,
    impressions: 50000,
    experimentMode: "full",
    diversityWeight: 0.08,
    highlights: splitHighlights(dom.highlights?.value),
    textGenerationMode: dom.textGenerationMode?.value || "api",
    imageGenerationMode: dom.imageGenerationMode?.value || "api",
    imageGenerationCount: dom.imageGenerationCount?.value || "top1",
  };
}


export async function readPayload(dom) {
  const payload = readForm(dom);
  const caseAssets = [];

  const imageFile = dom.caseImage?.files?.[0];
  if (imageFile) {
    caseAssets.push({
      kind: "image",
      name: imageFile.name,
      mimeType: imageFile.type,
      dataBase64: await fileToBase64(imageFile),
    });
  }

  const audioFile = dom.caseAudio?.files?.[0];
  if (audioFile) {
    caseAssets.push({
      kind: "audio",
      name: audioFile.name,
      mimeType: audioFile.type,
      dataBase64: await fileToBase64(audioFile),
    });
  }

  return {
    ...payload,
    caseAssets,
  };
}


export function populateForm(dom, sample) {
  if (dom.caseText) dom.caseText.value = sample.caseText || "";
  if (dom.productName) dom.productName.value = sample.productName || "";
  if (dom.brandName) dom.brandName.value = sample.brandName || "";
  if (dom.category) dom.category.value = sample.category || "beauty";
  if (dom.price) dom.price.value = sample.price ?? 199;
  if (dom.audience) dom.audience.value = sample.audience || "";
  if (dom.objective) dom.objective.value = sample.objective || "balanced";
  if (dom.platform) dom.platform.value = sample.platform || "feed";
  if (dom.tone) dom.tone.value = sample.tone || "premium";
  if (dom.caseUnderstandingMode) dom.caseUnderstandingMode.value = sample.caseUnderstandingMode || "api";
  if (dom.imageGenerationCount) dom.imageGenerationCount.value = sample.imageGenerationCount || "top1";
  if (dom.highlights) dom.highlights.value = sample.highlights || "";
  if (dom.caseImage) dom.caseImage.value = "";
  if (dom.caseAudio) dom.caseAudio.value = "";
}
