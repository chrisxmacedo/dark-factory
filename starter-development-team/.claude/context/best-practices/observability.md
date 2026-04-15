# Observability best practices

Read by: all teams, all starters

## Three pillars — all required

- **Logs**: structured JSON (Pino for TS, structlog for Python)
- **Traces**: OpenTelemetry SDK in every service
- **Metrics**: request rate, error rate, latency percentiles via OTel

## Structured logging

- Every log entry MUST include: timestamp, level, service name, correlation ID
- Request logging: log on entry (method, path, correlationId) and exit (statusCode, durationMs)
- Error logging: include full context (message, stack, request, correlation ID)
- Business logic logging: log key decisions (user authenticated, payment processed, email sent)
- Use child loggers for context: `createRequestLogger(requestId, path)`, `createJobLogger(jobId)`
- Log level: `debug` in dev, `info` in production, `warn` in CI

NEVER:
- Use console.log / console.error — always use the project logger
- Log secrets, tokens, passwords, PII, or full request bodies containing sensitive data
- Log at `error` level for expected conditions (user not found is `warn`, not `error`)

## Correlation IDs

- Every request gets an `x-request-id` header (generate UUID if not present)
- Propagate across ALL service boundaries (HTTP headers, queue message metadata)
- Include in every log entry, every trace span, every error report
- When calling another service, forward the correlation ID

## Health endpoints

- Every service: `/healthz` or `/api/health`
- Check ALL dependencies: database, Redis, S3, downstream services
- Response: `{ "status": "healthy"|"degraded", "checks": { "database": "ok"|"error" } }`
- Return 200 for healthy, 503 for degraded
- Return 503 during graceful shutdown
- Health checks should be fast (< 1s) — ping, don't query

## OpenTelemetry

- Initialise OTel SDK BEFORE all other imports (instrumentation must wrap modules at load time)
- Auto-instrumentation for HTTP, database, Redis
- Manual spans for business logic (workflow steps, batch job progress)
- Trace context propagation across service boundaries
- Export interval: 30s for metrics, immediate for traces
- In CI: export to stdout (no collector). In prod-parity: export to OTel Collector → Grafana LGTM

## Per-deliverable observability requirements

Observability is NOT a separate Deliverable — it is built into every Deliverable.

**Development Team (every feature):**
- Add custom OTel spans for new business logic (not just auto-instrumented HTTP)
- Add structured log entries at every decision point
- Propagate correlation ID through any new service call or queue message
- Include `x-request-id` in queue message metadata when enqueuing jobs
- Create child spans linked to parent when processing queued jobs

**Per-deliverable-type scoping:**
- **Infrastructure**: verify health endpoints emit logs, OTel initialises without errors
- **Feature**: verify structured logs at decision points, new signals present, custom spans added, correlation ID flows end-to-end through the feature's data path
- **Bug fix**: verify fix path emits same signals as happy path

**Integration Test (CI — per Deliverable):**
- Observability Checker verifies correlation IDs appear in stdout logs
- Verifies new spans are present for the feature's business logic
- Verifies no defined-but-unused infrastructure

**E2E Regression (RC — per Deliverable):**
- Journey tests should include trace verification: trigger the flow, verify the correlation ID appears in all expected services' logs

**Smoke Tests (Prod-parity — per release):**
- Query Tempo for traces spanning the feature's full data path
- Query Loki for correlated log entries
- Query Prometheus for new metrics emitted by the feature

## Correlation ID propagation chain

Every request must be traceable end-to-end:

```
Browser → Web API (x-request-id generated)
  → Log: request received with correlationId
  → OTel span: http.METHOD /path
  → If calling another service: forward x-request-id header
  → If enqueuing job: include correlationId in message metadata
  → Worker picks up job: extract correlationId, create linked child span
  → Worker logs include correlationId
  → Grafana: search by correlationId → see the full chain
```

If the chain breaks at any point, the Observability Checker must flag it.

## Defined-but-unused infrastructure

- If a module exists (rate-limit, logger, error tracker) but no code uses it — that's a bug
- The Observability Checker and Devil's Advocate must flag this
- Code that exists but isn't wired in creates a false sense of coverage
