---
description: Create a new project — local folder, Jira project, Confluence space, idea migration, architecture selection, and ticket creation
---

# Create Project: $ARGUMENTS

Orchestrate the full project creation process from start to finish. Work
through each stage collaboratively — never rushing ahead or batching steps.

---

## Config

Machine- and client-specific settings live in `~/.config/pipeline-toolkit/config.env`,
written by `install.sh` in the pipeline-toolkit repo. Each shell command runs in
a fresh shell, so start every bash block that uses these values with:

```bash
source ~/.config/pipeline-toolkit/config.env
```

If that file doesn't exist, stop and ask the user to run `install.sh` from the
pipeline-toolkit repo. Values: `$ATLASSIAN_SITE` (Atlassian cloud ID / site),
`$JIRA_URL`, `$CONFLUENCE_URL`, `$PROJECTS_DIR`, `$IDEAS_DIR`, `$TOOLKIT_DIR`,
plus working preferences `$PROMOTE_POLICY`, `$NEXT_TICKET_POLICY`, `$GITHUB_ISSUES`.

---

## CRITICAL — Step-by-step collaborative process

Work through this one stage at a time. After each stage, stop and wait
for the user to confirm before moving to the next.

1. **Name & create folder** → user confirms name → local project folder created
2. **Move idea** → idea folder moved into project folder
3. **Create Jira project** → run `/create-jira-project`
4. **Create Confluence space** → run `/create-confluence-space`
5. **Migrate idea to Confluence** → run `/migrate-idea`
6. **Select architecture** → user picks architecture tier
7. **Set up pipeline templates** → copy the development-team template to project
8. **Create service repos** → init git repos for each service
9. **Set up Docker environments** → configure infra/, tests/, workflows
10. **Create Jira components** → run `/create-jira-components`
11. **Create Initiatives** → run `/create-jira-initiative` for each
12. **Create Deliverables** → run `/create-jira-deliverable` for each
13. **Create Tasks** → run `/create-jira-task` for each deliverable

Never skip a stage. Never combine stages. Always wait for user confirmation.

---

## Stage 1 — Name and create the project folder

Parse `$ARGUMENTS` for a project name. If not provided, ask:

> "What is the project name? This will be the folder name in Projects/
> (e.g. `clausehub`, `hindsite`, `raretee`)."

Confirm the name, then create the folder:

```bash
mkdir -p "$PROJECTS_DIR/{name}"
```

Tell the user:

> "Project folder created at Projects/{name}. Now let's move the idea."

**Stop and wait.**

---

## Stage 2 — Move the idea folder

List available ideas:

```bash
ls "$IDEAS_DIR"
```

Ask the user which idea belongs to this project. Move it:

```bash
mv "$IDEAS_DIR/{idea}" "$PROJECTS_DIR/{name}/idea-{idea}"
```

Tell the user:

> "Idea moved to Projects/{name}/idea-{idea}. Now let's set up Jira."

**Stop and wait.**

---

## Stage 3 — Create Jira project

Run `/create-jira-project {name}`.

This guides the user through creating a company-managed Jira project with
the correct issue type hierarchy:

```
Initiative (Level 2)
  └─ Deliverable (Level 1)
      └─ Task (Level 0)
          └─ Sub-task (Level -1)
```

Capture the **project key** (e.g. `ENERGY`, `HIND`). This key is used for
all subsequent ticket creation.

**Stop and wait.**

---

## Stage 4 — Create Confluence space

Run `/create-confluence-space {name}`.

This guides the user through creating a Confluence space. The space key
should match the Jira project key where possible.

Capture the **space ID** for the migration step.

**Stop and wait.**

---

## Stage 5 — Migrate idea to Confluence

Run `/migrate-idea {idea name}`.

This reads all HTML pages from `Projects/{name}/idea-{idea}/` and creates
structured Confluence pages in the space from Stage 4:

- Problem statement
- Product vision (architecture, data model, deployment)
- Strategy
- Metrics / OKRs
- Initiatives

Tell the user:

> "Idea content migrated to Confluence. All documentation is now in
> {CONFLUENCE_URL}/wiki/spaces/{key}. Now let's choose the architecture."

**Stop and wait.**

---

## Stage 6 — Select architecture

Read the idea's architecture sections — specifically:

- **Section 6: Technical Services** — lists every service, what it does, and
  which starter template it maps to
