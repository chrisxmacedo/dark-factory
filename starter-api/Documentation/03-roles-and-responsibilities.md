# Roles and Responsibilities

## The two-role model

The pipeline separates work into two distinct professional roles. This
separation reflects a genuine difference in perspective, objective, and
skill — not just a naming convention.

---

## Software Engineer

**Primary concern:** Is the implementation correct?

The Software Engineer is responsible for:
- Understanding the acceptance criteria and translating them into code
- Exploring the existing codebase before writing anything new
- Making implementation decisions coherent with existing patterns
- Writing code that is correct, maintainable, and **testable**
- Writing unit tests and component tests as part of implementation —
  not as a separate activity, but as part of building the feature

The Software Engineer operates on the feature branch and owns the
implementation decisions.

### Why engineers write unit and component tests

Unit and component tests are the engineer's primary mechanism for
verifying their implementation is correct. They are written alongside
the code because:

1. They are the fastest feedback loop — a unit test catches a regression
   in milliseconds, not minutes
2. They force the engineer to think about testability while implementing,
   not after the fact
3. They document the expected behaviour of each unit at the level of
   detail only the engineer has while writing it

These tests are not the Test Developer's responsibility because they
require intimate knowledge of the implementation internals. The Test
Developer cannot write a meaningful unit test for code they have not
written — they can only verify behaviour from the outside.

---

## Test Developer

**Primary concern:** Does the system behave correctly?

The Test Developer is responsible for:
- Defining test scenarios that cover the acceptance criteria from a
  behavioural perspective (what the system should do, not how it does it)
- Designing tests that validate system-level interactions: integration,
  end-to-end flows, cross-service consistency
- Ensuring data is validated at the right points — not just surface
  responses, but underlying state
- Ensuring the system is observable: that failures produce useful signals
  and correct behaviour is confirmed through those signals

The Test Developer operates across multiple pipeline stages, beginning
after the engineer's implementation is complete.

### Why test developers are separate from engineers

The Test Developer brings a different kind of scepticism. Where the
engineer is optimistic about their implementation (they wrote it to work),
the Test Developer's role is to find the ways it does not.

Additionally, the Test Developer is responsible for system-level
validation the engineer is not positioned to perform:
- The engineer wrote the feature in isolation; the Test Developer tests
  it against the real system
- The engineer knows what their code does; the Test Developer validates
  whether it does what the acceptance criteria requires
- The engineer tested their component; the Test Developer validates
  the contracts between components

---

## Agent team members and their role alignment

### Software Engineer role
| Agent | Stage | Responsibility |
|-------|-------|----------------|
| Implementer | Development | Implements feature, writes unit/component tests |
| Fix Agent (dev) | Local Test | Fixes implementation failures found by tests |

### Test Developer role
| Agent | Stage | Responsibility |
|-------|-------|----------------|
| Test Writer | Local Test | Writes behaviour and integration tests |
| Test Runner | Local Test | Executes test suite, captures evidence |
| Fix Agent (test) | Local Test | Diagnoses failures — implementation or test |
| Integration Analyst | Integration | Validates contracts, downstream impact, data consistency |
| Observability Checker | Integration | Confirms observability signals are present |
| Impact Analyst | E2E Impact | Maps affected journeys, data paths, observability hooks |
| E2E Runner | E2E Impact | Executes impact-scoped E2E tests with data assertions |
| Regression Runner | Regression | Executes full regression suite |
| Regression Analyst | Regression | Assesses release readiness holistically |
| Flake Investigator | Regression | Distinguishes flaky tests from genuine regressions |

### Oversight and operations roles
| Agent | Stage | Responsibility |
|-------|-------|----------------|
| Devil's Advocate | Development | Critiques implementation in real time |
| CI Monitor | Integration | Monitors the CI pipeline |
| Release Manager | Release | Manages RC-to-Main merge and pre-release steps |
| Deploy Agent | Release | Triggers and monitors the deployment pipeline |
| Production Smoke Tester | Release | Validates production health post-deploy |
| Production Observer | Release | Monitors production stability for 15 min post-deploy |

---

## The Devil's Advocate — rationale

The Devil's Advocate runs in parallel with the Implementer during
development, reviewing each commit as it is made and sending critiques
via inbox.

**Real-time critique is more valuable than post-implementation review.**
When a critique arrives while the engineer is still implementing, it can
be addressed in the next commit. When it arrives after implementation is
complete, addressing it requires unpicking decisions that may have
cascading effects. The earlier a problem is surfaced, the cheaper it is
to fix.

**The Implementer and Devil's Advocate have different information.**
The Implementer knows the implementation in detail. The Devil's Advocate
knows the acceptance criteria and the existing codebase patterns. Running
in parallel and communicating through the inbox combines both perspectives
in real time.

**Critique is advisory unless severity is high.**
Low and medium findings are recorded but do not stop the Implementer.
High-severity findings — security issues, data integrity risks, clear
acceptance criteria violations — require acknowledgement before the
completion gate passes. This adds quality without becoming a bottleneck.

---

## The Team Lead — rationale

The Team Lead does not write code, run tests, or deploy. Its role is
coordination and gate-keeping.

**Why a dedicated Team Lead rather than having agents self-coordinate?**

Self-coordination between agents is fragile. If the Implementer signals
the Test Writer directly, the logic for what happens next is distributed
across multiple agents — and any could miss a message, misinterpret a
state, or make a transition prematurely.

The Team Lead centralises these decisions. It reads the ticket and passes
context to every agent it spawns. It receives structured inbox messages
from all agents. It verifies completion gates before any Jira transition.
It is the single agent that writes to Jira.

This means Jira state is always consistent with what the Team Lead has
explicitly verified — not with what any individual agent claims.
