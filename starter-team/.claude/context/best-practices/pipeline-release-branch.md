# Pipeline best practices — Release branch

Read by: Regression Team, Release Team

Covers: Ready for Full E2E Regression → In Full E2E Regression → human approval → merge to main → Release / Production

## Branch

- `release-rc-{n}` — single-use, cut fresh from ci HEAD
- Only the Fix Agent may commit here — and only for genuine regressions
- No new features on the RC branch — stabilisation only
- Branch is NEVER deleted after merge — kept for audit

## Docker environment

- RC Docker environment: `docker-compose.base.yml` + `docker-compose.ci.yml` + `docker-compose.test.yml`
- Images tagged `:rc` — built from release-rc-{n} branch source
- Fixture-seeded data for deterministic regression testing
- Ports offset +100 from CI (web on 3100, sync on 8101, etc.)
- After RC cut: `envctl rebuild rc && envctl test rc` (mandatory)

## RC test gates (16 gates)

### Scripted gates (run by `envctl test rc`)

| # | Gate | Tool | Fails → |
|---|------|------|---------|
| 1 | Data integrity: all fixture records intact | Playwright `tests/e2e/data-integrity.spec.ts` | Fix on RC, re-run |
| 2 | Health: services healthy after seeding | Playwright `tests/e2e/health-seeded.spec.ts` | Fix on RC |
| 3 | Journey: inbox thread list | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 4 | Journey: thread tree rendering | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 5 | Journey: annotation CRUD (all 5 types) | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 6 | Journey: cross-thread links | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 7 | Journey: group management | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 8 | Journey: AI summary display | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 9 | Referential integrity across all tables | Playwright `tests/e2e/data-integrity.spec.ts` | Fix on RC |

### Reasoning gates (Regression Analyst — Claude)

| # | Gate | Fails → |
|---|------|---------|
| 10 | Environment parity assessment | Noted in readiness report |
| 11 | Migration sequencing review | Noted in readiness report |
| 12 | Feature flag status | Noted in readiness report |
| 13 | Third-party integration readiness | Noted in readiness report |
| 14 | Observability readiness | Noted in readiness report |
| 15 | Rollback plan defined | Noted in readiness report |
| 16 | Docker build gate before merge to main | BLOCKED — fix RC first |

## Flake investigation

- If tests fail: Flake Investigator re-runs to distinguish flaky from genuine
- Flaky: document evidence, recommend whether to proceed
- Genuine: Fix Agent commits fix to `release-rc-{n}` (up to 2 attempts)

## Defects found on the RC branch

This is different from feature branch defects:
1. Create an **Issue** ticket in Jira describing the regression
2. Fix Agent commits the fix to `release-rc-{n}` (not ci, not main)
3. **Merge RC back into ci** so ci gets the fix:
   ```
   git checkout ci && git merge --no-ff release-rc-{n}
   git push origin ci
   ```
4. Re-run full regression on RC: `envctl test rc`
5. Only proceed when regression is fully green
6. Do NOT cut a new RC — fix the existing one

## Human approval gate

After regression passes:
- Team Lead posts: "✅ Regression complete. Awaiting human approval to promote to Main."
- Do NOT merge until human explicitly replies: "Approve promote {PROJECT_KEY}-{key}"
- This is a business decision — timing, risk tolerance, and context require human judgement

## Merge to main

Run by `pipelinectl merge-rc {KEY}-{key} {N}`:
1. Build gate: verify RC Docker image builds
2. Merge RC → main (`--no-ff`, no rebase)
3. Tag main with semver (increment minor per Deliverable)
4. Push main + tags
5. Back-merge main → ci (`--no-ff`, no rebase)
6. `envctl rebuild prod && envctl test prod` (mandatory)

## Prod-parity environment

- Docker environment: `docker-compose.base.yml` + `docker-compose.prod-parity.yml`
- Images tagged `:prod` — built from main branch source
- Persisted volumes, real API shapes, full OTel → Grafana LGTM stack
- Ports offset +200 from CI (web on 3200, Grafana on 4000)

## Main branch test gates (13 gates)

### Scripted gates (run by `envctl test prod`)

| # | Gate | Tool | Fails → |
|---|------|------|---------|
| 1 | Health: all web replicas | Playwright `tests/smoke/health-smoke.spec.ts` | STOP — report to human |
| 2 | Health: sync service | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 3 | Health: MinIO | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 4 | Health: Grafana reachable | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 5 | Health: Prometheus reachable | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 6 | Health: Redis exporter metrics | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 7 | Health: Postgres exporter metrics | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 8 | OTel: traces arrive in Tempo | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |
| 9 | OTel: logs arrive in Loki | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |
| 10 | OTel: metrics arrive in Prometheus | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |

### Reasoning gates (Production Observer — Claude, 15 minutes)

| # | Gate | Fails → |
|---|------|---------|
| 11 | Error rate baseline — no spikes | Report anomaly to human |
| 12 | Latency baseline — no increases | Report anomaly to human |
| 13 | Log anomaly detection — no unexpected patterns | Report anomaly to human |

## Session reset

After merge to main completes:
- Team Lead suggests fresh session for the next ticket
- PostToolUse hook fires: "Release complete. Run /compact."

NEVER:
- Merge RC to main without human approval
- Merge RC to main if the Docker build is failing
- Cut a new RC instead of fixing the existing one
- Rebase the RC branch — merge only
- Delete the RC branch after merge
- Skip the back-merge to ci — ci must always include everything on main
- Tag main before the merge commit is pushed

