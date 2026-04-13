# Workflow Improvements — All Projects (Chronological)

Master log of pipeline improvements, agent team retrospectives, and process
changes across all projects. Entries are chronological and queryable by date,
project, team, and category.

**Format:** `## YYYY-MM-DD — [PROJECT] Summary` with tags for searchability.

**Projects:** HIN (Hindsite), TREEM (Treemail), CH (ClauseHub)

**Categories:** `[process]` `[git]` `[testing]` `[ci]` `[observability]`
`[security]` `[architecture]` `[infrastructure]` `[critical]` `[retrospective]`

---

## 2026-03-15 — [CH] Initial API scaffold and OpenAPI-first client generation
`[architecture]`

Energy API scaffolded with FastAPI, SQLAlchemy, Alembic. PRD.md and PLAN.md
created (6 phases, 47 endpoints). Auto-generated Python and TypeScript
clients from OpenAPI spec. `publish-clients.yml` triggers on every main push.

**Rule:** Client libraries are always auto-generated — never hand-written.

---

## 2026-03-15 — [CH] GitHub Issues used instead of Jira
`[process]`

ClauseHub uses GitHub Issues and Mission Control board, not Jira. Predates
the progressive confidence pipeline used by Hindsite and Treemail.

---

## 2026-03-17 — [CH] CRITICAL: 15 pre-existing test failures on CI
`[critical]` `[testing]` `[ci]`

CI red with 15 failures: asyncpg event loop conflicts, SlowAPIMiddleware
blocking test client, missing PostgreSQL service container, missing
psycopg2-binary. Fixed across 6 commits. Added PostgreSQL 16 service
container, created async engine per test, stripped middleware from test
client.

**Rule:** CI must be green before any merge. Never use `continue-on-error`.

---

## 2026-03-17 — [CH] Contract test tool deprecation
`[ci]` `[infrastructure]`

`openapi-diff-cli` (npm) was abandoned and failing. Replaced with
Docker-based `oasdiff` image for breaking change detection.

**Rule:** Prefer container-based CI tools over npm CLI packages.

---

## 2026-03-17 — [CH] Security: python-jose replaced with PyJWT
`[security]`

python-jose had known ECDSA vulnerability and was unmaintained. Replaced
with PyJWT + ES256 via Supabase JWKS.

**Rule:** Audit auth dependencies quarterly. Prefer actively maintained libs.

---

## 2026-03-17 — [CH] Rate limit increased 60→300 req/min
`[infrastructure]`

Scraper hitting 429s during bulk tariff ingestion. Blunt global increase.
Better approach: per-role limits or dedicated ingestion endpoint.

---

## 2026-03-17 — [CH] Auth endpoint exempt from JSON:API content-type
`[architecture]`

`POST /auth/login` rejected for sending `application/json`. Exempted from
JSON:API enforcement. Auth endpoints should always accept standard JSON.

---

## 2026-03-17 — [CH] Scraper extracted to dedicated repo
`[architecture]`

Scraper moved from energy-api to `energy-api-scraper` with own cron workflow
(daily 06:00 UTC). Submits via `energy-api-client-py`.

**Rule:** Data ingestion pipelines should be separate repos from the API.

---

## 2026-03-17 — [CH] Unified Kraken API scrapers
`[architecture]`

Octopus, EDF, E.ON Next all use Kraken API. Three duplicated scrapers
unified into one with supplier-specific config.

**Rule:** Shared underlying API → single scraper with configuration.

---

## 2026-03-18 — [CH] CRITICAL: Observability pipeline silently broken
`[critical]` `[observability]`

Structured logs not reaching Axiom. 6 root causes fixed: middleware not
registered, OTLP paths double-suffixed with `/v1/logs`, OTEL exporter
silently dropping payloads (replaced with direct Axiom POST), logs/traces
mixed in one dataset (split), structlog handler chain swallowing events,
debug prints left in.

**Rule:** After configuring observability, verify end-to-end at the
destination. Silent telemetry failures are common.

---

## 2026-03-18 — [CH] Agent worktrees active without retrospective process
`[process]`

