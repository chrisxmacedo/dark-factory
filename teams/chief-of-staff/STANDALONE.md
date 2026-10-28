# Technical chief of staff

This directory is a Claude Code project for the CTO's operating rhythm. It does not include an engineering delivery team. Counts come from scripts. Narrative comes from Claude. GitHub, Jira, and Linear are reached with the credentials in your environment.

## Deploy Chief of Staff standalone at work

You are already in the exported directory. If you are still in the toolkit, create this directory first:

```bash
./harness/export-chief-of-staff.sh ~/work/cto-office
cd ~/work/cto-office
```

### 1. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude
```

Log in once. Leave that first session with `/exit` if it opens.

### 2. Configure the office, not the tokens

```bash
cp config/ara.env.example config/ara.env
cp config/positions.example.md config/positions.md
cp config/holidays.example.txt config/holidays.txt
```

Edit `config/ara.env`: timezone, the spend caps your organisation actually approved, `BOARD_DATES`, and the tracker ids (`GITHUB_REPOS`, `JIRA_SITE`, `JIRA_EMAIL`, `JIRA_PROJECTS`, `LINEAR_TEAM_IDS`). `JIRA_SITE` is the hostname only, with no scheme.

Edit `config/positions.md` so it contains only positions the CTO has already agreed. Until you do, the agent drafts and does not decide.

Edit `config/holidays.txt` with your office's non-working dates, one ISO date per line.

Do not put tokens in those files.

### 3. Export tokens into the environment

Set whichever systems you use. At least one of GitHub, Jira, or Linear must be set or the delivery pull stops.

| Variable | Used for |
|---|---|
| `GITHUB_TOKEN` | GitHub REST pulls and the GitHub MCP server. A fine-grained token that can read pull requests, actions, and deployments, and can create issues if you want chases filed there. |
| `GITHUB_REPOS` | Comma-separated `owner/name` list. Already in `ara.env`. |
| `JIRA_API_TOKEN` | Jira Cloud REST. Create it in your Atlassian account security settings. |
| `JIRA_SITE`, `JIRA_EMAIL`, `JIRA_PROJECTS` | Hostname, login email, project keys. In `ara.env`. |
| `LINEAR_API_KEY` | Linear GraphQL and the Linear MCP server. |
| `LINEAR_TEAM_IDS` | Optional comma-separated team ids. In `ara.env`. |
| `ANTHROPIC_API_KEY` | Only if `claude` is not already logged in with a subscription. |

Optional URL overrides, if your organisation hosts its own MCP endpoints: `GITHUB_MCP_URL`, `ATLASSIAN_MCP_URL`, `LINEAR_MCP_URL`.

### 4. Check the wiring without calling a model

```bash
python3 scripts/working_days.py --date 2026-10-07
python3 scripts/run_due.py --list --at 2026-10-02T17:00:00
./scripts/claude-headless.sh --dry-run --agent weekly-delivery --prompt-file schedules/prompts/weekly-delivery.md
./scripts/install-schedule.sh --print
python3 -m unittest discover -s tests -v
```

`--list` prints which deadlines are open at that moment. `--dry-run` prints the `claude -p` command and does not start it.

### 5. Open the coordinator

```bash
claude
```

Claude reads `CLAUDE.md` and is the chief of staff. The first session asks you to approve the MCP servers in `.mcp.json` unless settings already enable project MCP servers (the exported settings do, so a scheduled run is not left waiting). Read `.mcp.json` before you rely on that.

### 6. Schedule the deadlines

```bash
./scripts/install-schedule.sh --install
```

This writes a marked block into your user crontab. Each line runs `scripts/run-due.sh --job <id>`, which runs the data scripts first and starts Claude only when that deadline is actually open. The timezone is `OFFICE_TZ`.

Run one job by hand:

```bash
./scripts/run-due.sh --job weekly-delivery
```

Model spend for that run is capped by `CLAUDE_MAX_BUDGET_USD` (default 2). That ceiling is not the office tooling cap.

### 7. Drops from other people

| Drop | Path |
|---|---|
| Meeting note | `inbox/meetings/<name>.md` with an `ended_at:` line |
| Finance actuals | `inbox/finance/actuals.csv` |
| Initiative the CTO assigned | `inbox/initiatives/<id>/meta.json` |
| Director commitments | `inbox/plans/` |

Reports land in `outputs/`. Anything outside the role lands in `drafts/` and is not sent.

## What this role will not do

It will not change product code, merge or review pull requests, transition or reprioritise engineering tickets, approve spend over the configured caps, or take a position that is not in `config/positions.md`. The hook in `.claude/settings.json` blocks the tool calls. The scripts block invented metrics.
