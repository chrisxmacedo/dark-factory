# CLAUDE.md -- {PROJECT_NAME}-ml

This file covers coding conventions for this ML serving service. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack

- **Python 3.12**
- **API framework:** FastAPI (reuses starter-api patterns)
- **Model registry:** MLflow (experiment tracking, model versioning, promotion)
- **ML frameworks:** scikit-learn, XGBoost, PyTorch (project-dependent)
- **Validation:** Pydantic v2 (request/response schemas)
- **Feature store:** Redis (pre-computed feature retrieval)
- **Database:** PostgreSQL via SQLAlchemy + Alembic (metadata, predictions log)
- **Logging:** structlog (structured JSON)
- **Observability:** OpenTelemetry SDK (traces, metrics)
- **Testing:** pytest + hypothesis (property-based testing for model inputs)
- **Linting/formatting:** ruff
- **Type checking:** mypy (strict)
- **Package manager:** uv (or pip with requirements.txt)
- **GPU:** Optional CUDA support via PyTorch/ONNX Runtime

---

## Project structure (planned)

```
src/
├── main.py                    # FastAPI app entry point
├── api/
│   ├── routes/
│   │   ├── predict.py         # POST /predict (single), POST /predict/batch
│   │   ├── health.py          # GET /health (includes model readiness)
│   │   └── models.py          # GET /models (list loaded models, versions)
│   ├── schemas/
│   │   ├── predict.py         # Pydantic request/response schemas
│   │   └── health.py          # Health check response schema
│   └── middleware/
│       ├── logging.py         # Request/response logging
│       └── metrics.py         # Prediction latency, throughput metrics
├── models/
│   ├── registry.py            # MLflow client: load, version, promote
│   ├── loader.py              # Model loading and warm-up on startup
│   └── base.py                # Abstract base class for model wrappers
├── inference/
│   ├── predictor.py           # Sync single-prediction logic
│   └── batch.py               # Async batch inference (chunked processing)
├── features/
│   ├── store.py               # Redis feature store client
│   └── transforms.py          # Feature engineering / preprocessing
├── monitoring/
│   ├── drift.py               # Input/output drift detection (KS test, PSI)
│   └── metrics.py             # Model performance metrics collection
├── lib/
│   ├── config.py              # Settings via pydantic-settings
│   ├── database.py            # SQLAlchemy engine + session factory
│   ├── redis.py               # Redis client singleton
│   ├── logger.py              # structlog configuration
│   └── otel.py                # OpenTelemetry SDK initialisation
├── migrations/                # Alembic migrations
│   └── versions/
└── tests/
    ├── api/                   # API endpoint tests
    ├── models/                # Model loading and registry tests
    ├── inference/             # Prediction logic tests
    ├── features/              # Feature store and transform tests
    ├── monitoring/            # Drift detection tests
    ├── conftest.py            # Shared fixtures
    └── evaluation/            # Model evaluation metrics (accuracy, F1, AUC)
```

---

## Conventions

### General
- All functions must have type annotations (enforced by mypy strict)
- Never use `print()` -- use structlog via `src/lib/logger.py`
- Never hardcode secrets or URLs -- read from environment via pydantic-settings
- Never commit `.env` -- use `.env.example` as the reference
- Follow starter-api patterns for FastAPI structure, middleware, and error handling

### Model serving
- Models are loaded once at startup and held in memory -- never reload per-request
- Use the abstract base class in `src/models/base.py` for all model wrappers
- Every model wrapper implements `predict(features) -> prediction` and
  `predict_batch(features_list) -> predictions_list`
- Model version is always included in prediction responses
- Warm up models on startup by running a dummy prediction before accepting traffic

### Model registry (MLflow)
- Every trained model is registered in MLflow with experiment ID and run metadata
- Models progress through stages: None -> Staging -> Production -> Archived
- The serving service loads the "Production" stage model by default
- Model loading supports version pinning via environment variable for rollback

### Feature store
- Pre-computed features are stored in Redis with TTL
- Feature retrieval uses `src/features/store.py` -- never read features from
  the database at prediction time
- Feature transforms in `src/features/transforms.py` must be deterministic
  and match the transforms used during training
- Log feature values alongside predictions for monitoring and debugging

### Sync API (POST /predict)
- Accepts a single input, returns a single prediction
- Target latency: < 100ms p99 (excluding model-dependent compute)
- Validate input with Pydantic before passing to the model
- Return: `{ "prediction": ..., "confidence": ..., "model_version": "...", "request_id": "..." }`

### Batch inference (POST /predict/batch)
- Accepts a list of inputs, processes in configurable chunk sizes
- Returns results asynchronously (poll endpoint or webhook callback)
- Checkpoint progress for large batches (resumable on failure)
- Rate-limit batch size to prevent resource exhaustion

### Drift monitoring
- Track input feature distributions against training baseline
- Track prediction output distributions over time
- Use statistical tests (Kolmogorov-Smirnov, Population Stability Index)
- Alert when drift exceeds configurable thresholds
- Log drift metrics to the observability stack

### Health checks
- `GET /health` returns model readiness in addition to standard checks
- Checks: database connectivity, Redis connectivity, model loaded, model warm
- Return 503 if the model is not loaded or is in a degraded state
- Include model version and last-loaded timestamp in health response

### Logging
- Use structlog with bound context: `request_id`, `model_version`, `user_id`
- Log every prediction: input hash (not raw PII), output, confidence, latency
- Log model loading, version changes, and drift alerts at `warning` level
- Never log raw input data that may contain PII -- hash or redact

### Observability
- Initialise OTel before any other imports in `src/main.py`
- Track metrics: prediction latency (histogram), throughput (counter),
  error rate (counter), model version (gauge), drift score (gauge)
- Span attributes: `model.name`, `model.version`, `prediction.confidence`,
  `batch.size`

### Security
- Validate and sanitise all model inputs (Pydantic strict mode)
- Rate-limit prediction endpoints to prevent model extraction attacks
- Do not expose model internals (weights, architecture) via any endpoint
- Log prediction audit trail for compliance (especially in financial/healthcare)
- Encrypt model artifacts at rest in the registry

### Testing
- Every model wrapper needs unit tests with fixture data
- Test API endpoints with httpx async client
- Test feature transforms produce expected output for known inputs
- Evaluation tests: assert model metrics (accuracy, F1, AUC, RMSE) meet
  minimum thresholds -- these tests fail if a retrained model degrades
- Test drift detection with synthetic shifted distributions
- Mock Redis and database -- never call real services in unit tests
- Tests must not depend on each other or on execution order

---

## Common commands (planned)

```bash
uv sync                        # Install dependencies
uv run uvicorn src.main:app --reload  # Start dev server
uv run alembic upgrade head    # Run migrations
uv run pytest                  # Run tests
uv run pytest tests/evaluation # Run model evaluation tests only
uv run ruff check .            # Lint
uv run ruff format .           # Format
uv run mypy src/               # Type check
uv run mlflow ui               # Launch MLflow UI (experiment tracking)
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (lint, type check, unit tests, evaluation tests)
- Model evaluation tests gate PRs -- if metrics degrade below threshold, PR is blocked
- Docker multi-stage build: slim image without training dependencies
- Optional CUDA base image for GPU deployments
- Blue/green deployment: new model version serves shadow traffic before promotion

---

## Before opening a PR

```bash
uv run ruff check . && uv run mypy src/ && uv run pytest
```
