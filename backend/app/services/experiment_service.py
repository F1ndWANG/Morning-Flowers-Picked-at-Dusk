from datetime import datetime


def create_history_record(campaign: dict, active_strategy: dict) -> dict:
  winner = active_strategy["winner"]
  return {
    "id": str(int(datetime.now().timestamp() * 1000)),
    "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "productName": campaign["productName"],
    "brandName": campaign["brandName"],
    "experimentMode": campaign["experimentMode"],
    "objective": campaign["objective"],
    "winnerTitle": winner["title"],
    "ctr": winner["metrics"]["ctr"],
    "cvr": winner["metrics"]["cvr"],
    "ecpm": winner["metrics"]["ecpm"],
    "riskLevel": winner.get("compliance", {}).get("riskLevel", "低"),
  }
