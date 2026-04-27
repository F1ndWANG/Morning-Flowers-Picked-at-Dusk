from dataclasses import asdict, dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]


SILICONFLOW_IMAGE_MODELS = [
  {
    "modelId": "black-forest-labs/FLUX.1-schnell",
    "label": "FLUX.1-schnell",
    "pricePerImageUsd": 0.0014,
    "defaultSize": "1024x1024",
    "qualityTier": "fast-low-cost",
    "recommendation": "最低成本优先，适合快速预览和批量验证。",
  },
  {
    "modelId": "Tongyi-MAI/Z-Image-Turbo",
    "label": "Z-Image-Turbo",
    "pricePerImageUsd": 0.005,
    "defaultSize": "1024x1024",
    "qualityTier": "cost-effective",
    "recommendation": "低价且综合质量较好，适合默认业务生成。",
  },
  {
    "modelId": "Kwai-Kolors/Kolors",
    "label": "Kolors",
    "pricePerImageUsd": 0.01,
    "defaultSize": "1024x1024",
    "qualityTier": "balanced",
    "recommendation": "适合中文广告视觉与通用营销图片。",
  },
  {
    "modelId": "Qwen/Qwen-Image",
    "label": "Qwen-Image",
    "pricePerImageUsd": 0.02,
    "defaultSize": "1328x1328",
    "qualityTier": "text-layout",
    "recommendation": "适合复杂中英文文字和广告排版，但成本更高。",
  },
  {
    "modelId": "black-forest-labs/FLUX.1-dev",
    "label": "FLUX.1-dev",
    "pricePerImageUsd": 0.025,
    "defaultSize": "1024x1024",
    "qualityTier": "high-quality",
    "recommendation": "质量更高，适合最终精选图验证。",
  },
]


def get_image_model_catalog() -> list[dict]:
  return sorted(SILICONFLOW_IMAGE_MODELS, key=lambda item: item["pricePerImageUsd"])


def get_image_model_config(model_id: str | None) -> dict:
  catalog = get_image_model_catalog()
  for item in catalog:
    if item["modelId"] == model_id:
      return item
  return catalog[0]


def _load_env_file(path: Path) -> None:
  if not path.exists():
    return

  for raw_line in path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    os.environ[key] = value


def _bootstrap_env() -> None:
  _load_env_file(BASE_DIR / ".env.local")
  _load_env_file(BASE_DIR / ".env")


@dataclass
class IntegrationSettings:
  llm_provider: str
  llm_api_base: str
  llm_api_key: str
  llm_model: str
  vision_model: str
  audio_model: str
  image_provider: str
  image_api_base: str
  image_api_key: str
  image_model: str
  image_size: str
  image_timeout_seconds: int
  image_concurrency: int
  image_cache_enabled: bool


def get_settings() -> IntegrationSettings:
  _bootstrap_env()
  llm_model = os.getenv("AIGCSAR_LLM_MODEL", "MiniMax-M2.5")
  llm_api_base = os.getenv("AIGCSAR_LLM_API_BASE", "https://api.minimaxi.com/v1")
  image_timeout_seconds = int(os.getenv("AIGCSAR_IMAGE_TIMEOUT_SECONDS", "90"))
  image_concurrency = int(os.getenv("AIGCSAR_IMAGE_CONCURRENCY", "3"))
  return IntegrationSettings(
    llm_provider=os.getenv("AIGCSAR_LLM_PROVIDER", "minimax-openai-compatible"),
    llm_api_base=llm_api_base,
    llm_api_key=os.getenv("AIGCSAR_LLM_API_KEY", ""),
    llm_model=llm_model,
    vision_model=os.getenv("AIGCSAR_VISION_MODEL", llm_model),
    audio_model=os.getenv("AIGCSAR_AUDIO_MODEL", "Speech-02-HD"),
    image_provider=os.getenv("AIGCSAR_IMAGE_PROVIDER", "openai-compatible"),
    image_api_base=os.getenv("AIGCSAR_IMAGE_API_BASE", "https://api.openai.com/v1"),
    image_api_key=os.getenv("AIGCSAR_IMAGE_API_KEY", ""),
    image_model=os.getenv("AIGCSAR_IMAGE_MODEL", get_image_model_catalog()[0]["modelId"]),
    image_size=os.getenv("AIGCSAR_IMAGE_SIZE", get_image_model_catalog()[0]["defaultSize"]),
    image_timeout_seconds=max(15, min(image_timeout_seconds, 240)),
    image_concurrency=max(1, min(image_concurrency, 6)),
    image_cache_enabled=os.getenv("AIGCSAR_IMAGE_CACHE_ENABLED", "true").lower() not in {"0", "false", "no"},
  )


def _mask_secret(value: str) -> str:
  if not value:
    return ""
  if len(value) <= 10:
    return "***configured***"
  return f"{value[:6]}***{value[-4:]}"


def get_integration_catalog() -> dict:
  settings = get_settings()
  text_configured = bool(settings.llm_api_key)
  image_configured = bool(settings.image_api_key)
  catalog = {
    "multimodalUnderstanding": {
      "provider": settings.llm_provider,
      "defaultMode": "mock",
      "configured": text_configured,
      "model": settings.vision_model,
      "baseUrl": settings.llm_api_base,
      "requiredEnv": ["AIGCSAR_LLM_API_KEY", "AIGCSAR_VISION_MODEL", "AIGCSAR_AUDIO_MODEL"],
      "apiMarked": True,
      "supports": ["text", "image", "audio"],
      "note": "Case understanding stays local by default. It can be upgraded later with a dedicated multimodal mode.",
    },
    "textGeneration": {
      "provider": settings.llm_provider,
      "defaultMode": "api" if text_configured else "mock",
      "configured": text_configured,
      "model": settings.llm_model,
      "baseUrl": settings.llm_api_base,
      "requiredEnv": ["AIGCSAR_LLM_API_KEY", "AIGCSAR_LLM_MODEL", "AIGCSAR_LLM_API_BASE"],
      "apiMarked": True,
      "note": "Ad title, description, selling-point, and image-copy generation now supports MiniMax via the OpenAI-compatible endpoint.",
    },
    "imageGeneration": {
      "provider": settings.image_provider,
      "defaultMode": "api" if image_configured else "mock",
      "configured": image_configured,
      "model": settings.image_model,
      "availableModels": get_image_model_catalog(),
      "baseUrl": settings.image_api_base,
      "requiredEnv": [
        "AIGCSAR_IMAGE_API_KEY",
        "AIGCSAR_IMAGE_MODEL",
        "AIGCSAR_IMAGE_API_BASE",
        "AIGCSAR_IMAGE_SIZE",
        "AIGCSAR_IMAGE_TIMEOUT_SECONDS",
        "AIGCSAR_IMAGE_CONCURRENCY",
      ],
      "apiMarked": True,
      "note": "Image generation supports SiliconFlow-compatible APIs, concurrent generation, local prompt caching, and SVG fallback.",
    },
    "raw": asdict(settings),
  }
  catalog["raw"]["llm_api_key"] = _mask_secret(settings.llm_api_key)
  catalog["raw"]["image_api_key"] = _mask_secret(settings.image_api_key)
  return catalog
