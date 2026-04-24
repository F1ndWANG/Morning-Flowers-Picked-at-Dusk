import { formatPercent } from "../utils/format.js";

function imageMarkup(creative) {
  if (creative.imageAssetUrl) {
    return `<img class="generated-visual" src="${creative.imageAssetUrl}" alt="${creative.title}" />`;
  }
  return "";
}

export function renderLeaderboard(dom, creatives) {
  dom.leaderboard.innerHTML = "";
  const head = document.createElement("div");
  head.className = "leaderboard-row head";
  head.innerHTML = `
    <div>排名</div>
    <div>创意标题</div>
    <div>CTR</div>
    <div>CVR</div>
    <div class="hide-mobile">eCPM</div>
    <div class="hide-tablet">多样性</div>
    <div class="hide-tablet">总分</div>
  `;
  dom.leaderboard.appendChild(head);

  creatives.slice(0, 6).forEach((creative) => {
    const row = document.createElement("div");
    row.className = "leaderboard-row";
    row.innerHTML = `
      <div class="leaderboard-rank">Top ${creative.rank}</div>
      <div class="leaderboard-title">${creative.title}</div>
      <div class="leaderboard-metric">${formatPercent(creative.metrics.ctr)}</div>
      <div class="leaderboard-metric">${formatPercent(creative.metrics.cvr)}</div>
      <div class="leaderboard-metric hide-mobile">${creative.metrics.ecpm.toFixed(1)}</div>
      <div class="leaderboard-metric hide-tablet">${creative.diversity.toFixed(2)}</div>
      <div class="leaderboard-metric hide-tablet">${creative.score.toFixed(3)}</div>
    `;
    dom.leaderboard.appendChild(row);
  });
}

export function renderCreatives(dom, creatives) {
  dom.creativeGrid.innerHTML = "";

  creatives.forEach((creative) => {
    const fragment = dom.creativeCardTemplate.content.cloneNode(true);
    const bannerSurface = fragment.querySelector(".banner-surface");
    const bannerVisual = fragment.querySelector(".banner-visual");
    const bannerTag = fragment.querySelector(".banner-tag");
    const bannerLine = fragment.querySelector(".banner-line");
    const rankBadge = fragment.querySelector(".rank-badge");
    const channelChip = fragment.querySelector(".channel-chip");
    const title = fragment.querySelector(".creative-title");
    const desc = fragment.querySelector(".creative-desc");
    const imagePrompt = fragment.querySelector(".image-prompt-copy");
    const generationMeta = fragment.querySelector(".generation-meta");
    const sellingPoints = fragment.querySelector(".selling-points");
    const metricRow = fragment.querySelector(".metric-row");

    const [colorA, colorB, colorC] = creative.palette;
    bannerSurface.style.background = `
      radial-gradient(circle at 22% 22%, rgba(255,255,255,0.42), transparent 20%),
      radial-gradient(circle at 78% 28%, rgba(255,255,255,0.22), transparent 24%),
      linear-gradient(135deg, ${colorA}, ${colorB} 56%, ${colorC})
    `;

    bannerVisual.innerHTML = imageMarkup(creative);
    bannerTag.textContent = creative.visual;
    bannerLine.textContent = creative.imageLine;
    rankBadge.textContent = `Rank ${creative.rank}`;
    channelChip.textContent = `${creative.channel} · ${creative.angle}`;
    title.textContent = creative.title;
    desc.textContent = creative.description;
    imagePrompt.textContent = creative.imagePrompt ?? "未生成图片 Prompt";
    generationMeta.innerHTML = `
      <span>文本：${creative.generationMeta?.textSource ?? "unknown"}</span>
      <span>图片：${creative.imageMeta?.assetState ?? "prompt-only"}</span>
    `;

    creative.sellingPoints.forEach((point) => {
      const chip = document.createElement("span");
      chip.textContent = point;
      sellingPoints.appendChild(chip);
    });

    metricRow.innerHTML = `
      <div class="metric-pill"><span>CTR</span><strong>${formatPercent(creative.metrics.ctr)}</strong></div>
      <div class="metric-pill"><span>CVR</span><strong>${formatPercent(creative.metrics.cvr)}</strong></div>
      <div class="metric-pill"><span>eCPM</span><strong>${creative.metrics.ecpm.toFixed(1)}</strong></div>
      <div class="metric-pill"><span>Diversity</span><strong>${creative.diversity.toFixed(2)}</strong></div>
    `;

    dom.creativeGrid.appendChild(fragment);
  });
}

export function renderBaselinePool(dom, baseline) {
  dom.leaderboard.innerHTML = "";
  const row = document.createElement("div");
  row.className = "leaderboard-row";
  row.innerHTML = `
    <div class="leaderboard-rank">Base</div>
    <div class="leaderboard-title">${baseline.title}</div>
    <div class="leaderboard-metric">${formatPercent(baseline.metrics.ctr)}</div>
    <div class="leaderboard-metric">${formatPercent(baseline.metrics.cvr)}</div>
    <div class="leaderboard-metric hide-mobile">${baseline.metrics.ecpm.toFixed(1)}</div>
    <div class="leaderboard-metric hide-tablet">0.22</div>
    <div class="leaderboard-metric hide-tablet">0.000</div>
  `;
  dom.leaderboard.appendChild(row);
  dom.creativeGrid.innerHTML = "";
}
