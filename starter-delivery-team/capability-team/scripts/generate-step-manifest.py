#!/usr/bin/env python3
"""
Generate a per-step data manifest for a journey. Cross-references
journey phases with API contracts, event catalogues, and data models
to produce a single view of what data is needed, produced, and
exchanged at each step.

Output: artefacts/models/{journey}/step-manifest.json

Usage: python3 generate-step-manifest.py <journey-slug>
       python3 generate-step-manifest.py --all
"""

import json
import re
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def load_json(path):
    try:
        return json.load(open(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def extract_entity_fields(entity_data):
    """Extract field names and types from an entity definition."""
    fields = {}
    for f in entity_data.get("fields", []):
        name = f.get("name", "")
        if name:
            fields[name] = {
                "type": f.get("type", ""),
                "required": f.get("required", f.get("nullable", "") != True),
                "validation": f.get("validation_rule", f.get("validation", "")),
                "computed_from": f.get("computed_from", None),
            }
    return fields


def build_entity_map():
    """Build entity_id → {name, fields} from central model."""
    entities = {}
    edir = CENTRAL / "entities"
    if edir.exists():
        for f in edir.glob("*.json"):
            if f.name.startswith("_"):
                continue
            data = load_json(f)
            if data:
                eid = data.get("id", data.get("entity_id", ""))
                if eid:
                    entities[eid] = {
                        "name": data.get("name", ""),
                        "fields": extract_entity_fields(data),
                    }

    # Also from journey data models
    for dm in MODELS.rglob("data-model.json"):
        data = load_json(dm)
        if not data:
            continue
        for ent in data.get("entities", data.get("new_entities", [])):
            eid = ent.get("id", ent.get("entity_id", ""))
            if eid and eid not in entities:
                entities[eid] = {
                    "name": ent.get("name", ""),
                    "fields": extract_entity_fields(ent),
                }
    return entities


def extract_events_for_phase(event_catalogue, phase_id):
    """Find events triggered during a specific phase."""
    events = []
    all_events = event_catalogue.get("events", [])
    if not all_events:
        for k, v in event_catalogue.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                all_events.extend(v)

    for evt in all_events:
        jp = evt.get("journey_phase", "")
        if phase_id in str(jp):
            payload_fields = {}
            ps = evt.get("payload_schema", {})
            if isinstance(ps, dict):
                for fname, fdef in ps.items():
                    if isinstance(fdef, dict):
                        payload_fields[fname] = {
                            "type": fdef.get("type", "string"),
                            "derived_from": fdef.get("derived_from", ""),
                        }
                    else:
                        payload_fields[fname] = {"type": str(fdef), "derived_from": ""}

            events.append({
                "event_id": evt.get("event_id", ""),
                "name": evt.get("name", ""),
                "source_service": evt.get("source_service", ""),
                "topic": evt.get("topic", ""),
                "payload_fields": payload_fields,
            })
    return events


def extract_api_endpoints_for_phase(api_contracts_dir, phase_id, sequence_steps):
    """Find API endpoints called during a specific phase from sequence diagrams."""
    endpoints = []

    # Look at sequence diagram steps for this phase
    for step in sequence_steps:
        phase_ref = step.get("phase", step.get("journey_phase", ""))
        if phase_id not in str(phase_ref):
            continue

        label = str(step.get("label", step.get("action", step.get("description", ""))))

        # Extract API call patterns (POST /xxx, GET /xxx)
        api_matches = re.findall(r'(GET|POST|PUT|PATCH|DELETE)\s+(/\S+)', label)
        for method, path in api_matches:
            # Try to find this endpoint in the API contracts
            endpoint_info = {"method": method, "path": path}

            if api_contracts_dir.exists():
                for api_file in api_contracts_dir.glob("*.json"):
                    api = load_json(api_file)
                    if not api:
                        continue
                    paths = api.get("paths", {})
                    # Normalise path for matching
                    for api_path, methods in paths.items():
                        normalised = re.sub(r'\{[^}]+\}', '{id}', api_path)
                        path_normalised = re.sub(r'\{[^}]+\}', '{id}', path)
                        if normalised == path_normalised and method.lower() in methods:
                            op = methods[method.lower()]
                            # Extract request body schema
                            req_body = op.get("requestBody", {})
                            if req_body:
                                content = req_body.get("content", {})
                                for ct, ct_def in content.items():
                                    schema = ct_def.get("schema", {})
                                    props = schema.get("properties", {})
                                    required = schema.get("required", [])
                                    endpoint_info["request_fields"] = {
                                        fname: {
                                            "type": fdef.get("type", ""),
                                            "required": fname in required,
                                        }
                                        for fname, fdef in props.items()
                                    }

                            # Extract response schema
                            responses = op.get("responses", {})
                            for code, resp in responses.items():
                                if code.startswith("2"):
                                    content = resp.get("content", {})
                                    for ct, ct_def in content.items():
                                        schema = ct_def.get("schema", {})
                                        props = schema.get("properties", {})
                                        endpoint_info["response_fields"] = {
                                            fname: {"type": fdef.get("type", "")}
                                            for fname, fdef in props.items()
                                        }
                                    break

                            endpoint_info["capability"] = api.get("info", {}).get("title", api_file.stem)

            endpoints.append(endpoint_info)

    return endpoints


def extract_entities_modified(data_model, service_boundaries, phase_id, events):
    """Determine which entities are created/modified during a phase."""
    entities_modified = []

    # From events — which entities are the source
    for evt in events:
        source = evt.get("source_service", "")
        # Check service boundaries for owned entities
        if service_boundaries:
            services = service_boundaries.get("services", service_boundaries.get("service_boundaries", []))
            for svc in services:
                sid = svc.get("service_id", svc.get("id", ""))
                if sid == source or source in str(sid):
                    for ent_id in svc.get("owned_entities", []):
                        if isinstance(ent_id, str):
                            clean_id = re.match(r'(ENT-\d{3})', ent_id)
                            if clean_id:
                                entities_modified.append(clean_id.group(1))

    return list(set(entities_modified))


def generate_manifest(journey_slug):
    """Generate the per-step data manifest for a journey."""
    journey_dir = MODELS / journey_slug

    detail = load_json(journey_dir / "journey-detail.json")
    if not detail:
        print(f"  {YELLOW}SKIP{RESET}: No journey-detail.json for {journey_slug}")
        return None

    data_model = load_json(journey_dir / "data-model.json")
    event_catalogue = load_json(journey_dir / "events" / "event-catalogue.json") or {}
    service_boundaries = load_json(journey_dir / "service-boundaries.json")
    participant_interaction = load_json(journey_dir / "participant-interaction.json")
    entity_map = build_entity_map()

    # Load sequence diagram steps
    all_seq_steps = []
    seq_dir = journey_dir / "sequence-diagrams"
    if seq_dir.exists():
        for sf in seq_dir.glob("*.json"):
            sd = load_json(sf)
            if sd:
                all_seq_steps.extend(sd.get("steps", sd.get("interactions", [])))

    api_dir = journey_dir / "api-contracts"

    phases = detail.get("phases", [])
    manifest = {
        "journey_id": detail.get("journey_id", ""),
        "journey_name": detail.get("name", ""),
        "generated": "deterministic — from journey artefacts",
        "steps": [],
    }

    for phase in phases:
        phase_id = phase.get("id", phase.get("phase_id", ""))
        phase_name = phase.get("name", "")

        # Events published during this phase
        phase_events = extract_events_for_phase(event_catalogue, phase_id)

        # API endpoints called during this phase
        phase_apis = extract_api_endpoints_for_phase(api_dir, phase_id, all_seq_steps)

        # Entities modified during this phase
        entities_modified = extract_entities_modified(data_model, service_boundaries, phase_id, phase_events)

        # Participant projections for this phase
        projections = {}
        if participant_interaction:
            for participant in participant_interaction.get("participants", []):
                pid = participant.get("id", participant.get("persona_id", ""))
                phases_data = participant.get("phases", participant.get("phase_interactions", []))
                if isinstance(phases_data, list):
                    for pd in phases_data:
                        if not isinstance(pd, dict):
                            continue
                        ref = pd.get("phase_id", pd.get("phase", ""))
                        if phase_id in str(ref):
                            projections[pid] = {
                                "sees": pd.get("projection", pd.get("projections", pd.get("data_visible", []))),
                                "can_do": pd.get("entitlement", pd.get("entitlements", pd.get("actions", []))),
                            }
                elif isinstance(phases_data, dict):
                    if phase_id in phases_data:
                        pd = phases_data[phase_id]
                        projections[pid] = {
                            "sees": pd.get("projection", []),
                            "can_do": pd.get("entitlement", []),
                        }

        # Entity field details for modified entities
        entity_details = {}
        for eid in entities_modified:
            if eid in entity_map:
                entity_details[eid] = {
                    "name": entity_map[eid]["name"],
                    "fields": entity_map[eid]["fields"],
                }

        step = {
            "phase_id": phase_id,
            "phase_name": phase_name,
            "description": phase.get("description", ""),
            "actors": phase.get("actors", []),
            "governance_rules": phase.get("governance_rules", []),
            "data_flow": {
                "api_calls": phase_apis,
                "events_published": phase_events,
                "entities_modified": entities_modified,
                "entity_field_details": entity_details,
                "participant_projections": projections,
            },
        }

        manifest["steps"].append(step)

    # Write manifest
    out_path = journey_dir / "step-manifest.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main():
    all_mode = "--all" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args and not all_mode:
        print("Usage: python3 generate-step-manifest.py <journey-slug>")
        print("       python3 generate-step-manifest.py --all")
        sys.exit(1)

    if all_mode:
        journeys = sorted(d.name for d in MODELS.iterdir() if d.is_dir())
    else:
        journeys = args

    print(f"\n{'='*60}")
    print("Generating per-step data manifests")
    print(f"{'='*60}\n")

    generated = 0
    for slug in journeys:
        manifest = generate_manifest(slug)
        if manifest:
            steps = len(manifest["steps"])
            events = sum(len(s["data_flow"]["events_published"]) for s in manifest["steps"])
            apis = sum(len(s["data_flow"]["api_calls"]) for s in manifest["steps"])
            print(f"  {GREEN}OK{RESET}: {slug} — {steps} steps, {events} events, {apis} API calls")
            generated += 1

    print(f"\n{'='*60}")
    print(f"Generated {generated} step manifests")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
