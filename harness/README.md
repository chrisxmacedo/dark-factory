# Harness

Shared Claude Code runtime for this toolkit. Agent teams sit on top of it and can be enabled one at a time.

| Piece | Where it lives | What a checkout uses it for |
|---|---|---|
| Permissions and hooks | `claude/settings.json` | What the agent may run, and the authority hook |
| Authority hook | `scripts/guard_authority.py` | Blocks code changes, pull-request edits, and tracker reprioritisation |
| MCP servers | `mcp/mcp.json` | GitHub, Jira, and Linear. Tokens stay in the environment |
| Headless runs | `scripts/claude-headless.sh` | `claude -p` for a deadline, with a spend ceiling |
| Schedules | `scripts/install-schedule.sh` | Cron lines that call a team's `run-due.sh` |
| Escalation | `escalation.md` and `skills/human-escalation/` | What must be drafted for a person |
| Office config loader | `scripts/office_env.py` | Reads `config/ara.env` without shell execution |

`export-chief-of-staff.sh` copies this core and `teams/chief-of-staff` into an empty directory. It does not copy the delivery team.

The delivery team keeps its own Claude Code project shape: a lead prompt, specialist prompts, and the pipeline scripts that already ship with that template. It is not rewritten to import this harness, because those files are what an existing product install expects. New teams use this harness instead of growing a second copy of the same runtime rules.
