# AIGCSAR Formal Prediction System

This project is a formalized interview-ready prototype for an AIGC algorithm engineer role. It is no longer only a frontend demo. The backend now executes a complete pipeline:

- Accept a case in `text / image / audio`
- Run multimodal case understanding
- Generate multiple ad titles, descriptions, selling points, and image-copy lines
- Produce a sample-image prompt and optionally call an image API later
- Predict `CTR / CVR / eCPM`
- Rerank creatives with multi-objective weights and diversity constraints
- Return projections for `feed / search / video / mall`

## Current Capabilities

- Multimodal input: text, image, and audio case assets
- Formal prediction pipeline driven by FastAPI
- Creative generation with mock mode and reserved real API integration slots
- Sample-image prompt generation with reserved image API integration slots
- Runtime prediction metadata for the active model
- Predictor health metadata for the active model
- Model registry and activation workflow
- Artifact-backed predictor runtime for trained-model migration demos
- Offline benchmark on built-in cases
- Experiment history and snapshot export

## Key Directories

- [index.html](/E:/AIGCSAR/index.html): frontend entry page
- [src/app/controller.js](/E:/AIGCSAR/src/app/controller.js): frontend orchestration and rendering
- [src/ui/dom.js](/E:/AIGCSAR/src/ui/dom.js): form reading and payload assembly
- [backend/app/api/routes.py](/E:/AIGCSAR/backend/app/api/routes.py): API routes
- [backend/app/services/pipeline_service.py](/E:/AIGCSAR/backend/app/services/pipeline_service.py): end-to-end pipeline
- [backend/app/services/multimodal_service.py](/E:/AIGCSAR/backend/app/services/multimodal_service.py): text/image/audio understanding
- [backend/app/services/llm_service.py](/E:/AIGCSAR/backend/app/services/llm_service.py): text LLM integration slot
- [backend/app/services/image_generation_service.py](/E:/AIGCSAR/backend/app/services/image_generation_service.py): image generation integration slot
- [backend/app/services/scoring_service.py](/E:/AIGCSAR/backend/app/services/scoring_service.py): CTR/CVR/eCPM prediction
- [backend/app/services/model_runtime_service.py](/E:/AIGCSAR/backend/app/services/model_runtime_service.py): active model runtime metadata
- [backend/app/services/predictor_service.py](/E:/AIGCSAR/backend/app/services/predictor_service.py): pluggable predictor runtime and artifact loading
- [backend/app/services/model_registry_service.py](/E:/AIGCSAR/backend/app/services/model_registry_service.py): model registry and activation
- [backend/app/services/benchmark_service.py](/E:/AIGCSAR/backend/app/services/benchmark_service.py): offline benchmark runner

## API Endpoints

- `GET /api/v1/catalog`: category, objective, platform, and tone config
- `GET /api/v1/samples`: built-in demo cases
- `GET /api/v1/integrations`: LLM and image integration status
- `GET /api/v1/models/runtime`: active model runtime metadata
- `GET /api/v1/models/health`: active predictor runtime health and source
- `GET /api/v1/models/registry`: registered models
- `POST /api/v1/models/activate`: switch active model
- `GET /api/v1/benchmarks/offline`: run offline benchmark on built-in cases
- `POST /api/v1/pipeline/run`: execute the full pipeline
- `POST /api/v1/experiments/snapshot`: export a snapshot JSON
- `GET /api/v1/experiments/history`: list recent experiment history
- `POST /api/v1/experiments/history`: run and persist one record
- `DELETE /api/v1/experiments/history`: clear history

## API Integration Slots You Need to Fill Later

Text and multimodal understanding:

- `AIGCSAR_LLM_API_KEY`
- `AIGCSAR_LLM_MODEL`
- `AIGCSAR_LLM_API_BASE`
- `AIGCSAR_VISION_MODEL`
- `AIGCSAR_AUDIO_MODEL`

Image generation:

- `AIGCSAR_IMAGE_API_KEY`
- `AIGCSAR_IMAGE_MODEL`
- `AIGCSAR_IMAGE_API_BASE`
- `AIGCSAR_IMAGE_SIZE`

The template is in [backend/.env.example](/E:/AIGCSAR/backend/.env.example).

## Run

Frontend:

```powershell
cd E:\AIGCSAR
.\scripts\start_frontend.ps1
```

Backend:

```powershell
cd E:\AIGCSAR
.\scripts\start_backend.ps1
```

Then open [http://localhost:8080](http://localhost:8080).

## Demo Flow for Interview

1. Load one built-in case and run the full pipeline.
2. Show case understanding, generated creative pool, and the predicted top winner.
3. Open the model runtime panel to explain explainable prediction features and objective weights.
4. Open the model registry and switch between `linear-runtime` and `artifact-runtime`.
5. Use the predictor runtime card to explain inline weights vs artifact-backed inference.
6. Refresh the offline benchmark to compare aggregate behavior across cases.
7. Export a snapshot to show experiment traceability.
