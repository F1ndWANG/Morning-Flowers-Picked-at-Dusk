export function renderIntegrationPanel(dom, integrationInfo) {
  if (!dom.integrationGrid) {
    return;
  }

  dom.integrationGrid.innerHTML = "";
  const items = [
    {
      key: "textGeneration",
      title: "文本大模型",
      data: integrationInfo.textGeneration
    },
    {
      key: "imageGeneration",
      title: "文生图接口",
      data: integrationInfo.imageGeneration
    }
  ];

  items.forEach((item) => {
    const envVars = item.data.requiredEnv ?? item.data.apiRequiredEnv ?? [];
    const card = document.createElement("article");
    card.className = "integration-card";
    card.innerHTML = `
      <div class="integration-head">
        <div>
          <span>API Marked</span>
          <strong>${item.title}</strong>
        </div>
        <span>${item.data.usedApi ? "Live API" : "Mock / Prompt Only"}</span>
      </div>
      <div class="integration-meta">
        <span>requested: ${item.data.requestedMode ?? item.data.defaultMode ?? item.data.mode}</span>
        <span>mode: ${item.data.mode}</span>
        <span>provider: ${item.data.provider}</span>
        <span>configured: ${item.data.configured ? "yes" : "no"}</span>
      </div>
      <p class="integration-note">${item.data.note}</p>
      <div class="integration-envs">${envVars
        .map((envName) => `<code>${envName}</code>`)
        .join("")}</div>
    `;
    dom.integrationGrid.appendChild(card);
  });
}
