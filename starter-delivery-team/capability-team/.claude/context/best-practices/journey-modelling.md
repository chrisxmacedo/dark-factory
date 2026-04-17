# Journey modelling best practices

Read by: Journey Modelling Team (Phase C)

A journey is the unit of work in Phase C. One journey = one cycle
through steps 7-13.

## What a journey is

- **Design-time specification, not runtime orchestration** — journeys
  define steps, data requirements, and valid transitions, but nothing
  reads them at runtime.
- The channel UI uses journey specs to build the interaction flow; AI
  agents use them to understand how capabilities compose.
- Data status within capabilities implicitly represents journey progress
  — a KYC record with status "pending" means the onboarding journey is
  in progress. No separate state machine needed.
- Actual coordination happens through capabilities reacting to each
  other's published events.

## Structural requirements

- Every journey must have: **happy path, at least one alternative path,
  at least one exception path**.
- Phases within a journey are the natural breakpoints — each phase can
  have different actors, different governance rules, different NFRs.
- A journey crosses service boundaries — that's what makes it a journey,
  not a feature.

## Cross-capability journeys

A journey may span multiple capabilities. This is **expected and
desirable** — it reveals the integration points between capability
domains.

- The sequence diagram is the primary artefact that reveals integration
  points — which services in which capability domains need to
  communicate, what data crosses the boundary, and in what order.
- Cross-capability communication in sequences is exclusively async
  events via the Event Bus.
- When a journey spans capabilities, flag cross-capability integration
  points explicitly in the completion signal.

## Journey priority and dependencies

- Journey inventory (step 6) is the prioritised backlog.
- Priority respects capability dependencies — you cannot model JRN-003
  (Mortgage) until JRN-001 (Account Opening) establishes the Customer
  and Account entities.
- Each journey grows the central model. Later journeys add fields to
  existing entities rather than inventing parallel entities.

## Intra-journey feedback loops

If step 12 (API contracts/sequences) reveals a missing entity or field:

1. Document the gap in the API contract artefact.
2. Return to step 10 (data model) and add the entity/field.
3. Update steps 11-12 to reflect the change.
4. Continue forward from the point of discovery.

Log every feedback loop in PIPELINE-STATE.md for the active journey.

## Cross-journey feedback

When journey N reveals that a central-model entity from journey N-k
needs restructuring:

1. Create a refinement entry in PIPELINE-STATE.md under "Open refinement
   tickets".
2. Link the source and target journeys.
3. The Capability Lead prioritises the refinement.
4. Do NOT block — continue with the current journey.

## Anti-patterns

- Modelling a journey without reading the foundation artefacts first.
- Inventing entities not reachable from any journey phase.
- Treating a journey as a UI flow — journeys are headless system flows;
  UI is a separate concern.
- Skipping the alternative or exception paths because they "aren't needed
  yet" — they reveal edge-case service boundaries.