5 agent worktrees active but no retrospective logging. Improvements
discovered ad-hoc. ClauseHub does not use the progressive confidence
pipeline. Gap identified for future adoption.

---

## 2026-03-20 — [HIN] Repo scope correction
`[git]` `[infrastructure]`

`git init` at `/Projects/hindsite/` included Documentation/, idea-Hindsite/,
.claude/ in the repo. Added `.gitignore`, removed non-code from tracking.

**Rule:** Only code directories tracked in git. Docs and config stay local.

---

## 2026-03-20 — [HIN] GitHub org correction
`[git]`

Agent pushed to personal account instead of `hindsite-cxm` org. Updated
remote, pushed to correct org.

**Rule:** All repos under `hindsite-cxm` GitHub org.

---

## 2026-03-20 — [HIN] Jira pipeline statuses created
`[process]` `[infrastructure]`

CLAUDE.md referenced 9 statuses that didn't exist in Jira. Created all 9,
retrieved transition IDs, updated CLAUDE.md.

**Rule:** Create Jira statuses before referencing them. Run
`getTransitionsForJiraIssue` to confirm IDs.

---

## 2026-03-20 — [HIN] Task vs Deliverable workflow separation
`[process]`

Tasks use simple 3-status (Backlog → In Progress → Done). Deliverables
flow through the full 13-status pipeline. Tasks are work breakdown — they
don't need independent testing stages.

---

## 2026-03-20 — [HIN] Lint/format gate added to integration stage
`[ci]` `[testing]`

Development team didn't run `ruff check` or `ruff format --check` before
completion. Integration team found 4 unused imports and 6 unformatted files.

**Rule:** Dev team must run lint and format checks before signalling complete.

---

## 2026-03-20 — [HIN] User-Agent header gap
`[testing]`

E2E team found `fetch.py` sends requests to Wikipedia without User-Agent.
Wikipedia returns 403. Tracked for follow-up — doesn't block current
release but must be fixed before scrapers go live.

---

## 2026-03-20 — [HIN] CLAUDE.md changes must go directly to ci
`[process]` `[git]`

Transition table update was on feature branch, not ci/main. Pipeline
config is infrastructure, not feature code.

**Rule:** CLAUDE.md changes committed directly to ci, merged to main
promptly.

---

## 2026-03-20 — [HIN] Separate repos per service
`[architecture]` `[git]`

Monorepo at `/Projects/hindsite/` broke tool expectations. Each service
gets its own git repo under `hindsite-cxm`.

---

## 2026-03-20 — [HIN] Team retrospectives after every pipeline stage
`[process]`

Every spawned team now reports workflow issues and suggestions at
completion. Pipeline becomes self-improving. Suggestions appended to
workflow-improvements.md.

---

## 2026-03-20 — [HIN] Jira ID required in all commit messages
`[git]` `[process]`

Commits like "T3: Implement COinS parser" didn't link to Jira. Updated
all agents: every commit prefixed with Deliverable Jira ID.

**Rule:** All commits prefixed with Jira Deliverable ID.

---

## 2026-03-20 — [HIN] Rebase before every merge
`[git]`

Merge commits without rebase create unnecessary bubbles. Updated: rebase
source onto target, then `git merge --no-ff`.

**Rule:** `git rebase <target>` then `git merge --no-ff` for all merges.

---

## 2026-03-20 — [HIN] Commit after every file change
`[git]`

Agents batching 11 file changes into one commit. Updated: one file change
= one commit. Each explains what and why, includes Jira ID.

---

## 2026-03-20 — [HIN] HIN-209 Development Team Retrospective
`[retrospective]`

Need .gitignore in scraper repo (__pycache__ tracked). Real HTML fixtures
would strengthen E2E tests beyond mock HTML.

---

## 2026-03-20 — [HIN] CRITICAL: Rebase must not rewrite shared branch history
`[critical]` `[git]`

Rebasing release/rc-2 onto main rewrote ci's merge commit, flattening
the integration topology. RC merges lost their merge commits.

**Rule:** Rebase feature branches only. NEVER rebase ci, release, or main.
RC→main: `git merge --no-ff` only. Back-merge: `git merge --no-ff` only.