- **Section 7: C4 Containers** — maps services to deployable names and tech

If the idea defines architecture tiers (Current/Startup/Enterprise), present
them and ask the user to pick one:

> "The idea documentation defines these architecture tiers:
>
> 1. **Current** — Minimal proof-of-concept (~$30/mo)
> 2. **Startup** — Low cost, fast iteration (~$61-135/mo)
> 3. **Enterprise** — 99.9%+ availability ($7.4k-18.2k/mo)
>
> Which tier should we implement?"

If no tiers are defined, use the Technical Services table directly.

**After the user picks a tier**, extract the **service list** from the idea.
Each service in the Technical Services table (Section 6) has a `Starter template`
column that maps it to a starter. The C4 Containers table (Section 7) gives
the deployable name.

Present the derived service list:

> "Based on the {selected tier} architecture, these services will be created:
>
> | Deployable name | Service | Starter template |
> |---|---|---|
> | {e.g. acme-api} | {Customer Profile Service} | starter-api |
> | {e.g. acme-web} | {Customer Portal} | starter-web |
> | {e.g. acme-worker} | {Payments Processing} | starter-worker |
>
> Approve, or modify?"

Capture the approved service list. **This list drives Stages 7, 8, and 9** —
the number of repos, Docker Compose services, and pipeline configuration all
come from it.

**Stop and wait.**

---

## Stage 7 — Set up pipeline templates

Copy the build-pipeline (development-team) templates into the project:

> This installs the **build pipeline only** (one Jira project, Team Lead at
> `.claude/CLAUDE.md`). If the project also needs the capability-driven
> design pipeline (Phases A–C, FOUND/MODEL/DEV Jira projects, Programme Lead),
> copy the whole `templates/starter-delivery-team/` instead and follow its
> `CONTEXT.md` → "How to kick off a new project". Ask the user which they want
> before running this stage.

```bash
TEMPLATES_DIR=$TOOLKIT_DIR/starter-delivery-team/development-team

# Copy pipeline orchestration (becomes .claude/CLAUDE.md)
mkdir -p "$PROJECTS_DIR/{name}/.claude"
cp "$TEMPLATES_DIR/PIPELINE.md" "$PROJECTS_DIR/{name}/.claude/CLAUDE.md"

# Copy agent team files
mkdir -p "$PROJECTS_DIR/{name}/.claude/agents"
cp "$TEMPLATES_DIR/.claude/agents/"*.md "$PROJECTS_DIR/{name}/.claude/agents/"

# Copy context directory (agent rules, pipeline stages, best practices, etc.)
cp -r "$TEMPLATES_DIR/.claude/context" "$PROJECTS_DIR/{name}/.claude/context"

# Copy hooks and settings
cp "$TEMPLATES_DIR/.claude/settings.local.json" "$PROJECTS_DIR/{name}/.claude/settings.local.json"

# Copy architecture template
cp "$TEMPLATES_DIR/ARCHITECTURE.md" "$PROJECTS_DIR/{name}/ARCHITECTURE.md"

# Create workflow-improvements.md log
cat > "$PROJECTS_DIR/{name}/workflow-improvements.md" << 'EOF'
# Workflow Improvements — {PROJECT_NAME}

Retrospective log from agent team completions.

---

<!-- Entries are appended here by the Team Lead after each team completes -->
EOF
```

Replace ALL placeholders in CLAUDE.md, agent files, and context files:

| Placeholder | Replace with | Source |
|---|---|---|
| `{PROJECT_KEY}` | Jira project key (e.g. `ACME`) | Stage 3 |
| `{PROJECT_NAME}` | Project name (e.g. `acme`) | Stage 1 |
| `{CLOUD_ID}` | `$ATLASSIAN_SITE` | Config |
| `{JIRA_SITE}` | `$ATLASSIAN_SITE` | Config |
| `{SERVICE_REPOS}` | Space-separated service names (e.g. `acme-api acme-web`) | Stage 6 |
| `{service-1}`, `{service-2}`, etc. | Actual service names (match the Stage 6 list) | Stage 6 |

These placeholders appear in PIPELINE.md (startup checks iterate `{SERVICE_REPOS}`),
`context/project.md` (describes repo structure), and agent files (branch naming).

