# Review Team

Triggered by: journey model submitted for review (all steps 7-13 complete)
Spawned by: Programme Lead
Shuts down when: review verdict delivered (approved / revisions required)

Pipeline stage: **All phases — cross-cutting quality gate**
Confidence goal: "This journey model is correct, consistent, complete, machine-readable, and architecturally compliant"

The Review Team provides independent quality assurance. It is spawned
after the Journey Modelling Team signals JOURNEY MODEL COMPLETE. The
Review Team does not produce artefacts — it validates them.

## Review process

The review has two stages: deterministic (scripted) and reasoning-based.

### Stage 1: Deterministic validation (scripted)

Run the validation scripts against the journey directory. These are
non-negotiable gates — any failure blocks the review.

```bash
# From the project root
python3 scripts/validate-journey.py {journey-slug}
python3 scripts/validate-sequences.py {journey-slug}
```

**validate-journey.py checks:**
- All required files exist (journey-detail, participant-interaction,
  nfr, data-model, service-boundaries, event-catalogue, API contracts,
  sequence diagram pairs)
- ID format compliance (PH-NNN, ENT-NNN, EVT-NNN — no prefixes)
- Format compliance (owned_entities are plain ID strings, no annotations)
- Entity ownership (every entity has exactly one owner in service-boundaries)
- Central model sync (entities exist in central-model/entities/,
  events exist in central event catalogue, services exist in service map)

**validate-sequences.py checks:**
- No synchronous cross-capability calls in sequence diagrams
- Channel services and platform services are excluded from checks
- Both JSON and Mermaid files are validated

If either script fails, the verdict is **revisions required** with the
script output as the issues list. Do not proceed to Stage 2.

### Stage 2: Reasoning-based review

If Stage 1 passes, review the journey model against these dimensions:

#### 1. Architectural compliance
- Cross-capability communication is exclusively async events
- Personas interact through channels, never directly with services
- API contracts are per-capability, not per-service
- Sequence diagrams show Channel → Capability API, not Channel → Service
- Data transformations are specified (derived_from, computed_from, maps_to)

#### 2. Internal consistency
- Phase references in participant-interaction match journey-detail phases
- Entity references in service-boundaries match data-model entities
- Event references in service-boundaries match event-catalogue events
- NFR phase references match journey-detail phases
- API contract schemas reference data-model entity fields correctly

#### 3. Cross-artefact consistency
- Entity names match across data-model, service-boundaries, central model
- Event names match across event-catalogue, service-boundaries, central model
- Service IDs match the service-dependencies and service-catalogue
- Governance rule references point to real rules in governance files
- No naming conflicts with previously completed journeys

#### 4. Completeness
- Journey has happy path + at least one alternative + at least one exception
- All participant types from journey-detail appear in participant-interaction
- All entities in data-model have fields with types and validation rules
- All events have payload schemas, consumers, topics, WORM flags
- Every file is complete — no empty arrays, no stubs, no placeholders

#### 5. Buildability
- Can a development team consume each artefact and build from it?
- Are field types precise enough for code generation?
- Are API contracts complete enough for stub generation?
- Do sequence diagrams specify enough detail for integration tests?

## Error handling

If the Review Team encounters a failure reading files or running scripts:
1. Report the failure to the Programme Lead
2. Do not issue a verdict — the review is incomplete

## Signal to Programme Lead

```
REVIEW COMPLETE.
Journey: [{journey-id} {journey-name}]
Verdict: [approved | revisions required]

Stage 1 — Deterministic:
  validate-journey.py: [pass | fail — error count]
  validate-sequences.py: [pass | fail — violation count]

Stage 2 — Reasoning:
  Architectural compliance: [pass | [count] issues]
  Internal consistency: [pass | [count] issues]
  Cross-artefact consistency: [pass | [count] issues]
  Completeness: [pass | [count] issues]
  Buildability: [pass | [count] issues]

Issues (if any):
  - [severity]: [description] — [file] — [suggestion]
  ...
```

If verdict is "revisions required", the journey returns to the
Journey Modelling Team with the issues list. The Programme Lead
spawns the Journey Modelling Team again with the issues as input.
The cycle repeats until a clean review is received.
