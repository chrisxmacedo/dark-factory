# Testing best practices

Read by: all teams, all starters

## Test pyramid

- **Many** unit tests (fast, isolated, cheap)
- **Fewer** integration tests (real containers, slower)
- **Fewest** E2E tests (full system, slowest)
- If your E2E tests outnumber your unit tests, the pyramid is inverted — fix it

## Test types and where they run

| Type | What it tests | Where it runs | Docker env | Spec files |
|---|---|---|---|---|
| Unit | Individual function/class | Feature branch | None | `src/__tests__/` |
| Component | Module boundary with mocks | Feature branch | None | `src/__tests__/` |
| Behaviour | One per Gherkin acceptance criterion | Feature branch | None | `src/__tests__/` |
| Edge case | Boundary conditions from Devil's Advocate | Feature branch | None | `src/__tests__/` |
| Integration | Health, LLM stub, correlation IDs, storage | CI (after merge) | CI | `tests/integration/` |
| **Browser interaction** | **Click, navigate, verify what user sees** | **CI (after merge)** | **CI** | **`tests/browser/`** |
| E2E regression | Full user journeys with fixture data | RC (after cut) | Test | `tests/e2e/` |
| Smoke | All service health + OTel pipeline | Main (after merge) | Prod-parity | `tests/smoke/` |

## Browser interaction tests

API-level tests verify data and status codes. Browser tests verify **what the user actually sees**. Both are required.

Browser tests use Playwright in browser mode (not API mode):
- Navigate to pages, click elements, fill forms, assert visible text
- Run against the CI Docker environment (authenticated via dev-login)
- Every Gherkin scenario that describes a user action ("when the user clicks...") must have a browser test
- Browser tests catch: rendering errors, broken navigation, missing data binding, JavaScript exceptions, responsive layout issues

**What browser tests catch that API tests don't:**
- "Failed to load thread" — API returns 200 but the frontend component crashes
- Missing navigation links — routes exist but no link points to them
- Broken forms — API accepts data but the form doesn't submit
- Visual regressions — layout shifts, missing styles, hidden elements

NEVER rely solely on API tests for features that have a UI.

## Gate count per branch

| Branch | Scripted gates | Reasoning gates | Total |
|---|---|---|---|
| Feature | 7 (tests, build, lint, format) | Devil's Advocate (continuous) | ~7 + review |
| CI | 11 scripted + 1 build gate | 12 analysis (analyst, observability, E2E, quality) | 24 |
| RC | 9 scripted + 1 build gate | 6 readiness checks | 16 |
| Main | 10 scripted | 3 observation (15 min) | 13 |
| **Total** | **39** | **21 + review** | **~60** |

For the specific gates per branch, see:
- `pipeline-feature-branch.md` — 7 gates
- `pipeline-ci-branch.md` — 18 gates
- `pipeline-release-branch.md` — 16 RC gates + 13 Main gates

## Naming

- Describe WHAT is being tested and the EXPECTED outcome
- YES: `"returns 404 when user not found"`
- NO: `"test getUserById"` or `"test case 3"`
- Group by feature/module in describe blocks

## Data-level assertions

- Every state-mutating test MUST verify database state — not just the API response
- After a POST: query the DB and assert the record exists with correct fields
- After a DELETE: query the DB and assert the record is gone
- After a bulk operation: verify counts and relationships

## Fixture data

- Deterministic IDs: `test-user-001`, `test-thread-001` — never random in fixtures
- Idempotent seeding: `ON CONFLICT DO NOTHING` — safe to run multiple times
- Minimum coverage: 2+ users (isolation), all entity types, all enum variants, at least one relationship chain
- Separate from test assertions — fixtures create the world, tests verify behaviour

## Acceptance criteria → tests

Gherkin scenarios in the ticket define four types of expected behaviour:

| Type | What it tests | Example |
|---|---|---|
| Successful | Happy path works | "Given user has threads, When user views inbox, Then threads are listed" |
| Edge case | Boundary conditions | "Given user has 0 threads, When user views inbox, Then empty state shown" |
| Corner case | Unusual but valid | "Given two users create a group simultaneously, When both submit, Then both groups created" |
| Exception | Invalid/error states | "Given user is not authenticated, When user views inbox, Then redirected to sign-in" |

Mapping scenarios to tests:
- One Gherkin scenario = one unit/behaviour test minimum (validates data state)
- Gherkin scenarios with user actions ("When the user clicks...") also need a browser test (validates UI renders the data state)
- **Given** maps to test setup (seed data, create fixtures)
- **When** maps to the action under test (API call, function call, page click)
- **Then** maps to assertions (database state, API response, visible UI text)
- If a scenario can't be tested automatically, flag it as `NO E2E COVERAGE`

## Test isolation

- Each test creates its own state — never depends on another test's output
- Clean up after yourself or use per-test transactions that roll back
- Tests must pass in any order — no sequential dependencies

## Mocking rules

- Mock at the boundary, not the implementation
- Never mock what you don't own — wrap the external dependency, mock the wrapper
- In unit tests: mock DB, Redis, external APIs
- In integration tests: use real DB + Redis containers, mock only external APIs (via LLM stub)
- In E2E tests: mock nothing except external APIs (via LLM stub)

