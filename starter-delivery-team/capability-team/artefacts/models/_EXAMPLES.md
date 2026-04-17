# Journey artefact examples

The scaffold script `scripts/scaffold-journey.py` creates a full set of
template JSON files for a new journey, including `_manifest.json`,
`journey-detail.json`, `data-model.json`, `service-boundaries.json`,
`events/event-catalogue.json`, `participant-interaction.json`, and
`nfr.json`.

This file documents the **shape** of each artefact so a reviewer or a
downstream dev consumer can understand what to expect in
`models/{journey-slug}/` without reading the scaffold script.

## _refinement-brief.md

Produced by the Refinement Team before the scaffold. See
`.claude/agents/refinement-team.md` for the contents and structure.

## _manifest.json

Produced by `scaffold-journey.py`. Contains:
- `journey_id`, `journey_slug`
- `id_rules` — start numbers for PH / ENT / EVT with strict format rules
- `format_rules` — allowed shapes for `owned_entities`, `published_events`,
  `consumed_events`, `service_ids`

## journey-detail.json — step 7

```
{
  "journey_id": "JRN-001",
  "name": "",
  "status": "Draft | Stable | Revised",
  "triggering_persona": "PER-001",
  "capabilities_touched": ["CAP-001"],
  "phases": [
    {
      "id": "PH-001",
      "name": "",
      "description": "",
      "actors": [],
      "services": [],
      "governance_rules": ["GOV-001"],
      "entry_conditions": [],
      "exit_conditions": []
    }
  ],
  "paths": {
    "happy_path": { "description": "", "phases": ["PH-001"] },
    "alternative_paths": [],
    "exception_paths": []
  },
  "design_decisions": []
}
```

## participant-interaction.json — step 8

```
{
  "journey_id": "JRN-001",
  "participants": [
    {
      "persona_id": "PER-001",
      "phases": [
        {
          "phase_id": "PH-001",
          "projection": "Fields visible to this persona in this phase.",
          "entitlements": ["What this persona may do."],
          "notifications": ["Events this persona is notified of."]
        }
      ]
    }
  ]
}
```

## nfr.json — step 9

```
{
  "journey_id": "JRN-001",
  "per_phase_nfrs": [
    {
      "phase_id": "PH-001",
      "latency_p99_ms": 0,
      "throughput_rps": 0,
      "availability": "",
      "security_classification": "public | internal | confidential | regulated"
    }
  ],
  "cross_cutting_nfrs": [],
  "regulatory_slas": [
    {
      "rule_id": "GOV-001",
      "sla": ""
    }
  ]
}
```

## data-model.json — step 10

```
{
  "journey_id": "JRN-001",
  "new_entities": [
    {
      "id": "ENT-001",
      "name": "",
      "description": "",
      "owning_service": "SVC-001",
      "fields": [
        {
          "name": "",
          "type": "",
          "required": true,
          "validation": "",
          "data_classification": "public | internal | confidential | regulated",
          "computed_from": null
        }
      ],
      "relationships": []
    }
  ],
  "referenced_existing_entities": [],
  "entity_extensions": [
    {
      "entity_id": "ENT-000",
      "added_fields": []
    }
  ]
}
```

## service-boundaries.json — step 11

```
{
  "journey_id": "JRN-001",
  "architectural_principle": "Cross-capability communication is exclusively async events. Within a capability, services communicate freely.",
  "services": [
    {
      "service_id": "SVC-001",
      "service_name": "",
      "capability_id": "CAP-001",
      "owned_entities": ["ENT-001"],
      "published_events": ["EVT-001"],
      "consumed_events": [
        {
          "event_id": "EVT-000",
          "name": "",
          "maps_to": {
            "ENT-001.field_a": "payload.field_x"
          }
        }
      ],
      "consumed_apis": [],
      "design_decisions": []
    }
  ]
}
```

## api-contracts/{capability}.openapi.json — step 12

Standard OpenAPI 3.1. One contract **per capability**, not per service.
Response schemas `$ref` entities in `central-model/entities/`.
Projection notes are inline per endpoint.

## sequence-diagrams/{phase-or-path}.json + .mmd — step 12

The JSON is structured data; the `.mmd` is Mermaid text. Both committed
together. See `context/best-practices/sequence-diagrams.md` for the
four-path rule.

## events/event-catalogue.json — step 13

```
{
  "journey_id": "JRN-001",
  "events": [
    {
      "event_id": "EVT-001",
      "name": "ExampleEventCompleted",
      "source_service": "SVC-001",
      "source_entity": "ENT-001",
      "trigger": "",
      "journey_phase": "PH-001",
      "payload_schema": { "type": "object", "properties": {} },
      "derived_from": {
        "payload.field_x": "ENT-001.field_a"
      },
      "consumers": [],
      "ordering_guarantees": "per-aggregate ordered",
      "topic": "",
      "data_classification": "public | internal | confidential | regulated",
      "worm_audit_pipeline": true,
      "retention": "",
      "cloudevents_type": "com.{PROJECT}.ExampleEventCompleted.v1"
    }
  ]
}
```

## evidence/

Populated by the Review Team and Capability Lead:
- `validate-journey.txt`
- `validate-sequences.txt`
- `review-stage2.md`
- `central-model-impact.txt`
- `sync-summary.txt`

Gate 2 requires all five to be present.
