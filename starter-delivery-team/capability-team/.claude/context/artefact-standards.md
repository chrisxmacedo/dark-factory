# Artefact standards

Read by: all teams

## Format

- All artefacts are **JSON files** stored in the `artefacts/` directory
- No PDFs, no slide decks, no Word documents, no diagrams-only
- Every artefact must validate against its JSON schema in `artefacts/schemas/`
- If a schema doesn't exist yet, create it before creating the artefact

### Exceptions to JSON-only rule

Two artefact types use specialised formats alongside their JSON source:

- **C4 architecture model**: `architecture/c4-workspace.dsl` — Structurizr DSL format.
  This is the single source of truth for all C4 diagrams (System Context, Container,
  Component). The DSL is a living artefact that grows across all phases. It references
  JSON artefacts by path but is not itself JSON.
- **Sequence diagrams**: `models/{journey}/sequence-diagrams/*.mmd` — Mermaid format.
  Generated from the structured JSON sequence data (`sequence-diagrams/*.json`).
  The JSON is the source of truth; the `.mmd` file is the renderable representation.
  Both files must be committed together and kept in sync.

## Naming

- Directories: lowercase, hyphens for spaces (e.g. `settlement-instruction/`)
- Files: lowercase, hyphens, descriptive (e.g. `journey-detail.json`, not `step7.json`)
- Entity names: PascalCase in JSON (e.g. `"SettlementInstruction"`)
- Field names: snake_case in JSON (e.g. `"settlement_date"`)
- Use the same name for the same concept everywhere — `Institution` in the
  data model must be `Institution` in the API contract and all consuming artefacts

## Version control

- Commit after every artefact change
- Never batch multiple artefacts into one commit
- Commit message format: `{PROJECT_KEY}-{key}: {step} — {what changed}`
  - Example: `MODEL-42: Step 10 — Add priority_level field to SettlementInstruction`
- Push immediately after every commit

## Artefact lifecycle

| Status | Meaning |
|--------|---------|
| Draft | Being produced by the team |
| In review | Submitted for review — no further changes until review completes |
| Approved | Passed review — no structural changes without a new review |
| Baselined | Frozen (Phase A + B only) — changes require formal change request |
| Stable | Phase C journey model complete and internally consistent |
| Revised | Previously stable/approved, now being updated due to feedback |

## Central model aggregation

After completing a journey (Phase C):
1. Check if any entities from this journey already exist in `central-model/entities/`
2. If new: copy the entity file
3. If existing: merge new fields, resolve conflicts with the Architect
4. Record every merge decision as a Jira comment
5. Update `central-model/service-map.json` with new services
6. Update `central-model/event-catalogue.json` with new events

## Design decisions

Every non-obvious design choice must be recorded in the artefact:

```json
{
  "design_decisions": [
    {
      "id": "DD-001",
      "decision": "Use event-sourced ledger for settlement positions",
      "rationale": "Audit trail required by regulation X, CQRS enables...",
      "alternatives_considered": ["Mutable state with audit log", "..."],
      "rejected_because": "Cannot guarantee consistency under..."
    }
  ]
}
```

## Vocabulary

