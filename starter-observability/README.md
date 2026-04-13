# Observability Stack

Telemetry collection, storage, dashboarding, and alerting infrastructure. This stack receives OpenTelemetry data from all services and provides unified observability.

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ starter-api │  │ starter-web │  │starter-worker│  ... all services
└──────┬──────┘  └──────┬──────┘  └──────┬───────┘
       │                │               │
       │  OTLP (gRPC :4317 / HTTP :4318)
       │                │               │
       └────────────────┼───────────────┘
                        ▼
              ┌─────────────────┐
              │  OTel Collector │  ← receives, batches, samples, routes
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌─────────┐ ┌──────────┐
   │ Prometheus │ │  Tempo  │ │   Loki   │
   │  (metrics) │ │(traces) │ │  (logs)  │
   └─────┬──────┘ └────┬────┘ └────┬─────┘
         │              │           │
         └──────────────┼───────────┘
                        ▼
                  ┌──────────┐
                  │ Grafana  │  ← dashboards, alerts, exploration
                  │  :4000   │
                  └──────────┘
```

## Quick start (local)

### 1. Copy and configure

```bash
cp .env.example .env
# Edit .env — set GF_SECURITY_ADMIN_PASSWORD at minimum
```

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Verify

- Grafana: http://localhost:4000 (admin / your password)
- OTel Collector gRPC: localhost:4317
- OTel Collector HTTP: localhost:4318
- Prometheus: http://localhost:9090

### 4. Point your services at the collector

In each service's environment (`.env`, `docker-compose.yml`, or deployment config):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
# or if services run in Docker on the same network:
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-lgtm:4317
```

Every starter template (starter-api, starter-web, starter-worker, starter-gateway, starter-batch) already has OpenTelemetry SDK instrumentation. Setting this environment variable is the only configuration needed to connect them.

### 5. Import dashboards

In Grafana, go to Dashboards > Import and upload the JSON files from `dashboards/`:
- `service-health.json` — request rate, error rate, latency percentiles
- `request-flow.json` — distributed traces, service dependency graph
- `error-breakdown.json` — error analysis with trace correlation

## Running alongside service Docker Compose

If your services use their own `docker-compose.yml`, create a shared network:

```yaml
# In your service's docker-compose.yml
networks:
  observability:
    external: true

services:
  your-service:
    networks:
      - observability
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-lgtm:4317
```

Create the network before starting either stack:

```bash
docker network create observability
```

The observability `docker-compose.yml` already defines this network.

## Production setup

### Grafana Cloud

1. Create a Grafana Cloud account at https://grafana.com/products/cloud/
2. In `otel-collector-config.yml`, uncomment the `otlphttp/grafana_cloud` exporter section
3. Set the environment variables in `.env`:
   ```
   GRAFANA_CLOUD_OTLP_ENDPOINT=https://otlp-gateway-{region}.grafana.net/otlp
   GRAFANA_CLOUD_INSTANCE_ID=your-instance-id
   GRAFANA_CLOUD_API_KEY=your-api-key
   ```
4. Update the `service.pipelines` section to route to the Grafana Cloud exporter

### Datadog

1. In `otel-collector-config.yml`, uncomment the `datadog` exporter section
2. Set `DATADOG_API_KEY` in `.env`
3. Update the `service.pipelines` section to route to the Datadog exporter

### AWS CloudWatch / X-Ray

1. In `otel-collector-config.yml`, uncomment the `awsxray` and `awsemf` exporter sections
2. Set `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` in `.env`
3. Update the `service.pipelines` section to route to the AWS exporters

### Self-hosted production

For self-hosted production deployments, replace `grafana/otel-lgtm` with individual services:
- **Grafana** — `grafana/grafana:latest` with persistent volume
- **Prometheus** — `prom/prometheus:latest` with retention and storage config
- **Tempo** — `grafana/tempo:latest` with S3/GCS backend
- **Loki** — `grafana/loki:latest` with S3/GCS backend
- **OTel Collector** — `otel/opentelemetry-collector-contrib:latest` with the config from this template

## Alert rules

Prometheus alerting rules are defined in `alerts/rules.yml`. To activate them:

1. Mount the rules file into Prometheus (already configured in docker-compose.yml for local)
2. Configure Alertmanager for your notification channels (Slack, PagerDuty, email)
3. See commented-out notification config in `alerts/rules.yml`

## Synthetic monitoring

`synthetic/health-checks.yml` defines health endpoint checks for each service type. Use with:
- Grafana Synthetic Monitoring (cloud)
- Blackbox Exporter (self-hosted)
- Any HTTP monitoring tool that accepts YAML config

## Environment variables

See `.env.example` for all configurable values. Key variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password | `admin` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Where services send telemetry | `http://localhost:4317` |
| `POSTGRES_EXPORTER_DSN` | PostgreSQL connection for metrics export | — |
| `REDIS_EXPORTER_ADDR` | Redis address for metrics export | `redis://localhost:6379` |
