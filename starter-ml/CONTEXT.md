# starter-ml

Starter template for ML model serving and inference (Python).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Services that serve trained machine learning models for real-time and batch
inference:
- Real-time prediction APIs (fraud scoring, credit risk, content classification)
- Batch inference pipelines (score entire datasets, generate recommendations)
- Model registry and versioning (track experiments, promote models to production)
- Feature serving (retrieve pre-computed features for inference)
- Model monitoring (drift detection, performance degradation alerts)

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Serve ML models via HTTP API | **starter-ml** |
| General REST API (no ML) | starter-api |
| Batch data processing (ETL, reports) | starter-batch |
| Background job processing (queue consumer) | starter-worker |
| Real-time event stream processing | starter-worker + ML library |

**Rule of thumb:** if the service loads a trained model and returns
predictions, use starter-ml. If it only does data transformation or
API routing, use starter-api or starter-batch.

## Compatible starters

- **starter-api** -- starter-ml reuses starter-api patterns (FastAPI, Alembic, structured logging); the main API can proxy prediction requests to the ML service
- **starter-worker** -- workers can enqueue batch inference jobs for the ML service
- **starter-batch** -- batch jobs can call the ML service for bulk scoring
- **starter-gateway** -- API gateway routes prediction requests with rate limiting
- **starter-audit** -- prediction decisions logged as audit events for compliance
- **starter-observability** -- model metrics (latency, throughput, drift) feed into Grafana
- **starter-infrastructure** -- Terraform manages GPU instances, model storage, and autoscaling

## Key characteristics

- **Sync API + async batch** -- real-time single predictions and batch scoring
- **Model registry** -- MLflow for versioning, staging, and promotion
- **Feature store** -- Redis-backed feature retrieval for consistent inference
- **Drift monitoring** -- statistical tests on input distributions and prediction outputs
- **GPU optional** -- runs on CPU by default, CUDA support for GPU acceleration
- **Health checks** -- model-aware health (model loaded, warm, ready to serve)

## Tech stack

Python 3.12, FastAPI, MLflow, scikit-learn/PyTorch/XGBoost, Pydantic v2,
Redis (feature store), PostgreSQL (metadata), pytest, structlog, OpenTelemetry

## Market applications

### Banking & Finance
- Fraud detection (real-time transaction scoring)
- Credit risk assessment (loan application scoring)
- Anti-money laundering (suspicious activity detection)
- Customer churn prediction

### Insurance
- Claims fraud detection
- Risk pricing and underwriting models
- Document classification (claim forms, medical records)
- Damage assessment from images

### E-commerce & Retail
- Product recommendations (collaborative filtering, content-based)
- Dynamic pricing optimisation
- Customer segmentation
- Search ranking and relevance scoring

### Healthcare
- Diagnostic assistance (image classification, symptom analysis)
- Patient risk stratification
- Drug interaction prediction
- Clinical document classification (ICD coding)

### Content & Media
- Content moderation (text, image, video classification)
- Spam and abuse detection
- Sentiment analysis and topic classification
- Personalised content ranking

### Legal & Compliance
- Contract clause extraction and classification
- Regulatory change impact assessment
- Case outcome prediction
- Document similarity and deduplication
