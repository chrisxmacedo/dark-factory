# Review Team

Triggered by: artefact submitted for review at any phase
Spawned by: Programme Lead
Shuts down when: review verdict delivered (approved / revisions required)

Pipeline stage: **All phases — cross-cutting quality gate**
Confidence goal: "This artefact is correct, consistent, complete, and machine-readable"

The Review Team provides independent quality assurance across all
phases. It is spawned whenever an artefact moves from Draft to
In review. The team does not produce artefacts — it validates them.

## Review dimensions

Every artefact is reviewed against five dimensions:

### 1. Schema compliance
- Does the JSON validate against its schema?
- Are all required fields populated?
- Are enums using the allowed values?
- Are cross-references (e.g. entity names, persona IDs) valid?

### 2. Internal consistency
- Do references within the artefact point to things that exist?
- Are there contradictions (e.g. a field marked "public" in the data
  model but "internal only" in the participant interaction model)?
- Do counts match (e.g. journey phases in the detail match phases
  referenced in the participant interaction)?

### 3. Cross-artefact consistency
- Does this artefact align with previously baselined artefacts?
- Are entity names, persona names, service names used identically?
- Does a new entity in journey B conflict with the same entity
  from journey A in the central model?
- Do governance rules from the foundation constrain this journey
  correctly?
- Does the C4 workspace match the JSON artefacts? Every service in
  `service-map.json` must appear as a container in the DSL. Every
  component must trace to an entity or service boundary. Every portal
  must have relationships to the backend containers its screens reference.

### 4. Completeness
- Are all paths covered (happy path, alternative paths, exception paths)?
- Are all participant types accounted for?
- For screen specs: are all six states addressed (loading, empty,
  happy, partial, error, forbidden)?
- For data models: are all relationships explicit (not implied)?

### 5. Buildability
- Can a development team consume this artefact and build from it
  without ambiguity?
- Are there implicit assumptions that should be explicit?
- Are field types, validation rules, and constraints precise enough
  for an engineer to implement?

### 6. Diagram consistency
- Do sequence diagram `.mmd` files match their corresponding `.json` source?
- Does the C4 workspace DSL render without errors in Structurizr?
- Are C4 diagram levels consistent (L1 personas match `personas/*.json`,
  L2 containers match `service-map.json`, L3 components match
  `service-boundaries.json`)?

## Team composition

### Schema Validator (automated)
- Runs JSON schema validation against every artefact
- Reports: field-level errors, missing required fields, type mismatches
- This is a scripted check, not a reasoning gate

### Consistency Checker (reasoning)
- Cross-references the artefact against all previously baselined artefacts
- Checks naming, entity references, persona references, service references
- Reports conflicts with specific file paths and field names

### Domain Validator (reasoning)
- Asks: "Does this artefact reflect how the institution actually operates?"
- Checks governance rules are applied correctly
- Checks participant access rights make sense
- This requires reading the foundation artefacts for context

## Signal to Programme Lead

```
REVIEW COMPLETE.
Artefact: [{file-path}]
Verdict: [approved | revisions required]
Schema: [pass | fail — detail if fail]
Consistency: [pass | [count] issues found]
Domain: [pass | [count] concerns]
Buildability: [pass | [count] ambiguities]
Diagrams: [pass | [count] inconsistencies — C4/Mermaid]
Issues:
  - [severity]: [description] — [file:field if known] — [suggestion]
  ...
```

If verdict is "revisions required", the artefact returns to the
producing team with the issues list. The Programme Lead does not
advance the artefact until a clean review is received.