---

## 2026-03-20 — [HIN] HIN-209 Local Test Team Retrospective
`[retrospective]`

pyyaml not available (not a dependency). Mock HTML duplicated across test
files — consider shared `tests/fixtures/` module.

---

## 2026-03-20 — [HIN] Jira transitions must not be batched with rejectable calls
`[critical]` `[process]`

HIN-212 transition was discarded when user rejected a batched Bash command.
Ticket stayed in wrong status while work proceeded.

**Rule:** Jira transitions sent as own message. Confirm before proceeding.

---

## 2026-03-20 — [HIN] Push to origin after every commit
`[git]`

Commits accumulated locally — work lost if session interrupted. Updated:
every `git commit` immediately followed by `git push origin <branch>`.

---

## 2026-03-20 — [HIN] Tag main on every release
`[git]` `[process]`

Releases merged to main had no version tags. Added: tag merge commit with
semver, push tag immediately. Back-merge happens after tagging.

---

## 2026-03-20 — [HIN] Platform file for external service configuration
`[infrastructure]`

External service details scattered across config files. Created
`platform.md` documenting all services, env vars, configuration.

**Rule:** Update `platform.md` when any service is set up or changed.

---

## 2026-03-20 — [HIN] Database schema location consideration
`[architecture]`

D02 schema implemented in hindsite-api. Models/validators correctly live
with API. Alembic migrations also in API for now. Could extract to
dedicated db repo later.

---

## 2026-03-20 — [HIN] One ticket at a time
`[process]`

Concurrent tickets increase merge conflict risk and reduce focus. Updated:
single ticket in flight, complete full pipeline before polling next.

---

## 2026-03-20 — [HIN] Dev team must transition task tickets
`[process]`

Task tickets moved in bulk by Team Lead after dev finished. Updated: dev
team transitions tasks to In Progress/Done as they work, giving real-time
visibility.

---

## 2026-03-20 — [HIN] CRITICAL: Startup smoke test required
`[critical]` `[testing]`

All 249 tests passed but app returned 500 on every endpoint.
`Base.metadata.create_all()` never called in `app.py`. Tests passed
because `conftest.py` created tables in fixtures, masking the issue.

**Rule:** Never rely solely on test fixtures. Always verify app boots
cleanly from zero. Startup smoke test required for dev and local test teams.

---

## 2026-03-20 — [HIN] No direct commits on main
`[git]` `[process]`

create_all fix committed directly to main, causing merge conflict with RC.

**Rule:** Main only receives merges from release branches. All changes
go through feature → ci → RC → main. Even hotfixes.

---

## 2026-03-20 — [HIN] Bug analysis must inspect actual data flow
`[process]` `[testing]`

Three successive bugs (500 error, 403 User-Agent, CORS) diagnosed one at
a time because each investigation stopped at first plausible cause. Actual
root cause was CORS but two other bugs fixed first.

**Rule:** Trace the full request path: browser → frontend → API → service
→ external dependency. Check CORS, headers, bodies, status codes at each hop.

---

## 2026-03-21 — [HIN] HIN-358 Development Team Retrospective
`[retrospective]`

Dev dependencies (pytest, ruff) not in lockfile. Pre-existing test failures
should be tracked separately. Duplicated EventDetail construction
refactored to shared helper.

---

## 2026-03-21 — [HIN] Jira status name mismatch
`[process]` `[infrastructure]`

CLAUDE.md referenced "Ready for Dev" but Jira status is "Selected for
Development". Polling queries returned no results.

**Rule:** When adding/renaming Jira statuses, update CLAUDE.md polling
queries. Consider adding status-name mapping table.

---

## 2026-03-21 — [HIN] HIN-358 Local Test Team Retrospective
`[retrospective]`

Stale path dependency: API venv had old hindsite-scraper missing new
exports. Need `uv sync --reinstall-package`. Pre-existing CI failures
(5 tests, 1 type error) should be tracked. Leaflet CSS type error
fixed with `@ts-ignore`.

---

## 2026-03-21 — [HIN] HIN-358 Integration Test Team Retrospective
`[retrospective]`

