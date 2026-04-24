from functools import lru_cache

from backend.app.services.data_service import load_model_artifact, load_model_registry, save_model_registry
from backend.app.services.predictor_service import clear_predictor_cache


@lru_cache(maxsize=1)
def get_model_registry() -> dict:
  registry = load_model_registry()
  models = registry.get("models", [])
  active_id = registry.get("activeModelId")
  active_model = next((item for item in models if item["modelId"] == active_id), models[0] if models else None)
  return {
    "activeModelId": active_id,
    "activeModel": active_model,
    "models": models,
  }


@lru_cache(maxsize=4)
def get_model_artifact(model_id: str | None = None) -> dict:
  registry = get_model_registry()
  target_id = model_id or registry["activeModelId"]
  target = next(item for item in registry["models"] if item["modelId"] == target_id)
  return load_model_artifact(target["artifactFile"])


def get_active_model_entry() -> dict:
  return get_model_registry()["activeModel"]


def get_registry_payload() -> dict:
  return get_model_registry()


def activate_model(model_id: str) -> dict:
  registry = load_model_registry()
  models = registry.get("models", [])
  if not any(item["modelId"] == model_id for item in models):
    raise ValueError(f"Unknown modelId: {model_id}")

  updated_models = []
  for item in models:
    updated = dict(item)
    updated["status"] = "active" if item["modelId"] == model_id else "candidate"
    updated_models.append(updated)

  updated_registry = {
    **registry,
    "activeModelId": model_id,
    "models": updated_models,
  }
  save_model_registry(updated_registry)
  get_model_registry.cache_clear()
  get_model_artifact.cache_clear()
  clear_predictor_cache()
  return get_registry_payload()
