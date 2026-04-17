# Sequence diagram best practices

Read by: Journey Modelling Team (step 12)

## Format — JSON source, Mermaid render

- The sequence is expressed in structured JSON
  (`sequence-diagrams/*.json`) — the **source of truth**.
- A Mermaid `.mmd` file is produced alongside (`sequence-diagrams/*.mmd`)
  as the renderable representation.
- Both files must be committed together and kept in sync.
- `validate-journey.py` checks that every `.json` has a matching `.mmd`
  and vice versa.

## The only four communication paths

There are exactly four ways a service can be reached. A sequence diagram
must only show these:

1. **Channel → Capability API** — sync REST. The channel calls the
   capability's published REST API.
2. **Event Bus → Capability** — async event consumed by a capability's
   event consumer. The sole mechanism for cross-capability communication.
3. **Service → Service (within the same capability)** — direct method
   call, shared DB, internal REST/gRPC, internal queue. Internal
   implementation detail.
4. **Service → Platform service** — any service may call IAM, Audit,
   Observability, Cache, Schema Registry, Notifications.

No other paths exist. `validate-sequences.py` checks for sync
cross-capability violations.

## Personas never call services directly

In sequence diagrams:

- Show `Persona → Channel → Capability API`
- Never `Persona → Service`
- Never `Persona → Capability API` (persona must use a channel)
- A credit analyst using an internal tool is using a channel.

## Show capability boundaries, not service IDs

- Show `Channel → CAP-002 API` not `Channel → SVC-005`.
- Internal routing (capability API to service) is an L3 concern,
  outside the sequence diagram.
- Within a capability, show service-to-service calls if they are
  relevant to the journey — but these are internal detail.

## Every phase produces at least one sequence

Each journey phase must have at least one sequence diagram pair (JSON
+ Mermaid) showing the call and event flow for that phase.

Cross-capability journeys need sequences that make the event flow
between capabilities explicit — these are the primary integration-design
input.

## Anti-patterns

- Sync arrows across capability boundaries (blocked by
  `validate-sequences.py`).
- Personas drawn calling services or capabilities directly.
- JSON updated without regenerating the `.mmd`.
- Sequences that hide the Event Bus — cross-capability events should
  travel through an explicit Event Bus participant, not arrow-hopping
  from publisher to consumer.
