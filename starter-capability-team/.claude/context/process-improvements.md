# Process improvements

Generalised learnings from running the capability pipeline. These inform
the scaffold scripts, validation scripts, team instructions, and review
gates.

## Pre-creation enforcement (scaffold)

1. **Global sequential IDs** — phase IDs (PH-NNN), entity IDs (ENT-NNN),
   and event IDs (EVT-NNN) must be globally sequential across all
   journeys. Journey-specific prefixes (PY-, BPH-, FR-PH-, ENT-B,
   EVT-P) cause inconsistency and break cross-references. The scaffold
   script scans all existing artefacts to assign the next available IDs.

2. **Template files** — the scaffold pre-creates template JSON files with
   the correct structure. The modelling agent overwrites them with full
   content but keeps the structure. This prevents structural drift
   between journeys.

3. **Manifest file** — each journey directory contains a `_manifest.json`
   with the ID ranges and format rules. The modelling agent MUST read
   this before producing any artefact.

4. **Format rules in manifest** — `owned_entities` must be plain ID
   strings (`"ENT-012"`), never annotated (`"ENT-012 (Name)"`). Same
   for `published_events` and `service_ids`. This enables deterministic
   validation.

## Post-creation validation

5. **Central model sync verification** — after updating the central
   event catalogue or service map, the agent must read the file back to
   confirm the update was applied. Silent write failures have been
   observed where the event catalogue was not updated despite the agent
   reporting success.

6. **Cross-capability communication validation** — sequence diagrams
   (both JSON and Mermaid) must be validated for synchronous calls
   between services in different capabilities. The only valid
   cross-capability communication is async events via the Event Bus.
   The `validate-sequences.py` script enforces this deterministically.

7. **Entity ownership validation** — every entity in the data model must
   have exactly one owning service declared in `service-boundaries.json`.
   Unowned entities are a bug.

8. **Sequence diagram pairing** — every `.json` sequence diagram must
   have a corresponding `.mmd` Mermaid file, and vice versa. Unpaired
   files indicate incomplete work.

## Architectural classifications

9. **Channel services are not capabilities** — services that act as a
   frontend/BFF layer (e.g. Digital Channels, Online Banking, Mobile
   App) sit outside the system boundary. They are allowed to call any
   capability's REST API synchronously. They must be classified as
   `channel` in service-dependencies.json, not mapped to a capability.

10. **Notification is a platform service** — notification delivery is
    shared infrastructure, not a business capability. If it were a
    capability, every other capability would need async events just to
    send a notification, which adds unnecessary complexity. Classify as
    `foundation` in service-dependencies.json.

11. **Platform services are invisible to cross-capability checks** —
    calls to/from platform services (IAM, Event Bus, Audit, Observability,
    Notifications, etc.) are not cross-capability violations. They are
    shared infrastructure.

## Error handling

12. **Agents must report failures immediately** — if a file write fails,
    a central model update conflicts, or a tool call errors, the agent
    stops and reports to the Programme Lead. No silent continuation with
    incomplete artefacts. No partial central model updates.

13. **Validation runs after every journey** — the Programme Lead runs
    `validate-journey.py` and `validate-sequences.py` after each journey
    model is completed. Failures block Gate 2.

## Script inventory

| Script | Purpose | When to run |
|--------|---------|-------------|
| `scaffold-journey.py` | Creates directory, manifest, templates with next available IDs | Before modelling each journey |
| `validate-journey.py` | Checks files, ID formats, entity ownership, central model sync | After modelling each journey |
| `validate-sequences.py` | Checks sequence diagrams for cross-capability sync violations | After modelling each journey |
