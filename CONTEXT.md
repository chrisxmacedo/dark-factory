# templates/

Reusable starter kits for bootstrapping new services and clients. These are scaffolds, not active products. Each starter is a complete, minimal, functional skeleton — copy it, replace {PLACEHOLDER} values, and start building.

## Template catalogue

### Pipeline orchestration (1 per project)
- **starter-team/** — Agent team pipeline: Team Lead, 6 specialist teams, Docker Compose environments (CI/Test/Prod-parity), token-saving scripts (jiractl, pipelinectl, envctl), test infrastructure (LLM stub, fixture seeder), GitHub Actions workflows, environment dashboard.

### Service starters (1 per service repo)
- **starter-api/** — REST API backend. Python/FastAPI, Alembic migrations, Supabase auth, structured logging, rate limiting, idempotency middleware, versioned models.
- **starter-web/** — Web frontend. Next.js 14, TypeScript, Tailwind CSS, Prisma, NextAuth.js, multi-stage Dockerfile with build-arg support.
- **starter-worker/** — Event consumer / job processor. Redis/Kafka consumption, idempotent handlers, retry with exponential backoff, circuit breakers, dead-letter queue, graceful shutdown.
- **starter-gateway/** — API gateway / BFF. JWT auth, Redis rate limiting, circuit breaker on internal service calls, correlation ID propagation, versioned routes (/v1/...), response aggregation.
- **starter-batch/** — Scheduled batch processor. Cron/QStash triggered, idempotent and resumable jobs, checkpoint/resume, progress logging, S3 output, bounded runtime.
- **starter-notification/** — Multi-channel notification delivery. Email (Resend/SES), SMS, push (FCM/APNS), in-app. Template rendering, user preferences, delivery tracking, per-channel retry.
- **starter-docs/** — Document generation + storage. PDF/DOCX from templates, S3/MinIO storage, signed URLs, versioning, bulk generation.
- **starter-orchestrator/** — Workflow state machine. Multi-step processes with branching, approval gates, timeouts, compensation (rollback), event-driven state transitions.
- **starter-realtime/** — WebSocket/SSE live updates. Room/channel subscriptions, presence detection, Redis pub/sub for horizontal scaling, backpressure handling.
- **starter-audit/** — Immutable audit log + compliance. Append-only event store, hash chain tamper detection, retention policies, regulatory query/export.

### Infrastructure (1 per project, alongside starter-team)
- **starter-observability/** — Observability collection, routing, alerting, dashboards. OTel Collector config, Grafana dashboard templates, Prometheus alert rules, synthetic monitoring. Not a service — infrastructure config only.

### Client starters (auto-generated from API specs)
- **starter-client-py/** — Python SDK client.
- **starter-client-ts/** — TypeScript SDK client.

### Mobile & desktop starters (PLACEHOLDER — conventions only, no code scaffold yet)
- **starter-ios/** — Swift/SwiftUI iOS app. MVVM, URLSession with retry, Keychain, os_log, XCTest.
- **starter-android/** — Kotlin/Jetpack Compose Android app. MVVM with Flow, Hilt, OkHttp, Room, Espresso.
- **starter-desktop/** — Cross-platform desktop (Tauri or Electron). React frontend, auto-update, code signing.
- **starter-chrome-extension/** — Browser extension (Chrome/Firefox). Manifest v3, service worker, content scripts, React popup.

### Tooling & platform starters (PLACEHOLDER — conventions only, no code scaffold yet)
- **starter-cli/** — Command-line tool (Node.js/TypeScript or Go). Structured output, config files, --verbose/--dry-run.
- **starter-serverless/** — Serverless functions (Lambda, Workers, Edge). Stateless, cold-start optimised, webhook receivers.
- **starter-ml/** — ML model serving (Python/FastAPI). Model registry, sync/async inference, drift monitoring.
- **starter-infrastructure/** — Infrastructure as Code (Terraform/Pulumi). Modules, environments, remote state, security scanning.

## Technology stack

### Languages & runtimes
| Technology | Used by | Version |
|---|---|---|
| TypeScript | web, worker, gateway, batch, notification, docs, orchestrator, realtime, audit | ^5.3 |
| Python | api, client-py | ^3.12 |
| Node.js | All TypeScript starters | 22 (Alpine) |

### Frameworks
| Technology | Used by | Purpose |
|---|---|---|
| Next.js 14 | web | SSR, App Router, API routes |
| FastAPI | api | Python REST API |
| Express | gateway | HTTP routing, middleware chain |

### Database & ORM
| Technology | Used by | Purpose |
|---|---|---|
| PostgreSQL | api, web, worker, batch, notification, docs, orchestrator, audit | Primary database |
| Prisma | web, worker, batch, notification, docs, orchestrator, audit | TypeScript ORM |
| SQLAlchemy + Alembic | api | Python ORM + migrations |

### Caching & queues
| Technology | Used by | Purpose |
|---|---|---|
| Redis (ioredis) | All TypeScript starters | Cache, rate limiting, job queues, pub/sub |
| Redis pub/sub | realtime, notification | Cross-instance event broadcasting |
| Kafka/Redpanda | worker, notification, audit | Event streaming (optional, Redis fallback) |

### Storage
| Technology | Used by | Purpose |
|---|---|---|
| MinIO / S3 | docs, batch, web | Object storage (local MinIO, prod S3/Spaces) |
| AWS SDK v3 | docs, batch | S3 client with signed URLs |

### Authentication
| Technology | Used by | Purpose |
|---|---|---|
| NextAuth.js | web | OAuth (Google, Microsoft), session management |
| JWT (jsonwebtoken) | gateway, realtime | Token validation on API/WebSocket requests |
| JWKS (jwks-rsa) | gateway | Key rotation support |

### Observability
| Technology | Used by | Purpose |
|---|---|---|
| OpenTelemetry SDK | All service starters | Traces, metrics, logs instrumentation |
| Pino | All TypeScript starters | Structured JSON logging |
| structlog | api | Python structured logging |
| Grafana LGTM | observability | Loki + Grafana + Tempo + Prometheus (all-in-one) |
| Redis Exporter | observability | Redis metrics for Prometheus |
| Postgres Exporter | observability | PostgreSQL metrics for Prometheus |

### Testing
| Technology | Used by | Purpose |
|---|---|---|
| Jest + ts-jest | All TypeScript starters | Unit + component tests |
| Playwright | web, team (integration/e2e/smoke) | Browser + API-level E2E tests |
| pytest | api | Python tests |
| httpx | api | Async HTTP test client |
| factory-boy | api | Test data factories |

### Build & deployment
| Technology | Used by | Purpose |
|---|---|---|
| Docker | All starters | Multi-stage builds, per-environment images |
| Docker Compose | team | CI, RC, Prod-parity environments |
| GitHub Actions | team | CI/CD workflows |

### Code quality
| Technology | Used by | Purpose |
|---|---|---|
| ESLint | All TypeScript starters | Linting |
| Prettier | All TypeScript starters | Formatting |
| ruff | api | Python linting + formatting |
| mypy | api | Python type checking |
| Zod | web, gateway, audit | Runtime schema validation |

### Resilience patterns
| Pattern | Implemented in | Purpose |
|---|---|---|
| Retry with backoff | worker, gateway, notification | Transient failure recovery |
| Circuit breaker | worker, gateway, notification | Fast-fail on persistent failures |
| Dead-letter queue | worker, notification | Failed job isolation |
| Idempotency | worker, batch, notification, orchestrator | Safe re-execution |
| Checkpoint/resume | batch | Interrupted job recovery |
| Graceful shutdown | All service starters | Drain connections, finish current work |
| Health checks | All service starters | /healthz or /api/health with dependency checks |

## For agents

- When creating a new product service, copy from the relevant starter template rather than building from scratch.
- Each starter has a `CLAUDE.md` with coding conventions — read it before modifying.
- `starter-team/` provides pipeline orchestration — copy once per project workspace.
- Service starters are copied per service repo within a project.
- All TypeScript starters share the same patterns: Pino logging, ioredis singleton, Prisma client, OTel instrumentation, health endpoint, graceful shutdown.
- `starter-observability/` is infrastructure config, not a service — it's integrated into `starter-team/`'s Docker Compose environments.

## Compatibility matrix

All starters are designed to work together. Common integration patterns:

| Producer | Consumer | Integration |
|---|---|---|
| Any service | audit | Emit audit events to queue → audit consumes |
| Any service | observability | OTel SDK → OTel Collector → Grafana stack |
| gateway | api, web | HTTP routing with correlation ID forwarding |
| api/web | notification | Emit "send notification" event → notification delivers |
| api/web | docs | POST /generate with template + data → PDF returned |
| orchestrator | worker | Orchestrator triggers step → worker executes → reports back |
| worker/batch | realtime | Publish event to Redis pub/sub → realtime broadcasts to clients |
| batch | docs | Generate bulk documents (statements, reports) |
