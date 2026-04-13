# Testing Strategy

## Overview

Testing in this pipeline is a series of distinct validation layers, each
designed to answer a different question at the appropriate level of
fidelity and speed.

The layers build on each other. Tests written at an earlier stage continue
to run at later stages. Each stage adds a new layer of validation on top
of the existing ones.

---

## Test types and where they belong

### Unit tests
**Owner:** Software Engineer (Implementer)
**Stage:** In Development
**Question:** Does this function/class do what it is supposed to do?

Unit tests operate on the smallest units of code: individual functions,
methods, and classes. They run in complete isolation — all dependencies
are mocked or stubbed. They are fast (milliseconds), deterministic, and
produce highly specific failure messages.

Written by the engineer alongside the implementation. They require
knowledge of implementation internals and serve as the engineer's
primary self-verification tool.

### Component tests
**Owner:** Software Engineer (Implementer)
**Stage:** In Development
**Question:** Does this module/service boundary behave correctly?

Component tests operate at a higher level than unit tests — the public
interface of a module or service — with external dependencies mocked.
They validate that the component integrates correctly within its own
boundary without requiring real external systems.

Like unit tests, written by the engineer. They verify the individual
service or module is correct before integration with anything else.

### Local integration tests (mocked/partial)
**Owner:** Test Developer (Test Writer)
**Stage:** In Local Test
**Question:** Do the components within this feature interact correctly?

Validate interaction between components within the feature boundary.
External dependencies (databases, other services, third-party APIs) are
mocked or use test doubles, because real external systems are not
available on the feature branch.

Written by the Test Developer, focusing on the contracts between
components rather than the internals of each one.

### Behaviour tests
**Owner:** Test Developer (Test Writer)
**Stage:** In Local Test
**Question:** Does the implementation satisfy the acceptance criteria?

Validate each acceptance criterion explicitly — minimum one test per
criterion. Written from the outside, as a user or consumer of the
feature would experience it, without knowledge of implementation
internals.

These are the primary audit trail between the ticket's acceptance
criteria and the implemented code.

### Integration tests (real services)
**Owner:** Test Developer (Integration Analyst)
**Stage:** In Integration Test
**Question:** Do components work together in the shared environment?

Run against the CI/integration environment where real service instances
are available. Validate service-to-service API contracts, event
publishing and consumption, database schema compatibility across services,
and real-time data flow between components.

### Contract tests
**Owner:** Test Developer (Integration Analyst)
**Stage:** In Integration Test
**Question:** Are the interfaces between services compatible?

A specific subset of integration tests that verify interface contracts
between services: request/response schemas, event payload formats, API
versioning. Contract failures are one of the most common sources of
integration bugs and one of the hardest to debug without explicit
contract validation.

### E2E impact tests
**Owner:** Test Developer (Impact Analyst + E2E Runner)
**Stage:** In E2E Impact Test
**Question:** Does this change work within the real system flows it affects?

Scoped to the user journeys and system flows directly affected by the
change — not a full regression. The Impact Analyst produces an impact
map before tests run, identifying: which journeys are affected, which
services and data stores are involved, what data assertions to make,
and what observability signals to check.

This scoping is deliberate. Running the full regression suite at the CI
stage would be slow and would generate noise from in-flight changes by
other developers. Impact-scoped E2E testing gives system-level confidence
without those costs.

### Full E2E regression
**Owner:** Test Developer (Regression Runner + Regression Analyst)
**Stage:** In Full E2E Regression
**Question:** Does the entire system still work?

Every test, every journey — cross-system validation against the release
candidate. Running this only on the release candidate (not every CI
merge) is deliberate. The release candidate is a stable snapshot, so
the results are not polluted by other in-flight changes and are directly
actionable.

---

## Data validation strategy

Surface-level test assertions are not sufficient for critical flows. A
test can pass — the API returns 200, the UI shows the right data — while
the underlying data is silently incorrect.

### Feature Branch (Local Test)
For any test that mutates state:
- Verify the database row was created/updated/deleted as expected
- Verify the returned data structure matches the expected schema
- Verify that nothing was silently dropped (e.g. a nullable field
  that should have been populated)

### CI (Integration Test)
- Trace data mutations across service boundaries using correlation IDs
- Verify that events published by one service are received and processed
  correctly by consuming services
- Verify cross-service data consistency: if service A writes to the DB
  and publishes an event, and service B consumes it and writes to its
  own DB, both stores should be in a consistent state

### CI (E2E Impact Test)
For each affected journey:
- Verify end-to-end data integrity — data enters the system, is
  transformed correctly at each stage, and exits in the expected state
- Use correlation IDs to trace a request through every service it
  touches and confirm it completed correctly at each hop

### Release Candidate (Regression)
- Re-verify all of the above against the release candidate environment
- Confirm that data migrations have been applied correctly and have
  not corrupted existing data

---

## Observability requirements

Observability is a validation requirement at every stage from CI onwards.
A change that cannot be observed cannot be validated in production.

### Structured logging
Every service must emit structured logs (JSON or equivalent) at key
decision points:
- Request received (with correlation ID)
- Key business logic decisions
- Errors and exceptions (with full context)
- Request completed (with outcome)

Structured logs enable automated assertion: the test can verify not just
that the API returned 200, but that the correct log lines were emitted
at the correct points.

### Correlation IDs
Every request that crosses a service boundary must carry a correlation ID.
This enables:
- Tracing a request end-to-end across multiple services in a single query
- Confirming that a request completed at every hop, not just at entry
- Debugging failures in production without needing to reproduce them

The Observability Checker at the integration stage explicitly verifies
that correlation IDs are present and propagated correctly.

### Metrics and traces
Where available:
- Request latency histograms (p50, p95, p99)
- Error rate counters
- Distributed traces for multi-service flows

Monitored by the Production Observer in the 15-minute stabilisation
window after every production deployment.

### Why observability is a gate, not a suggestion

If a change ships to production without the correct observability signals,
and something goes wrong, the time-to-diagnosis is dramatically longer.
Worse, the problem may not be detected at all until it has caused
significant impact.

Making observability a gate at the integration stage — where it is
cheapest to fix — ensures that every change that reaches production
can be monitored, debugged, and validated.

---

## Test anti-patterns this strategy explicitly avoids

### Over-reliance on E2E tests
E2E tests are slow, expensive, and brittle. A pipeline that relies
primarily on E2E tests will be slow to run, slow to debug on failure,
and prone to false positives from environmental instability.

The mitigation is investment in unit, component, and integration tests.
E2E tests in this pipeline are scoped — they test what unit and
integration tests cannot test, not everything.

### CI instability
A CI environment that is unreliable produces noise that obscures real
failures. The mitigation is strong pre-merge validation (local test stage)
ensuring only clean code reaches the integration branch.

### False positives in E2E
E2E tests that pass with incorrect data are worse than E2E tests that
fail — they create false confidence. The mitigation is the data
validation requirement: every E2E test must include assertions on the
underlying state, not just the surface response.