| Term | Definition | Stable over |
|------|-----------|-------------|
| Capability | A business domain grouping containing one or more independently deployable technical services that together fulfil that domain's responsibilities. Owns its data (one or more databases/schemas), publishes event contracts, and exposes a REST API surface. Cross-capability communication is exclusively asynchronous events — no capability calls another capability's API. See `context/architecture-specification.md` for the full definition. | Decades — changes only when mandate changes |
| Sub-capability | A subdivision of a capability. May be promoted to a separate service if it meets 3+ of 4 promotion criteria (distinct participants, distinct legal framework, distinct lifecycle, distinct data domain). Promoted sub-capabilities become separate services but remain inside the capability boundary. | Years |
| Shared sub-capability | A sub-capability concept that appears in more than one capability. Each capability owns its own representation — no shared data models. Synchronisation through domain events. | Years |
| Technical service | An independently deployable component within a capability — an API, worker, processor, or scheduled job. Services within the same capability may share databases and communicate freely. Services in different capabilities communicate only via async events. | Project lifetime |
| Governance rule | A legislative, regulatory, or policy constraint that bounds a capability — who can do what, under what conditions, with what approvals. | Changes with legislation/policy |
| Persona | A person or organisational role that interacts with capabilities. Internal (employees) or external (counterparties, regulators, public). | Years |
| Channel | How a persona type accesses the system — each channel has its own auth model, rate limits, data projection, and audit requirements. | Project lifetime |
| Journey | A complete end-to-end flow of work triggered by a persona interacting with a sub-capability. The unit of iterative modelling in Phase C. A journey may span multiple capabilities — this is expected and reveals integration points between capability domains. **Journeys are design-time specifications** — they define steps, data requirements, and valid transitions, but are not runtime orchestration. Data status within capabilities implicitly represents journey progress. Coordination happens through capabilities reacting to each other's published events. | Modelling cycle |
| Journey phase | A distinct stage within a journey where different actors, rules, or NFRs apply. | Per journey |
| Sequence | The flow of data and control between participants and services during a journey. Expressed as a Mermaid sequence diagram (`.mmd`) derived from structured JSON. A sequence makes cross-capability interactions visible — when a journey spans multiple capabilities, the sequence diagram shows exactly how data moves from one capability's services to another's. | Per journey |
| C4 model | The Structurizr DSL workspace (`c4-workspace.dsl`) containing System Context, Container, and Component diagrams. A living artefact that grows across all phases — Discovery produces L1+L2, Journey Modelling refines L2 and adds L3. | Project lifetime (continuously updated) |
| Participant interaction | What each persona sees (projection), can do (entitlement), and is notified about at each journey phase. | Per journey |
| NFR | Non-functional requirement per journey — latency, throughput, availability, security classification. | Per journey |
| Entity | A data model object derived from journeys. Aggregated into the central model. | Grows with each journey |
| Service boundary | The ownership line around a group of entities — determines which service owns which data. | Per journey, architect decision |
| API contract | OpenAPI specification for a capability's published REST API surface — one contract per capability, not per service. Channels call the capability API; the capability routes internally. Design-time artefact — lives in the repo and CI pipeline. Runtime validation is handled by the application framework. Not used for cross-capability communication (which is events-only). | Per capability (grows with each journey) |
| Event | A fact about what happened (past tense). Published by a capability, consumed by other capabilities via the Event Bus. The sole mechanism for cross-capability communication. Validated at runtime by the Schema Registry. | Per journey |
| Service dependency tier | Build tier (T0 Foundation → T4 Overlay) assigned to each service based on upstream dependencies. Determines build order. | Project lifetime |
| Dependency criticality | Classification of each service-to-service dependency as **hard** (sync, immediate failure if down) or **soft** (async/degradable). Drives blast radius analysis. | Per service pair |
| Observability model | Architecture-level definition of log routing, instrumentation standards, logging schemas by category, and data freshness contracts. Produced at Discovery, consumed by all teams. | Project lifetime (updated as services added) |
| Security model | Architecture-level definition of zero-trust policy, mTLS requirements, data classification levels, network segmentation, and security posture controls. | Project lifetime (updated as services added) |
| service.yaml | Machine-readable manifest per service repo: id, tier, depends_on (with protocol and criticality), topics_produced, topics_consumed, data_classification, secrets with rotation_days. The authoritative source for the zero-trust policy engine. | Per service |
| Environment specification | Defines CI, RC, and prod-parity environment configurations derived from the service catalogue, dependencies, and security model. Specifies what is real vs stubbed in each environment. | Project lifetime |
| Platform layer | Shared runtime infrastructure that all capabilities depend on: Event Bus, Schema Registry, Observability, Audit Pipeline, Auth, Cache. Principle: share the mechanism, isolate the state. Contains no business logic. | Project lifetime |
| Contract layer | Design-time specification artefacts consumed by channel UIs and AI development agents: API contracts (OpenAPI), event contracts (schemas), journey contracts (process specs). Live in the repo and CI pipeline — not runtime containers, not on C4 diagrams. The Schema Registry is the sole runtime manifestation and sits in the Platform Layer. | Per journey |

## Cross-references

Artefacts reference each other by path and entity name:
- Governance rules reference regulations: `"source.reference": "../../../../starter-regulations/data-protection.json#DP-EU-GDPR"` (from `artefacts/foundation/governance/` up to `templates/` then down into `starter-regulations/`)
- Data model references governance rules: `"governed_by": "governance/monetary-policy.json#rule-3"`
- API contract references data model: `"$ref": "../../../central-model/entities/Institution.json"` (from `artefacts/models/{slug}/api-contracts/` up to `artefacts/central-model/`)

All cross-references must resolve to existing files and fields.

## Stub tracking

Artefacts may be authored as stubs — placeholders where the shape is
agreed but the detail is still being worked out. To stay honest about
what is done versus what still needs work, mark stubs explicitly:

```json
{
  "x-status": "stub",
  "x-todo": "What is missing, who owns completing it, and by when"
}
```

`scripts/validate-completeness.py` counts these markers and surfaces
them as warnings. Stubs are acceptable during iteration; silently
incomplete artefacts are not. When the stub is resolved, delete
`x-status` and `x-todo` — the warning count drops automatically.

Stubs applied to sequence diagrams **must** come in pairs — a `.mmd`
and its matching `.json`. Run `scripts/generate-sequence-json-stubs.py`
after adding any Mermaid stub to ensure the JSON pair is created
(validate-journey fails on orphan Mermaid files).

See `.claude/context/completeness-validation.md` for the full gate
rules.

## Transparency annotations (when applicable)

If the organisation has public accountability obligations, every entity
gains transparency annotations:

```json
{
  "transparency": {
    "public_fields": ["status", "submission_date", "decision"],
    "redacted_fields": ["internal_notes", "officer_id"],
    "delay_rule": "Publish 24 hours after decision",
    "projection": "summary"
  }
}
```

NEVER:
- Create artefacts that don't validate against their schema
- Use different names for the same concept across artefacts
- Commit artefacts with unresolved cross-references
- Merge into the central model without checking for conflicts
- Produce artefacts in any format other than JSON (except C4 DSL and Mermaid as documented)
- Make design decisions without recording the rationale
- Update C4 workspace without verifying it matches the JSON artefacts
- Commit a sequence diagram JSON without its corresponding `.mmd` file
