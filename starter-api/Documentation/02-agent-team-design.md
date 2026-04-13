# Agent Team Design

## What Claude Code agent teams are

Claude Code's agent team feature allows a session to spawn multiple
sub-agents that collaborate through two shared primitives:

1. **A shared task list** — a JSON file maintained in `~/.claude/teams/`
   that agents can read, claim tasks from, and mark complete. Tasks can
   have dependencies and blockers, so that later tasks do not start until
   earlier ones are resolved.

2. **An inbox system** — each agent has a message inbox. Agents can send
   findings, critiques, and status updates to each other and to the team
   lead in real time during a session.

These two primitives together enable genuine parallel collaboration —
agents can work on different parts of a problem simultaneously while
staying coordinated through the inbox.

---

## The three agent spawning patterns

Claude Code supports three distinct ways to use sub-agents:

### Pattern 1: One-shot task sub-agent
A single agent is spawned to do a focused, short-lived task and return
the result directly to the main agent. No shared task list. Used for
simple delegation.

### Pattern 2: Persistent teammate team
A team lead spawns multiple teammates from a shared task list. Teammates
persist between tasks within a session, can message each other, and report
back to the team lead. The team lead itself is long-lived and can be resumed.

### Pattern 3: Sequential single agents
No team structure. Single agents each handle one status, work independently,
and shut down when done.

---

## Why Pattern 2 was chosen for this pipeline

**Each stage has a different skill and risk profile**

Implementation requires creativity, exploration, and iteration. Testing
requires rigour and scepticism. Deployment requires caution and
conservatism above everything else. These capabilities are better served
by teams configured differently rather than a single monolithic team
trying to change its character mid-session.

**Jira is the reliable handoff mechanism**

By having each team read from Jira cold — fetching the ticket, the PR,
and any comments from the previous team — the system avoids depending on
in-memory state from a previous session. Each team must ground itself in
the artefacts: what was built, what the tests found, what the analyst
assessed. This forces explicit documentation of decisions at each stage
via Jira comments, making the pipeline state auditable across sessions.

**Parallel agents within a stage provide real-time quality control**

Within each team, specialist agents work in parallel. In the Development
Team, the Devil's Advocate reviews commits as they are made — not after
the implementation is complete. In the Integration Team, the Observability
Checker runs in parallel with the CI Monitor and Integration Analyst, so
all three dimensions of validation proceed simultaneously.

This is meaningfully different from a serial approach. The inbox system
allows a team to converge on a result from multiple angles at once.

**Teams are long-lived within a session**

The Team Lead does not shut down between tickets. This means:
- The developer can start a session, move tickets to Ready for Dev, and
  the Team Lead will work them through progressively without intervention
- The developer can message the Team Lead at any point for a status report,
  to skip a ticket, or adjust priority
- Tickets in different stages can be worked in parallel

---

## How the internal task list relates to Jira

This is the most important architectural distinction:

**Claude Code's internal task list is not Jira.** It is a short-lived
coordination mechanism local to a session. It allows a team lead to
decompose a ticket into sub-tasks that teammates claim and work.

**Jira is the system of record** for pipeline state. It tracks which
stage each ticket is at across sessions, what decisions were made via
comments, and what the human has approved.

```
Jira (persistent, cross-session)
  PROJ-12: In Development
    ↓
Team Lead reads PROJ-12, creates internal task list:
  [Task A] Explore codebase — claimed by Implementer
  [Task B] Review implementation — claimed by Devil's Advocate
    ↓
When both complete, Team Lead updates Jira:
  PROJ-12: Ready for Local Test
  Comment: "🔨 Development complete. Branch: ..."
```

The internal task list lives only for the duration of the team's work on
that ticket. The Jira transition and comment are the permanent record.

This design is resilient to session interruptions. If a session ends
mid-ticket, the ticket remains in its "In…" status in Jira. On the next
session, the Team Lead sees it and can restart the team from that stage.

---

## How to start a session

```bash
cd /path/to/your-project
claude
```

Claude reads `PIPELINE.md` and becomes the Team Lead. It polls Jira
immediately on startup and begins working any tickets in a "Ready for…"
status. The session persists until you close it.

Interact with the Team Lead conversationally at any point:
- "What are you working on?"
- "Skip PROJ-12 for now"
- "Prioritise PROJ-15"
- "Approve promote PROJ-10"

---

## File structure reference

```
project-root/
├── PIPELINE.md                      ← Team Lead (configure per project)
├── CLAUDE.md                        ← Coding conventions (existing)
└── .claude/
    ├── agents/
    │   ├── development-team.md      ← Spawned for: In Development
    │   ├── local-test-team.md       ← Spawned for: In Local Test
    │   ├── integration-test-team.md ← Spawned for: In Integration Test
    │   ├── e2e-impact-team.md       ← Spawned for: In E2E Impact Test
    │   ├── regression-team.md       ← Spawned for: In Full E2E Regression
    │   └── release-team.md          ← Spawned for: Release / Production
    ├── commands/                    ← Slash command overrides (existing)
    └── settings.local.json          ← Permissions (existing)
```

Each agent file defines the team members, their individual responsibilities,
the completion gate (what evidence must exist before transitioning), and
the failure path (how to handle unresolvable blockers).
