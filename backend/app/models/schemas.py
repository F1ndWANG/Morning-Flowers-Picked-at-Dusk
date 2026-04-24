from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, model_validator


class CaseAssetInput(BaseModel):
  id: str | None = None
  kind: Literal["text", "image", "audio"]
  name: str = ""
  mimeType: str = ""
  dataBase64: str | None = None
  text: str | None = None


class CampaignRequest(BaseModel):
  caseText: str = ""
  caseAssets: List[CaseAssetInput] = Field(default_factory=list)
  caseUnderstandingMode: str = "api"
  productName: str = ""
  brandName: str = ""
  category: str = "beauty"
  price: float = Field(default=199, ge=0)
  audience: str = ""
  objective: str = "balanced"
  platform: str = "feed"
  tone: str = "premium"
  creativeCount: int = Field(default=8, ge=4, le=12)
  impressions: int = Field(default=100000, ge=1000)
  experimentMode: str = "full"
  diversityWeight: float = Field(default=0.08, ge=0, le=0.25)
  highlights: List[str] = Field(default_factory=list)
  textGenerationMode: str = "mock"
  imageGenerationMode: str = "mock"

  @model_validator(mode="after")
  def validate_case_presence(self) -> "CampaignRequest":
    if not self.caseText and not self.caseAssets and not (self.productName or self.brandName or self.highlights):
      raise ValueError("At least one case input is required: caseText, caseAssets, or product fields.")
    return self


class PipelineResponse(BaseModel):
  campaign: Dict[str, Any]
  case_context: Dict[str, Any]
  baseline: Dict[str, Any]
  strategies: Dict[str, Any]
  active_strategy: Dict[str, Any]
  ranked_creatives: List[Dict[str, Any]]
  prompts: Dict[str, Any]
  report: str
  integration_info: Dict[str, Any]
  surface_predictions: Dict[str, Any]
  prediction_runtime: Dict[str, Any]


class ExperimentRecord(BaseModel):
  id: str
  createdAt: str
  productName: str
  brandName: str
  experimentMode: str
  objective: str
  winnerTitle: str
  ctr: float
  cvr: float
  ecpm: float
  riskLevel: str


class HistoryResponse(BaseModel):
  items: List[ExperimentRecord]


class ModelActivationRequest(BaseModel):
  modelId: str
