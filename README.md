# Pipeline Toolkit

Reusable starter templates, agent-team definitions, pipeline scripts and setup guides for running an **AI-native delivery pipeline**: Claude Code agent teams that take a product from capability design through to tested, released services, with Jira as the system of record.

The toolkit has four layers:

1. **Harness.** `harness/` is the shared Claude Code runtime: permissions and hooks, the authority hook, MCP server config, headless `claude -p` runs, and schedule installation. Teams sit on this rather than each carrying their own copy.
2. **Teams.** A team is a rulebook plus specialists, and each one can be installed on its own. The delivery team is `starter-delivery-team/` (design and build). The technical chief of staff is `teams/chief-of-staff/`. See [Harness and teams](#harness-and-teams).
3. **Service starters.** `starter-*/` are minimal, working skeletons for each kind of service the development team builds: API, web, worker, gateway and more.
4. **Reference material.** These are the setup guides, the capability meta-model, regulation and standards libraries, an idea template and Claude Code slash commands.

Everything here is a template. Copy what you need into a project workspace, replace the `{PLACEHOLDER}` values and start building. Nothing in this repo runs as a product.

The delivery pipeline was already a Claude Code project (lead prompts, `.claude/agents/`, slash commands, permission baselines). That layout is unchanged, so existing installs keep working. The harness is the shared runtime for teams that should run on Claude Code's own conventions — `CLAUDE.md`, subagents, skills, `.mcp.json`, settings, and headless runs — and the chief of staff is the first team built that way. It sits alongside the delivery team. It does not replace it.

---

## Harness and teams

| Team | Template | What it is allowed to do |
|---|---|---|
| Development | `starter-delivery-team/` | Design the system and build it. Install with [Usage step 4](#4-start-a-project-with-the-delivery-pipeline) or `/create-project` for the build pipeline only. |
| Technical chief of staff | `teams/chief-of-staff/` | Run the technology organisation's operating rhythm for the CTO. Install with the [standalone export](#deploy-chief-of-staff-standalone-at-work). |

The chief of staff may **read** the engineering organisation's pull requests, CI results, tickets, and delivery metrics, and it may **raise issues and chase deadlines**. It reads those systems directly (GitHub, Jira, Linear) through scripts and MCP. It does not need the delivery template on disk.

It must **not** change product code, merge or review pull requests, transition engineering tickets, or reprioritise the delivery team's work. A hook blocks those tool calls. Spend above the configured caps, architecture, people decisions, and any position the CTO has not already written down are drafts for a human.

Enable either team without the other. `/create-project` does not install the chief of staff. The export script does not copy the delivery team.

---

## Deploy Chief of Staff standalone at work

Use this when the chief of staff should run in a work repository on its own, with no delivery team and no other templates from this repo.

From the toolkit:

```bash
./harness/export-chief-of-staff.sh ~/work/cto-office
cd ~/work/cto-office
```

The destination must be missing or empty. It receives the harness (settings, MCP config, authority hook, headless runner, scheduler) and `teams/chief-of-staff` (the ARA rulebook, specialists, skills, scripts, and schedules). Nothing under `starter-delivery-team/` is copied.

### 1. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude
```

Log in once, then leave the session.

### 2. Configure the office, not the tokens

```bash
cp config/ara.env.example config/ara.env
cp config/positions.example.md config/positions.md
cp config/holidays.example.txt config/holidays.txt
```

In `config/ara.env` set the timezone, the spend caps your organisation approved, `BOARD_DATES`, and the tracker ids. The numbers in the example file are examples, not an approval. Caps are inclusive. `JIRA_SITE` is the hostname only, with no scheme.

In `config/positions.md` write only positions the CTO has already agreed. Until that file exists, the agent drafts and does not decide.

In `config/holidays.txt` put non-working dates, one ISO date per line. Weekends are already skipped.

Do not put tokens in those files. They are gitignored.

### 3. Export tokens into the environment

At least one of GitHub, Jira, or Linear must be configured, or the delivery pull stops before it calls a model.

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | Read pull requests, Actions, and deployments. Create issues if chases should be filed on GitHub. Also sent to the GitHub MCP server. |
| `GITHUB_REPOS` | Comma-separated `owner/name`. Set in `ara.env`. |
| `JIRA_API_TOKEN` | Jira Cloud REST. Create it in your Atlassian account security settings. |
| `JIRA_SITE` | Jira hostname, no scheme. Set in `ara.env`. |
| `JIRA_EMAIL` | Atlassian login email. Set in `ara.env`. |
| `JIRA_PROJECTS` | Comma-separated project keys. Set in `ara.env`. |
| `LINEAR_API_KEY` | Linear GraphQL and the Linear MCP server. |
| `LINEAR_TEAM_IDS` | Optional team ids, comma-separated. Set in `ara.env`. |
| `ANTHROPIC_API_KEY` | Only when `claude` is not already logged in. |

Optional, if your organisation hosts its own MCP endpoints: `GITHUB_MCP_URL`, `ATLASSIAN_MCP_URL`, `LINEAR_MCP_URL`.

Scheduled runs call the HTTP APIs from `scripts/pull_delivery.py` so the counts do not spend a model call. `.mcp.json` is how the agent reads a ticket or a pull request when the JSON is not enough. Both are configured only by these variables.

### 4. Check the wiring without calling a model

```bash
python3 scripts/working_days.py --date 2026-10-07
python3 scripts/run_due.py --list --at 2026-10-02T17:00:00
./scripts/claude-headless.sh --dry-run --agent weekly-delivery --prompt-file schedules/prompts/weekly-delivery.md
./scripts/install-schedule.sh --print
python3 -m unittest discover -s tests -v
```

`--list` shows which deadlines are open at that moment. `--dry-run` prints the `claude -p` command and does not start Claude.

### 5. Open the coordinator

```bash
claude
```

`CLAUDE.md` is the chief of staff. Specialists are `.claude/agents/` (`weekly-delivery`, `meeting-actions`, `planning`, `budget-tracker`, `initiative`). Procedures are `.claude/skills/`. The exported `.claude/settings.json` turns on project MCP servers so a scheduled run is not left at an approval prompt. Read `.mcp.json` before you rely on that.

### 6. Schedule the deadlines

```bash
./scripts/install-schedule.sh --install
```

This replaces the marked block in your user crontab and leaves every other line alone. The timezone is `OFFICE_TZ`. Each line runs `scripts/run-due.sh --job <id>`. That script runs the data scripts first and starts Claude only when the gate is open (for example, working day 5, or a meeting note newer than 24 hours).

| Responsibility | Job | When it actually calls Claude |
|---|---|---|
| Weekly delivery status | `weekly-delivery` | Friday 17:00 |
| Decision and action log | `meeting-log` | Hourly on weekdays, and only when a note in `inbox/meetings/` has no log yet |
| Deadline chase | `chase-deadlines` | Weekday 08:30, and only when an action is due or late |
| Quarterly plan and OKRs | `quarterly-plan` | One week before the quarter, or the previous working day if that date is not a working day |
| Board-pack technology section | `board-pack` | 10 working days before a date in `BOARD_DATES` |
| Monthly budget tracker | `budget` | Working day 5 |
| Monthly organisation update | `monthly-update` | Working day 6 |
| Initiative brief, plan, closure, RAID | `initiative` | Weekdays, when a milestone, a close date, or a missing kickoff brief is due |

Run one by hand:

```bash
./scripts/run-due.sh --job weekly-delivery
```

`CLAUDE_MAX_BUDGET_USD` (default 2) is the model-spend ceiling for that run. It is not the office tooling cap.

### 7. Drops from other people

| Drop | Path |
|---|---|
| Meeting note, with an `ended_at:` line | `inbox/meetings/<name>.md` |
| Finance actuals | `inbox/finance/actuals.csv` |
| Initiative the CTO assigned | `inbox/initiatives/<id>/meta.json` |
| Director commitments | `inbox/plans/` |

Reports are written under `outputs/`. Anything outside the role is written under `drafts/` and is not sent.

Headless runs use `claude -p` with `--permission-mode dontAsk`, so a prompt that would have asked a person is denied. The authority hook still blocks writes outside `outputs/` and `drafts/`.

---

---

## Repository layout

| Path | What it is |
|---|---|
| `harness/` | Shared Claude Code runtime: settings, MCP config, authority hook, headless runs, scheduling. |
| `teams/chief-of-staff/` | Technical chief of staff. ARA rulebook, five specialists, metric scripts, and deadline schedules. Export it on its own with `harness/export-chief-of-staff.sh`. |
| `teams/development/` | Pointer to the delivery team. The files stay in `starter-delivery-team/` so existing installs keep their paths. |
| `starter-delivery-team/` | The end-to-end pipeline. Copy it once per project. Contains the Programme Lead, `capability-team/` and `development-team/`. |
| `starter-delivery-team/capability-team/` | Design pipeline. Phases A–C produce a machine-readable system specification (capabilities, journeys, APIs, events, data model) as JSON. It has 4 agent teams and Python validators. |
| `starter-delivery-team/development-team/` | Build pipeline. Refinement → development → local, integration, E2E-impact and regression testing → release. It has 8 agent teams, Docker environments, CI workflows and the `jiractl`/`pipelinectl`/`envctl` tools. |
| `starter-api/` … `starter-worker/` | Service starters, one per service repo. See [Service starters](#service-starters). |
| `starter-client-py/`, `starter-client-ts/` | SDK clients generated from a service's OpenAPI spec. |
| `starter-observability/` | OpenTelemetry Collector, Grafana dashboards, Prometheus alerts and synthetic checks. This is infrastructure config, not a service. |
| `starter-regulations/` | Regulations grouped by sector, tagged with the countries that apply them. Read by the capability team in Phase A. |
| `starter-standards/` | Non-regulatory standards (WCAG, ISO 27001, SOC 2, ISO 9001 …). Read by both teams. |
| `capability-meta-model/` | Sector-neutral JSON Schemas for capabilities, journeys, services, events, data stores, NFRs and more. This is the base that sector packs build on. |
| `idea-template/` | Product and architecture blueprint: a Markdown template, a single-file HTML blueprint (`blueprint/`), and the design system plus worked example that `/idea` builds its pages from (`design-system/`). |
| `commands/` | Claude Code slash commands for Jira, Confluence and project setup (`/create-project`, `/take-task`, `/prd` …). `install.sh` symlinks them into `~/.claude/commands/`. |
| `install.sh` | One-time setup per machine or client. It asks for settings and working preferences, writes `~/.config/pipeline-toolkit/config.env`, and links the commands. |
| `config/` | `permissions.baseline.json`: shareable Claude Code allow rules for a projects workspace. |
| `development-pipeline-config/` | Setup guide for the build pipeline: HTML pages, plus `development-pipeline-configuration-guide.md` as a single-file reference. |
| `capability-pipeline-config/` | Methodology guide for the capability-driven design pipeline (`claude-setup.html`). |
| `CONTEXT.md` | Template catalogue and technology stack, written for agents. |
| `CLAUDE.md` | Rules for working on the toolkit itself: no client values in the repo, how placeholders work, and how to test. |

Each starter and team folder has its own `CONTEXT.md`, which explains what the folder is. Code starters also have a `CLAUDE.md` with coding conventions. Agents read both before changing anything.

---

## Prerequisites

| Need | Notes |
|---|---|
| Claude Code | `npm install -g @anthropic-ai/claude-code`. Needs a Pro or Max plan. |
| Jira Cloud | The free tier works. You also need an API token from https://id.atlassian.com/manage-profile/security/api-tokens |
| Atlassian MCP | Used for Jira operations when `jiractl` isn't configured |
| GitHub + `gh` CLI | One GitHub organisation per project. Install the *GitHub for Jira* app on it. |
| Docker Desktop (or OrbStack) | Runs the CI, RC and prod-parity environments. Needs Docker Compose 2.24.4 or later. |
| Git 2.x | |
| Node.js 22 | For the TypeScript starters |
| Python 3.12 + [uv](https://docs.astral.sh/uv/) | For `starter-api`. The capability-team scripts only need Python 3's standard library. |

---

## Usage

### 1. Get the toolkit

```bash
git clone https://github.com/chrisxmacedo/pipeline-toolkit.git ~/Projects/templates
```

Any location works. `install.sh` records where the toolkit is, so nothing depends on the path.

### 2. Run the installer (once per machine or client)

```bash
~/Projects/templates/install.sh
```

The installer:
- **Checks the prerequisites.**
- **Asks for this machine's settings:** projects and ideas folders, the client's Atlassian site, your login email, the GitHub org, and the Mission Control board.
- **Asks your working preferences:**
  - promote to production with human approval or automatically
  - start the next ticket automatically, or ask first
  - whether to also track work as GitHub issues
- **Writes everything to `~/.config/pipeline-toolkit/config.env`.** It stays outside the repo, so the repo never holds client details.
- **Symlinks the slash commands** into `~/.claude/commands/`, so edits in the repo take effect immediately. If an installed command has local edits, it's moved to a `.backup-…` folder instead of being overwritten.
- **Optionally merges `config/permissions.baseline.json`** into your projects workspace's `.claude/settings.json`. That file holds the git, gh, docker compose, infra-script and Atlassian rules, and nothing destructive.

Re-run it to change answers or to switch to a different client; the current answers are offered as defaults. `--defaults` re-applies them without asking. No secrets are stored. Jira API tokens go in each project's `infra/.env.jira`, and for the Mission Control bot token only the *name* of the environment variable that holds it is recorded.

`/create-project` writes your working preferences into each new project's `.claude/context/project.md` ("Working preferences"). You can change them there for an individual project.

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
./jiractl poll | status KEY-22 | transition KEY-22 <id>
./jiractl comment KEY-22 "msg" | report.md | -     # inline, markdown file, or stdin → Jira rich text
./jiractl transitions KEY-22                       # valid transition IDs, live from Jira
./pipelinectl poll | local-gate KEY-22 | ci-gate KEY-22 | merge-to-ci KEY-22 | cut-rc KEY-22 | merge-rc KEY-22 N
./envctl up|rebuild ci|rc|prod|all                 # images built from each env's branch, no checkout
./envctl rebuild-local ci                          # build from the working tree (first Deliverable)
./envctl test rc integration                       # boot, run suite against BASE_URL, tear down
./envctl down ci|rc|prod [--wipe]                  # prod keeps its volumes unless --wipe
./dashboard.py                                     # environment dashboard on :4400 (--port to change)
```

- **`local-gate`** runs in every repo that has the feature branch. By default it picks lint / format:check / typecheck / build / test from `package.json` scripts, or ruff / mypy / pytest for `pyproject.toml` repos. Set `LOCAL_GATE_CMDS` in `pipelinectl` to override.
- **`ci-gate`** builds the Test stack (CI services plus fixture seeding) from `ci` and runs the integration suite against it, so integration tests can rely on seeded records. Set the suite commands (`INTEGRATION_TEST_CMD` etc.) in `envctl`.
- **CI, RC and prod-parity run side by side** on base ports, +100 and +200. Host ports live only in the per-environment Compose overrides, and the RC stack re-binds CI's ports with `ports: !override`.

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

- **Build-only vs full pipeline.** `/create-project` installs the development team on its own (one Jira project, Team Lead at `.claude/CLAUDE.md`). For the design and build pipeline together, copy the whole `starter-delivery-team/` as described in [Usage step 4](#4-start-a-project-with-the-delivery-pipeline). Neither path installs the chief of staff.
- **Chief of staff.** Install only that team with `./harness/export-chief-of-staff.sh <empty-dir>`. See [Deploy Chief of Staff standalone at work](#deploy-chief-of-staff-standalone-at-work).
- **HTML guide pages** in `development-pipeline-config/` predate the Diagnostics Team and the 12-status workflow. Where they disagree, `development-pipeline-configuration-guide.md` is the current reference.
- **Placeholder starters.** The mobile, desktop, CLI, serverless, ML and IaC starters have documented conventions but no code scaffold.
- **Client starters** reference a specific GitHub org and npm scope (`ClauseHub` / `@clausehub`). Replace them with your own.
