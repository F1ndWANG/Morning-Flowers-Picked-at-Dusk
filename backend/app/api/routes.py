from fastapi import APIRouter

from backend.app.core.settings import get_integration_catalog
from backend.app.models.schemas import CampaignRequest, HistoryResponse, ModelActivationRequest, PipelineResponse
from backend.app.services.data_service import load_catalog_data, load_sample_data
from backend.app.services.experiment_service import create_history_record
from backend.app.services.history_service import clear_history, load_history, save_history_record
from backend.app.services.benchmark_service import run_offline_benchmark
from backend.app.services.model_registry_service import activate_model
from backend.app.services.model_runtime_service import get_model_health, get_model_registry_view, get_model_runtime
from backend.app.services.pipeline_service import run_pipeline
from backend.app.services.snapshot_service import build_snapshot_payload, save_snapshot

router = APIRouter()


@router.get("/catalog")
def get_catalog() -> dict:
  return load_catalog_data()


@router.get("/samples")
def get_samples() -> dict:
  return load_sample_data()


@router.get("/integrations")
def get_integrations() -> dict:
  return get_integration_catalog()


@router.get("/models/runtime")
def get_runtime_model() -> dict:
  return get_model_runtime()


@router.get("/models/registry")
def get_model_registry() -> dict:
  return get_model_registry_view()


@router.get("/models/health")
def get_runtime_model_health() -> dict:
  return get_model_health()


@router.post("/models/activate")
def activate_runtime_model(payload: ModelActivationRequest) -> dict:
  return activate_model(payload.modelId)


@router.get("/benchmarks/offline")
def get_offline_benchmark() -> dict:
  return run_offline_benchmark()


@router.post("/pipeline/run", response_model=PipelineResponse)
def run_pipeline_endpoint(payload: CampaignRequest) -> PipelineResponse:
  return PipelineResponse(**run_pipeline(payload.model_dump()))


@router.get("/experiments/history", response_model=HistoryResponse)
def get_experiment_history() -> HistoryResponse:
  return HistoryResponse(items=load_history())


@router.post("/experiments/history", response_model=HistoryResponse)
def save_experiment_history(payload: CampaignRequest) -> HistoryResponse:
  result = run_pipeline(payload.model_dump())
  record = create_history_record(result["campaign"], result["active_strategy"])
  return HistoryResponse(items=save_history_record(record))


@router.post("/experiments/snapshot")
def create_experiment_snapshot(payload: CampaignRequest) -> dict:
  payload_dict = payload.model_dump()
  result = run_pipeline(payload_dict)
  snapshot = save_snapshot(build_snapshot_payload(payload_dict, result))
  return snapshot


@router.delete("/experiments/history", response_model=HistoryResponse)
def clear_experiment_history() -> HistoryResponse:
  return HistoryResponse(items=clear_history())
