# Jira + Claude Code Pipeline Configuration Guide

Complete, reproducible configuration for running an automated software development pipeline using Jira for ticket management and Claude Code agent teams for implementation, testing, and deployment.

---

## 1. Overview

Every ticket flows through a progressive confidence pipeline where specialist agent teams handle each stage, gated by evidence-based criteria and two human checkpoints.

### Pipeline at a Glance

- **6 pipeline stages** — Development, Local Test, Integration Test, E2E Impact Test, Full E2E Regression, Release
- **6 agent teams** — one per stage, with specialised roles
- **2 human gates** — entering the pipeline (Ready for Dev) and promoting to production (Approve promote)
- **Token-saving scripts** — jiractl, pipelinectl, envctl handle mechanical operations without Claude tokens
- **3 concurrent Docker environments** — CI (:3000), RC (:3100), Prod-parity (:3200), always running

### Progressive Confidence Stages

| Stage | Question Answered | Branch | Scripted or Claude? |
|-------|-------------------|--------|---------------------|
| Development | Does the code work in isolation? | feature/* | Claude (writes code) |
| Local Test | Do all tests pass locally? | feature/* | Script (pipelinectl local-gate) |
| Integration Test | Do components work together? | ci | Script + Claude (gates + analysis) |
| E2E Impact Test | Does the change work in real flows? | ci | Claude (journey analysis) |
| Full E2E Regression | Does the system still work overall? | release-rc-* | Script + Claude (tests + readiness) |
| Release / Production | Is this version production-ready? | main | Script + Claude (merge + observation) |

### Starter Templates

All configuration files live in `templates/starter-team/`. When setting up a new project, copy these templates and replace the `{PLACEHOLDER}` values.

```
starter-team/
    PIPELINE.md                         — Team Lead orchestration (becomes .claude/CLAUDE.md)
    ARCHITECTURE.md                     — Technical architecture template
    SOLUTION-ARCHITECT-INPUTS.md        — Inputs checklist
    .secrets.md.template                — Shared secrets documentation template
    .githooks/
        pre-push                        — Prevents direct pushes to main
    .claude/
        agents/                         — 6 specialist team files
        context/
            project.md                  — Project identity, Jira config, repos
            branching.md                — Branch types, merge rules, no worktrees
            pipeline-stages.md          — Polling, claiming, spawning, gating
            scripts.md                  — jiractl, pipelinectl, envctl reference
            agent-rules.md              — Spawning rules, rate limits, error handling
            defect-handling.md          — Feature vs RC vs production defects
            decomposition.md            — Journey-first, app shell first
            environment-config.md       — Docker tags, build args, NEXT_PUBLIC_*
            best-practices/
                typescript.md           — TypeScript conventions
                python.md               — Python conventions
                nextjs.md               — Next.js conventions
                fastapi.md              — FastAPI conventions
                docker.md               — Dockerfile + Compose patterns
                testing.md              — Test pyramid, fixtures, assertions
                observability.md        — Logging, tracing, health endpoints
                security.md             — Validation, auth, encryption, secrets
                resilience.md           — Retry, circuit breaker, transactions
                pipeline-feature-branch.md  — Rules for Dev + Local Test
                pipeline-ci-branch.md       — Rules for Integration + E2E Impact
                pipeline-release-branch.md  — Rules for Regression + Release
                pipeline-orchestration.md   — Rules for Team Lead
    infra/
        docker-compose.base.yml         — Shared services (no host ports, image tags)
        docker-compose.ci.yml           — CI (builds from source, :ci tags)
        docker-compose.test.yml         — RC (uses :rc tags, fixture seeding)
        docker-compose.prod-parity.yml  — Prod (uses :prod tags, OTel stack)
        .env.ci / .env.test / .env.prod-parity.example
        envctl                          — Docker environment management
        envwatch                        — Auto-rebuild watcher
        jiractl                         — Jira API (poll, create, transition, comment)
        pipelinectl                     — Mechanical pipeline ops with build gates
        dashboard.py + dashboard.html   — Web UI for environment + test status
    tests/
        integration/                    — CI environment tests
        e2e/                            — RC regression tests
        smoke/                          — Prod-parity smoke + OTel validation
        fixtures/seed.py + Dockerfile   — Fixture seeder
        mocks/llm_stub/                 — Anthropic + OpenAI stub server
    .github/workflows/
        ci.yml                          — feature/* and ci branches
        release.yml                     — release-rc-* branches
```

### Docker Environment → Pipeline Stage Mapping

| Docker Environment | Branch | Image Tags | Agent Teams | Test Suite |
|---|---|---|---|---|
| CI (base + ci) | ci | :ci | integration-test, e2e-impact | `tests/integration/` |
| RC (base + ci + test) | release-rc-{n} | :rc | regression | `tests/e2e/` |
| Prod-parity (base + prod-parity) | main | :prod | release | `tests/smoke/` |

### Concurrent Browsable Environments

All three environments run simultaneously with non-clashing ports via env vars.

| Service | CI | RC | Prod-parity |
|---|---|---|---|
| Web app | ${WEB_PORT} (3000) | +100 (3100) | +200 (3200) |
| Worker/sync health | ${SYNC_PORT} (8001) | +100 (8101) | +200 (8201) |
| MinIO | ${MINIO_PORT} (9000) | +100 (9100) | +200 (9200) |
| LLM stub | ${LLM_STUB_PORT} (11434) | +100 (11534) | *(real API)* |
| Grafana | — | — | 4000 |

### Docker Image Strategy

Build once per environment, run instantly. Only CI builds from source.

```bash
envctl rebuild ci     # checks out ci, builds :ci images (slow — full build)
envctl rebuild rc     # checks out release-rc-*, builds :rc images
envctl rebuild prod   # checks out main, builds :prod images

envctl up ci          # starts from existing :ci images (fast — no build)
envctl up rc          # starts from existing :rc images
envctl up prod        # starts from existing :prod images
```

Each environment has its own tagged images. Rebuilding one doesn't affect the others.

### Token-Saving Scripts

~40-50% token savings per Deliverable by scripting mechanical operations.

| Script | What it does | Replaces |
|---|---|---|
| `jiractl poll` | Find actionable tickets | MCP JQL queries |
| `jiractl create TYPE SUMMARY` | Create Jira issues | MCP createJiraIssue |
| `jiractl transition KEY ID` | Move tickets | MCP transitionJiraIssue |
| `jiractl comment KEY msg` | Add comments | MCP addCommentToJiraIssue |
| `pipelinectl local-gate KEY` | Run tests + build + lint | Local Test Team agent |
| `pipelinectl ci-gate KEY` | Run CI gates | CI Monitor agent |
| `pipelinectl merge-to-ci KEY` | Build gate → rebase → merge | Manual git |
| `pipelinectl cut-rc KEY` | Build gate → cut from ci HEAD | Manual git |
| `pipelinectl merge-rc KEY N` | Build gate → merge → tag → back-merge | Manual git |
| `envctl rebuild ENV` | Build tagged Docker images | Manual docker build |
| `envctl test ENV` | Run Playwright test suite | Manual test execution |

**Jira API rate limiting:** jiractl monitors `X-RateLimit-Remaining` headers, pauses at 98% usage, retries on 429 with backoff.

**Credentials:** `infra/.env.jira` with `JIRA_EMAIL` and `JIRA_API_TOKEN`. If missing, fall back to Atlassian MCP.

### Mandatory Environment Rebuilds

After EVERY branch operation, the corresponding Docker environment MUST be rebuilt and tested. This is enforced by PostToolUse hooks.

| Event | Commands | Hook trigger |
|---|---|---|
| Merge to ci | `envctl rebuild ci && envctl test ci` | `git push origin ci` |
| Cut RC | `envctl rebuild rc && envctl test rc` | `git push origin release-rc-*` |
| Merge to main | `envctl rebuild prod && envctl test prod` | `git push origin main` |

### Build Verification Hard Gates

A failing build BLOCKS the pipeline. Non-negotiable.

| Gate | When | What's checked |
|---|---|---|
| Before merge to ci | `pipelinectl merge-to-ci` | Build verification on feature branch |
| Before cutting RC | `pipelinectl cut-rc` | Docker build on ci branch |
| Before merge to main | `pipelinectl merge-rc` | Docker build on RC branch |

### Infrastructure Replacements in Docker

| Production Service | Local Docker Replacement |
|---|---|
| Cloud PostgreSQL | Vanilla PostgreSQL (or pgvector) |
| Cloud Object Storage | MinIO (S3-compatible) |
| Cloud Redis | Vanilla Redis |
| Cloud Message Queue | Redpanda (Kafka-compatible) |
| LLM API (Anthropic, OpenAI) | LLM stub server |
| Observability (Datadog, etc.) | grafana/otel-lgtm |

### Environment Dashboard

Web UI at `http://localhost:4400` showing:
- Per-environment status (Started/Stopped/Starting Up/Shutting Down)
- Per-container status with health indicators
- Start/Stop/Rebuild buttons (background execution, no browser timeout)
- Test results with individual test pass/fail and history
- Direct links to web apps, health endpoints, Grafana

```bash
./infra/envctl dashboard    # Start on port 4400
```

---

## 2. Prerequisites

### Accounts & Services

| Service | Purpose | Plan Required |
|---------|---------|---------------|
| Jira Cloud | Ticket management & pipeline statuses | Free tier works |
| GitHub | Source control & PRs | Free tier (branch protection needs Pro) |
| Claude Code | AI agent teams | Claude Pro or Max subscription |
| Atlassian MCP | Claude-Jira integration | Included with Claude |

### Local Tooling

- **Claude Code CLI** — `npm install -g @anthropic-ai/claude-code`
- **Git** — version 2.x or later
- **GitHub CLI** (`gh`) — for PR creation and management
- **Docker Desktop** — for CI/RC/Prod-parity environments
- **Node.js 22** (TypeScript projects) or **Python 3.12 + uv** (Python projects)

### GitHub Organisation

Create a GitHub organisation for your project. All repos under this org.

**GitHub for Jira app:** Install on the org (Settings → GitHub Apps → Jira from Atlassian) to get commits, branches, PRs, and CI build status in Jira's Development panel.

### Pre-push Hook

Every service repo gets a pre-push hook preventing direct pushes to main:
```bash
git config core.hooksPath .githooks
```

### Jira API Token

For token-saving scripts (jiractl, pipelinectl):
```bash
# Create at https://id.atlassian.com/manage-profile/security/api-tokens
cat > infra/.env.jira << 'EOF'
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-token
EOF
```

---

## 3. Jira Setup

### Create the Jira Project

Company-managed project with short key (e.g. `PRJ`).

### Issue Types

| Issue Type | Purpose | Workflow |
|------------|---------|----------|
| **Deliverable** | Features flowing through full pipeline | 13-status pipeline |
| **Task** | Work breakdown within a Deliverable | Backlog → In Progress → Done |
| **Initiative** | High-level grouping | Simple workflow |
| **Issue** | Bugs and defects | Simple or pipeline |

### Pipeline Statuses (13)

| # | Status Name | Category |
|---|-------------|----------|
| 1 | Backlog | To Do |
| 2 | Selected for Development | To Do |
| 3 | In Development | In Progress |
| 4 | Ready for Local Test | To Do |
| 5 | In Local Test | In Progress |
| 6 | Ready for Integration Test | To Do |
| 7 | In Integration Test | In Progress |
| 8 | Ready for E2E Impact Test | To Do |
| 9 | In E2E Impact Test | In Progress |
| 10 | Ready for Full E2E Regression | To Do |
| 11 | In Full E2E Regression | In Progress |
| 12 | Release / Production | Done |
| 13 | Done | Done |

### Retrieve Transition IDs

```
getTransitionsForJiraIssue(cloudId: "your-cloud-id", issueIdOrKey: "PRJ-1")
```

Populate the transition table in CLAUDE.md.

### Deliverable Template

Every Deliverable must include:
- **Summary** — one sentence
- **Business Rules** — "A user/consumer can..." with exceptions
- **Acceptance Criteria** — Gherkin scenarios (one per business rule)
- **Data Model Changes** — schema/migration impact
- **API Surface** — new/changed endpoints
- **Components** — affected repos
- **Dependencies** — what must be done first
- **Supporting Documentation** — links

---

## 4. Claude Code Setup

### Copy Starter Templates

```bash
cp -r templates/starter-team/* your-project/
```

### Replace Placeholders

| Placeholder | Replace With |
|-------------|-------------|
| `{PROJECT_NAME}` | Full project name |
| `{PROJECT_KEY}` | Jira project key |
| `{CLOUD_ID}` | Atlassian Cloud ID |
| `{JIRA_URL}` | Jira instance URL |
| `{JIRA_SITE}` | Jira site hostname |

### Context File Split

CLAUDE.md is slim — it references context files that agents read selectively.

| File | Who reads it | When |
|------|-------------|------|
| `context/project.md` | Everyone | Always |
| `context/branching.md` | Everyone | When committing/merging |
| `context/pipeline-stages.md` | Team Lead | When orchestrating |
| `context/scripts.md` | Team Lead | When running scripts |
| `context/agent-rules.md` | Team Lead | When spawning/responding |
| `context/defect-handling.md` | Team Lead, test teams | When defects found |
| `context/decomposition.md` | Team Lead | When creating Deliverables |
| `context/environment-config.md` | Team Lead, dev team | When configuring Docker |

### Best Practice Documents

Agents read the ones relevant to their stage and stack:

**Pipeline (by branch stage):**
- `pipeline-feature-branch.md` — Development + Local Test teams
- `pipeline-ci-branch.md` — Integration + E2E Impact teams
- `pipeline-release-branch.md` — Regression + Release teams
- `pipeline-orchestration.md` — Team Lead

**Development (by technology):**
- `typescript.md` / `python.md` — language conventions
- `nextjs.md` / `fastapi.md` — framework conventions
- `docker.md` — Dockerfile + Compose patterns
- `testing.md` — test pyramid, fixtures, assertions
- `observability.md` — logging, tracing, health
- `security.md` — validation, auth, encryption
- `resilience.md` — retry, circuit breaker, transactions

### PostToolUse Hooks

Auto-enforced via `.claude/settings.json`:
- `git push origin ci` → "MANDATORY: rebuild CI now"
- `git push origin release-rc-*` → "MANDATORY: rebuild RC now"
- `git push origin main` → "MANDATORY: rebuild Prod, then /compact"

---

## 5. Pipeline Specification

### Agent Spawning Rules

**NEVER combine multiple pipeline stages into one agent spawn.** Each stage is a separate invocation. The Team Lead orchestrates between them.

Exception: `pipelinectl` scripts handle mechanical gates without Claude tokens.

### Stage Actions

| Status | Transition to | Action |
|---|---|---|
| Ready for Dev | In Development | **SPAWN:** development-team.md |
| Ready for Local Test | In Local Test | **SCRIPT:** `pipelinectl local-gate` → merge if pass, Fix Agent if fail |
| Ready for Integration Test | In Integration Test | **SCRIPT:** `pipelinectl ci-gate` → **SPAWN:** Analyst + Observability Checker |
| Ready for E2E Impact Test | In E2E Impact Test | **SPAWN:** e2e-impact-team.md → **SCRIPT:** `pipelinectl cut-rc` |
| Ready for Full E2E Regression | In Full E2E Regression | **SCRIPT:** `envctl test rc` → **SPAWN:** Regression Analyst |
| Release / Production | (human approval) | **SCRIPT:** `pipelinectl merge-rc` → **SPAWN:** Production Observer |

### Completion Signals

Every team's completion signal includes:
- **RETROSPECTIVE** — issues, improvements, next-run suggestions
- **FUTURE WORK IDENTIFIED** — new Deliverables with business rules, components, rationale

Team Lead creates Backlog tickets for future work with full Deliverable template detail.

### Test Matrix by Branch

Every gate listed below must pass before the pipeline advances. Scripted gates run
without Claude tokens. Reasoning gates require agent spawns.

#### Feature branch gates (Development + Local Test)

Run by: `pipelinectl local-gate` (scripted)

| # | Gate | Type | Tool | Fails → |
|---|------|------|------|---------|
| 1 | Unit tests | Scripted | `npm test` / `pytest` | Return to In Development |
| 2 | Component tests | Scripted | `npm test` / `pytest` | Return to In Development |
| 3 | Behaviour tests (1 per Gherkin AC) | Scripted | `npm test` / `pytest` | Return to In Development |
| 4 | Edge case tests | Scripted | `npm test` / `pytest` | Return to In Development |
| 5 | Build verification | Scripted | `next build` / `tsc` / `mypy` | Return to In Development |
| 6 | Lint | Scripted | `eslint` / `ruff check` | Return to In Development |
| 7 | Format | Scripted | `prettier --check` / `ruff format --check` | Return to In Development |

All state-mutating tests must include **data-level assertions** (verify DB state, not just response).

#### CI branch gates (Integration Test + E2E Impact)

Run by: `pipelinectl ci-gate` (scripted) + agents (reasoning)

| # | Gate | Type | Tool / Agent | Fails → |
|---|------|------|-------------|---------|
| 1 | Unit tests in Docker | Scripted | `docker compose exec npm test` | Fix Agent on ci (2 attempts) |
| 2 | Lint in Docker | Scripted | `docker compose exec npm run lint` | Fix Agent on ci |
| 3 | Format in Docker | Scripted | `docker compose exec npm run format:check` | Fix Agent on ci |
| 4 | Integration: health endpoints | Scripted | Playwright `tests/integration/health.spec.ts` | Fix Agent on ci |
| 5 | Integration: LLM stub flow | Scripted | Playwright `tests/integration/llm-stub.spec.ts` | Fix Agent on ci |
| 6 | Integration: correlation IDs | Scripted | Playwright `tests/integration/correlation.spec.ts` | Fix Agent on ci |
| 7 | Integration: storage (MinIO) | Scripted | Playwright `tests/integration/minio.spec.ts` | Fix Agent on ci |
| 8 | Contract validation | Reasoning | Integration Analyst (Claude) | Back to Ready for Local Test |
| 9 | Downstream impact assessment | Reasoning | Integration Analyst (Claude) | Back to Ready for Local Test |
| 10 | Data consistency (correlation ID tracing) | Reasoning | Integration Analyst (Claude) | Back to Ready for Local Test |
| 11 | Migration safety | Reasoning | Integration Analyst (Claude) | Back to Ready for Local Test |
| 12 | Observability: structured logs at decision points | Reasoning | Observability Checker (Claude) | Noted, may not block |
| 13 | Observability: correlation IDs propagating | Reasoning | Observability Checker (Claude) | Noted, may not block |
| 14 | Observability: new signals appearing | Reasoning | Observability Checker (Claude) | Noted, may not block |
| 15 | Observability: defined-but-unused detection | Reasoning | Observability Checker (Claude) | Flagged as gap |
| 16 | E2E: affected user journeys pass | Reasoning | E2E Runner (Claude) | Fix Agent on ci (2 attempts) |
| 17 | E2E: data-level assertions per journey | Reasoning | E2E Runner (Claude) | Fix Agent on ci |
| 18 | Docker build gate before RC cut | Scripted | `docker build` on ci | BLOCKED — fix ci first |

Docker environment: CI (base + ci), ephemeral, LLM stub, images tagged `:ci`.

#### RC branch gates (Full E2E Regression)

Run by: `envctl test rc` (scripted) + agent (reasoning)

| # | Gate | Type | Tool / Agent | Fails → |
|---|------|------|-------------|---------|
| 1 | Data integrity: all fixture records intact | Scripted | Playwright `tests/e2e/data-integrity.spec.ts` | Fix on RC, re-run |
| 2 | Health: services healthy after seeding | Scripted | Playwright `tests/e2e/health-seeded.spec.ts` | Fix on RC |
| 3 | Journey: inbox thread list | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 4 | Journey: thread tree rendering | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 5 | Journey: annotation CRUD (all 5 types) | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 6 | Journey: cross-thread links | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 7 | Journey: group management | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 8 | Journey: AI summary display | Scripted | Playwright `tests/e2e/journeys.spec.ts` | Fix on RC |
| 9 | Referential integrity across all tables | Scripted | Playwright `tests/e2e/data-integrity.spec.ts` | Fix on RC |
| 10 | Environment parity assessment | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 11 | Migration sequencing review | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 12 | Feature flag status | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 13 | Third-party integration readiness | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 14 | Observability readiness | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 15 | Rollback plan defined | Reasoning | Regression Analyst (Claude) | Noted in readiness report |
| 16 | Docker build gate before merge to main | Scripted | `docker build` on RC | BLOCKED — fix RC first |

Docker environment: RC (base + ci + test), fixture-seeded, images tagged `:rc`.

Defects on RC: Create Issue ticket, fix on RC, merge RC back to ci, re-run regression.

**Human gate:** "Approve promote {KEY}-{key}" required before merge to main.

#### Main branch gates (Release / Production)

Run by: `envctl test prod` (scripted) + agent (observation)

| # | Gate | Type | Tool / Agent | Fails → |
|---|------|------|-------------|---------|
| 1 | Smoke: all service health (both web replicas) | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP — report to human |
| 2 | Smoke: sync service health | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 3 | Smoke: MinIO health | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 4 | Smoke: Grafana reachable | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 5 | Smoke: Prometheus reachable | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 6 | Smoke: Redis exporter metrics | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 7 | Smoke: Postgres exporter metrics | Scripted | Playwright `tests/smoke/health-smoke.spec.ts` | STOP |
| 8 | OTel: traces in Tempo | Scripted | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |
| 9 | OTel: logs in Loki | Scripted | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |
| 10 | OTel: metrics in Prometheus | Scripted | Playwright `tests/smoke/otel-validation.spec.ts` | STOP |
| 11 | Error rate baseline (15 min) | Reasoning | Production Observer (Claude) | Report anomaly to human |
| 12 | Latency baseline (15 min) | Reasoning | Production Observer (Claude) | Report anomaly to human |
| 13 | Log anomaly detection (15 min) | Reasoning | Production Observer (Claude) | Report anomaly to human |

Docker environment: Prod-parity (base + prod-parity), persisted, OTel stack, images tagged `:prod`.

Defects in production: Create Issue with `production-defect` label, human decides priority.

Session reset: `/compact` after release completes.

#### Gate count summary

| Branch | Scripted | Reasoning | Total |
|--------|----------|-----------|-------|
| Feature | 7 | Devil's Advocate (continuous) | ~7 + review |
| CI | 7 scripted + 1 build gate | 10 analysis gates | 18 |
| RC | 9 scripted + 1 build gate | 6 readiness checks | 16 |
| Main | 10 scripted | 3 observation checks | 13 |
| **Total** | **35** | **19 + review** | **~54** |

### Defect Handling

| Where found | Action |
|---|---|
| Feature branch | Return to In Development, fix on same branch, no separate ticket |
| RC branch | Create Issue, fix on RC, merge RC back to ci, re-run regression |
| Production | Create Issue with `production-defect` label, human decides |

### Rate Limit Handling

- **90%+ Claude API**: finish current work, don't spawn new agents
- **98% or hit**: stop, report, wait for reset automatically
- **Jira API**: jiractl retries on 429, pauses at 98%

### Session Management

After merge to main: suggest `/compact`. PostToolUse hook fires automatically.

---

## 6. Agent Teams

### 0. Refinement Team

**Branch:** None (pre-code analysis) | **Goal:** "Implementation approach is sound, tasks are concrete"

- **Solution Designer** — reads Deliverable + ARCHITECTURE.md + REPO_MAP.md, proposes implementation approach (repos, files, patterns, data flow, integration points)
- **Task Planner** — breaks approach into Jira Tasks with file paths, patterns, acceptance criteria, dependencies, complexity (S/M/L)
- **Risk Assessor** — checks for architectural violations, code conflicts, missing dependencies, migration risks, security concerns, test gaps

**Gate:** Solution design received, Tasks created, risks assessed. If insufficient detail → return to Backlog. If blocking risks → `needs-human` label.

### 1. Development Team

**Branch:** `feature/{KEY}-{n}/{slug}` | **Goal:** "Works in isolation"

- **Implementer** — writes code + unit/component tests, opens PR
- **Devil's Advocate** — real-time review with mandatory pattern checks (transactions, retry, middleware, validation, logging, unused infrastructure)
- **Test Writer** — behaviour + edge case + integration tests with data assertions

**Gate:** All signals received, tests pass, lint/format clean, build passes.

### 2. Local Test Team

**Branch:** `feature/{KEY}-{n}/{slug}` | **Scripted**

`pipelinectl local-gate`: tests → build verification → lint → format. Fix Agent (Claude) only if gates fail.

### 3. Integration Test Team

**Branch:** `ci` | **Script + Claude**

`pipelinectl ci-gate` for mechanical checks. Then spawn:
- **Integration Analyst** — contracts, downstream, data consistency, migrations
- **Observability Checker** — scoped by deliverable type, defined-but-unused detection

### 4. E2E Impact Team

**Branch:** `ci` | **Claude**

- **Impact Analyst** — affected journeys, data paths
- **E2E Runner** — targeted tests with data assertions + correlation ID tracing

After pass: `pipelinectl cut-rc` (always from ci HEAD, never from previous RC).

### 5. Regression Team

**Branch:** `release-rc-{n}` | **Script + Claude**

`envctl test rc` for full regression. Then spawn **Regression Analyst** for release readiness.

**Human gate:** "Approve promote {KEY}-{key}" required before merge to main.

### 6. Release Team

**Branch:** `main` | **Script + Claude**

`pipelinectl merge-rc` (build gate → merge → tag → back-merge). `envctl test prod` for smoke tests. Then spawn **Production Observer** for 15-minute monitoring.

---

## 7. Branching Model

```
main        ← RC merges only (after human approval)
  │
  └─► ci    ← feature merges + RC back-merges
        │
        ├─► feature/{KEY}-{n}/{slug}    ← dev + local test
        │
        └─► release-rc-{n}             ← ALWAYS from ci HEAD, never from previous RC
```

**Rules:**
- Rebase feature branches onto ci before merging
- NEVER rebase ci, release, or main
- All merges use `--no-ff`
- Never delete any branch
- Never squash
- Never commit directly to main
- Pre-push hook blocks non-merge commits to main

---

## 8. Decomposition Rules

### Journey-first, not component-first

Decompose by user journey first, technical capability second. Every Deliverable answers: "what can the user do after this is done?"

### App Shell must be first

After infrastructure, the first feature Deliverable is always the **App Shell** — layout, navigation, auth redirect. Before building feature components, there must be a page to put them on.

### Deliverable ordering

1. Infrastructure Setup (pipeline, Docker, CI/CD)
2. App Shell (layout, navigation, auth, first page)
3. Core data flow (primary user journey end-to-end)
4. Feature Deliverables (each adds to the shell)
5. Polish (performance, analytics, edge cases)

---

## 9. Pipeline Rationale

### The Core Problem

Software failures come from undetected problems accumulating across layers. This pipeline is designed around **progressive confidence** — each stage answers one question at the right fidelity.

### Stage Rationale

- **Early stages** — fast, isolated, rapid developer feedback
- **Middle stages** — progressive system interaction, contract and interface validation
- **Late stages** — system-wide confidence against stable release candidate

> Failures are caught by the stage best positioned to diagnose them.

### Evidence-Based Gating

| Evidence Type | What It Verifies |
|---|---|
| Test results | Pass/fail, failure messages, coverage delta |
| Data validation | Database state, event payloads, data structures |
| Observability | Structured logs, correlation IDs, traces, metrics |

> A pipeline that passes without evidence is not a pipeline — it is an optimism machine.

### Human Gates

| Gate | Why |
|---|---|
| Ready for Dev | Refinement requires product + engineering judgement |
| Promote to Main | Deploying is a business decision |

### Agent Design

- Shared task list (session-local) + inbox system for real-time coordination
- Jira is the persistent system of record
- Teams are stage-specific: different skill, different risk profile
- Devil's Advocate runs in parallel — real-time critique is cheaper than post-implementation review
- Team Lead centralises all Jira writes and transition decisions

### Testing Strategy

| Stage | Owner | Test Type |
|---|---|---|
| Development | Engineer | Unit, component |
| Local Test | Test Dev | Behaviour, edge case, local integration |
| Integration Test | Test Dev | Real containers, contracts |
| E2E Impact | Test Dev | Targeted journey tests |
| Regression | Test Dev | Full system regression |

---

## 10. Lessons Learned

25+ improvements from Hindsite and Treemail:

### Repository & Git
1. Separate repos per service — no monorepos
2. Push to org, not personal accounts
3. Rebase only features — never shared branches
4. No direct commits to main — pre-push hook enforces
5. Never delete branches — audit trail

### Pipeline Operations
6. One commit per file change, Jira ID in every commit
7. Push after every commit
8. One ticket at a time
9. CLAUDE.md changes go direct to ci (operational config)
10. Tag main on every release

### Docker & Environments
11. Docker environments must be project-specific (not copied verbatim)
12. Mandatory rebuild after every branch operation
13. Build verification before every merge/cut/promote
14. Images tagged per environment (:ci, :rc, :prod)
15. NEXT_PUBLIC_* must be Docker build args, not runtime env vars
16. Environments must always be running and reflect current branch state

### Decomposition
17. Journey-first decomposition — not component-first
18. App Shell must be first feature Deliverable
19. Every Deliverable must answer "what can the user do?"

### Quality
20. Defined-but-unused infrastructure is a bug
21. Mandatory patterns: transactions, retry, middleware, validation, logging
22. Per-deliverable observability scoping (infrastructure vs feature vs bugfix)
23. Data-level assertions on every state-mutating test

### Process
24. Teams report FUTURE WORK — Team Lead creates Backlog tickets with full template
25. Defect routing by location: feature branch vs RC vs production
26. Session reset after merge to main (/compact)
27. Rate limit handling: pause at 98%, resume automatically
28. Never combine pipeline stages into one agent spawn

---

## 11. Starter Template Repository

14 scaffolded starters + 8 placeholder starters = 22 total.

### Service Starters (scaffolded)
| Starter | Stack | Purpose |
|---|---|---|
| starter-api | Python/FastAPI | REST API backend |
| starter-web | Next.js/TypeScript | Web frontend |
| starter-worker | Node.js/TypeScript | Event consumer, job processor |
| starter-gateway | Express/TypeScript | API gateway / BFF |
| starter-batch | Node.js/TypeScript | Scheduled batch processing |
| starter-notification | Node.js/TypeScript | Multi-channel delivery |
| starter-docs | Node.js/TypeScript | Document generation + storage |
| starter-orchestrator | Node.js/TypeScript | Workflow state machine |
| starter-realtime | Node.js/TypeScript | WebSocket/SSE live updates |
| starter-audit | Node.js/TypeScript | Immutable audit log |
| starter-observability | Config only | OTel collector, Grafana dashboards, alerts |

### Placeholder Starters (conventions only)
| Starter | Stack | Status |
|---|---|---|
| starter-ios | Swift/SwiftUI | Conventions documented |
| starter-android | Kotlin/Compose | Conventions documented |
| starter-desktop | Tauri/Electron | Conventions documented |
| starter-chrome-extension | Manifest v3 | Conventions documented |
| starter-cli | Node.js or Go | Conventions documented |
| starter-serverless | Lambda/Workers | Conventions documented |
| starter-ml | Python/FastAPI | Conventions documented |
| starter-infrastructure | Terraform/Pulumi | Conventions documented |

### Auto-generated Clients
| Starter | Purpose |
|---|---|
| starter-client-py | Python SDK from OpenAPI spec |
| starter-client-ts | TypeScript SDK from OpenAPI spec |

---

## 12. Updates Since Initial Release

The following features were added after the initial pipeline configuration and are not yet integrated into the sections above. They apply to both the starter-team template and live projects.

### 12.1 Diagnostics Team

A dedicated agent team (`diagnostics-team.md`) replaces inline Fix Agents across all test teams. The Team Lead spawns the Diagnostics Team whenever a defect is found at any pipeline stage.

**Triage methodology:** Read error → Reproduce → Isolate → Diagnose → Fix → Verify

- Maximum 2 fix cycles before escalating to human
- Commits only to the branch specified by the Team Lead (feature, ci, or release-rc)
- Separates investigation (Investigator role) from repair (Fixer role)
- Must read `context/environment-config.md` for Docker/environment defects

The local-test, integration-test, e2e-impact, and regression teams no longer have inline Fix Agents. They report failures and the Team Lead spawns the Diagnostics Team.

### 12.2 Git Notes for Branch Tracking

`pipelinectl` annotates merge commits and branch-off points using `git notes append`. This makes branch relationships queryable without parent-hash inference.

| Event | Note on | Note content |
|---|---|---|
| Feature merged into ci | ci merge commit | `merge: feature/{key}/{slug} into ci — {key}` |
| Feature branched from ci | ci commit at branch point | `branch-off: feature/{key}/{slug} from ci — {key}` |
| RC cut from ci | ci commit at cut point | `branch-off: release-rc-{n} from ci — {key}` |
| RC merged into main | main merge commit | `merge: release-rc-{n} into main — {key}` |
| Main back-merged into ci | ci merge commit | `merge: main (v{x}.{y}.0) back-merge into ci — {key}` |

Notes are pushed to the remote via `refs/notes/commits`. The environment dashboard reads these to render the pipeline activity visualisation.

**Backfilling:** Run `infra/backfill-notes.sh` to annotate historical commits.

**Startup check:** The Team Lead syncs notes on every new session:
```bash
for svc in {SERVICE_REPOS}; do
  (cd "../$svc" && git fetch origin refs/notes/commits:refs/notes/commits 2>/dev/null) || true
done
```

### 12.3 PIPELINE-STATE.md (Crash Recovery)

A `PIPELINE-STATE.md` file at the workspace root tracks the current pipeline state. The Team Lead updates it after every Jira transition and agent signal. After session compaction or restart, the Team Lead reads it to recover.

`jiractl transition` auto-updates PIPELINE-STATE.md with the new status, ticket key, summary, and timestamp.

### 12.4 jiractl Enhancements

**`jiractl backlog`** — queries the Backlog for the next Deliverable. Used by the Team Lead after a ticket reaches Done (Step 7 auto-advance). Added to the startup checks in CLAUDE.md.

**`jiractl create` (unified)** — single command for all ticket creation. Description can be a file, stdin, inline text, or omitted (auto-loads template). Validates that Deliverables have required sections (Problem, Business Rules, Acceptance Criteria) and Issues have required sections (Symptom, Evidence). Strips HTML comments from templates before submitting.

**Component matching** — case-insensitive, hyphen-to-space matching. `prediction-service` matches Jira component "Prediction Service".

**Component enforcement** — components are NOT set at ticket creation. The Implementer sets them during development (step 5 in the completion checklist). The Team Lead's completion gate blocks transition if components are "none".

### 12.5 RC Skip for Unchanged Repos

`pipelinectl cut-rc` checks each repo for non-merge commits since the last RC using `git log --no-merges`. Back-merges from main are excluded. Repos with no new work are skipped — no RC branch is created.

The Jira comment on RC cut reports which repos were included and which were skipped.

### 12.6 Ticket Templates

Three templates in `infra/ticket-templates/`:

| Template | Type | Required sections |
|---|---|---|
| `deliverable.md` | Deliverable | Problem, Business Rules, Acceptance Criteria, Data Model, API Surface, Dependencies |
| `issue.md` | Issue | Symptom, Evidence, Environment, Impact, Steps to Reproduce, Root Cause, Suggested Fix |
| `task.md` | Task | What to do, Acceptance Criteria, Files to modify |

`jiractl create` auto-loads the matching template when no description is provided. Validates required sections and warns about empty (unfilled) sections.

### 12.7 Best Practices (25 files)

Best practices are split into three categories:

**Cross-cutting (14 files)** — read once per session, stay in `.claude/context/best-practices/`:
testing, security, docker, observability, resilience, database, redis, api-design, queues-events, error-handling, migration-safety, authentication, performance, git-conventions

**Language-specific (7 files)** — copied into service repos at project creation:
python + fastapi + async-python → starter-api; typescript + async-typescript → all TS starters; nextjs + css-tailwind → starter-web

**Pipeline (4 files)** — Team Lead only:
pipeline-orchestration, pipeline-feature-branch, pipeline-ci-branch, pipeline-release-branch

### 12.8 Environment Dashboard Enhancements

The environment dashboard (`infra/dashboard.py`) includes:

- **Pipeline Activity tracks** — four-track visualisation (feature, ci, rc, main) using git notes for branch/merge relationships
- **Per-repo carousel** — tab per service repo, auto-switches to repo with latest commit
- **Rich commit tooltips** — hover shows hash, subject, author, files changed, lines added/removed (via `/api/commit-detail` endpoint)
- **Pulsing active commits** — commits deployed in running environments pulse (requires `git.commit` Docker image label from `envctl rebuild`)
- **Service status dots** — green (healthy), red (unhealthy), amber pulsing (starting/stopping), grey (not running/exited)
- **Transitional action states** — clicking Start/Stop/Rebuild immediately shows STARTING/STOPPING/REBUILDING before the action completes
- **Threaded HTTP server** — concurrent request handling so tooltips don't block track refreshes
- **15-second response cache** — tracks endpoint cached to avoid repeated git operations

### 12.9 Docker Build Improvements

**`envctl rebuild`** uses `git archive` to extract branch content into a temp directory — the working tree is untouched. Dev teams stay on their feature branch while environments rebuild from ci/main.

**`envctl up`** starts from pre-built tagged images only — no checkout, no rebuild.

**Build labels:** `envctl rebuild` stamps `--label git.commit={hash}` and `--label git.branch={branch}` on every image.

**Auto-prune:** After every rebuild, `docker image prune -f` and `docker builder prune -f --keep-storage=5GB` run to prevent disk exhaustion.

**`merge-rc` build gate:** Verifies Docker build passes on every repo that has the RC branch (not just the first repo).

### 12.10 Pre-push Hook

The `.githooks/pre-push` hook blocks direct pushes to both `main` AND `ci` — only `--no-ff` merge commits are allowed through.

### 12.11 Commit Message Hook

The `.githooks/commit-msg` hook validates commit messages start with a ticket key (`SENT-42:`) or conventional prefix (`chore:`, `fix:`, `feat:`, etc.).

