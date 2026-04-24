from backend.app.services.image_generation_service import build_image_prompt


def build_prompt_bundle(campaign: dict, case_context: dict, winner: dict | None = None) -> dict[str, str | list[str]]:
  analyses = "\n".join(
    f"- {item['kind']}: {item['summary']}" for item in case_context.get("assetAnalyses", [])
  ) or "- 无补充素材"

  case_prompt = "\n".join(
    [
      "你是一名多模态案例理解助手。",
      "请从文本、图片和音频素材中提取商品、品牌、受众、卖点和广告表达建议。",
      "输出字段包括 productName、brandName、category、audience、price、highlights、caseSummary。",
      "",
      f"用户案例：{campaign['caseText'] or campaign['caseSummary']}",
      f"素材分析：\n{analyses}",
    ]
  )

  text_system_prompt = "\n".join(
    [
      "你是一名广告创意生成与投放优化助手。",
      "任务是为给定案例生成多版本广告标题、描述、卖点和图片文案。",
      "输出结果需要兼顾点击、转化、合规和多样性。",
    ]
  )

  text_user_prompt = "\n".join(
    [
      f"商品：{campaign['brandName']} {campaign['productName']}",
      f"类目：{campaign['category']}",
      f"价格：{campaign['price']} 元",
      f"受众：{campaign['audience']}",
      f"目标：{campaign['objective']}",
      f"平台：{campaign['platform']}",
      f"风格：{campaign['tone']}",
      f"卖点：{'、'.join(campaign['highlights'])}",
      f"案例摘要：{campaign['caseSummary']}",
      f"请生成 {campaign['creativeCount']} 组适合搜广推场景的广告创意。",
    ]
  )

  image_prompt = build_image_prompt(winner, campaign, case_context) if winner else "请先完成创意生成，再构造图片 Prompt。"

  return {
    "caseUnderstandingPrompt": case_prompt,
    "textSystemPrompt": text_system_prompt,
    "textUserPrompt": text_user_prompt,
    "imagePrompt": image_prompt,
    "apiMarkers": [
      "多模态理解接入位：AIGCSAR_LLM_API_KEY / AIGCSAR_VISION_MODEL / AIGCSAR_AUDIO_MODEL",
      "文本生成接入位：AIGCSAR_LLM_API_KEY / AIGCSAR_LLM_MODEL / AIGCSAR_LLM_API_BASE",
      "文生图接入位：AIGCSAR_IMAGE_API_KEY / AIGCSAR_IMAGE_MODEL / AIGCSAR_IMAGE_API_BASE",
    ],
  }
