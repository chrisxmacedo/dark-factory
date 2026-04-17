# Cross-pipeline flow

Read by: Programme Lead (always), Capability Lead (orientation), Team
Lead (orientation).

How work moves from design through Jira into build and on to production.

## The three boundaries

```
┌──────────────────┐  Gate 1    ┌─────────────────┐  Gate 2         ┌───────────────────────┐
│ Phase A + B      │ ─────────► │ Phase C journey │ ──────────────► │ DEV Deliverable      │
│ Capability Lead  │            │ Capability Lead │  Programme Lead │ Team Lead             │
│                  │            │                 │  creates Jira   │                        │
│ Outputs:         │            │ Outputs:        │  Deliverable    │ Outputs:               │
│  - capabilities  │            │  - journey spec │                 │  - running code in prod│
│  - personas      │            │  - API contracts│                 │  - evidence of quality │
│  - governance    │            │  - events       │                 │    gates at every stage│
│  - services      │            │  - sequences    │                 │                        │
│  - C4 L1 + L2    │            │  - data model   │                 │                        │
│  - obs, sec, env │            │  - NFRs         │                 │                        │
│  - journey       │            │  - evidence/    │                 │                        │
│    inventory     │            │    bundle       │                 │                        │
└──────────────────┘            └─────────────────┘                 └───────────────────────┘
```

## Parallelism

- **Phase A + B is sequential.** Gate 1 passes once, never revisited.
- **Phase C is per-journey.** One journey at a time through scaffold →
  model → review → stable. Multiple journeys can be "stable" before
  the Team Lead starts building them.
- **Build is per-Deliverable.** The Team Lead processes one Deliverable
  at a time (per `development-team/.claude/context/agent-rules.md`),
  but new Deliverables can accumulate in the Backlog.
- **Design and build overlap.** Phase C journey N+1 can be in
  modelling while DEV Deliverable for journey N is in integration test.

## Handoff cadence

| From                | To                   | Trigger                           | Artefact that moves          |
|---------------------|----------------------|-----------------------------------|------------------------------|
| Human               | Capability Lead      | Project kickoff                   | Mandate + legislation refs   |
| Capability Lead     | Programme Lead       | Gate 1 passed                     | Sprint 0 brief               |
| Programme Lead      | Team Lead            | DEV Deliverable created           | Deliverable in Backlog       |
| Capability Lead     | Programme Lead       | Gate 2 passed (per journey)       | Journey handoff brief        |
| Team Lead           | Programme Lead       | Deliverable Done                  | Release version + link       |
| Team Lead           | Programme Lead       | SPEC DEFECT RAISED                | Diagnostics report           |
| Programme Lead      | Capability Lead      | Spec defect routed                | Refinement ticket            |
| Capability Lead     | Programme Lead       | Refinement resolved               | Updated Stable journey       |
| Either Lead         | Programme Lead       | FIX EXHAUSTED                     | Escalation report            |
| Programme Lead      | Human                | FIX EXHAUSTED                     | Summary + decision request   |

## Why this split

- **Design and build have different rhythms.** Design is thinking-heavy,
  low CI cost, tolerates rework via refinements. Build is validation-
  heavy, high CI cost, protected by gates. One Lead per rhythm.
- **Jira is the boundary artefact.** Everything the Team Lead needs
  lives in a Deliverable ticket — no direct reads of the capability
  team's artefacts during build (though the Refinement Team may
  consult them). This makes the Deliverable the contract.
- **The Programme Lead is the only role that reads both sides.** This
  prevents either Lead from becoming aware of cross-team concerns that
  distort its own pipeline.

## Things that break if the Programme Lead drops the ball

- A Deliverable created without the evidence bundle → dev team
  cannot audit which checks passed upstream.
- A Gate 2 pass without the handoff ever created → the journey is
  stable but nobody's building it.
- A spec defect detected in build but not routed to the capability
  team → the defect is fixed locally in code and the specification
  diverges from implementation.
- A refinement that resolves without the Deliverable being unblocked
  → the build pipeline stalls invisibly.

The state files (`PIPELINE-STATE.md`, `PORTFOLIO-MAP.md`) are the
defence against all four. Keep them current.

## Build order — journey slices on a ghost architecture

The delivery team builds in **journey slices**, not inside-out.

```
  [Sprint 0]  →  [Journey 1 slice]  →  [Journey 2 slice]  →  …  →  [Remainder?]
   platform        JRN-001                 JRN-002                   (usually none)
   foundation      realises part           realises next
                   of architecture         part …
```

### The three components of the build plan

1. **Sprint 0** — the portion of the architecture that has **no
   journey-specific content**. Platform services (T0/T1), environments,
   CI, zero-trust policy scaffolding, observability stores. Built once,
   before any journey slice. See `jira-lifecycle.md` §4 for the scope
   rule.

2. **Journey slices** — one DEV Deliverable per stable journey. Each
   slice realises the part of the architecture the journey touches:
   new services, new entities, new APIs, new events. The architecture
   is known (the "ghost") — each slice fills in one area. See
   `jira-lifecycle.md` §5 for the slice rule.

3. **Remainder** — everything in the architecture not touched by any
   journey. By default, this means the architecture was over-specified.
   Remove from the catalogue rather than build speculatively. The one
   exception is genuinely cross-cutting work (e.g. periodic
   reconciliation across capabilities) which becomes one Remainder
   Deliverable after the last prioritised journey. See
   `jira-lifecycle.md` §6.

### Why slices, not inside-out

- **Feedback loop.** Each slice is a week or two from Gate 2 to Done.
  Inside-out hides architectural mistakes until far later.
- **Continuous architectural validation.** If journey 2 reveals journey
  1 drew a service boundary wrong, it's cheap to fix after one slice.
  It's expensive after the whole platform is built.
- **Capability-team cadence matches.** Gate 2 is per-journey. Building
  inside-out would force a massive sync delay between design and
  build.
- **AI agents prefer slices.** A journey fits in a context window.
  A whole platform does not.
- **Ghost architecture answers the usual objection.** The full
  architecture is specified at Phase B. Slices don't discover
  architecture — they realise a known plan progressively.

### Journey priority — who decides

Capability Lead produces `journey-inventory.json` at Phase B step 6,
with priority and `rationale_for_priority` per row. Recommended
ordering:

1. Foundational-data journeys (Customer, Account) — they establish
   entities later journeys depend on.
2. Compliance-critical journeys (KYC, sanctions, fraud) — must be live
   before money-moving journeys.
3. Money-movers and revenue journeys.
4. Reporting and overlay journeys.

At Gate 1 the Capability Lead creates MODEL epics in priority order.
Humans can reorder MODEL epics directly in Jira — the Capability Lead
always picks the highest-priority Backlog epic on its next cycle, so
reordering "just works" without a separate approval gate.

### What the Programme Lead tracks per slice

- `PORTFOLIO-MAP.md` — journey row: Design → Stable → Building → Live
- `PIPELINE-STATE.md` — handoff queue and last action
- In each Deliverable ticket: the `cap:{CAP-NNN}` label, `slice:journey`
  label, and an "implements" link to the MODEL epic