5 pre-existing test failures and 8 ruff lint errors on ci make it hard
to distinguish new regressions from existing debt.

**Rule:** Track and fix pre-existing failures to maintain green ci baseline.

---

## 2026-03-21 — [HIN] CRITICAL: Web app rendering not validated by any team
`[critical]` `[testing]`

hindsite-web doesn't build (`next build` fails on VideoCarousel type error)
and doesn't render (404 with missing error components). ALL pipeline teams
passed without catching this. Every team treated "pre-existing" as "not our
problem" — but a non-rendering website is ALWAYS a blocker.

**Fixes:** Web projects MUST pass `next build` as hard gate. Page render
check is hard gate (load homepage + one content page, confirm content).
"Pre-existing failure" is NOT acceptable if application is non-functional.

**Rule:** Pipeline must validate application is USABLE at every stage, not
just that tests pass. Broken build = hard stop. Non-rendering page = hard
stop. No exceptions for "pre-existing".

---

## 2026-03-21 — [HIN] HIN-358 Regression Team Retrospective
`[retrospective]`

5 pre-existing failures make regression harder. Suggests "known failures"
baseline file per repo to auto-distinguish pre-existing from new.

**Rule:** Fix pre-existing failures before next release cycle.

---

## 2026-03-21 — [HIN] CRITICAL: CI must be green before any gate passes
`[critical]` `[ci]`

API CI failing throughout HIN-358 pipeline — no team checked GitHub Actions.
6 compounding issues: cross-repo path dependency, GITHUB_TOKEN scope, dev
deps missing in CI, branch mismatch, no web CI workflow, ESLint unconfigured.

**Rule:** CI green is prerequisite for every gate. Teams must check GitHub
Actions, not just local results.

---

## 2026-03-21 — [HIN] CRITICAL: Corrupted SWC binary produced empty CSS
`[critical]` `[testing]`

`@next/swc-darwin-arm64` corrupted → CSS compilation silently produced 0-byte
output. App rendered without any styles. Build succeeded, tests passed, pages
returned 200. Every team dismissed SWC warnings.

**Rule:** Render tests must check CSS is loaded and non-empty. Page returning
200 with 0-byte CSS is a failure.

---

## 2026-03-21 — [HIN] CRITICAL: Missing inline migration for new columns
`[critical]` `[testing]`

Development team added 3 columns to Event model but not to inline migration.
API crashed with `OperationalError: no such column`. Tests passed because
fixtures create all columns.

**Rule:** Every column addition requires corresponding inline migration.
Render tests with real (non-test) database would catch this immediately.

---

## 2026-03-21 — [HIN] Render tests must include full-stack validation
`[testing]`

All teams checked HTTP 200 on homepage. But API wasn't running (event pages
404), CSS was empty (no styles), TopPages was client-side (empty in curl).

**Rule:** Render tests must: start API + web together, verify CSS size > 0,
load event pages with data, verify client-side components render.

---

## 2026-03-30 — [TREEM] TREEM-1 Development Team Retrospective
`[retrospective]`

Redis eager init broke Next.js build (fixed with lazy `getRedis()`).
ts-node missing for Jest TypeScript config. Suggests batch Jira task
transitions and project template/generator for scaffolding.

---

## 2026-03-31 — [TREEM] TREEM-1 Local Test Team Retrospective
`[retrospective]`

Clean run (19 tests, 0 failures). Jest coverage config should add JSX
transform for .tsx coverage collection.

---

## 2026-03-31 — [TREEM] TREEM-1 Integration Test Team Retrospective
`[retrospective]`

Auth callback `signIn` uses `providerAccountId` as User.id lookup — will
error when auth flow first exercised (not blocking for I0). Suggests
per-deliverable-type observability checklist and shared types package.

---

## 2026-03-31 — [TREEM] TREEM-1 E2E Impact Team Retrospective
`[retrospective]`

Clean pass. Suggests minimal Docker Compose smoke test for health endpoints.
OTel build warnings should be added to webpack `externals`.

---

## 2026-03-31 — [TREEM] TREEM-1 Regression Team Retrospective
`[retrospective]`

