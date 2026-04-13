# Pipeline Rationale

## The core problem this pipeline solves

Software development failures rarely come from a single cause. They come
from the accumulation of undetected problems across multiple layers:
a function that works in isolation but breaks when integrated, an integration
that passes tests but corrupts data silently, a release that passes all
automated checks but degrades under real traffic.

Traditional pipelines often conflate these layers — running everything in
one CI job, or doing a single round of testing before release. The result is
that failures are discovered late, when they are expensive to fix, and the
signals that would have caught them early were never designed in.

This pipeline is designed around a different principle: **progressive
confidence**. Each stage is designed to answer one specific question, at
the right level of fidelity, with the right kind of evidence.

---

## The progressive confidence principle

Each stage answers a distinct question:

| Stage | Environment | Question |
|-------|-------------|----------|
| In Development | Feature Branch | Does the code work in isolation? |
| In Local Test | Feature Branch | Does the behaviour match the specification? |
| In Integration Test | CI | Do components work together? |
| In E2E Impact Test | CI | Does the change work within real system flows? |
| In Full E2E Regression | Release Candidate | Does the system still work overall? |
| Release / Production | Main | Is this version production-ready and live? |

The value of this structure is that it optimises for **finding the right
problem at the right time**:

**Early stages** are fast and isolated. They give the developer rapid
feedback on whether their implementation is correct. Running a full
regression suite at the feature branch stage would be slow, noisy, and
misleading — many tests would fail for reasons unrelated to the change.

**Middle stages** introduce real system interaction progressively.
Integration tests catch interface and contract failures that unit tests
cannot detect. E2E impact tests confirm the change works in real flows
without the noise of testing the entire system.

**Late stages** provide system-wide confidence. The full regression suite
only runs against a stable release candidate — not against every feature
branch, where it would produce false negatives from in-flight changes by
other developers.

Failures are caught by the stage that is best positioned to diagnose them,
not by whatever stage happens to run them first.

---

## Why repository states matter

The pipeline is not just a sequence of test runs — it is a sequence of
**repository states**, each representing a different level of stability:

### Feature Branch
The developer's working environment. It is explicitly safe to break here.
Rapid iteration is the goal. The only concern is whether the implementation
is correct in isolation and will integrate cleanly.

### CI / Integration Branch
The first shared environment. Multiple feature branches merge here. Component
interactions are tested for the first time against real dependencies. It is
expected to be less stable than the RC, which is why fixes are acceptable
here before promoting.

### Release Candidate
A snapshot taken from CI. Once cut, it enters a stabilisation phase — no
new features, only targeted fixes. Full regression runs here because it
represents what would actually be released.

### Main
Production-ready or deployed code. The system of record. Nothing reaches
Main without passing every preceding gate and receiving explicit human
approval.

The further right a ticket moves, the higher the confidence — and the
higher the cost of a failure discovered at that stage. The pipeline is
designed to catch failures as far left as possible.

---

## Why evidence-based gating

Each stage gate requires concrete evidence, not a teammate's claim or a
pipeline passing without inspection:

**Test results** — pass/fail counts, specific failure messages, coverage
delta. Not just "tests passed" — which tests, how many, what changed.

**Data validation** — where state is mutated, the gate requires verification
that the database state, event payloads, or data structures are correct.
Surface-level response checks can pass while data is silently corrupted.

**Observability** — structured logs, correlation IDs, traces, and metrics
must be confirmed present before a stage can pass. This validates that the
change is working correctly in the environment, and ensures the system
remains observable in production.

A pipeline that passes without evidence is not a pipeline — it is an
optimism machine.

---

## Why two human gates and not more

The pipeline has exactly two points where a human must take explicit action:

1. **Moving a ticket to Ready for Dev** — the human decides when a ticket
   is refined and ready. This requires product and engineering judgement
   about priority, scope, and dependencies that no agent can make.

2. **Approving promotion to Main** — the human reviews the release readiness
   report and decides whether to deploy to production. Deploying is a
   business decision, not a technical one. Automated gates provide evidence,
   but the decision belongs to the human.

Every other transition is automated — because every other transition is
based on objective, verifiable evidence that an agent team can assess.
Adding more human gates would slow the pipeline without adding safety.
Removing these two would eliminate the human judgement that cannot be
automated.

---

## Why this pipeline for a solo or small team

The progressive confidence model is sometimes associated with large
engineering organisations. For a solo developer or small team, the
rationale is different but equally strong:

The cost of a production incident is disproportionately high. There is no
on-call rotation, no dedicated QA, no second pair of eyes. The pipeline
compensates for the absence of those human checks by encoding them as
automated gates at every stage.

The agent team system means the overhead of running this pipeline is low.
Teams are spawned automatically, work in parallel, and report structured
results. The developer interacts with the pipeline at the two human gates
and is otherwise free to work on the next ticket while the current one
progresses through the stages.
