#!/usr/bin/env python3
"""
Scaffold the directory structure, ID registry, and template files for a new journey.
Ensures consistent IDs and structure before the modelling agent starts.

Usage: python3 scaffold-journey.py <journey-id> <journey-slug>
Example: python3 scaffold-journey.py JRN-007 business-loan-origination
"""

import json
import re
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"


def scan_max_id(pattern, search_dir):
    """Scan all JSON files in a directory tree for the highest numeric ID matching a pattern."""
    max_val = 0
    for f in search_dir.rglob("*.json"):
        try:
            text = f.read_text()
            matches = re.findall(pattern, text)
            for m in matches:
                num = int(m)
                max_val = max(max_val, num)
        except (UnicodeDecodeError, ValueError):
            pass
    return max_val


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scaffold-journey.py <journey-id> <journey-slug>")
        sys.exit(1)

    journey_id = sys.argv[1]
    journey_slug = sys.argv[2]
    journey_dir = MODELS / journey_slug

    if journey_dir.exists():
        print(f"Directory already exists: {journey_dir}")
        sys.exit(1)

    # Create directories
    (journey_dir / "api-contracts").mkdir(parents=True)
    (journey_dir / "sequence-diagrams").mkdir(parents=True)
    (journey_dir / "events").mkdir(parents=True)

    # Scan for next available IDs across ALL existing artefacts
    next_phase = scan_max_id(r'"PH-(\d{3})"', MODELS) + 1
    next_entity = scan_max_id(r'"ENT-(\d{3})"', ARTEFACTS) + 1
    next_event = scan_max_id(r'"EVT-(\d{3})"', ARTEFACTS) + 1

    # Write manifest
    manifest = {
        "journey_id": journey_id,
        "journey_slug": journey_slug,
        "id_rules": {
            "phase_format": "PH-{NNN}",
            "phase_start": next_phase,
            "entity_format": "ENT-{NNN}",
            "entity_start": next_entity,
            "event_format": "EVT-{NNN}",
            "event_start": next_event,
            "STRICT": "Use ONLY these formats. No journey-specific prefixes. No parenthetical annotations in ID fields."
        },
        "format_rules": {
            "owned_entities": "Array of plain ID strings: [\"ENT-012\", \"ENT-013\"]. NOT \"ENT-012 (Name)\".",
            "published_events": "Array of plain ID strings: [\"EVT-020\"]. NOT \"EVT-020 (EventName)\".",
            "consumed_events": "Array of objects: [{\"event_id\": \"EVT-020\", \"name\": \"EventName\", ...}].",
            "service_ids": "Plain strings: \"SVC-001\". NOT \"SVC-001 (ServiceName)\"."
        }
    }
    (journey_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))

    # Write journey-detail template
    detail_template = {
        "journey_id": journey_id,
        "name": "",
        "status": "Draft",
        "triggering_persona": "",
        "capabilities_touched": [],
        "phases": [
            {
                "id": f"PH-{next_phase:03d}",
                "name": "",
                "description": "",
                "actors": [],
                "services": [],
                "governance_rules": [],
                "entry_conditions": [],
                "exit_conditions": []
            }
        ],
        "paths": {
            "happy_path": {"description": "", "phases": []},
            "alternative_paths": [],
            "exception_paths": []
        },
        "design_decisions": []
    }
    (journey_dir / "journey-detail.json").write_text(json.dumps(detail_template, indent=2))

    # Write data-model template
    dm_template = {
        "journey_id": journey_id,
        "document_version": "0.1.0",
        "status": "Draft",
        "new_entities": [
            {
                "id": f"ENT-{next_entity:03d}",
                "name": "",
                "description": "",
                "owning_service": "",
                "fields": [],
                "relationships": [],
                "design_decisions": []
            }
        ],
        "referenced_existing_entities": [],
        "entity_extensions": []
    }
    (journey_dir / "data-model.json").write_text(json.dumps(dm_template, indent=2))

    # Write service-boundaries template
    sb_template = {
        "journey_id": journey_id,
        "document_version": "0.1.0",
        "status": "Draft",
        "architectural_principle": "Cross-capability communication is exclusively async events. Within a capability, services communicate freely.",
        "services": [
            {
                "service_id": "",
                "service_name": "",
                "capability_id": "",
                "owned_entities": [],
                "published_events": [],
                "consumed_events": [],
                "consumed_apis": [],
                "design_decisions": []
            }
        ],
        "cross_service_interaction_summary": []
    }
    (journey_dir / "service-boundaries.json").write_text(json.dumps(sb_template, indent=2))

    # Write event-catalogue template
    evt_template = {
        "journey_id": journey_id,
        "document_version": "0.1.0",
        "events": [
            {
                "event_id": f"EVT-{next_event:03d}",
                "name": "",
                "source_service": "",
                "source_entity": "",
                "trigger": "",
                "journey_phase": "",
                "payload_schema": {},
                "consumers": [],
                "ordering_guarantees": "",
                "topic": "",
                "data_classification": "",
                "worm_audit_pipeline": True,
                "retention": "",
                "cloudevents_type": ""
            }
        ]
    }
    (journey_dir / "events" / "event-catalogue.json").write_text(json.dumps(evt_template, indent=2))

    # Write participant-interaction template
    pi_template = {
        "journey_id": journey_id,
        "document_version": "0.1.0",
        "status": "Draft",
        "participants": []
    }
    (journey_dir / "participant-interaction.json").write_text(json.dumps(pi_template, indent=2))

    # Write nfr template
    nfr_template = {
        "journey_id": journey_id,
        "document_version": "0.1.0",
        "status": "Draft",
        "per_phase_nfrs": [],
        "cross_cutting_nfrs": [],
        "regulatory_slas": []
    }
    (journey_dir / "nfr.json").write_text(json.dumps(nfr_template, indent=2))

    print(f"Scaffolded: {journey_dir}")
    print(f"  Next phase ID:  PH-{next_phase:03d}")
    print(f"  Next entity ID: ENT-{next_entity:03d}")
    print(f"  Next event ID:  EVT-{next_event:03d}")
    print(f"  Template files: journey-detail, data-model, service-boundaries,")
    print(f"                  event-catalogue, participant-interaction, nfr")
    print(f"\n  Agent MUST read _manifest.json and use template structures.")


if __name__ == "__main__":
    main()
