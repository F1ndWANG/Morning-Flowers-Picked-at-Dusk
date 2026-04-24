export function buildMetricBars(metrics, mount) {
  const items = [
    { label: "CTR", value: metrics.ctr, max: 0.05 },
    { label: "CVR", value: metrics.cvr, max: 0.04 },
    { label: "eCPM", value: metrics.ecpm, max: 240 },
    { label: "多样性", value: metrics.diversity ?? 0.22, max: 1 }
  ];

  mount.innerHTML = "";
  items.forEach((item) => {
    const wrapper = document.createElement("div");
    wrapper.className = "bar-item";
    wrapper.innerHTML = `
      <div class="bar-label">
        <span>${item.label}</span>
        <span>${item.label === "eCPM" ? item.value.toFixed(1) : item.value.toFixed(2)}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${Math.min(100, (item.value / item.max) * 100)}%"></div>
      </div>
    `;
    mount.appendChild(wrapper);
  });
}

export function renderReasonList(target, items, formatter) {
  target.innerHTML = "";
  items.forEach((item) => {
    const chip = document.createElement("div");
    chip.className = "reason-chip";
    chip.innerHTML = formatter(item);
    target.appendChild(chip);
  });
}
