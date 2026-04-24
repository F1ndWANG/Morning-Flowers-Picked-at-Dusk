from statistics import mean

from backend.app.services.data_service import load_sample_data
from backend.app.services.pipeline_service import run_pipeline


def _build_request(sample: dict) -> dict:
  highlights = sample.get("highlights", "")
  if isinstance(highlights, str):
    highlight_list = [item.strip() for item in highlights.replace("\n", ",").split(",") if item.strip()]
  else:
    highlight_list = highlights

  return {
    "caseText": sample.get("caseText", ""),
    "caseAssets": [],
    "productName": sample.get("productName", ""),
    "brandName": sample.get("brandName", ""),
    "category": sample.get("category", "beauty"),
    "price": sample.get("price", 199),
    "audience": sample.get("audience", ""),
    "objective": sample.get("objective", "balanced"),
    "platform": sample.get("platform", "feed"),
    "tone": sample.get("tone", "premium"),
    "creativeCount": sample.get("creativeCount", 8),
    "impressions": sample.get("impressions", 100000),
    "experimentMode": sample.get("experimentMode", "full"),
    "diversityWeight": sample.get("diversityWeight", 0.08),
    "highlights": highlight_list,
    "textGenerationMode": sample.get("textGenerationMode", "mock"),
    "imageGenerationMode": sample.get("imageGenerationMode", "mock"),
  }


def run_offline_benchmark() -> dict:
  samples = load_sample_data().get("samples", {})
  rows = []

  for sample_key, sample in samples.items():
    payload = _build_request(sample)
    result = run_pipeline(payload)
    baseline = result["baseline"]
    winner = result["active_strategy"]["winner"]
    rows.append(
      {
        "sampleKey": sample_key,
        "label": sample.get("label", sample_key),
        "productName": result["campaign"]["productName"],
        "platform": result["campaign"]["platform"],
        "objective": result["campaign"]["objective"],
        "baselineCtr": baseline["metrics"]["ctr"],
        "baselineCvr": baseline["metrics"]["cvr"],
        "baselineEcpm": baseline["metrics"]["ecpm"],
        "winnerCtr": winner["metrics"]["ctr"],
        "winnerCvr": winner["metrics"]["cvr"],
        "winnerEcpm": winner["metrics"]["ecpm"],
        "coverageRate": result["active_strategy"]["metrics"]["coverageRate"],
        "diversity": result["active_strategy"]["metrics"]["averageDiversity"],
        "winnerTitle": winner["title"],
      }
    )

  benchmark = {
    "sampleCount": len(rows),
    "avgWinnerCtr": mean(row["winnerCtr"] for row in rows) if rows else 0,
    "avgWinnerCvr": mean(row["winnerCvr"] for row in rows) if rows else 0,
    "avgWinnerEcpm": mean(row["winnerEcpm"] for row in rows) if rows else 0,
    "avgCoverageRate": mean(row["coverageRate"] for row in rows) if rows else 0,
    "avgDiversity": mean(row["diversity"] for row in rows) if rows else 0,
    "bestEcpmSample": max(rows, key=lambda item: item["winnerEcpm"]) if rows else None,
    "rows": rows,
  }
  return benchmark
