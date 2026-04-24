import json
from pathlib import Path


MAX_ITEMS = 20
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_FILE = DATA_DIR / "experiment_history.json"


def _ensure_data_file() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")


def load_history() -> list[dict]:
  _ensure_data_file()
  try:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return []


def save_history_record(record: dict) -> list[dict]:
  history = load_history()
  next_history = [record, *history][:MAX_ITEMS]
  DATA_FILE.write_text(json.dumps(next_history, ensure_ascii=False, indent=2), encoding="utf-8")
  return next_history


def clear_history() -> list[dict]:
  _ensure_data_file()
  DATA_FILE.write_text("[]", encoding="utf-8")
  return []
