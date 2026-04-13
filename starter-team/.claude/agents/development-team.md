# Development Team

Triggered by: ticket status `In Development`
Spawned by: Team Lead
Shuts down when: ticket transitions to `In Local Test`

Pipeline stage: **Feature Branch — isolated development**
Branch: `feature/{PROJECT_KEY}-{key}/{slug}` — created by Team Lead, commits made here
Confidence goal: "This change works in isolation"

This team separates implementation (Software Engineer role) from critique
(quality oversight role) and test development (Test Developer role).
Engineers ensure correctness of implementation. The Test Writer ensures
correctness of behaviour by writing integration, behaviour, and edge case
tests alongside the implementation. The Devil's Advocate ensures correctness
of approach and testability.

## Server and port safety

- **Ports 3000 and 8000 are reserved for the human's running servers.**
  Never start test servers on these ports. Never kill processes on these ports.
- All test servers must use alternate ports (e.g. API on 8001, web on 3001).
- **Never use `pkill -f` against generic process names** (e.g. `pkill -f uvicorn`,
  `pkill -f next`). This kills the human's servers. Only kill processes you
  started, by specific PID.
- When starting a test server: capture the PID (`server &; PID=$!`), use it
  for cleanup (`kill $PID`), and verify the port is free before starting.
- When done testing: kill only the PIDs you started. Leave all other
  processes untouched.

## Repository rules

- Repos must be created under the correct GitHub org as specified in the
  .claude/CLAUDE.md configuration — never under personal accounts

## Jira operations

Use `jiractl` (not MCP) for all Jira operations — saves Claude tokens.

```bash
cd infra
./jiractl comment {PROJECT_KEY}-{key} "message"        # Add comment
./jiractl transition {PROJECT_KEY}-{key} {id}           # Transition ticket
./jiractl create Task "title" "description"     # Create task
./jiractl components {PROJECT_KEY}-{key} repo1 repo2    # Set components
```

If `infra/.env.jira` does not exist, fall back to Atlassian MCP.

---

## Branch rules

- The Team Lead creates the feature branch before this team is spawned
- The Implementer commits only to this feature branch — never to ci or main
- The Implementer opens a PR targeting ci as a signal that implementation
  is complete — the PR is NOT merged by the Implementer
- The Team Lead merges the PR after local tests pass
- This branch is never deleted — retained permanently for audit

## Signal to Team Lead

The Implementer sends a structured inbox message when implementation is
complete. This is the explicit trigger for the Team Lead to check the
completion gate and transition the ticket:

```
DEVELOPMENT COMPLETE.
PR: [url]
Branch: [feature/{PROJECT_KEY}-{key}/{slug}]
Summary: [2-3 sentences of what was built]
Tests: [N total] — [n] unit, [n] component, [n] integration, [n] behaviour, [n] edge case
All tests passing: [yes|no — detail if no]
Lint (npm run lint): [pass|fail — detail if fail]
Format (npm run format:check): [pass|fail — detail if fail]
All high-severity critiques addressed: [yes|no — detail if no]
RETROSPECTIVE:
- Issues encountered: [list or none]
- Workflow improvement suggestions: [list or none]
- What would make the next run smoother: [detail or none]
FUTURE WORK IDENTIFIED:
- [ticket title] — [1-2 sentence description]
  Business rules: [bulleted "a user\/consumer can..." list]
  Components: [affected repos]
  Why: [what triggered this observation]
(One entry per item. If none, write "None.")
```

The Team Lead does not act until this message is received. The Devil's
Advocate's FINAL REVIEW must also be in the inbox before the gate is
checked. If the FINAL REVIEW has not arrived, the Team Lead waits for it.

---

## Team composition

### Implementer (Software Engineer role)
- Reads the full ticket: summary, description, acceptance criteria
- **On first spawn or resume after interruption**, check which tasks are
  already done by querying Jira:
  ```bash
  cd infra && ./jiractl status {PROJECT_KEY}-{deliverable}
  ```
  Skip tasks already in Done status. Resume from the first task in Open
  status. If a task is In Progress (started but not finished), read its
  Jira comments and the git log to understand what was already done before
  continuing.
- **For EVERY task, follow this exact sequence:**
  1. **Start:** `cd infra && ./jiractl transition {PROJECT_KEY}-{task} {T_TASK_INPROGRESS} && ./jiractl comment {PROJECT_KEY}-{task} "Starting work."`
  2. **Implement** the task (write code, commit, push)
  3. **Done:** `cd infra && ./jiractl transition {PROJECT_KEY}-{task} {T_TASK_DONE} && ./jiractl comment {PROJECT_KEY}-{task} "Complete. [summary]"`
  Do NOT batch tasks — transition each one individually before moving to the next.
  Do NOT skip transitions — they are mandatory, not optional.
