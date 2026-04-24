from backend.app.services.model_registry_service import get_active_model_entry, get_model_artifact, get_registry_payload
from backend.app.services.predictor_service import get_predictor_health


def get_model_runtime() -> dict:
  artifact = get_model_artifact()
  registry_entry = get_active_model_entry()
  meta = artifact["modelMeta"]
  return {
    "modelId": meta["modelId"],
    "family": meta["family"],
    "version": meta["version"],
    "trainedAt": meta["trainedAt"],
    "owner": meta["owner"],
    "description": meta["description"],
    "supportedObjectives": meta["supportedObjectives"],
    "supportedSurfaces": meta["supportedSurfaces"],
    "featureNames": meta["featureNames"],
    "objectiveWeights": artifact["objectiveWeights"],
    "surfaceWeights": artifact["surfaceWeights"],
    "calibration": artifact["calibration"],
    "registryEntry": registry_entry,
    "predictor": get_predictor_health(),
  }


def get_metric_weights(metric_name: str) -> dict:
  return get_model_artifact()["featureWeights"][metric_name]


def get_objective_weights() -> dict:
  return get_model_artifact()["objectiveWeights"]


def get_surface_weights() -> dict:
  return get_model_artifact()["surfaceWeights"]


def get_calibration(metric_name: str) -> dict:
  return get_model_artifact()["calibration"][metric_name]


def get_model_registry_view() -> dict:
  return get_registry_payload()


def get_model_health() -> dict:
  runtime = get_model_runtime()
  return {
    "modelId": runtime["modelId"],
    "version": runtime["version"],
    "family": runtime["family"],
    "registryEntry": runtime["registryEntry"],
    "predictor": runtime["predictor"],
  }
