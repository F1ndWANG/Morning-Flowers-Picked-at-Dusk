import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(filename: str) -> dict:
  path = DATA_DIR / filename
  return json.loads(path.read_text(encoding="utf-8"))


def load_catalog_data() -> dict:
  return _load_json("catalog.json")


def load_sample_data() -> dict:
  return _load_json("samples.json")


def load_model_bundle() -> dict:
  return _load_json("model_bundle.json")


def load_model_registry() -> dict:
  return _load_json("model_registry.json")


def load_model_artifact(filename: str) -> dict:
  return _load_json(filename)


def _save_json(filename: str, payload: dict) -> None:
  path = DATA_DIR / filename
  path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_model_registry(payload: dict) -> dict:
  _save_json("model_registry.json", payload)
  return payload
