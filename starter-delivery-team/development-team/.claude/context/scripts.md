# Token-saving scripts

Read by: Team Lead only

Shell scripts in `infra/` handle mechanical pipeline operations without
using Claude tokens. **Use these instead of MCP calls or spawning agents
for mechanical work.**

## SETUP REQUIRED — customise scripts before first use

These scripts are copied from the starter template with `{PLACEHOLDER}`
values. The Team Lead MUST customise them during Stage 7 (pipeline setup)
or the first Infrastructure Setup deliverable:

### `infra/envctl`
- `SERVICE_REPOS` — list all service repo paths
- `WEB_PORT_CI` — base port for the first service (RC = +100, Prod-parity = +200)
- `INTEGRATION_TEST_CMD` / `E2E_TEST_CMD` / `SMOKE_TEST_CMD` — test runners for
  `envctl test` (default: Python suites in `tests/`; `BASE_URL` is exported)
- Needs Docker Compose >= 2.24.4 (`ports: !override` in docker-compose.test.yml)

### `infra/pipelinectl`
- `PROJECT_KEY` — Jira project key (e.g. `SENT`, `HIND`)
- `SERVICE_REPOS` — same list as envctl
- `T_BACKLOG`, `T_IN_DEV`, etc. — Jira transition IDs (`./jiractl transitions ISSUE-KEY`
  lists them live; query a Deliverable and a Task — their workflows differ)
- `{BUILD_COMMAND}` — production build run before merge to ci
- `LOCAL_GATE_CMDS` — `(auto)` derives lint/format/typecheck/build/test per repo
  from `package.json` scripts or `pyproject.toml`; override with `"label|command"` pairs

### `infra/jiractl` — CONFIGURE FIRST
- Requires `infra/.env.jira` with `JIRA_EMAIL` and `JIRA_API_TOKEN`
- Create token at: https://id.atlassian.com/manage-profile/security/api-tokens
- **This MUST be configured during project setup (Stage 8).** Without it,
  the pipeline cannot transition tickets, which is a hard gate for all
  team spawns. If both jiractl and MCP are unavailable, the pipeline stops.

### `infra/dashboard.py`
- `PROJECT_SLUG` — Docker Compose project name prefix
- `WEB_PORT_CI` — must match envctl
- `SERVICES` array in HTML — list your services and ports

**Do not skip this.** Uncustomised scripts will fail with placeholder
errors or operate on wrong repos/ports.

| Script | Purpose | Replaces |
|--------|---------|----------|
| `infra/jiractl` | Jira transitions, comments, polling, components | Atlassian MCP calls |
| `infra/pipelinectl` | CI gates, local tests, branch ops, RC cuts | Agent spawns for mechanical stages |
| `infra/envctl` | Docker environment management | Manual docker compose |

**Rule:** For every operation, check if `pipelinectl` or `jiractl` can do it
before using MCP or spawning an agent. Only use Claude tokens for reasoning
tasks (development, code review, analysis, impact assessment).

**Credentials:** Scripts require `infra/.env.jira` with `JIRA_EMAIL` and
`JIRA_API_TOKEN`. If this file does not exist, **fall back to Atlassian MCP**
for Jira operations — do not fail silently. Check for the file before
attempting to use `jiractl`:
```bash
test -f infra/.env.jira && ./infra/jiractl poll || echo "No .env.jira — use MCP"
```

## Branch operations via pipelinectl

| Action | Command |
|--------|---------|
| Merge feature PR into ci | `cd infra && ./pipelinectl merge-to-ci {PROJECT_KEY}-{key}` |
| Cut release-rc-{n} from ci | `cd infra && ./pipelinectl cut-rc {PROJECT_KEY}-{key}` (always from ci HEAD) |
| Merge RC into main + tag + back-merge | `cd infra && ./pipelinectl merge-rc {PROJECT_KEY}-{key} {N}` |

## Gates via pipelinectl

| Stage | Command | What it runs |
|-------|---------|--------------|
| In Local Test | `./pipelinectl local-gate {PROJECT_KEY}-{key}` | Every repo with the feature branch: `LOCAL_GATE_CMDS`. All gates run; any failure fails the stage |
| In Integration Test | `./pipelinectl ci-gate {PROJECT_KEY}-{key}` | Builds the rc (Test) stack from `ci` — CI services + fixture seeding — then `envctl test rc integration` |

## Docker environments via envctl

```bash
cd infra
./envctl up ci|rc|prod                # start from :env images (builds from the env's branch if missing)
./envctl rebuild ci|rc|prod           # rebuild :env images from the env's branch, no checkout
REBUILD_BRANCH=ci ./envctl rebuild rc # build an env from a different branch
./envctl rebuild-local ci             # build from the working tree (first Deliverable / debugging)
./envctl test rc integration          # boot, run suite against BASE_URL, tear down
./envctl down prod                    # keeps prod-parity volumes; add --wipe to delete them
```

## Jira operations via jiractl

```bash
cd infra
./jiractl poll                              # Find actionable tickets
./jiractl backlog                           # Show next Deliverable in Backlog
./jiractl transition {PROJECT_KEY}-{key} {id}       # Transition ticket
./jiractl comment {PROJECT_KEY}-{key} "message"     # Add comment (inline text)
./jiractl comment {PROJECT_KEY}-{key} report.md     # ...or a markdown file (headings, lists, code fences → ADF)
some-cmd | ./jiractl comment {PROJECT_KEY}-{key} -  # ...or stdin
./jiractl transitions {PROJECT_KEY}-{key}           # Valid transition IDs from this ticket's status (live)
./jiractl components {PROJECT_KEY}-{key} svc1 svc2  # Set components
./jiractl status {PROJECT_KEY}-{key}                # Show ticket info
```
