# AIGCSAR: AIGC Advertising Creative Generation and Prediction System

AIGCSAR is an end-to-end advertising creative system that combines AIGC generation, multimodal case understanding, CTR/CVR/eCPM prediction, and multi-objective reranking.

The system accepts a product campaign task, generates multiple ad creative candidates, predicts their performance across search, feed, video, and mall recommendation surfaces, and lets users compare and switch between ranked creative plans in a frontend workbench.

## Features

- **Campaign task input**: product, brand, category, price, audience, platform, tone, optimization objective, case text, selling-point hints, image assets, and audio assets.
- **Multimodal case understanding**: converts text, image, and audio inputs into a unified campaign context for downstream generation and prediction.
- **Multi-creative generation**: generates multiple candidate ad titles, descriptions, selling points, and image-copy lines for one task.
- **Text generation modes**: supports local mock templates and real LLM API integration.
- **Image generation pipeline**: builds structured image prompts internally and optionally calls an image generation API. The frontend only shows final ad images or image-copy lines.
- **Performance prediction**: predicts CTR, CVR, eCPM, confidence, confidence intervals, and risk-adjusted eCPM for each creative.
- **Search/ads/recommendation forecasting**: estimates each creative's performance on search ads, feed ads, video recommendation, and mall recommendation surfaces.
- **Multi-objective reranking**: ranks creative candidates using CTR, CVR, eCPM, risk-adjusted eCPM, confidence, compliance score, and diversity-aware MMR penalty.
- **Interactive frontend workbench**: displays a ranked creative queue and lets users switch between all generated plans.
- **Model runtime management**: includes model registry, active model metadata, predictor health, offline benchmark, experiment history, and snapshot export.

## System Flow

```text
User task / uploaded assets
        ↓
Multimodal case understanding
        ↓
Generate multiple ad creatives
        ↓
Generate ad image / image-copy line
        ↓
Predict CTR / CVR / eCPM for each creative
        ↓
Forecast search / feed / video / mall performance
        ↓
Multi-objective rerank
        ↓
Frontend creative comparison and switching
```

## Project Structure

```text
AIGCSAR/
├── index.html                         # Frontend entry
├── src/
│   ├── app/                           # Frontend API client and controller
│   ├── ui/                            # DOM, rendering, UI helpers
│   ├── core/                          # Local fallback pipeline modules
│   ├── styles/                        # Workbench styles
│   └── utils/                         # Formatting and text utilities
├── backend/
│   ├── app/
│   │   ├── api/                       # FastAPI routes
│   │   ├── core/                      # Catalog and integration settings
│   │   ├── models/                    # Request/response schemas
│   │   └── services/                  # Pipeline, generation, scoring, rerank
│   ├── data/                          # Catalog, sample cases, model artifacts
│   ├── requirements.txt
│   └── .env.example                   # API configuration template
├── docs/
│   └── ARCHITECTURE.md
└── scripts/
    ├── start_backend.ps1
    └── start_frontend.ps1
```

## Main Backend Modules

- `backend/app/services/pipeline_service.py`: orchestrates the full generation, prediction, rerank, and report pipeline.
- `backend/app/services/multimodal_service.py`: handles text/image/audio case understanding.
- `backend/app/services/generator_service.py`: builds baseline and template creative drafts.
- `backend/app/services/llm_service.py`: calls real LLM APIs or falls back to local templates.
- `backend/app/services/image_generation_service.py`: builds image-generation prompts and calls image APIs.
- `backend/app/services/scoring_service.py`: extracts features and predicts CTR/CVR/eCPM.
- `backend/app/services/predictor_service.py`: loads the active prediction artifact and runs metric heads.
- `backend/app/services/strategy_service.py`: performs multi-objective reranking with diversity control.
- `backend/app/services/model_registry_service.py`: manages model registry and activation.
- `backend/app/services/benchmark_service.py`: runs offline benchmark cases.

## API Endpoints

