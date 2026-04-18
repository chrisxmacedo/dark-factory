# Observability model best practices

Read by: Discovery Team (step 5), Journey Modelling Team (when new log
categories emerge)

## Starter baselines to pull from

- `../../../../starter-regulations/cybersecurity-and-resilience.json`
  — incident notification windows vary by jurisdiction (72h GDPR/NIS2,
  24h NYDFS for extortion, 12h AU SOCI for critical incidents) and
  shape log retention + alerting requirements
- `../../../../starter-regulations/data-protection.json` — audit
  logging and access logging requirements per privacy regime
- `../../../../starter-standards/information-security.json` — NIST CSF
  Detect function and ISO 27001 logging/monitoring controls inform
  baseline coverage

## Ingestion

- OTel Collector is the sole telemetry ingestion point.
- Services NEVER connect to stores directly.
- PII scrubbing happens once, centrally, in the collector pipeline.

## Four stores

Incompatible retention and access requirements drive physical separation:

| Store   | Retention | Access              |
|---------|-----------|---------------------|
| Log     | 90 days   | Engineering         |
| Trace   | 30 days   | Engineering         |
| Metrics | 13 months | Engineering         |
| Audit   | 7 years   | Auditor-only (WORM) |

Audit storage is immutable — admin cannot delete within retention.

## Per-service instrumentation checklist (mandatory gate)

Six items every service must satisfy before marked Done:

1. Structured logs (JSON, per-category schema)
2. Distinct log categories emitted
3. Traces with service metadata
4. Metrics for throughput, latency, error rate
5. Health endpoint
6. service.yaml present and valid

## Logging categories (7)

Schema extensions are mandatory per service category:

| Category        | Fields beyond base                                    |
|-----------------|--------------------------------------------------------|
| API / edge      | `request_id`, `caller`, `route`, `status`             |
| Core domain     | `entity_id`, `operation`, `outcome`                   |
| Payment         | `payment_id`, `amount`, `currency`, `rail`            |
| Identity / auth | `subject_id`, `auth_method`, `mfa_used`               |
| Async / event   | `topic`, `event_id`, `correlation_id`                 |
| Admin / config  | `actor`, `config_key`, `before`, `after`              |
| Batch           | `job_id`, `batch_size`, `duration_ms`                 |

## service.yaml drives severity

- `data_classification` on the service drives SIEM alert severity.
- A CVE on a `pii` or `financial` service triggers an elevated alert
  automatically.
- Secrets listed in service.yaml with `rotation_days` drive rotation
  reminders.

## Data freshness contracts

Every store has a freshness SLA per category (e.g. logs available for
query within 60 seconds of emission). Freshness breaches are alerts,
not silent data loss.

## Anti-patterns

- Per-service PII scrubbing — scrubbing belongs centrally in the
  collector pipeline, not in each service.
- Services writing directly to log storage — defeats the single
  ingestion point.
- Audit data co-located with operational logs — violates retention
  and access requirements.
- Log categories invented ad hoc per service — categories are a
  closed set.