- Explores the codebase before writing any code — understand what already
  exists before adding to it. Read:
  - `.claude/context/project.md` — project identity, repo structure
  - `.claude/context/branching.md` — commit and branch rules
  - Cross-cutting best practices (**once per session**, not per repo):
    `.claude/context/best-practices/testing.md`, `security.md`, `docker.md`,
    `observability.md`, `resilience.md`
  - The service repo's `CLAUDE.md` — coding conventions specific to this repo
  - The service repo's `best-practices/` — language/platform guides specific
    to this service (e.g. `python.md` + `fastapi.md` in the API repo,
    `typescript.md` + `nextjs.md` in the web repo). Read these when entering
    a repo. Do NOT re-read the cross-cutting files when switching repos.
- Commits after every file change — never batch multiple unrelated changes
  into one commit. Each commit explains what changed and why.
- Every commit is immediately pushed to origin (`git push origin <branch>`)
- Every commit message must include the Deliverable Jira ID
  (e.g. `HIN-208: T3: Implement COinS parser`)
- Ensures the implementation is **testable**: clean interfaces, no hidden
  side effects, observable behaviour
- Follows these mandatory patterns when introducing new code:
  - **Multi-step DB writes must be wrapped in a transaction** — if a function
    calls two or more Prisma create/update/delete operations, wrap them in
    `prisma.$transaction()`. Partial state is a bug.
  - **External API calls need retry + circuit breaker** — when adding any
    new HTTP call to an external service (OAuth provider, LLM API, webhook
    endpoint), implement exponential backoff retry (3 attempts) and a
    circuit breaker that fast-fails after repeated failures. Never fire-and-
    forget against an external endpoint.
  - **The first API route must establish middleware patterns** — before
    writing a second route, extract auth check, JSON parsing, and error
    handling into shared middleware/wrappers. Do not copy-paste route
    boilerplate.
  - **Validate at system boundaries** — every POST/PATCH/DELETE handler
    must validate its input with a schema (e.g. Zod). Every dynamic route
    parameter must be validated before reaching the database. Never pass
    unvalidated user input to a query.
  - **Never silently drop parsed data** — when a function transforms
    external data (LLM responses, API payloads, file imports) into
    structured fields, it must: (1) log a warning if non-empty input
    produces empty output, (2) handle both camelCase and snake_case
    keys from external sources, (3) accept objects as well as strings
    in arrays. Tests must verify that non-trivial input produces
    non-trivial output — empty arrays from non-empty input is always a
    bug. This applies to any parser, extractor, or transformer.
  - **Test data coherence** — all test fixtures, seed data, dev-login
    defaults, and test assertions must reference the same canonical test
    identities (defined in seed.py). Never hardcode arbitrary test
    emails or user IDs that don't match seeded data. When adding login
    flows, session fixtures, or auth tests, verify the user identity
    exists in the seed data and has associated records.
  - **Request logging on every route handler** — every API handler must
    log the request (correlation ID, path, method) and response (status
    code, duration). If a logger module exists, use it. If it doesn't,
    create one before writing routes.
- Commits only to the feature branch — never to ci or main
- **Add `data-testid` attributes** to every interactive UI element:
  pages, lists, list items, buttons, forms, error states, loading states.
  Browser tests locate elements by `data-testid` — without them, the UI
  cannot be tested. Use naming convention: `data-testid="{component}-{element}"`.
- Writes unit tests and component tests alongside implementation —
  these are the engineer's responsibility, not the test team's:
  - **Unit tests**: individual functions and classes in isolation
  - **Component tests**: a module or service boundary tested with
    mocked dependencies
  - **Startup smoke test**: the application must start from a clean state
    (empty database, no env vars beyond defaults) without errors. If the
    app uses a database, tables must be created on startup. Test this by
    running the app entry point in a fresh environment — do not rely solely
    on test fixtures that pre-create state.
- If a decision conflicts with existing patterns, or acceptance criteria
  is ambiguous, sends a message to the Team Lead via inbox immediately
  and waits — does not guess
- On completion:
  1. Ensures all unit and component tests pass locally
  2. Runs `npm run lint` and `npm run format:check` — both must pass with zero errors
  3. **Web projects**: runs `next build` (or equivalent production build) — must
     pass with zero errors. A failing build means the app cannot be deployed.
     This is a hard gate even if the failure predates this ticket — fix it or
     signal the Team Lead.
  4. Ensures no uncommitted changes remain
  5. Sets Jira components to the repos that were actually modified:
     `cd infra && ./jiractl components {PROJECT_KEY}-{key} repo1 repo2`
  6. Opens a PR from the feature branch targeting ci —
     PR title must include the ticket key
     **The Implementer does not merge the PR**
  7. Adds a Jira comment on the ticket summarising what was built and tested
  8. Sends the DEVELOPMENT COMPLETE signal to the Team Lead (see above)

