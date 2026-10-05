# Pipeline Toolkit

Reusable starter templates, agent-team definitions, pipeline scripts and setup guides for running an **AI-native delivery pipeline**: Claude Code agent teams that take a product from capability design through to tested, released services, with Jira as the system of record.

The toolkit has three layers:

1. **Delivery pipeline.** `starter-delivery-team/` holds the agent teams that design the system (capability team) and build it (development team), plus a Programme Lead that moves work between them.
2. **Service starters.** `starter-*/` are minimal, working skeletons for each kind of service the development team builds: API, web, worker, gateway and more.
3. **Reference material.** These are the setup guides, the capability meta-model, regulation and standards libraries, an idea template and Claude Code slash commands.

Everything here is a template. Copy what you need into a project workspace, replace the `{PLACEHOLDER}` values and start building. Nothing in this repo runs as a product.

---

## Repository layout

| Path | What it is |
|---|---|
| `starter-delivery-team/` | The end-to-end pipeline. Copy it once per project. Contains the Programme Lead, `capability-team/` and `development-team/`. |
| `starter-delivery-team/capability-team/` | Design pipeline. Phases A–C produce a machine-readable system specification (capabilities, journeys, APIs, events, data model) as JSON. It has 4 agent teams and Python validators. |
| `starter-delivery-team/development-team/` | Build pipeline. Refinement → development → local, integration, E2E-impact and regression testing → release. It has 8 agent teams, Docker environments, CI workflows and the `jiractl`/`pipelinectl`/`envctl` tools. |
| `starter-api/` … `starter-worker/` | Service starters, one per service repo. See [Service starters](#service-starters). |
| `starter-client-py/`, `starter-client-ts/` | SDK clients generated from a service's OpenAPI spec. |
| `starter-observability/` | OpenTelemetry Collector, Grafana dashboards, Prometheus alerts and synthetic checks. This is infrastructure config, not a service. |
| `starter-regulations/` | Regulations grouped by sector, tagged with the countries that apply them. Read by the capability team in Phase A. |
| `starter-standards/` | Non-regulatory standards (WCAG, ISO 27001, SOC 2, ISO 9001 …). Read by both teams. |
| `capability-meta-model/` | Sector-neutral JSON Schemas for capabilities, journeys, services, events, data stores, NFRs and more. This is the base that sector packs build on. |
| `idea-template/` | Product and architecture blueprint template (Problem → Vision → Journeys → Capabilities → Initiatives). |
| `commands/` | Claude Code slash commands for Jira, Confluence and project setup (`/create-project`, `/take-task`, `/prd` …). |
| `development-pipeline-config/` | Setup guide for the build pipeline: HTML pages, plus `development-pipeline-configuration-guide.md` as a single-file reference. |
| `capability-pipeline-config/` | Methodology guide for the capability-driven design pipeline (`claude-setup.html`). |
| `CONTEXT.md` | Template catalogue and technology stack, written for agents. |

Each starter and team folder has its own `CONTEXT.md`, which explains what the folder is. Code starters also have a `CLAUDE.md` with coding conventions. Agents read both before changing anything.

---

## Prerequisites

| Need | Notes |
|---|---|
| Claude Code | `npm install -g @anthropic-ai/claude-code`. Needs a Pro or Max plan. |
| Jira Cloud | The free tier works. You also need an API token from https://id.atlassian.com/manage-profile/security/api-tokens |
| Atlassian MCP | Used for Jira operations when `jiractl` isn't configured |
| GitHub + `gh` CLI | One GitHub organisation per project. Install the *GitHub for Jira* app on it. |
| Docker Desktop | Runs the CI, RC and prod-parity environments |
| Git 2.x | |
| Node.js 22 | For the TypeScript starters |
| Python 3.12 + [uv](https://docs.astral.sh/uv/) | For `starter-api`. The capability-team scripts only need Python 3's standard library. |

---

## Usage

### 1. Get the toolkit

```bash
git clone https://github.com/chrisxmacedo/pipeline-toolkit.git ~/Projects/templates
```

The slash commands and some docs assume the toolkit lives at `~/Projects/templates`.

### 2. Install the slash commands

```bash
mkdir -p ~/.claude/commands
cp ~/Projects/templates/commands/*.md ~/.claude/commands/
```

| Command | Purpose |
|---|---|
| `/idea` | Turn problem observations into Problem, Vision, Strategy, Metrics and Initiatives pages |
| `/prd` | Generate `PRD.md` and `PLAN.md` for a new API project or feature |
| `/create-project` | Set up a project: local folder, Jira project, Confluence space, architecture and tickets |
| `/create-jira-project`, `/create-jira-components` | Guided Jira setup |
| `/create-jira-initiative`, `/create-jira-deliverable`, `/create-jira-task` | Create tickets at each level of the hierarchy |
| `/create-confluence-space`, `/migrate-idea` | Confluence setup and moving an idea into it |
| `/take-task` | Claim a Jira ticket and advance it through the pipeline |
| `/review-pr` | Self-review the current PR with a sub-agent |
| `/board`, `/create-ticket`, `/move-ticket`, `/update-ticket` | Mission Control (GitHub) board operations |

### 3. Read the guides

```bash
open ~/Projects/templates/development-pipeline-config/index.html
open ~/Projects/templates/capability-pipeline-config/claude-setup.html
```

Read the development guide pages in order: prerequisites → Jira setup → Claude setup → pipeline → agent teams → branching. The capability guide covers the 13 design steps, the gates and the artefact repository.

### 4. Start a project with the delivery pipeline

```bash
cp -r ~/Projects/templates/starter-delivery-team ~/Projects/my-project
cd ~/Projects/my-project
```

1. **Create three Jira projects** with `/create-jira-project`. The workflows each one needs are in `.claude/context/jira-lifecycle.md` §1.

   | Project | Owner | Holds |
   |---|---|---|
   | Foundation (`{FOUND_KEY}`) | Capability Lead | Phase A/B artefact tickets |
   | Modelling (`{MODEL_KEY}`) | Capability Lead | Phase C journey epics |
   | Development (`{DEV_KEY}`) | Programme Lead → Team Lead | One Deliverable per stable journey |

2. **Add Jira credentials** to `development-team/infra/.env.jira`:

   ```bash
   JIRA_EMAIL=you@example.com
   JIRA_API_TOKEN=your-token
   ```

3. **Replace every placeholder.** The top level, both sub-teams and all three `PIPELINE.md` files have them:

   ```bash
   grep -rn "{[A-Z_]\+}" . | grep -v node_modules
   ./development-team/infra/verify-placeholders.sh   # exit 0 = clean
   ```

   The top-level placeholders are `{PROJECT_NAME}`, `{ORG_NAME}`, `{FOUND_KEY}`, `{MODEL_KEY}` and `{DEV_KEY}`. Each sub-team `CONTEXT.md` lists its own.

4. **Start the Programme Lead.** Open Claude Code in the project folder and have it act as the Programme Lead defined in `PIPELINE.md`. It runs its startup checks, then spawns the Capability Lead. Don't create Jira components yet; they're added at Gate 1, once the service catalogue is stable.

#### How work flows

```
Capability Lead                     Programme Lead                  Team Lead
Phase A Discovery ─┐                                               Refinement
Phase B Framing    ├─ Gate 1 ──►  creates Sprint 0 (infra)  ──►   Development
Phase C per journey┘                                               Local / Integration
     └─ Gate 2 (journey stable) ─► DEV Deliverable + evidence ──►  E2E impact / Regression
                                                                   Release → Done
                  ◄── spec defects routed back ──  ◄── FIX EXHAUSTED / Done ──
```

- Design and build overlap. The first journey can be live while later ones are still being modelled.
- Humans gate only two points: a Deliverable entering development, and promotion to production.
- State lives on disk (`PIPELINE-STATE.md`, `PORTFOLIO-MAP.md`, `ARTEFACT-MAP.md`), so any Lead can be restarted. These files are ephemeral; don't commit them.
- Each pipeline appends lessons to its `workflow-improvements.md`.

#### Branching (development team)

`feature/*` → `ci` → `release-rc-{n}` → `main`. Each branch has its own Docker environment and its own gates. For full details see `development-team/.claude/context/branching.md` and the guide's *Branching* page.

### 5. Add services

For each service in the architecture, create a repo from the matching starter:

```bash
cp -r ~/Projects/templates/starter-worker ~/Projects/my-project/payments-worker
cd ~/Projects/my-project/payments-worker
grep -rn "{[A-Z_a-z-]\+}" . | grep -v node_modules   # replace placeholders
cp .env.example .env                                  # fill in real values
git init
mkdir -p .githooks                                     # pre-push hook blocks direct pushes to main/ci
cp ../development-team/.githooks/pre-push .githooks/ && chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

Then follow the repo's `CLAUDE.md`. To run a starter:

| Starter type | Commands |
|---|---|
| TypeScript starters | `npm install` · `npm run dev` · `npm test` · `npm run lint` · `npm run build` |
| `starter-api` (FastAPI) | `uv sync` · `uv run alembic upgrade head` · `uv run uvicorn src.main:app --reload`. Docs are served at `http://localhost:8000/docs`; see `docs/HUMAN_GUIDE.md`. |
| `starter-observability` | `docker compose up`. It receives OTLP on :4317 (gRPC) and :4318 (HTTP). |

Register each service in the development team's Docker Compose files (`development-team/infra/docker-compose.*.yml`) and its service list (`SERVICE_REPOS`).

### 6. Day-to-day tools

These scripts handle the routine pipeline work so it doesn't cost Claude tokens:

```bash
cd development-team/infra
./jiractl poll | status KEY-22 | transition KEY-22 <id> | comment KEY-22 "msg"
./pipelinectl poll | local-gate KEY-22 | ci-gate KEY-22 | merge-to-ci KEY-22 | cut-rc KEY-22 | merge-rc KEY-22 N
./envctl up|down|rebuild ci|rc|prod|all · ./envctl status · ./envctl logs ci
./dashboard.py              # environment dashboard on :4400 (--port to change)
```

Capability-team validators run from `capability-team/` and use only the Python standard library:

```bash
python3 scripts/scaffold-journey.py <journey-id> <journey-slug>   # before modelling a journey
python3 scripts/validate-journey.py <journey-dir-name>            # after: files, IDs, ownership, schemas
python3 scripts/validate-sequences.py <journey-dir-name>          # cross-capability violations
python3 scripts/sync-central-model.py <journey-dir-name>          # aggregate entities/events/service map
python3 scripts/validate-central-model-impact.py <journey-slug>   # cross-journey regressions (informational)
```

`validate-data-integrity.py`, `generate-step-manifest.py`, `generate-event-schemas.py` (Avro) and `validate-completeness.py` cover deeper checks. See `capability-team/.claude/context/process-improvements.md` for the full script list.

---

## Service starters

| Starter | Stack | Purpose |
|---|---|---|
| `starter-api` | Python 3.12, FastAPI, SQLAlchemy + Alembic | REST API backend |
| `starter-web` | Next.js 14, TypeScript, Tailwind, Prisma, NextAuth | Web frontend |
| `starter-worker` | TypeScript, Redis/Kafka | Event consumer / job processor (retry, circuit breaker, DLQ) |
| `starter-gateway` | Express, TypeScript | API gateway / BFF (JWT, rate limiting, correlation IDs) |
| `starter-batch` | TypeScript | Scheduled, resumable batch jobs |
| `starter-notification` | TypeScript | Email, SMS, push and in-app delivery |
| `starter-docs` | TypeScript, S3/MinIO | PDF/DOCX generation and storage |
| `starter-orchestrator` | TypeScript | Workflow state machine with compensation |
| `starter-realtime` | TypeScript, Redis pub/sub | WebSocket / SSE updates |
| `starter-audit` | TypeScript | Append-only, hash-chained audit log |
| `starter-client-py`, `starter-client-ts` | Generated | SDKs regenerated from the API's OpenAPI spec |
| `starter-observability` | OTel, Grafana LGTM | Telemetry collection, dashboards, alerts |

**Conventions only, no code yet:** `starter-ios`, `starter-android`, `starter-desktop`, `starter-chrome-extension`, `starter-cli`, `starter-serverless`, `starter-ml`, `starter-infrastructure`.

All TypeScript starters share the same baseline: Pino logging, an ioredis singleton, Prisma, OpenTelemetry, a health endpoint and graceful shutdown. `CONTEXT.md` has the full technology matrix and the producer → consumer patterns between starters.

---

## Status and known gaps

- **Build-only vs full pipeline.** `/create-project` installs the development team on its own (one Jira project, Team Lead at `.claude/CLAUDE.md`). For the design and build pipeline together, copy the whole `starter-delivery-team/` as described in [Usage step 4](#4-start-a-project-with-the-delivery-pipeline).
- **HTML guide pages** in `development-pipeline-config/` predate the Diagnostics Team and the 12-status workflow. Where they disagree, `development-pipeline-configuration-guide.md` is the current reference.
- **Placeholder starters.** The mobile, desktop, CLI, serverless, ML and IaC starters have documented conventions but no code scaffold.
- **Client starters** reference a specific GitHub org and npm scope (`ClauseHub` / `@clausehub`). Replace them with your own.
