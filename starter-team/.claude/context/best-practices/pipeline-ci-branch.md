# Pipeline best practices — CI branch

Read by: Integration Test Team, E2E Impact Team

Covers: Ready for Integration Test → In Integration Test → Ready for E2E Impact Test → In E2E Impact Test → cut RC

## Branch

- `ci` is a shared branch — the first point where changes interact with other features
- Only the Fix Agent (integration/E2E) may commit here — and only to fix CI gate failures
- Every commit includes the Deliverable Jira ID
- Push immediately after every commit

## Docker environment

- CI Docker environment: `docker-compose.base.yml` + `docker-compose.ci.yml`
- Images tagged `:ci` — built from ci branch source
- Ephemeral storage (tmpfs), LLM stub server, no OTel collector
- Ports: web on `${WEB_PORT}`, sync on `${SYNC_PORT}`, stub on `${LLM_STUB_PORT}`
- After every merge to ci: `envctl rebuild ci && envctl test ci` (mandatory)

## Test gates (18 gates)

### Scripted gates (run by `pipelinectl ci-gate`)

| # | Gate | Tool | Fails → |
|---|------|------|---------|
| 1 | Unit tests in Docker container | `docker compose exec npm test` | Fix Agent on ci (2 attempts) |
| 2 | Lint in Docker | `docker compose exec npm run lint` | Fix Agent on ci |
| 3 | Format in Docker | `docker compose exec npm run format:check` | Fix Agent on ci |
| 4 | Integration: health endpoints (web + sync) | Playwright `tests/integration/health.spec.ts` | Fix Agent on ci |
| 5 | Integration: LLM stub flow | Playwright `tests/integration/llm-stub.spec.ts` | Fix Agent on ci |
| 6 | Integration: correlation ID propagation | Playwright `tests/integration/correlation.spec.ts` | Fix Agent on ci |
| 7 | Integration: storage (MinIO) | Playwright `tests/integration/minio.spec.ts` | Fix Agent on ci |

### Reasoning gates (Claude agents — spawn after scripted gates pass)

**Integration Analyst:**

| # | Gate | Fails → |
|---|------|---------|
| 8 | Contract validation: interfaces match consumers | Back to Ready for Local Test |
| 9 | Downstream impact: services at risk from changes | Back to Ready for Local Test |
| 10 | Data consistency: correlation ID tracing across boundaries | Back to Ready for Local Test |
| 11 | Migration safety: schema changes safe to apply | Back to Ready for Local Test |

**Observability Checker (scoped by deliverable type):**

| # | Gate | Fails → |
|---|------|---------|
| 12 | Structured logs at key decision points | Flagged as gap |
| 13 | Correlation IDs propagating across boundaries | Flagged as gap |
| 14 | New signals appearing (features) or same signals (bugfix) | Flagged as gap |
| 15 | Defined-but-unused infrastructure detection | Flagged as gap |

**E2E Impact (Impact Analyst + E2E Runner):**

| # | Gate | Fails → |
|---|------|---------|
| 16 | Affected user journeys identified and tested | Fix Agent on ci (2 attempts) |
| 17 | Data-level assertions per journey confirmed | Fix Agent on ci |
| 18 | Docker build gate before RC cut | BLOCKED — fix ci first |

## Cutting the RC

- After E2E impact passes: `pipelinectl cut-rc {KEY}-{key}`
- **ALWAYS from ci HEAD** — never from a previous RC branch
- Each RC is independent and unrelated to previous RCs
- After cut: `envctl rebuild rc && envctl test rc` (mandatory)
- Transition to Ready for Full E2E Regression

## Build gate before cutting RC

- `pipelinectl cut-rc` verifies ci builds as a Docker image before cutting
- If the Docker build fails → BLOCKED, do not cut RC, fix ci first

## Defects found on ci

- If the CI gate fails: Fix Agent commits to ci (up to 2 attempts)
- If analysis reveals a design issue: return to Ready for Local Test with Jira comment
- If E2E impact fails: Fix Agent on ci (up to 2 attempts), or back to Ready for Integration Test

NEVER:
- Cut an RC from a previous RC branch — always from ci HEAD
- Cut an RC if the Docker build is failing
- Skip the Integration Analyst or Observability Checker — reasoning gates are not optional
- Merge unrelated features to ci while E2E impact testing is in progress

