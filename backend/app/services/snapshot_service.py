import json
from datetime import datetime
from pathlib import Path


SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots"


def _ensure_dir() -> None:
  SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def build_snapshot_payload(request_payload: dict, result: dict) -> dict:
  winner = result["active_strategy"]["winner"]
  return {
    "snapshotId": datetime.now().strftime("%Y%m%d-%H%M%S-%f"),
    "createdAt": datetime.now().isoformat(),
    "request": request_payload,
    "campaign": result["campaign"],
    "caseContext": result["case_context"],
    "winner": {
      "title": winner["title"],
      "description": winner["description"],
      "imageLine": winner["imageLine"],
      "sellingPoints": winner["sellingPoints"],
      "metrics": winner["metrics"],
      "riskLevel": winner.get("compliance", {}).get("riskLevel", "低"),
      "reasons": winner["reasons"],
      "imagePrompt": winner.get("imagePrompt", ""),
    },
    "surfacePredictions": result["surface_predictions"],
    "predictionRuntime": result["prediction_runtime"],
    "integrationInfo": result["integration_info"],
    "topCreatives": result["ranked_creatives"][:5],
    "report": result["report"],
  }


def save_snapshot(snapshot_payload: dict) -> dict:
  _ensure_dir()
  filename = f"{snapshot_payload['snapshotId']}.json"
  path = SNAPSHOT_DIR / filename
  body = json.dumps(snapshot_payload, ensure_ascii=False, indent=2)
  path.write_text(body, encoding="utf-8")
  return {
    "snapshotId": snapshot_payload["snapshotId"],
    "filename": filename,
    "sizeBytes": len(body.encode("utf-8")),
    "path": str(path),
    "payload": snapshot_payload,
  }
