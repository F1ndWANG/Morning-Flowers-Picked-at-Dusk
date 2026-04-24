import re


RISK_RULES = [
  {
    "key": "absolute_claim",
    "label": "绝对化表达",
    "pattern": r"(第一|顶级|永久|100%|绝对|稳赚|包过|根治)",
    "penalty": 0.12,
    "message": "包含绝对化或结果承诺词，存在投放审核风险。",
  },
  {
    "key": "medical_claim",
    "label": "医疗功效宣称",
    "pattern": r"(治疗|治愈|药用|处方|根治|医美级)",
    "penalty": 0.16,
    "message": "文案含医疗或过强功效表达，建议人工复核。",
  },
  {
    "key": "finance_claim",
    "label": "收益承诺",
    "pattern": r"(稳赚|保本|躺赚|无风险收益)",
    "penalty": 0.18,
    "message": "文案含收益承诺，可能触发金融类审核限制。",
  },
]


def evaluate_compliance(creative: dict, campaign: dict) -> dict:
  text = " ".join([creative["title"], creative["description"], creative["imageLine"]])
  issues: list[dict] = []

  for rule in RISK_RULES:
    if re.search(rule["pattern"], text):
      issues.append(
        {
          "key": rule["key"],
          "label": rule["label"],
          "penalty": rule["penalty"],
          "message": rule["message"],
        }
      )

  if len(creative["title"]) > 28:
    issues.append(
      {
        "key": "title_length",
        "label": "标题过长",
        "penalty": 0.05,
        "message": "标题较长，可能影响首屏阅读效率与点击。",
      }
    )

  if campaign["brandName"] and campaign["brandName"] not in text:
    issues.append(
      {
        "key": "brand_visibility",
        "label": "品牌露出不足",
        "penalty": 0.04,
        "message": "品牌词露出较弱，不利于记忆和信任建立。",
      }
    )

  risk_penalty = sum(item["penalty"] for item in issues)
  risk_level = "高" if risk_penalty >= 0.22 else "中" if risk_penalty >= 0.10 else "低"
  score_factor = max(0.55, 1 - risk_penalty)

  passes = []
  if campaign["brandName"] and campaign["brandName"] in text:
    passes.append("品牌露出清晰")
  if any(char.isdigit() for char in text):
    passes.append("包含数字化表达")
  if len(creative["sellingPoints"]) >= 3:
    passes.append("卖点结构完整")
  if not issues:
    passes.append("未命中高风险规则")

  return {
    "riskPenalty": risk_penalty,
    "riskLevel": risk_level,
    "scoreFactor": score_factor,
    "issues": issues,
    "passes": passes,
  }


def attach_compliance(creatives: list[dict], campaign: dict) -> list[dict]:
  return [{**creative, "compliance": evaluate_compliance(creative, campaign)} for creative in creatives]
