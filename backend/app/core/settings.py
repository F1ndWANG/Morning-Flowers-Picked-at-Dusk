from dataclasses import asdict, dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]


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


def get_settings() -> IntegrationSettings:
  _bootstrap_env()
  llm_model = os.getenv("AIGCSAR_LLM_MODEL", "MiniMax-M2.5")
  llm_api_base = os.getenv("AIGCSAR_LLM_API_BASE", "https://api.minimaxi.com/v1")
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
    image_model=os.getenv("AIGCSAR_IMAGE_MODEL", "Qwen/Qwen-Image"),
    image_size=os.getenv("AIGCSAR_IMAGE_SIZE", "1328x1328"),
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
      "baseUrl": settings.image_api_base,
      "requiredEnv": ["AIGCSAR_IMAGE_API_KEY", "AIGCSAR_IMAGE_MODEL", "AIGCSAR_IMAGE_API_BASE", "AIGCSAR_IMAGE_SIZE"],
      "apiMarked": True,
      "note": "Image generation now supports a real SiliconFlow image API when configured, and falls back to prompt-only mode otherwise.",
    },
    "raw": asdict(settings),
  }
  catalog["raw"]["llm_api_key"] = _mask_secret(settings.llm_api_key)
  catalog["raw"]["image_api_key"] = _mask_secret(settings.image_api_key)
  return catalog