**Apply working preferences** from the config (answers given to `install.sh`)
to `.claude/context/project.md` → "Working preferences":

| Placeholder | Config value → text to write |
|---|---|
| `{PROMOTE_POLICY}` | `human` → "Human approval — wait for \"Approve promote {PROJECT_KEY}-N\"". `auto` → "Automatic when the regression readiness report is green; any failure or warning still waits for the human" |
| `{NEXT_TICKET_POLICY}` | `auto` → "Pick up the next Backlog Deliverable automatically". `ask` → "Stop and ask the human before starting the next ticket" |
| `{GITHUB_ISSUES_POLICY}` | `yes` → "Create a GitHub issue before starting work, reference it in the PR, close it on merge". `no` → "Not used — Jira is the only tracker" |

Tell the user which preferences were applied and that they can be changed per
project by editing that section.

**Discover transition IDs** — these change per project and cannot be hardcoded.
After Stages 11-13 create the first tickets, query Jira for the actual IDs:

```bash
# Deliverable transitions (query a Deliverable ticket)
cd infra && ./jiractl transitions {PROJECT_KEY}-{first_deliverable}
# Task transitions (query a Task ticket)
cd infra && ./jiractl transitions {PROJECT_KEY}-{first_task}
```

Replace the transition ID placeholders in `context/pipeline-stages.md`,
`agents/development-team.md`, and `infra/pipelinectl`:

| Placeholder | Deliverable workflow |
|---|---|
| `{T_BACKLOG}` | → Backlog |
| `{T_REFINE}` | → In Refinement |
| `{T_DEV}` | → In Development |
| `{T_LOCAL}` | → In Local Test |
| `{T_INTEG}` | → In Integration Test |
| `{T_E2E}` | → In E2E Impact Test |
| `{T_REGRESS}` | → In Full E2E Regression |
| `{T_RELEASE}` | → Release / Production |
| `{T_DONE}` | → Done |

| Placeholder | Task workflow |
|---|---|
| `{T_TASK_INPROGRESS}` | → In Progress |
| `{T_TASK_DONE}` | → Done |

Then create a minimal AGENT-CONTEXT.md so the Team Lead's first startup check
doesn't fail:

```bash
cat > "$PROJECTS_DIR/{name}/AGENT-CONTEXT.md" << EOF
# AGENT-CONTEXT — {PROJECT_NAME}

## Services

| Service | Type | Port | Repo |
|---------|------|------|------|
$(for svc in {service-list}; do echo "| $svc | {type} | {port} | $svc/ |"; done)

## Current state

Project just created. No code scaffolded yet.
First Deliverable (Local Development & CI Pipeline) will scaffold all services.

After the first Deliverable reaches Done, regenerate this file:
\`cd infra && ./repomap all\`
EOF
```

Create an empty PIPELINE-STATE.md so the Team Lead can write state from the
first transition (used for recovery after compaction):

```bash
cat > "$PROJECTS_DIR/{name}/PIPELINE-STATE.md" << 'EOF'
# Pipeline State — {PROJECT_NAME}

## Active ticket

No ticket in progress. Pipeline not yet started.

## Signals received

(none)

## Branch state

All repos on main.

## Last action

Project created. Awaiting first ticket to be moved to In Refinement.

## Docker environments

| Env | Running? | Last rebuilt |
|-----|----------|-------------|
| CI  | no       | —            |
| RC  | no       | —            |
| Prod| no       | —            |
EOF
```

Tell the user:

> "Pipeline templates installed:
> - CLAUDE.md and 8 agent team files
> - Context docs (agent rules, pipeline stages, best practices, decomposition)
> - Hooks (repo verification on git operations)
> - AGENT-CONTEXT.md (minimal project map for first session)
> - PIPELINE-STATE.md (crash recovery state file)
>
> All configured for {PROJECT_KEY}. Now let's create the service repos."

**Stop and wait.**

---

## Stage 8 — Create service repos

Use the service list approved in Stage 6. Each row has a deployable name
and its starter template — iterate over all of them.

Create each service repo:

