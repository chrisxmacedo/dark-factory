# Refinement Team

Triggered by: ticket status `In Refinement`
Spawned by: Team Lead
Shuts down when: ticket transitions to `In Development`
                 OR back to `Backlog` if the Deliverable lacks sufficient detail

Pipeline stage: **Pre-development — solution design and task breakdown**
Branch: None — this is analysis only, no code is written
Confidence goal: "The implementation approach is sound and the tasks are concrete"

At this stage the Deliverable has been moved to In Refinement by the human. The Refinement Team analyses the ticket, the target architecture,
and the current repository structure to produce a concrete task breakdown
that the Development Team will follow.

No code is written. No branches are created. The output is Jira Tasks.

## What this team reads

- The Deliverable ticket (summary, business rules, Gherkin AC, data model,
  API surface, components, dependencies)
- `CLAUDE.md` at the workspace root — project architecture (service graph, providers, auth flow, inter-service communication)
- `ARCHITECTURE.md` if it exists — detailed architecture specification
- `REPO_MAP.md` in each affected service repo — current structure, modules,
  patterns in use
- `context/best-practices/` — relevant technology and pipeline best practices
- `context/decomposition.md` — journey-first decomposition rules

## Branch rules

- No branches are created
- No code is committed
- All output is via Jira (Tasks + comments)

---

## Team composition

### Solution Designer
- Reads the full Deliverable: business rules, acceptance criteria, data model
  changes, API surface, dependencies
- Reads ARCHITECTURE.md to understand where this feature fits
- Reads REPO_MAP.md for each affected repo to understand current structure
- Proposes an **implementation approach**:
  - Which service repos are affected
  - Which existing modules/files will be modified
  - Which new modules/files will be created
  - Which patterns from best-practices apply
  - How data flows through the system for this feature
  - Integration points with other services
- Sends to Team Lead:
  `SOLUTION DESIGN: [approach summary]
   Repos: [list]
   Modified: [file list]
   Created: [file list]
   Patterns: [list from best-practices]
   Data flow: [description]
   Integration points: [list]`

### Task Planner
- Receives the Solution Design
- Breaks the approach into concrete **Jira Tasks** under the Deliverable
- Each Task must specify:
  - **Title**: one concrete action (e.g. "Add thread search API route")
  - **Files to create/modify**: specific paths (e.g. `src/app/api/threads/search/route.ts`)
  - **Pattern to follow**: reference to best-practice or existing similar code
  - **Acceptance criteria**: what "done" looks like for this task — MUST include
    observability: structured logs at key decision points, domain-specific
    Prometheus metrics where relevant, correlation ID propagation on cross-service calls
  - **Dependencies**: which other tasks in this Deliverable must complete first
  - **Complexity**: S (< 1 hour), M (1-4 hours), L (4+ hours)
- Tasks should be ordered by dependency — the Development Team works through
  them in sequence
- **Do NOT create Tasks for environment validation** (e.g. "Verify in CI",
  "Test in all 3 environments"). The pipeline stages handle this automatically:
  Integration Test → CI, E2E Impact → RC, Regression → RC on release-rc,
  Release → Prod-parity. Only create Tasks for code changes and local verification.
- Creates the Tasks as children of the Deliverable:
  `jiractl create Task "title" "description" "components" TREEM-{key}`
  The last argument is the parent Deliverable key — Tasks MUST be children.
- Sends to Team Lead:
  `TASKS CREATED: [N] tasks under {KEY}-{key}
   Task list: [numbered list with complexity]
   Critical path: [which tasks are sequential vs parallel]
   Total estimated complexity: [S/M/L counts]`

### Risk Assessor
- Runs in parallel with Task Planner
- Reviews the Solution Design for:
  - **Architectural violations**: does the approach break any pattern in
    ARCHITECTURE.md or best-practices?
  - **Existing code conflicts**: will the proposed changes break existing
    functionality? Check REPO_MAP.md for affected modules.
  - **Missing dependencies**: does this Deliverable depend on work that
    isn't done yet? Check the Dependencies section.
  - **Schema migration risks**: are data model changes backward-compatible?
    Will they require data backfill?
  - **Security concerns**: new endpoints, new user input paths, new external
    service calls — flag anything that needs security review
  - **Test coverage gaps**: are there user journeys that this feature affects
    but has no test for?
- Sends findings to Team Lead:
  `RISK ASSESSMENT: [clean|concerns]
   Architectural: [ok|violations found]
   Existing code: [ok|conflicts identified]
   Dependencies: [ok|missing prerequisites]
   Migration: [ok|risks identified]
   Security: [ok|concerns flagged]
   Test gaps: [ok|gaps identified]`

---

## Completion gate

Before transitioning to `In Development`, verify:

- [ ] Solution Design received and reviewed
- [ ] All Tasks created in Jira with file paths, patterns, and acceptance criteria
- [ ] Tasks are ordered by dependency
- [ ] Risk Assessment received with no blocking concerns
- [ ] Any blocking risks have been resolved or escalated to human
- [ ] The Deliverable description is updated with the implementation approach
  (add a "Solution Design" section to the ticket)

Team Lead adds a Jira comment:
"✅ Refinement complete. [N] Tasks created. Solution design: [summary].
 Risks: [clean|noted]. Ready for Development."

Each team member includes a retrospective and future work in their signal:
```
RETROSPECTIVE:
- Issues encountered: [list or none]
- Workflow improvement suggestions: [list or none]
- What would make the next run smoother: [detail or none]
FUTURE WORK IDENTIFIED:
- [ticket title] — [1-2 sentence description]
  Business rules: [bulleted "a user/consumer can..." list]
  Components: [affected repos]
  Why: [what triggered this observation]
(One entry per item. If none, write "None.")
```

Then transitions ticket to `In Development` (51).

## On insufficient detail

If the Deliverable lacks enough detail for the team to produce a solution
design (missing business rules, vague acceptance criteria, no data model):

- Add a Jira comment listing exactly what's missing
- Transition back to Backlog
- The human must add the missing detail before re-promoting

## On blocking risks

If the Risk Assessor identifies a blocking concern:

- Add a Jira comment with the specific risk and recommendation
- The Team Lead decides whether to proceed (transition to In Development),
  modify the approach, or transition back to Backlog for re-scoping
- Do NOT stop the pipeline to wait for human input — the Team Lead handles this
