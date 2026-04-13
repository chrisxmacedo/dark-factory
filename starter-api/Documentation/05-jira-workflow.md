# Jira Workflow

## Overview

Jira is the system of record for the entire pipeline. It holds the
authoritative state of every ticket across all sessions, all agent teams,
and all pipeline stages. Everything the agent teams do is reflected in
Jira — status transitions, comments, labels — so that the pipeline state
is always visible and auditable.

---

## Status design

The workflow uses a strict naming convention:

**"Ready for X"** — the ticket is waiting to be picked up for stage X.
The agent team for stage X has not yet started.

**"In X"** — the agent team for stage X is actively working the ticket.

This alternating pattern serves two purposes:

1. **Double-claim prevention**: the Team Lead transitions from "Ready for…"
   to "In…" immediately on claiming, before spawning any agents. If two
   sessions were running simultaneously, the second would see "In…" and skip.

2. **Human visibility**: at any point, a human can see exactly which tickets
   are waiting vs. actively being worked. A ticket stuck in "In…" with no
   recent Jira comments is a signal that something may have gone wrong.

---

## Full status list

### Feature Branch track

| Status | Type | Set by |
|--------|------|--------|
| Backlog | Queued | Human |
| Ready for Dev | Queued | Human (intentional gate) |
| In Development | Active | Team Lead (development-team spawned) |
| Ready for Local Test | Queued | development-team on completion |
| In Local Test | Active | Team Lead (local-test-team spawned) |

### CI track

| Status | Type | Set by |
|--------|------|--------|
| Ready for Integration Test | Queued | local-test-team on completion |
| In Integration Test | Active | Team Lead (integration-test-team spawned) |
| Ready for E2E Impact Test | Queued | integration-test-team on completion |
| In E2E Impact Test | Active | Team Lead (e2e-impact-team spawned) |

### Release Candidate track

| Status | Type | Set by |
|--------|------|--------|
| Ready for Full E2E Regression | Queued | e2e-impact-team on completion |
| In Full E2E Regression | Active | Team Lead (regression-team spawned) |

### Main track

| Status | Type | Set by |
|--------|------|--------|
| Release / Production | Final | release-team on completion |

---

## Jira setup instructions

### Step 1: Create the workflow statuses

Go to: **Jira → Project Settings → Workflows → Edit**

Add the following statuses:

**Feature Branch track:**
- Ready for Dev
- In Development
- Ready for Local Test
- In Local Test

**CI track:**
- Ready for Integration Test
- In Integration Test
- Ready for E2E Impact Test
- In E2E Impact Test

**Release Candidate track:**
- Ready for Full E2E Regression
- In Full E2E Regression

**Main track:**
- Release / Production

### Step 2: Configure transitions

Create transitions between statuses following the pipeline flow. The
minimum required set is the forward path (each stage to the next). Also
configure backward transitions for failure paths (e.g. In Local Test →
Ready for Dev) and a global Backlog transition for resetting stalled tickets.

### Step 3: Get real transition IDs

After creating the workflow, fetch transition IDs in a Claude session:

```
Call getTransitionsForJiraIssue with:
  cloudId: {CLOUD_ID}
  issueIdOrKey: {PROJECT_KEY}-[any ticket]
```

### Step 4: Update PIPELINE.md

Replace all TBC values in the transition table in `PIPELINE.md` with
the real IDs returned in Step 3.

---

## Jira comments as the audit trail

Every significant action is recorded as a Jira comment, providing a
persistent audit trail across sessions:

| Event | Comment format |
|-------|----------------|
| Team claims ticket | "🤖 Team Lead: Claimed by [team]. Starting." |
| Development complete | "🔨 Development complete. Branch: [...]. PR: [...]." |
| Local tests passed | "✅ Local tests passed. [N] tests. Branch merged." |
| Integration passed | "✅ Integration tests passed. CI green." |
| E2E impact passed | "✅ E2E impact tests passed. Promoted to RC." |
| Regression passed | "✅ Full E2E regression complete. Awaiting approval." |
| Released | "🚀 Released to production. [timestamp]. Stable." |
| Failure | "❌ [Stage] failed. [Detail]. Needs human review." |

A human can read the comment history of any ticket and reconstruct
exactly what happened at each stage without being present during any
agent session.

---

## Human gates in detail

### Gate 1: Ready for Dev

**Who sets it:** The human, manually in Jira.
**What it means:** The ticket has been refined — acceptance criteria are
clear, scope is defined, dependencies are resolved. Ready for an agent
team to implement without further clarification.

**Why this is a human gate:** Refinement requires product and engineering
judgement: priority relative to other tickets, confidence that acceptance
criteria are unambiguous, awareness of technical dependencies not visible
in the ticket itself. No agent team can make these assessments.

**The implicit contract:** By moving a ticket to Ready for Dev, you are
asserting that the acceptance criteria are complete enough for an agent
to implement without asking questions. If criteria are unclear, the
Implementer will send a blocker to the Team Lead, who will transition
the ticket back to Backlog with a `needs-human` label explaining what
is missing.

### Gate 2: Approve promote to Main

**Who triggers it:** The Team Lead, after Full E2E Regression passes.
**What it means:** All automated validation has passed. The human needs
to decide whether to deploy to production.

**Why this is a human gate:** Deploying to production is a business
decision, not a technical one. Even if all tests pass, there may be
reasons not to deploy: a scheduled maintenance window, a pending
marketing launch, a dependency on another release, or simply wanting to
be available to monitor it. No automated system can make this call.

**How to approve:** Reply to the Team Lead with
"Approve promote {PROJECT_KEY}-[key]". The Team Lead will spawn the
release-team and proceed.

**What to review:** The Regression Analyst's release readiness report in
the Jira comment covers:
- Environment parity gaps
- Database migration sequencing requirements
- Feature flags that need toggling
- Third-party integrations to verify manually
- The rollback plan if something goes wrong

---

## Handling stalled tickets

A ticket in an "In…" status with no active agent team is stalled. This
can happen if a session ends mid-work or if a team shuts down without
transitioning properly.

To detect stalled tickets:

```
JQL: project = {PROJECT_KEY} AND status in (
  "In Development", "In Local Test", "In Integration Test",
  "In E2E Impact Test", "In Full E2E Regression"
) AND updated < -2h
```

To resolve: transition the ticket back to the previous "Ready for…"
status manually in Jira. On the next session, the Team Lead picks it
up and restarts the relevant team from that stage.