```bash
TEAM_DIR=$TOOLKIT_DIR/starter-delivery-team/development-team
STARTERS_DIR=$TOOLKIT_DIR

for service in {service-1} {service-2} ...; do
  STARTER_TYPE={matching starter type for this service}

  mkdir -p "$PROJECTS_DIR/{name}/$service"
  cd "$PROJECTS_DIR/{name}/$service"
  git init
  git checkout -b main

  # Copy CLAUDE.md from the matching starter template
  # This brings coding conventions, "Before writing code" rules,
  # design system references, and pre-PR checklists
  if [ -f "$STARTERS_DIR/$STARTER_TYPE/CLAUDE.md" ]; then
    cp "$STARTERS_DIR/$STARTER_TYPE/CLAUDE.md" ./CLAUDE.md
    # Replace name placeholders
    sed -i '' "s/{project-name}/{name}/g; s/{PROJECT_NAME}/{name}/g; s/{repo-name}/$service/g" ./CLAUDE.md
  fi

  # Copy CONTEXT.md from the matching starter template
  if [ -f "$STARTERS_DIR/$STARTER_TYPE/CONTEXT.md" ]; then
    cp "$STARTERS_DIR/$STARTER_TYPE/CONTEXT.md" ./CONTEXT.md
  fi

  # Create .gitignore
  cat > .gitignore << 'EOF'
node_modules/
__pycache__/
*.pyc
.env
.env.local
.env.prod-parity
dist/
build/
.next/
coverage/
EOF

  # Create .env.example documenting all required environment variables
  cat > .env.example << 'ENVEOF'
# {service} environment variables
# Copy to .env and fill in real values
DATABASE_URL=
REDIS_URL=
ENVIRONMENT=development
LOG_LEVEL=debug
LOG_FORMAT=json
# Add service-specific vars below
ENVEOF

  # Copy language/platform best-practices into the repo
  # This is a deterministic mapping — no agent judgement required
  BP_SRC="$TEAM_DIR/.claude/context/best-practices"
  mkdir -p best-practices
  case "$STARTER_TYPE" in
    starter-api)
      cp "$BP_SRC/python.md" "$BP_SRC/fastapi.md" "$BP_SRC/async-python.md" best-practices/
      ;;
    starter-web)
      cp "$BP_SRC/typescript.md" "$BP_SRC/async-typescript.md" "$BP_SRC/nextjs.md" "$BP_SRC/css-tailwind.md" best-practices/
      ;;
    starter-worker|starter-gateway|starter-batch|starter-notification|starter-docs|starter-orchestrator|starter-realtime|starter-audit)
      cp "$BP_SRC/typescript.md" "$BP_SRC/async-typescript.md" best-practices/
      ;;
  esac

  # Copy pre-push hook to prevent direct pushes to main and ci
  mkdir -p .githooks
  cp "$TEAM_DIR/.githooks/pre-push" .githooks/pre-push
  chmod +x .githooks/pre-push
  git config core.hooksPath .githooks

  git add .gitignore .env.example .githooks/ CLAUDE.md best-practices/
  [ -f CONTEXT.md ] && git add CONTEXT.md
  git commit -m "chore: initialize $service repo with conventions from $STARTER_TYPE"

  # Create ci branch from main
  git checkout -b ci
  git checkout main
done
```

Note: The full service scaffold (Dockerfile, src/, tests/, package.json or
pyproject.toml) is NOT copied at this stage — that is the job of the "Local
Development & CI Pipeline" Deliverable. But the CLAUDE.md conventions MUST be
present from the first commit so every agent that touches the repo knows the
coding rules.

Present the repos created and guide the user through GitHub setup:

> "Service repos initialized locally with main + ci branches.
> Each repo includes CLAUDE.md (coding conventions from its starter template)
> and CONTEXT.md (service purpose and integration points).
>
> | Repo | Starter | Path |
> |------|---------|------|
> | {service-1} | {starter-type} | Projects/{name}/{service-1}/ |
> | {service-2} | {starter-type} | Projects/{name}/{service-2}/ |
>
> Now we need to push these to GitHub. Please:
>
> 1. **Create a GitHub organization** for this project (e.g. `{name}-cxm`)
>    at https://github.com/organizations/plan — Free tier is fine.
>
> 2. **Create repos** in the org for each service (public or private).
>
> 3. **Add remotes and push** — I'll do this once you confirm the org name.
>
> 4. **Connect GitHub for Jira** — go to the org's Settings → GitHub Apps,
>    find **Jira** (from Atlassian), and install it. Select all repos in the
>    org. This gives you commits, branches, PRs, and CI build status in the
>    Jira Development panel automatically.
>
> What's the GitHub org name?"

