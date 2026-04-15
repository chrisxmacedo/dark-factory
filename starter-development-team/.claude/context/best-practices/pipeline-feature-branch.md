# Pipeline best practices — Feature branch

Read by: Development Team, Local Test Team

Covers: In Development → Ready for Local Test → In Local Test → merge to ci

## Branch

- Branch name: `feature/{PROJECT_KEY}-{key}/{slug}` — created by Team Lead from ci
- Only the Development Team and Local Test Fix Agent commit here
- Never commit to ci or main from a feature branch

## Commits

- Commit after every file change — never batch unrelated changes
- Every commit message includes the Deliverable Jira ID: `{PROJECT_KEY}-42: T3: description`
- Push immediately after every commit: `git push origin <branch>`
- No squashing — full commit history preserved for audit

## Pull requests

- Implementer opens a PR targeting ci as a signal — does NOT merge
- PR title must include the ticket key
- The Team Lead merges after local tests pass — never the Implementer

## Code patterns (mandatory)

Before writing code, read the relevant best practices:
- `best-practices/typescript.md` or `best-practices/python.md`
- `best-practices/nextjs.md` or `best-practices/fastapi.md` (framework-specific)
- `best-practices/security.md`
- `best-practices/observability.md`
- `best-practices/resilience.md` (if calling external services)

Mandatory patterns — Devil's Advocate flags as HIGH if violated:
- Multi-step DB writes wrapped in a transaction
- External API calls with retry + circuit breaker
- Auth/error/parse middleware extracted before second route (no copy-paste)
- Schema validation on every POST/PATCH/DELETE handler
- Request logging on every route handler
- No defined-but-unused infrastructure

## Test gates (7 gates)

Run by `pipelinectl local-gate` (scripted, no Claude tokens).
All must pass before merge to ci.

| # | Gate | Who writes it | Tool | Fails → |
|---|------|--------------|------|---------|
| 1 | Unit tests — individual functions/classes | Engineer | `npm test` / `pytest` | Return to In Development |
| 2 | Component tests — module boundary with mocks | Engineer | `npm test` / `pytest` | Return to In Development |
| 3 | Behaviour tests — one per Gherkin acceptance criterion | Test Writer | `npm test` / `pytest` | Return to In Development |
| 4 | Edge case tests — boundary conditions from Devil's Advocate | Test Writer | `npm test` / `pytest` | Return to In Development |
| 5 | Build verification — code compiles into deployable artifact | Scripted | `next build` / `tsc` / `mypy` | Return to In Development |
| 6 | Lint — zero errors | Scripted | `eslint` / `ruff check` | Return to In Development |
| 7 | Format — zero errors | Scripted | `prettier --check` / `ruff format` | Return to In Development |

All state-mutating tests must include **data-level assertions** (verify DB state, not just response).

Fix Agent (Claude) gets 2 attempts if gates fail. If still failing → return to In Development.

## Merge to ci

- `pipelinectl merge-to-ci {KEY}-{key}` handles: build gate → rebase onto ci → merge --no-ff → push
- After merge: `envctl rebuild ci && envctl test ci` (mandatory, hook-enforced)
- The CI Docker environment must always reflect the latest ci branch

## Defects found on the feature branch

- Return the Deliverable to In Development (transition 51)
- Add Jira comment: "❌ [test/stage] failed. [what failed]."
- Fix on the same feature branch — do NOT create a separate Issue ticket
- Re-enter Local Test when fixed

NEVER:
- Merge to ci with failing tests
- Merge to ci with a failing build
- Commit directly to ci — only merge via PR
- Delete the feature branch after merge — kept for audit