- `GET /api/v1/catalog`: category, objective, platform, and tone configuration.
- `GET /api/v1/samples`: built-in sample campaign cases.
- `GET /api/v1/integrations`: LLM, multimodal, and image API integration status.
- `GET /api/v1/models/runtime`: active model runtime metadata.
- `GET /api/v1/models/health`: active predictor runtime health.
- `GET /api/v1/models/registry`: available model registry.
- `POST /api/v1/models/activate`: switch active prediction model.
- `GET /api/v1/benchmarks/offline`: run offline benchmark cases.
- `POST /api/v1/pipeline/run`: execute the full creative generation and prediction pipeline.
- `GET /api/v1/experiments/history`: list experiment history.
- `POST /api/v1/experiments/history`: run and persist one experiment record.
- `DELETE /api/v1/experiments/history`: clear experiment history.
- `POST /api/v1/experiments/snapshot`: export one experiment snapshot.

## Environment Configuration

Copy `backend/.env.example` to `backend/.env.local` and fill in the required API settings.

```powershell
Copy-Item backend/.env.example backend/.env.local
```

Text and multimodal generation:

```text
AIGCSAR_LLM_PROVIDER=
AIGCSAR_LLM_API_BASE=
AIGCSAR_LLM_API_KEY=
AIGCSAR_LLM_MODEL=
AIGCSAR_VISION_MODEL=
AIGCSAR_AUDIO_MODEL=
```

Image generation:

```text
AIGCSAR_IMAGE_PROVIDER=
AIGCSAR_IMAGE_API_BASE=
AIGCSAR_IMAGE_API_KEY=
AIGCSAR_IMAGE_MODEL=
AIGCSAR_IMAGE_SIZE=
AIGCSAR_IMAGE_TIMEOUT_SECONDS=90
AIGCSAR_IMAGE_CONCURRENCY=3
AIGCSAR_IMAGE_CACHE_ENABLED=true
```

Image generation performance controls:

- `AIGCSAR_IMAGE_CONCURRENCY`: number of images generated in parallel. Recommended `3`; raise only if the provider rate limit allows it.
- `AIGCSAR_IMAGE_TIMEOUT_SECONDS`: timeout for one image request. Lower values fail faster and use local fallback sooner.
- `AIGCSAR_IMAGE_CACHE_ENABLED`: caches image results by provider, model, size, and prompt, so repeated tests reuse existing image URLs.

`.env.local` is ignored by Git and should not be committed.

## Run Locally

Install backend dependencies:

```powershell
cd E:\AIGCSAR
pip install -r backend/requirements.txt
```

Start backend:

```powershell
cd E:\AIGCSAR
.\scripts\start_backend.ps1
```

Start frontend:

```powershell
cd E:\AIGCSAR
.\scripts\start_frontend.ps1
```

Open:

```text
http://localhost:8080
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

## Usage

1. Fill in the campaign task fields or select a built-in sample.
2. Choose case understanding, text generation, and image generation modes.
3. Click **Generate and Predict**.
4. Review the ranked creative queue.
5. Switch between candidate creatives to compare title, description, selling points, image copy, generated image, and predicted performance.
6. Use the search/feed/video/mall forecast panel to understand surface-specific performance.

## Prediction Model Notes

The current predictor is an explainable artifact-backed runtime designed for fast iteration and transparent scoring. It extracts structured creative and campaign features, predicts CTR/CVR, derives eCPM, estimates confidence intervals, and supports model registry switching.

The ranking layer now includes mainstream search/ads/recommendation prediction ideas:

- Wide&Deep/DCN-style feature crossing: brand-sell-point, trust-price, CTA-surface, audience-context, and image-copy alignment interactions.
- DeepFM-style interaction proxy: selling-point density, trust depth, readability, image-copy consistency, and multimodal grounding.
- ESMM-style multi-task consistency: CTR, CVR, CTCVR, post-click CVR, and click-conversion consistency are calculated together.
- Industrial reranking signals: the final rank score uses CTR, CVR, eCPM, risk-adjusted eCPM, confidence, compliance, diversity, Pareto bonus, DCN cross score, multi-task consistency, and user-interest proxy.

The prediction layer can be replaced with production-grade models such as DeepFM, DCNv2, MMoE, PLE, ESMM, or a learning-to-rank model trained on real impression/click/conversion logs.

## Git Safety

The repository ignores:

- `backend/.env.local`
- `backend/.env`
- runtime artifacts
- generated screenshots
- backend logs
- Python cache files
- browser profile/cache files

Do not commit API keys or generated private data.