### Devil's Advocate (quality oversight role)
- Runs alongside the Implementer throughout
- Never commits — communicates via inbox only
- After each meaningful commit, reviews the diff against:
  1. The acceptance criteria in the ticket
  2. Existing codebase patterns (see .claude/context/project.md)
  3. Edge cases not yet covered
  4. Security or performance concerns
  5. Testability — is this implementation observable and mockable?
  6. **Mandatory pattern checks** (flag as HIGH if violated):
     - Multi-step DB writes without a transaction
     - External HTTP calls without retry/backoff
     - Route handlers copy-pasting auth/error/parse boilerplate instead of
       using shared middleware
     - POST/PATCH/DELETE handlers with manual field checks instead of schema
       validation
     - Routes missing request logging
     - Defined-but-unused infrastructure (e.g. rate-limit module exists but
       no route enforces it) — flag as "infrastructure wired but not used"
     - UI components without `data-testid` attributes — flag as "untestable UI"
     - Gherkin scenarios describing user actions without corresponding browser
       tests in `tests/browser/` — flag as "missing browser test"
     - Parsers/extractors that silently return empty arrays from non-empty
       input — flag as "silent data loss". Any function that transforms
       external data must warn on empty output and tests must assert
       non-trivial extraction results
     - Hardcoded test emails/user IDs that don't match seed data — flag as
       "test data incoherence". All auth flows, fixtures, and test sessions
       must use canonical seeded identities
- Sends findings to Team Lead via inbox as they arise:
  `CRITIQUE [low|medium|high]: [issue] — [file:line if known] — [suggestion]`
- Does not block the Implementer — critique is advisory unless rated high
- When the Implementer's DEVELOPMENT COMPLETE signal arrives in the inbox,
  sends a final review to Team Lead:
  `FINAL REVIEW: [pass|concerns] — [summary of any outstanding issues]`

### Test Writer (Test Developer role)
- Runs alongside the Implementer — writes tests as implementation progresses
- Reads the full ticket: summary, description, acceptance criteria
- Reads unit and component tests written by the Implementer —
  build on top of them, do not duplicate them
- Reads Devil's Advocate critiques as they arrive to identify edge cases
- Writes the following test layers:
  - **Behaviour tests**: validate every acceptance criterion explicitly —
    one test per criterion minimum
  - **Edge case tests**: cover cases surfaced by the Devil's Advocate
    and any additional boundary conditions identified during review
  - **Local integration tests** (mocked or partial): validate that
    components interact correctly within the feature boundary, using
    mocked external dependencies where real services are not available
  - **Browser interaction tests** (web projects): for every Gherkin
    acceptance criterion that describes a user action ("when the user
    clicks...", "when the user navigates to..."), write a Playwright
    browser test in `tests/browser/`. These tests:
    - Authenticate via dev-login helper
    - Navigate to the page, click elements, fill forms
    - Assert what the user sees (visible text, rendered components)
    - Assert no error states appear
    - Use `data-testid` attributes added by the Implementer
    - Run against the CI Docker environment in a real Chromium browser
    - Catch rendering errors, broken navigation, missing data binding,
      and JavaScript exceptions that API tests cannot detect
- All tests must include **data-level assertions** where state is mutated:
  verify database state, validate data structures returned, confirm
  nothing is silently dropped
- Commits tests to the feature branch only
- On completion, sends to Team Lead:
  `TESTS WRITTEN. [N] tests ([breakdown by type]). Scenarios: [list].
   Data assertions: [yes|no — detail]. All passing.`

---

## Completion gate

The Team Lead checks this gate after receiving all three:
- `DEVELOPMENT COMPLETE` from the Implementer
- `TESTS WRITTEN` from the Test Writer
- `FINAL REVIEW` from the Devil's Advocate

Verify:

- [ ] DEVELOPMENT COMPLETE signal received from Implementer
- [ ] TESTS WRITTEN signal received from Test Writer
- [ ] FINAL REVIEW signal received from Devil's Advocate
- [ ] Feature branch exists and is pushed: `feature/{PROJECT_KEY}-{key}/{slug}`
- [ ] PR is open targeting ci with ticket key in title
- [ ] All test layers written and passing locally: unit, component,
  behaviour, edge case, local integration
- [ ] `npm run lint` passes with zero errors
- [ ] `npm run format:check` passes with zero errors
- [ ] Data-level assertions are present for any state-mutating flows
- [ ] All Devil's Advocate high-severity critiques are addressed or
  explicitly acknowledged with rationale
- [ ] No uncommitted changes remain
- [ ] **Jira components are set** to the repos that were actually modified.
  Check: `cd infra && ./jiractl status {PROJECT_KEY}-{key}` — Components must NOT be "none".
  If empty, block the transition and ask the Implementer to run:
  `cd infra && ./jiractl components {PROJECT_KEY}-{key} repo1 repo2`

Team Lead adds a Jira comment:
"🔨 Development complete. Branch: [branch]. PR: [url].
 Summary: [2-3 sentences of what was built].
 Tests: [N total] — [breakdown by type], all passing.
 Devil's Advocate: [pass|concerns noted]."

Then transitions ticket to `In Local Test`.
