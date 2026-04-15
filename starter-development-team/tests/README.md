# Test Infrastructure

Three test suites aligned to Docker environments and pipeline stages.

## Directory structure

```
tests/
├── integration/          # CI environment (base + ci)
│   └── *.spec.ts|*.py    # Health, LLM stub, correlation, storage
├── e2e/                  # Test environment (base + ci + test)
│   └── *.spec.ts|*.py    # Data integrity, user journeys, regression
├── smoke/                # Prod-parity environment (base + prod-parity)
│   └── *.spec.ts|*.py    # Service health, OTel validation, critical path
├── fixtures/
│   ├── seed.py           # DB seeder (runs as Docker init container)
│   ├── Dockerfile
│   └── {domain}/         # Fixture data files (JSON, SQL, PDF, etc.)
└── mocks/
    └── llm_stub/
        ├── server.py     # Stub for Anthropic + OpenAI APIs
        └── Dockerfile
```

## Which suite runs when

| Docker environment | Branch trigger | Pipeline stage | Agent team | Command |
|---|---|---|---|---|
| CI (base + ci) | Feature merge -> ci | Integration + E2E Impact | integration-test-team, e2e-impact-team | `{TEST_RUNNER} tests/integration/` |
| Test (base + ci + test) | RC cut from ci | Full E2E Regression | regression-team | `{TEST_RUNNER} tests/e2e/` |
| Prod-parity (base + prod-parity) | RC merge -> main | Release / Production | release-team | `{TEST_RUNNER} tests/smoke/` |

## Test runners

Choose one per stack:

- **Node.js/TypeScript**: Playwright (`@playwright/test`) for API-level tests
- **Python**: pytest with httpx for API-level tests

## Integration tests (CI)

Run after every merge to ci. Target < 2 minutes.
- Service health endpoints (real DB/Redis/S3 containers)
- LLM stub flow tests (deterministic responses)
- Request correlation ID propagation
- Cross-service health checks

## E2E tests (Test / regression)

Run on every release candidate. Uses fixture-seeded data.
- Data integrity assertions (all seeded records intact)
- User journey flows against fixture data
- Referential integrity validation
- All CRUD paths for every entity type

## Smoke tests (Prod-parity)

Run before production deploy. Validates infrastructure + observability.
- All service health endpoints (including replicas)
- OTel pipeline: traces in Tempo, logs in Loki, metrics in Prometheus
- Exporter health (Redis, Postgres)
- Critical path smoke (authenticate -> core operation -> verify)