## LLM stub

- Deterministic responses keyed by content hash
- Supports both Anthropic (POST /v1/messages) and OpenAI (POST /v1/chat/completions) formats
- Never call real LLM APIs in tests — costs money, non-deterministic
- Default fixture response for unmatched hashes

## Flaky tests

- Investigate immediately — never skip with TODO
- A skipped test is a lie about system behaviour
- Common causes: timing issues, shared state, network dependency, non-deterministic data
- If flaky after investigation: isolate the non-deterministic part, mock it

## Coverage enforcement

- **Minimum thresholds enforced at CI stage (HARD GATE):**
  - 80% line coverage, 70% branch coverage per service
  - New code in a PR must have ≥ 90% line coverage (diff coverage)
- Coverage is measured per-service, not as a project aggregate
- Coverage report is generated on every CI run and included in the Jira comment
- Coverage decreasing vs the previous CI run is flagged as a warning
- Focus on: error paths, boundary conditions, state mutations
- Coverage of happy path alone is insufficient

## Build verification

- `next build` (or equivalent) is a test — TypeScript errors caught here may not appear in `npm test`
- Include build verification in the CI gate, not just unit tests
- A passing test suite with a failing build is not releasable

## Cross-service data contracts

When one service produces data that another service consumes, the contract
between them MUST be tested end-to-end against real infrastructure (database
with real schema, real foreign key constraints, real queues).

Common failures that unit tests miss:
- Foreign key violations: Service A produces an ID that doesn't exist in
  Service B's reference table (e.g. parser produces `TIDM:XXX` but the
  ingest database only accepts ISINs from the companies table)
- Schema mismatches: Service A adds a column that Service B's query doesn't
  expect (e.g. `column f.status does not exist`)
- Type mismatches: Service A sends a string where Service B expects an int
- Encoding issues: Service A sends UTF-8 with emoji, Service B's schema
  truncates at a byte boundary

**Rule:** Every cross-service data path needs at least one integration test
that exercises the full chain from producer to consumer against real
infrastructure (not mocks). The test should use data that exercises edge
cases in the contract — not just the happy path with seed data.

## Contract testing

When service A produces an API that service B consumes, **both sides must
have contract tests** that verify the request/response shape:

- **Producer contract test**: verify that the actual response matches
  the documented schema (JSON Schema or TypeScript interface)
- **Consumer contract test**: verify that the consumer can parse and
  use the producer's response shape (using recorded fixtures, not mocks)
- Contract tests run at CI stage before integration tests
- A contract test failure is a **HARD GATE** — blocks promotion to RC
- When a service changes its API response, the contract tests for
  every consumer must be updated in the same PR
- Additive changes (new optional fields) are non-breaking and must pass
- Removal or renaming of fields is breaking and must fail

Location: `tests/contract/` — one file per service boundary.

## Migration safety

Database migrations must be tested against a populated schema before
being applied to shared environments:

- Every migration is tested against a snapshot of the current schema
  WITH seed data (not an empty database)
- The test verifies: no data loss (row counts match), no constraint
  violations, rollback works
- **Destructive migrations** (DROP TABLE, DROP COLUMN, ALTER TYPE) are
  flagged for human review — HARD GATE
- Every migration must have a corresponding down/rollback migration
- Migration safety is checked at CI stage before integration tests

## Data quality gates

Every service must validate its inputs at the boundary:

- Incoming HTTP requests: validate required fields, types, non-empty
  for mandatory fields, value ranges
- Queue messages: validate schema before processing
- Invalid data is rejected with a structured error (never silently accepted)
- Rejected data is logged with correlation ID, source service, and reason
- Quality metrics (accepted/rejected/error counts) exposed via Prometheus
- A function that transforms external data must log a warning if
  non-empty input produces empty output

## Dependency vulnerability scanning

Every CI build must run a dependency vulnerability scan:

- `npm audit` for JavaScript services, `pip-audit` for Python services
- Critical and high-severity vulnerabilities are a **HARD GATE** — block
  promotion to RC
- Medium-severity vulnerabilities are flagged as warnings
- A suppressions file allows known-accepted vulnerabilities with a
  documented reason and expiry date

## Rollback procedures

Every release must have a tested rollback plan:

- Docker images tagged with release version (not just `latest`),
  retained for at least 5 releases
- Every database migration has a tested down/rollback counterpart
- The rollback plan specifies: images to revert, migrations to roll
  back, environment variable changes, verification steps
- Rollback is tested in the RC environment before every release to main
- If rollback is not possible (destructive migration), this must be
  explicitly flagged and approved by the human before release
- Rollback must be executable in under 5 minutes

NEVER:
- Test implementation details (private methods, internal state)
- Use `test.skip()` as a permanent solution
- Write tests that pass regardless of the code (tautological tests)
- Share mutable state between tests
- Depend on test execution order
- Use real API keys or external services in automated tests
- Rely solely on fixture data with known-good IDs — test with data that
  exercises foreign key paths, nullable fields, and fallback identifiers
- Apply a migration to a shared environment without testing it against
  populated data first
- Deploy without a documented rollback plan
- Ignore dependency vulnerability scan results