Clean regression pass. OTel build warnings persist. Prisma migrations
directory empty — first DB deliverable needs documented migration creation.
Suggests `.env.example` per repo.

---

## 2026-03-31 — [TREEM] Cross-cutting: Test strategy by Docker environment
`[testing]` `[architecture]`

Decision record: CI environment runs unit + component + integration + LLM
stub tests (< 2min). Test environment runs full user journey tests with
fixture seeding. Prod-parity runs health checks + critical path smoke +
OTel pipeline validation.

**Gaps identified:** Integration tests, E2E journey tests, OTel validation
scripts, fixture seeder coverage — all needed but not yet written.

---

## 2026-03-31 — [TREEM] TREEM-15 Development Team Retrospective
`[retrospective]`

TypeScript strict mode caught unsafe casts. Fixed signIn callback bug from
I0. Prisma schema lacks Attachment/Recipient models. Suggests shared
encryption module between web and sync.

---

## 2026-03-31 — [TREEM] Process gap: Docker environments not validated during I0
`[critical]` `[infrastructure]`

Infrastructure Deliverables (TREEM-9 through TREEM-14) marked Done without
building Docker environments. Two Dockerfile bugs went undetected: missing
`public/` directory, Prisma version mismatch. Blocks all three Docker envs.

**Fix:** Agent files now include Docker environment sections. `/create-project`
creates a Deliverable that verifies each Docker environment builds.

**Rule:** No Deliverable reaches Done without all Docker environments
building successfully. Code changes outside the pipeline are not acceptable.

---

## 2026-03-31 — [TREEM] Process gap: No app shell Deliverable
`[critical]` `[architecture]`

TREEM-20, TREEM-22, TREEM-23 completed and merged but website shows blank
placeholder. Features built as isolated components with no composing page.
This is the **component-first vs journey-first decomposition trap**.

**Fix:** `/create-project` now requires app shell as first feature
Deliverable after infrastructure.

**Rule:** Decompose by user journey first, technical capability second.
First question for every Initiative: "what page does the user see?"

---

## 2026-04-05 — [TREEM] TREEM-172 Development Team Retrospective
`[retrospective]`

`jest.useFakeTimers()` accumulated time across retry loops causing circuit
breaker timeout to elapse during tests. Pre-existing Prettier format issues.
Suggests test-only constructor on CircuitBreaker for clock injection.

---

## 2026-04-05 — [TREEM] TREEM-172 Pipeline Observations
`[ci]` `[infrastructure]`

pipelinectl bugs: `get_feature_branch()` and `cmd_local_gate()` only
searched treemail-web, not treemail-sync (fixed). Docker build times
excessive (460MB+ sync, 1.18GB web contexts). 13 pre-existing browser
test failures. 8 skipped journey E2E tests never implemented.

**Rule:** Add `.dockerignore` to exclude node_modules from build context.

---

## 2026-04-05 — [TREEM] TREEM-199 Development Team Retrospective
`[retrospective]`

Wrong import in send-worker.ts (`createLinkedSpan` vs `withLinkedSpan`),
fixed immediately. Existing tests needed tracing mock after new dependency.

---

## 2026-04-05 — [TREEM] TREEM-199 Pipeline Observations
`[process]` `[git]`

Multi-repo merge: unstaged REPO_MAP.md changes blocked rebase during
merge-to-ci. Consider adding `git stash` to pipelinectl before rebase.
Refinement overestimated gap — 2 of 7 tasks already satisfied by prior work.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total entries | 48 |
| Critical issues | 9 |
| Projects: Hindsite | 27 entries |
| Projects: Treemail | 14 entries |
| Projects: ClauseHub | 7 entries |
| Categories: process | 16 |
| Categories: git | 12 |
| Categories: testing | 12 |
| Categories: critical | 9 |
| Categories: ci | 7 |
| Categories: retrospective | 12 |
| Categories: architecture | 7 |
| Categories: infrastructure | 7 |
| Categories: observability | 2 |
| Categories: security | 2 |
| Date range | 2026-03-15 to 2026-04-05 |