**Stop and wait for the org name.**

Once the user confirms, push all repos:

```bash
for service in {service-1} {service-2} ...; do
  cd "$PROJECTS_DIR/{name}/$service"
  git remote add origin https://github.com/{github-org}/$service.git
  git push -u origin main
  git push -u origin ci
done
```

Confirm the push succeeded:

> "All repos pushed. Please connect GitHub for Jira:
>
> Go to the `{github-org}` org's Settings → GitHub Apps → find **Jira**
> (Atlassian) → install it. Select all repos. This gives you commits,
> branches, PRs, and CI build status in the Jira Development panel.
>
> Now let's set up Docker environments."

**Stop and wait.**

---

## Stage 9 — Set up Docker environments

Copy and customize the Docker infrastructure, test skeleton, and CI workflows:

```bash
TEMPLATES_DIR=$TOOLKIT_DIR/starter-delivery-team/development-team

# Copy infra/
cp -r "$TEMPLATES_DIR/infra" "$PROJECTS_DIR/{name}/infra"

# Copy tests/
cp -r "$TEMPLATES_DIR/tests" "$PROJECTS_DIR/{name}/tests"

# Copy GitHub Actions workflows INTO EACH SERVICE REPO — the workspace root
# is not a git repo, so workflows placed there never run (Hearthstone HEARTH-7)
for service in {service-1} {service-2} ...; do
  mkdir -p "$PROJECTS_DIR/{name}/$service/.github/workflows" "$PROJECTS_DIR/{name}/$service/.github/compose"
  cp "$TEMPLATES_DIR/.github/workflows/"*.yml "$PROJECTS_DIR/{name}/$service/.github/workflows/"
done
# Then, per repo, follow the "WHERE THIS FILE GOES" header in ci.yml: vendor the
# compose overrides into .github/compose/ (context: ../$service → context: .)
# and point the workflow's compose paths at .github/compose.

# Create empty test suite directories
mkdir -p "$PROJECTS_DIR/{name}/tests/integration"
mkdir -p "$PROJECTS_DIR/{name}/tests/e2e"
mkdir -p "$PROJECTS_DIR/{name}/tests/smoke"
mkdir -p "$PROJECTS_DIR/{name}/tests/fixtures/db"
```

Then customize ALL `{PLACEHOLDER}` values in the copied files. There are two
groups — Docker/test placeholders and script-internal placeholders. Both MUST
be replaced or the pipeline will not function.

**The following placeholders are actually present in the infra files. Every
one must be replaced or the pipeline will not function.**

**Project identity** (in docker-compose, .env, scripts, workflows, dashboard):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{PROJECT_SLUG}` | project slug (e.g. `acme`) | docker-compose (22x), .env files, pipelinectl, envwatch, dashboard |
| `{PROJECT_NAME}` | project name | docker-compose.base.yml (comment), dashboard.py |
| `{PROJECT_KEY}` | Jira project key (e.g. `ACME`) | jiractl (7x), pipelinectl |

**Jira connection** (in jiractl):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{JIRA_SITE}` | `$ATLASSIAN_SITE` | jiractl config block |
| `{CLOUD_ID}` | `$ATLASSIAN_SITE` | jiractl config block |

**Service configuration** (in pipelinectl, envctl, envwatch, docker-compose, dashboard):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{service-1}`, `{service-2}`, etc. | Actual service names from Stage 6 list. Expand the arrays to include ALL services. The compose `image: {service}:${IMAGE_TAG}` names must match the repo folder names — envctl tags images by folder name. | pipelinectl and envctl `SERVICE_REPOS`, envwatch, dashboard, docker-compose examples |
| `{SERVICE_WITH_MIGRATIONS}` | Service that owns DB migrations (e.g. `acme-api`) | docker-compose.ci.yml, docker-compose.prod-parity.yml |
| `{SERVICE_WITH_TESTS}` | Primary service for unit tests | ci.yml, release.yml |
| `{SERVICE_1}` (uppercase, in comments) | First service name — replace or remove the example comments | docker-compose files (4x) |

**Port configuration** (in envctl, dashboard, docker-compose):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{WEB_PORT}` | Base web port for CI (e.g. `3000`); RC = +100, Prod-parity = +200 | envctl `WEB_PORT_CI`, dashboard, docker-compose comments |
| `{SYNC_PORT}` | Base sync/API port for CI (e.g. `8000`) | docker-compose.base.yml (comments) |
| `{PORT}` | Per-service ports in the example service block | docker-compose.base.yml (comments) |
| `{PORT_1}`, `{PORT_2}` | Per-service ports for dashboard | dashboard.py |
| `{GRAFANA_PORT}` | Grafana UI port (e.g. `4000`) | docker-compose.prod-parity.yml |
| `{PRIMARY_SERVICE_PORT}` | Main service port for smoke tests | release.yml |

