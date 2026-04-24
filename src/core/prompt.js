export function buildPromptBundle(form, winner = null) {
  const textSystemPrompt = [
    "你是一名广告创意生成与投放优化助手。",
    "任务是为给定商品生成多个创意版本，并确保输出适合竞价广告系统。",
    "生成结果必须覆盖不同创意角度，兼顾点击、转化和合规表达。",
    "输出字段包括：title、description、selling_points、image_copy、angle、channel。"
  ].join("\n");

  const textUserPrompt = [
    `商品名称：${form.productName}`,
    `品牌：${form.brandName}`,
    `类目：${form.category}`,
    `价格：${form.price} 元`,
    `目标人群：${form.audience}`,
    `投放渠道：${form.platform}`,
    `投放目标：${form.objective}`,
    `风格：${form.tone}`,
    `卖点：${form.highlights.join("、")}`,
    `请生成 ${form.creativeCount} 组不同角度的广告创意，优先突出效果、可信度和转化动机。`
  ].join("\n");

  const imagePrompt = winner
    ? `为商品 ${form.brandName} ${form.productName} 生成广告画面，主标题为“${winner.title}”，画面文案为“${winner.imageLine}”，卖点包含 ${winner.sellingPoints.join("、")}，留出 CTA 区域。`
    : "请先生成创意结果，再查看文生图 Prompt。";

  return {
    textSystemPrompt,
    textUserPrompt,
    imagePrompt,
    apiMarkers: [
      "文本大模型接入位：AIGCSAR_LLM_API_KEY",
      "文生图接口接入位：AIGCSAR_IMAGE_API_KEY"
    ]
  };
}
