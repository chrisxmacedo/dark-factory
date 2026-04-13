# starter-observability/

Observability infrastructure template. Copy this directory into a project workspace to get a working telemetry collection, routing, alerting, and dashboarding stack.

## What this is

This is **infrastructure, not a service**. It does not contain application code. It receives, processes, stores, and visualises telemetry (traces, logs, metrics) emitted by all other services in the project. It sits between per-service OpenTelemetry SDK instrumentation and the observability backends (Grafana, Prometheus, Tempo, Loki, or cloud equivalents).

Every service starter (starter-api, starter-web, starter-worker, starter-gateway, starter-batch) already includes OpenTelemetry SDK instrumentation that emits OTLP data. This template provides the collector that receives that data, the storage that holds it, the dashboards that visualise it, and the alert rules that act on it.

## When to use this

Use this template in every project that has at least one deployed service. Observability is not optional infrastructure — it is the mechanism by which you know whether your system is working.

## Market applications

**Banking and financial services:**
- SLA monitoring against regulatory uptime requirements (99.99% for payment rails)
- Transaction latency tracking across clearing, settlement, and reconciliation pipelines
- Fraud detection signal monitoring — anomalous latency or error patterns as early indicators
- Audit trail for compliance: trace every request from ingress to database mutation

**Healthcare:**
- System availability dashboards for critical patient-facing systems (EHR, lab results, prescriptions)
- Audit trail monitoring for HIPAA compliance — who accessed what, when, from where
- Alerting on degraded performance in time-sensitive workflows (emergency department triage, medication dispensing)

**E-commerce:**
- Checkout funnel monitoring — latency and error rate at each step from cart to confirmation
- Payment gateway health: real-time success/failure rates across providers (Stripe, PayPal, Adyen)
- Inventory sync latency between warehouse systems and storefront availability
- Black Friday / peak traffic capacity monitoring with auto-scaling trigger visibility

**SaaS platforms:**
- Multi-tenant resource usage tracking — identify noisy neighbours before they degrade others
- API rate limit monitoring with per-tenant breakdown
- Feature flag impact tracking — correlate flag changes with error rate and latency shifts
- Customer-facing status page data sourced directly from internal metrics

**Any production system:**
- Error rates by service, endpoint, and error type
- Latency percentiles (p50, p95, p99) with historical trends
- Service dependency health — which downstream is causing upstream failures
- Disk, memory, and connection pool saturation warnings before they become outages

## Contents

- **docker-compose.yml** — Standalone observability stack (Grafana + Loki + Tempo + Prometheus, database exporters)
- **otel-collector-config.yml** — OpenTelemetry Collector pipeline configuration (receivers, processors, exporters)
- **dashboards/** — Pre-built Grafana dashboard templates (service health, request flow, error breakdown)
- **alerts/rules.yml** — Prometheus alerting rules (error rate, latency, availability, disk)
- **synthetic/health-checks.yml** — Synthetic monitoring configuration for service health endpoints
- **.env.example** — Environment variable reference for local and cloud configurations

## For agents

- Replace all `{PLACEHOLDER}` values with project-specific configuration before use.
- This template is compatible with ALL service starters. Every service emits traces, logs, and metrics to the OTel Collector endpoint defined by `OTEL_EXPORTER_OTLP_ENDPOINT`.
- The docker-compose.yml is designed to run standalone or alongside service Docker Compose files using shared networks.
- For production, replace the local exporters in otel-collector-config.yml with your cloud provider's configuration (Grafana Cloud, Datadog, AWS CloudWatch). Commented-out examples are included.
- Dashboard JSON files are Grafana-importable. They use template variables for service name and environment so they work across all services without modification.
- Do not add application code to this template. If you need custom metrics or traces, add them to the service's own OTel SDK instrumentation, not here.
