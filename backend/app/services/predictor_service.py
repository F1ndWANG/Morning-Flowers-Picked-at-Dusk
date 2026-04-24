import json
import pickle
from functools import lru_cache
from pathlib import Path

from backend.app.services.data_service import load_model_artifact, load_model_registry


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _clamp(value: float, lower: float, upper: float) -> float:
  return max(lower, min(upper, value))


class BasePredictor:
  predictor_type = "base"

  def __init__(self, artifact: dict, registry_entry: dict):
    self.artifact = artifact
    self.registry_entry = registry_entry

  def predict_metric(self, metric_name: str, features: dict, seed: float = 0) -> tuple[float, dict]:
    raise NotImplementedError

  def build_health(self) -> dict:
    return {
      "predictorType": self.predictor_type,
      "loadState": "ready",
      "source": "inline-artifact",
      "artifactFile": self.registry_entry.get("artifactFile"),
      "supportsExternalArtifact": False,
      "details": [],
    }


class LinearRuntimePredictor(BasePredictor):
  predictor_type = "linear-runtime"

  def predict_metric(self, metric_name: str, features: dict, seed: float = 0) -> tuple[float, dict]:
    weights = self.artifact["featureWeights"][metric_name]
    score = weights["base"]
    contributions = {}
    for key, value in features.items():
      contribution = weights.get(key, 0) * value
      contributions[key] = contribution
      score += contribution

    calibration = self.artifact["calibration"][metric_name]
    score = _clamp(score + seed, calibration["min"], calibration["max"])
    return score, contributions


class ArtifactBundlePredictor(BasePredictor):
  predictor_type = "artifact-bundle"

  def __init__(self, artifact: dict, registry_entry: dict):
    super().__init__(artifact, registry_entry)
    self.runtime_config = artifact.get("runtimeConfig", {})
    self.metric_heads = artifact.get("metricHeads", {})
    self.load_state = "ready"
    self.source = self.runtime_config.get("artifactFormat", "json-bundle")
    self.details: list[str] = []
    self.supports_external_artifact = bool(self.runtime_config.get("externalArtifactPath"))
    self._try_load_external_artifact()

  def _try_load_external_artifact(self) -> None:
    external_path = self.runtime_config.get("externalArtifactPath")
    if not external_path:
      self.details.append("Using metric heads embedded in the artifact bundle.")
      return

    path = Path(external_path)
    if not path.is_absolute():
      path = DATA_DIR / external_path

    if not path.exists():
      self.load_state = "fallback"
      self.details.append(f"External artifact missing: {path.name}. Falling back to inline metric heads.")
      return

    loader = self.runtime_config.get("externalLoader", "pickle-dict")
    try:
      if loader == "pickle-dict":
        with path.open("rb") as handle:
          payload = pickle.load(handle)
      elif loader == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
      else:
        raise ValueError(f"Unsupported externalLoader: {loader}")
    except Exception as error:  # noqa: BLE001
      self.load_state = "fallback"
      self.details.append(f"Artifact load failed: {error}. Falling back to inline metric heads.")
      return

    if "metricHeads" in payload:
      self.metric_heads = payload["metricHeads"]
      self.load_state = "loaded"
      self.source = f"external-{loader}"
      self.details.append(f"Loaded external artifact from {path.name}.")
    else:
      self.load_state = "fallback"
      self.details.append("External artifact payload is invalid. Falling back to inline metric heads.")

  def predict_metric(self, metric_name: str, features: dict, seed: float = 0) -> tuple[float, dict]:
    head = self.metric_heads[metric_name]
    score = head["intercept"]
    contributions = {}
    coefficients = head["coefficients"]
    for key, value in features.items():
      contribution = coefficients.get(key, 0) * value
      contributions[key] = contribution
      score += contribution

    calibration = self.artifact["calibration"][metric_name]
    score = _clamp(score + seed, calibration["min"], calibration["max"])
    return score, contributions

  def build_health(self) -> dict:
    return {
      "predictorType": self.predictor_type,
      "loadState": self.load_state,
      "source": self.source,
      "artifactFile": self.registry_entry.get("artifactFile"),
      "supportsExternalArtifact": self.supports_external_artifact,
      "details": self.details,
    }


def _build_predictor(artifact: dict, registry_entry: dict) -> BasePredictor:
  runtime_config = artifact.get("runtimeConfig", {})
  predictor_type = runtime_config.get("predictorType") or artifact.get("modelMeta", {}).get("family", "linear-runtime")
  if predictor_type in {"artifact-bundle", "artifact-runtime"} or "metricHeads" in artifact:
    return ArtifactBundlePredictor(artifact, registry_entry)
  return LinearRuntimePredictor(artifact, registry_entry)


@lru_cache(maxsize=1)
def get_active_predictor() -> BasePredictor:
  registry = load_model_registry()
  active_id = registry["activeModelId"]
  registry_entry = next(item for item in registry["models"] if item["modelId"] == active_id)
  artifact = load_model_artifact(registry_entry["artifactFile"])
  return _build_predictor(artifact, registry_entry)


def clear_predictor_cache() -> None:
  get_active_predictor.cache_clear()


def predict_metric(metric_name: str, features: dict, seed: float = 0) -> tuple[float, dict]:
  return get_active_predictor().predict_metric(metric_name, features, seed)


def get_predictor_health() -> dict:
  predictor = get_active_predictor()
  return predictor.build_health()