**Build & test commands** (in pipelinectl, workflows):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{MIGRATION_COMMAND}` | e.g. `npx prisma migrate deploy` or `alembic upgrade head` | docker-compose.ci.yml, docker-compose.prod-parity.yml |
| `{BUILD_COMMAND}` | Production build run before merge to ci (e.g. `npm run build`) | pipelinectl `cmd_merge_to_ci` |
| `{UNIT_TEST_COMMAND}` | e.g. `npm test` or `pytest tests/unit/` | ci.yml, release.yml |
| `{INSTALL_TEST_DEPS_COMMAND}` | Test dependency install command | ci.yml, release.yml (3x) |
| `{INTEGRATION_TEST_COMMAND}` | Integration test runner | ci.yml |
| `{E2E_TEST_COMMAND}` | E2E test runner | release.yml |
| `{SMOKE_TEST_COMMAND}` | Smoke test runner | release.yml |

**Gate commands — no placeholders, but check them:**

- `pipelinectl` `LOCAL_GATE_CMDS=(auto)` runs lint / format:check / typecheck /
  build / test from each repo's `package.json` scripts, or ruff / mypy / pytest
  for `pyproject.toml` repos. Override with explicit `"label|command"` pairs if
  the defaults don't fit.
- `envctl` `INTEGRATION_TEST_CMD` / `E2E_TEST_CMD` / `SMOKE_TEST_CMD` default to
  the Python suites in `tests/`. For a Node project point them at the service's
  scripts, e.g. `cd {service-1} && npm run --silent test:integration`.
  `BASE_URL` is exported for the environment under test.
- For the very first Deliverable, before `ci` has any code, use
  `./envctl rebuild-local ci` (builds from the working tree); `envctl rebuild`
  also falls back to the working tree automatically when a branch has no
  Dockerfile yet.

**Storage & external services** (in docker-compose):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{S3_BUCKET_NAME}` | S3/MinIO bucket name | docker-compose.test.yml |
| `{LLM_API_ENV_VAR}` | Env var name for LLM API key (e.g. `ANTHROPIC_API_KEY`) | docker-compose.base.yml |
| `{LLM_API_BASE_ENV_VAR}` | Env var name for LLM base URL | docker-compose.base.yml, .ci.yml, .prod-parity.yml |
| `{LLM_API_KEY_ENV_VAR}` | Env var name for LLM API key | docker-compose.ci.yml, .prod-parity.yml |
| `{LLM_DEFAULT_BASE_URL}` | Default LLM base URL | docker-compose.base.yml |
| `{LLM_REAL_API_URL}` | Real LLM API URL (prod-parity only) | docker-compose.prod-parity.yml |

**Jira transition IDs** (in pipelinectl — uses `{TBC}`, discovered after tickets exist):

| Placeholder | Replace with | Found in |
|---|---|---|
| `{TBC}` (9 instances, the `T_*=` config block) | Actual Jira transition IDs discovered via `./jiractl transitions ISSUE-KEY` (fetched live) | pipelinectl |

These are the SAME IDs that go into `pipeline-stages.md` as `{T_BACKLOG}`,
`{T_REFINE}`, etc. — but pipelinectl uses `{TBC}` as its placeholder.

**Without ALL of these replacements, the pipeline will fail.** `jiractl` won't
connect, `pipelinectl` won't know which repos or transition IDs to use,
`envctl` won't know which services to rebuild, and Docker Compose won't boot.

**Add every service from the Stage 6 service list** to `docker-compose.base.yml`.
Each service needs: build context, environment variables, dependencies, health
check, and port mapping. The number of services in each Docker environment is
determined by the idea's Technical Services and C4 Containers tables — not
hardcoded. Reference existing project infra/ directories (Treemail or
ContractLayer) for the service definition pattern.

