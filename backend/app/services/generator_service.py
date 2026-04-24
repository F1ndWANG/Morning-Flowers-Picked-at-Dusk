from backend.app.core.catalog import CATEGORY_CONFIG, TONE_CONFIG
from backend.app.services.format_service import objective_text, platform_text


def _unique(values: list[str]) -> list[str]:
  seen: set[str] = set()
  result: list[str] = []
  for value in values:
    text = str(value).strip()
    if not text or text in seen:
      continue
    seen.add(text)
    result.append(text)
  return result


def merge_campaign(form: dict, case_context: dict) -> dict:
  category = form.get("category") or case_context.get("category") or "beauty"
  highlights = _unique((form.get("highlights") or []) + (case_context.get("highlights") or []))[:5]
  if not highlights:
    highlights = ["效果提升", "场景适配", "购买理由明确"]

  return {
    "caseText": form.get("caseText", "").strip(),
    "productName": form.get("productName") or case_context.get("productName") or "案例商品",
    "brandName": form.get("brandName") or case_context.get("brandName") or "案例品牌",
    "category": category,
    "price": float(form.get("price") or case_context.get("price") or 199),
    "audience": form.get("audience") or case_context.get("audience") or "对该品类感兴趣的潜在用户",
    "objective": form.get("objective") or case_context.get("objective") or "balanced",
    "platform": form.get("platform") or case_context.get("platform") or "feed",
    "tone": form.get("tone") or case_context.get("tone") or "premium",
    "creativeCount": int(form.get("creativeCount") or 8),
    "impressions": int(form.get("impressions") or 100000),
    "experimentMode": form.get("experimentMode") or "full",
    "diversityWeight": float(form.get("diversityWeight") or 0.08),
    "highlights": highlights,
    "caseSummary": case_context.get("caseSummary") or form.get("caseText") or "",
    "caseSignals": case_context.get("caseSignals") or [],
    "textGenerationMode": form.get("textGenerationMode", "mock"),
    "imageGenerationMode": form.get("imageGenerationMode", "mock"),
  }


def build_baseline(campaign: dict) -> dict:
  first_highlight = campaign["highlights"][0]
  title = f"{campaign['brandName']} {campaign['productName']}"
  description = (
    f"面向{campaign['audience']}，主打{first_highlight}，"
    f"在{platform_text(campaign['platform'])}场景中稳定传达核心卖点与转化入口。"
  )
  return {
    "id": "baseline",
    "rank": 0,
    "angle": "基础模板",
    "channel": platform_text(campaign["platform"]),
    "title": title,
    "description": description,
    "imageLine": f"{campaign['productName']}\n{first_highlight}",
    "sellingPoints": campaign["highlights"][:3],
    "visual": "标准产品主视觉",
    "palette": ["#605448", "#9d7d63", "#e9d5bc"],
    "generationMeta": {
      "textSource": "baseline-template",
      "provider": "local-baseline-builder",
      "apiMarked": False,
    },
  }


def generate_creative_drafts(campaign: dict, case_context: dict) -> list[dict]:
  category_config = CATEGORY_CONFIG[campaign["category"]]
  tone_config = TONE_CONFIG[campaign["tone"]]
  highlights = campaign["highlights"]
  case_summary = campaign["caseSummary"] or case_context.get("caseSummary", "")
  summary_snippet = case_summary[:48]
  objective_label = objective_text(campaign["objective"])
  price_text = (
    f"到手{int(campaign['price'])}元"
    if campaign["price"] >= 999
    else f"{int(campaign['price'])}元轻决策"
  )

  drafts: list[dict] = []
  for index in range(campaign["creativeCount"]):
    angle = category_config["angles"][index % len(category_config["angles"])]
    hook = category_config["hooks"][index % len(category_config["hooks"])]
    visual = category_config["visuals"][index % len(category_config["visuals"])]
    cta = category_config["cta"][index % len(category_config["cta"])]
    prefix = tone_config["prefixes"][index % len(tone_config["prefixes"])]
    suffix = tone_config["suffixes"][index % len(tone_config["suffixes"])]
    benefit_a = highlights[index % len(highlights)]
    benefit_b = highlights[(index + 1) % len(highlights)]
    benefit_c = highlights[(index + 2) % len(highlights)]

    title_candidates = [
      f"{prefix}｜{campaign['productName']}让{benefit_a}",
      f"{hook}，把{benefit_a}讲明白",
      f"{campaign['brandName']} {campaign['productName']}：{benefit_a}+{benefit_b}",
      f"{price_text}，把{benefit_a}做成购买理由",
    ]
    description_candidates = [
      f"围绕{angle}角度切入，突出{benefit_a}、{benefit_b}与{benefit_c}，服务{campaign['audience']}的真实决策场景。",
      f"先用“{hook}”抓住注意力，再用{benefit_a}和{price_text}解释性价比，最后用“{cta}”完成收口。",
      f"本条创意重点服务{objective_label}目标，强调{benefit_a}，并用{benefit_b}与{benefit_c}降低转化阻力。",
      f"结合案例输入“{summary_snippet}”，输出更适合{campaign['platform']}流量面的广告表达。",
    ]

    drafts.append(
      {
        "id": f"creative-{index + 1}",
        "rawIndex": index,
        "angle": angle,
        "channel": platform_text(campaign["platform"]),
        "title": title_candidates[index % len(title_candidates)],
        "description": description_candidates[(index + 1) % len(description_candidates)],
        "imageLine": f"{hook}\n{benefit_a}",
        "sellingPoints": [benefit_a, benefit_b, benefit_c],
        "visual": visual,
        "palette": tone_config["colorSet"],
        "generationMeta": {
          "textSource": "template-draft",
          "provider": "local-template-engine",
          "apiMarked": True,
          "apiRequiredEnv": "AIGCSAR_LLM_API_KEY",
        },
      }
    )

  return drafts