Port allocation: assign sequential ports per environment to avoid clashes.
For example, with 3 services (api, web, worker):
- CI: api=8000, web=3000, worker=9000
- RC: api=8100, web=3100, worker=9100
- Prod-parity: api=8200, web=3200, worker=9200

Infrastructure services (PostgreSQL, Redis, Kafka, MinIO, Grafana LGTM) are
added based on the idea's C4 Containers table — only include what the
services actually depend on.

Also replace placeholders in `envwatch` (auto-rebuild watcher — uses
`{service-1}` and `{PROJECT_SLUG}`).

Update the agent files' Docker environment sections with the project-specific
ports and commands.

**Set up Jira API credentials** for the token-saving scripts. Ask the user:

> "Docker environments configured. Now let's connect the pipeline scripts
> to Jira.
>
> 1. **Create a Jira API token** at
>    https://id.atlassian.com/manage-profile/security/api-tokens
>    → Create API token → name it 'pipelinectl' → copy the token.
>
> 2. **Paste the token** and I'll create the credentials file."

**Stop and wait for the token.**

Once the user provides the token, create the credentials file:

```bash
cat > "$PROJECTS_DIR/{name}/infra/.env.jira" << EOF
JIRA_EMAIL={user's email}
JIRA_API_TOKEN={token they provided}
EOF
```

Verify the connection:

```bash
cd "$PROJECTS_DIR/{name}/infra" && ./jiractl poll
```

Tell the user:

> "Jira API connected. Pipeline infrastructure complete:
>
> | Environment | Command |
> |---|---|
> | CI | `docker compose -f base.yml -f ci.yml --env-file .env.ci up --wait` |
> | Test | `docker compose -f base.yml -f ci.yml -f test.yml --env-file .env.test up --wait` |
> | Prod-parity | `docker compose -f base.yml -f prod-parity.yml --env-file .env.prod-parity up` |
>
> `jiractl`, `pipelinectl`, and `envctl` are configured and verified.
> Now let's set up Jira components."

**Stop and wait.**

---

## Stage 10 — Create Jira components

Run `/create-jira-components`.

This reads the selected architecture, identifies all services/platforms
(e.g. Fly.io, Supabase, Axiom, Cloudflare, Sentry, Checkly), and guides
the user through creating matching Jira components.

**Stop and wait.**

---

## Stage 11 — Create Initiatives

Read the idea's Initiatives page (from Confluence or local HTML). The FIRST
Initiative must always be **Infrastructure Setup** — this covers local
environment setup, Docker environments, CI/CD, and ensures the pipeline is
functional before any feature work begins.

Present the list:

> "I'll create these Initiatives in Jira from the idea documentation:"
>
> | # | Initiative | Description |
> |---|-----------|-------------|
> | 1 | Infrastructure Setup | Local repos, Docker environments, CI/CD, pipeline verification |
> | 2 | {initiative 2} | {description} |
> | ... | ... | ... |
>
> "Approve, or add/remove/modify any?"

Wait for approval, then run `/create-jira-initiative` for each one.

Show a summary of created Initiatives with their keys.

**Stop and wait.**

---

## Stage 12 — Create Deliverables

For each Initiative created in Stage 11, review the features and deliverables
listed under it in the idea documentation. Present them grouped by Initiative.

**TWO CRITICAL ordering rules for Deliverables:**

**1. Infrastructure first.** The Infrastructure Setup Initiative must include
a "Local Development & CI Pipeline" Deliverable. When it's Done, the full
pipeline runs green from feature branch through to prod-parity.

**2. App Shell before features.** The FIRST feature Deliverable (after
infrastructure) must ALWAYS be the **App Shell** — the main layout, sidebar
navigation, and page composition that gives users something to see. Before
building any individual feature component, there must be a page to put it on.

Without the app shell, feature Deliverables produce isolated components and
API routes that are invisible to users. This is the "component-first vs
journey-first" trap — building capabilities without building the surface
that composes them.

The app shell Deliverable should:
- Create the authenticated layout (redirect unauthenticated users to sign-in)
- Add sidebar navigation (core sections of the app)
- Create the main content area where feature components will be composed
- Wire in the first feature component so the app is immediately usable
- Be responsive (mobile sidebar collapses)

> **{KEY}-1: Infrastructure Setup**
> - **Local Development & CI Pipeline** — Service scaffolds, Docker Compose
>   environments (CI, Test, Prod-parity), LLM stub, fixture seeder, GitHub
>   Actions workflows, health endpoints, initial test suites.
> - Hosting & Deployment ({hosting provider})
> - Database & Auth ({auth provider})
> - Observability Stack ({observability providers})
>
> **{KEY}-N: {First feature Initiative}**
> - **App Shell** — Main layout, sidebar navigation, page composition,
>   auth redirect. This MUST be the first Deliverable in the first feature
>   Initiative. All subsequent feature Deliverables compose into this shell.
> - {Feature Deliverable 1} — builds on the shell
> - {Feature Deliverable 2} — builds on the shell
>
> "Approve, or modify?"

Wait for approval, then run `/create-jira-deliverable` for each one,
setting the parent to the corresponding Initiative.

Each Deliverable description must contain ALL known information about the
platform/system/feature so Tasks can be derived without looking elsewhere.

Show a summary of created Deliverables.

**Stop and wait.**

---

## Stage 13 — Create Tasks

For each Deliverable created in Stage 12, read its description and break it
down into concrete Tasks. Each Task should be one action that can be started,
completed, and verified in a single work session.

**For the "Local Development & CI Pipeline" Deliverable**, create these Tasks:

> - Scaffold service repos with Dockerfiles and health endpoints
> - Configure Docker Compose base.yml with all services
> - Configure Docker Compose ci.yml with LLM stub and migrations
> - Configure Docker Compose test.yml with fixture seeder
> - Configure Docker Compose prod-parity.yml with OTel stack
> - Write integration test suite (health, stub, correlation, storage)
> - Write fixture seeder with deterministic test data
> - Write E2E regression test suite against fixture data
> - Write smoke + OTel validation test suite
> - Configure GitHub Actions CI workflow (feature/ci branches)
> - Configure GitHub Actions release workflow (release-rc branches)
> - Verify CI environment boots and all integration tests pass
> - Verify Test environment boots, seeds fixtures, and E2E tests pass
> - Verify Prod-parity environment boots with OTel pipeline functional

Present all Tasks grouped by Deliverable:

> **{KEY}-2: Local Development & CI Pipeline**
> - Scaffold service repos with Dockerfiles and health endpoints
> - Configure Docker Compose base.yml with all services
> - ...
>
> **{KEY}-3: Hosting & Deployment**
> - {Task 1}
> - {Task 2}
>
> "Approve, or modify?"

Wait for approval, then run `/create-jira-task` for each one, setting the
parent to the corresponding Deliverable.

Show a final summary.

**Stop and wait.**

---

## Summary

```
Project {name} created

  Folder       : Projects/{name}/
  Idea         : Projects/{name}/idea-{idea}/
  Service repos: {list of repos with main+ci branches}
  Docker envs  : CI, Test, Prod-parity (infra/)
  Pipeline     : .claude/CLAUDE.md + 8 agent teams
  Jira         : {JIRA_URL}/jira/software/projects/{key}/board
  Confluence   : {CONFLUENCE_URL}/wiki/spaces/{key}
  Architecture : {selected tier}

  Tickets:
    Initiatives  : {count}
    Deliverables : {count}
    Tasks        : {count}
    Total        : {count}

  Next steps:
    1. Move the "Local Development & CI Pipeline" Deliverable to In Refinement
    2. The Team Lead will pick it up and run it through the full pipeline
    3. When it reaches Done, the pipeline is proven and ready for feature work
```

---

## Rules

- Never rush through stages — each needs user confirmation
- Every Initiative, Deliverable, and Task gets a full description
- Deliverable descriptions must be self-contained — include all platform/system context
- Task descriptions must be concrete and actionable — one work session each
- Use the sub-skills (`/create-jira-initiative`, `/create-jira-deliverable`,
  `/create-jira-task`) — do not create issues directly
- Idea content is the source of truth for Initiatives and their breakdown
- The selected architecture determines which components and services need tickets
- The Infrastructure Setup Initiative MUST be first — the pipeline must be
  functional before feature work begins
- The "Local Development & CI Pipeline" Deliverable is the gate — when it passes
  through the full pipeline to Done, every Docker environment works, every test
  suite passes, and the project is ready for real feature development
