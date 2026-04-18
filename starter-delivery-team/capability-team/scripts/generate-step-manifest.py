#!/usr/bin/env python3
"""
Generate a per-step data manifest for a journey. Cross-references
journey phases with API contracts, event catalogues, data models,
participant interactions, and sequence diagrams to produce a complete
view of data at every step:

- Input data (what the participant provides)
- Output data (what is returned to the participant)
- Data produced (entities created/modified, fields set)
- Events published (with full payload field tracing)
- Events consumed (from other capabilities, with field mapping)
- Data lineage (which field from step N feeds step N+M)

Output: artefacts/models/{journey}/step-manifest.json

Usage: python3 generate-step-manifest.py <journey-slug>
       python3 generate-step-manifest.py --all
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

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
    fields = {}
    for f in entity_data.get("fields", []):
        name = f.get("name", "")
        if name:
            fields[name] = {
                "type": f.get("type", ""),
                "required": f.get("required", True),
                "validation": f.get("validation_rule", f.get("validation", "")),
                "computed_from": f.get("computed_from", None),
            }
    return fields


def build_entity_map():
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


def extract_api_schemas(api_dir):
    """Extract all endpoint request/response schemas from API contracts."""
    endpoints = {}
    if not api_dir or not api_dir.exists():
        return endpoints

    for api_file in sorted(api_dir.glob("*.json")):
        data = load_json(api_file)
        if not data:
            continue

        capability = data.get("info", {}).get("title", api_file.stem)
        schemas = data.get("components", {}).get("schemas", {})

        for path, methods in data.get("paths", {}).items():
            for method, op in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue

                key = f"{method.upper()} {path}"
                endpoint = {
                    "method": method.upper(),
                    "path": path,
                    "capability": capability,
                    "summary": op.get("summary", ""),
                    "request_fields": {},
                    "response_fields": {},
                }

                # Extract request body fields
                req = op.get("requestBody", {})
                if req:
                    for ct, ct_def in req.get("content", {}).items():
                        schema = ct_def.get("schema", {})
                        # Resolve $ref
                        ref = schema.get("$ref", "")
                        if ref and ref.startswith("#/components/schemas/"):
                            schema_name = ref.split("/")[-1]
                            schema = schemas.get(schema_name, schema)
                        props = schema.get("properties", {})
                        required = schema.get("required", [])
                        for fname, fdef in props.items():
                            if isinstance(fdef, dict):
                                endpoint["request_fields"][fname] = {
                                    "type": fdef.get("type", fdef.get("format", "string")),
                                    "required": fname in required,
                                    "description": fdef.get("description", ""),
                                }
                            else:
                                endpoint["request_fields"][fname] = {
                                    "type": str(fdef), "required": fname in required, "description": "",
                                }
                        break

                # Extract response fields
                for code, resp in op.get("responses", {}).items():
                    if code.startswith("2"):
                        for ct, ct_def in resp.get("content", {}).items():
                            schema = ct_def.get("schema", {})
                            ref = schema.get("$ref", "")
                            if ref and ref.startswith("#/components/schemas/"):
                                schema_name = ref.split("/")[-1]
                                schema = schemas.get(schema_name, schema)
                            props = schema.get("properties", {})
                            for fname, fdef in props.items():
                                if isinstance(fdef, dict):
                                    endpoint["response_fields"][fname] = {
                                        "type": fdef.get("type", fdef.get("format", "string")),
                                        "description": fdef.get("description", ""),
                                    }
                                else:
                                    endpoint["response_fields"][fname] = {
                                        "type": str(fdef), "description": "",
                                    }
                            break
                        break

                endpoints[key] = endpoint

    return endpoints


def match_sequence_steps_to_phase(seq_steps, phase_id):
    """Find sequence diagram steps belonging to a phase."""
    matched = []
    for step in seq_steps:
        phase_ref = str(step.get("phase", step.get("journey_phase", "")))
        if phase_id in phase_ref:
            matched.append(step)
    return matched


def extract_data_from_step_label(label):
    """Extract field names and API calls mentioned in a sequence step label."""
    fields = set()
    apis = []

    # Extract {field_name, field_name} patterns
    brace_matches = re.findall(r'\{([^}]+)\}', label)
    for match in brace_matches:
        for field in match.split(","):
            field = field.strip().split(":")[0].strip().split("=")[0].strip()
            if field and not field.startswith("/") and len(field) < 50:
                fields.add(field)

    # Extract API call patterns
    api_matches = re.findall(r'(GET|POST|PUT|PATCH|DELETE)\s+(/\S+)', label)
    for method, path in api_matches:
        apis.append({"method": method, "path": path})

    return fields, apis


def extract_participant_data(participant_interaction, phase_id):
    """Extract what each participant sees and can do at this phase.
    Handles multiple structural variants found across journeys."""
    result = {}
    if not participant_interaction:
        return result

    for participant in participant_interaction.get("participants", []):
        pid = participant.get("id", participant.get("persona_id",
              participant.get("participant_id", "")))
        pname = participant.get("persona_name", participant.get("name", pid))
        if not pid:
            continue

        # Check for top-level projections/entitlements (hnw pattern)
        top_projections = participant.get("projections", [])
        top_entitlements = participant.get("entitlements", [])
        top_notifications = participant.get("notifications", [])

        if top_projections and isinstance(top_projections, list) and top_projections and isinstance(top_projections[0], dict):
            # projections is phase-keyed at top level
            for proj in top_projections:
                if not isinstance(proj, dict):
                    continue
                ref = str(proj.get("phase", proj.get("phase_id", "")))
                if phase_id in ref:
                    result[pid] = {
                        "data_visible": proj.get("data_exposed", proj.get("data_visible", [])),
                        "actions_permitted": [],
                        "notifications": [],
                        "data_withheld": proj.get("data_withheld", []),
                    }
                    if proj.get("projection_note"):
                        result[pid]["note"] = proj["projection_note"]
                    # Add entitlements if they exist at top level
                    if top_entitlements:
                        result[pid]["actions_permitted"] = top_entitlements if isinstance(top_entitlements, list) else [top_entitlements]
                    # Add notifications for this phase
                    if isinstance(top_notifications, list):
                        for notif in top_notifications:
                            if isinstance(notif, dict) and phase_id in str(notif.get("phase", "")):
                                result[pid]["notifications"].append(notif)
                    break
            if pid in result:
                continue

        # Try multiple keys for phase-level data
        phases_data = None
        phases_key = None
        for key in ["phases", "phase_interactions", "touchpoints", "interactions_by_phase",
                     "interaction_phases", "interactions"]:
            if key in participant:
                phases_data = participant[key]
                phases_key = key
                break

        # Some journeys have "phases" as a list of IDs AND "touchpoints" as the detail
        if isinstance(phases_data, list) and phases_data and isinstance(phases_data[0], str):
            # phases is just IDs — look for touchpoints as the detail
            for alt_key in ["touchpoints", "interaction_phases", "phase_interactions"]:
                if alt_key in participant and alt_key != phases_key:
                    alt_data = participant[alt_key]
                    if isinstance(alt_data, list) and alt_data and isinstance(alt_data[0], dict):
                        phases_data = alt_data
                        phases_key = alt_key
                        break

        if phases_data is None:
            continue

        # Handle list of strings (just phase IDs, no detail)
        if isinstance(phases_data, list) and phases_data and isinstance(phases_data[0], str):
            if phase_id in phases_data:
                result[pid] = {
                    "data_visible": [],
                    "actions_permitted": [],
                    "notifications": [],
                    "note": "Phase listed but no detail structure",
                }
            continue

        # Handle list of dicts (most common)
        if isinstance(phases_data, list):
            for pd in phases_data:
                if not isinstance(pd, dict):
                    continue

                # Handle nested interactions_by_phase: {phase_id, interactions: [...]}
                if "interactions" in pd and isinstance(pd["interactions"], list):
                    nested_ref = str(pd.get("phase_id", pd.get("phase", "")))
                    if phase_id in nested_ref:
                        all_projection = []
                        all_entitlement = []
                        all_notifications = []
                        for interaction in pd["interactions"]:
                            if isinstance(interaction, dict):
                                if interaction.get("data_received"):
                                    all_projection.append(interaction["data_received"])
                                if interaction.get("data_returned"):
                                    all_projection.append(interaction["data_returned"])
                                if interaction.get("data_provided"):
                                    all_entitlement.append(interaction["data_provided"])
                                if interaction.get("action"):
                                    all_entitlement.append(interaction["action"])
                                if interaction.get("notification"):
                                    all_notifications.append(interaction["notification"])
                            elif isinstance(interaction, str):
                                all_entitlement.append(interaction)
                        result[pid] = {
                            "data_visible": all_projection,
                            "actions_permitted": all_entitlement,
                            "notifications": all_notifications,
                        }
                    continue

                ref = str(pd.get("phase_id", pd.get("phase", "")))
                if phase_id not in ref:
                    continue

                # Extract projection/visibility — try many key names
                projection = (
                    pd.get("projection") or pd.get("projections") or
                    pd.get("data_visible") or pd.get("sees") or
                    pd.get("information_surfaced") or pd.get("data_visibility_rules") or
                    pd.get("data_shown") or pd.get("data_received") or
                    pd.get("data_returned") or pd.get("outcome") or
                    pd.get("information_disclosed_to_participant") or []
                )

                # Extract entitlements/actions
                entitlement = (
                    pd.get("entitlement") or pd.get("entitlements") or
                    pd.get("actions") or pd.get("can_do") or
                    pd.get("permitted_actions") or pd.get("action") or
                    pd.get("data_provided") or pd.get("interaction") or
                    pd.get("information_collected_from_participant") or []
                )

                # Extract notifications
                notifications = (
                    pd.get("notifications") or pd.get("notified") or
                    pd.get("notification_sent") or pd.get("alerts") or []
                )

                # Extract withheld data (important for tipping-off etc.)
                withheld = (
                    pd.get("information_withheld") or pd.get("data_withheld") or
                    pd.get("data_never_visible") or []
                )

                # Normalise to lists
                def to_list(v):
                    if isinstance(v, list):
                        return v
                    if isinstance(v, dict):
                        return [v]
                    if isinstance(v, str) and v:
                        return [v]
                    return []

                entry = {
                    "data_visible": to_list(projection),
                    "actions_permitted": to_list(entitlement),
                    "notifications": to_list(notifications),
                }
                if withheld:
                    entry["data_withheld"] = to_list(withheld)

                # Also pull description if present
                desc = pd.get("description", pd.get("interaction_type", ""))
                if desc:
                    entry["interaction_description"] = desc

                result[pid] = entry

        # Handle dict keyed by phase ID
        elif isinstance(phases_data, dict):
            if phase_id in phases_data:
                pd = phases_data[phase_id]
                if isinstance(pd, dict):
                    result[pid] = {
                        "data_visible": pd.get("projection", pd.get("sees", [])),
                        "actions_permitted": pd.get("entitlement", pd.get("actions", [])),
                        "notifications": pd.get("notifications", []),
                    }

        # Also check top-level participant fields for global visibility rules
        global_visible = participant.get("data_visible_to_persona", [])
        global_withheld = participant.get("data_never_visible_to_persona", [])
        if pid in result:
            if global_visible and not result[pid].get("data_visible"):
                result[pid]["data_visible_global"] = global_visible
            if global_withheld:
                result[pid]["data_withheld_global"] = global_withheld
        elif global_visible or global_withheld:
            # Participant has global rules but no phase-specific data
            result[pid] = {
                "data_visible": [],
                "actions_permitted": [],
                "notifications": [],
            }
            if global_visible:
                result[pid]["data_visible_global"] = global_visible
            if global_withheld:
                result[pid]["data_withheld_global"] = global_withheld

    return result


def get_events_for_phase(event_catalogue, phase_id):
    """Get all events published during a phase."""
    events = []
    all_events = event_catalogue.get("events", [])
    if not all_events:
        for k, v in event_catalogue.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                all_events.extend(v)

    for evt in all_events:
        jp = str(evt.get("journey_phase", ""))
        if phase_id in jp:
            payload = {}
            ps = evt.get("payload_schema", {})
            if isinstance(ps, dict):
                for fname, fdef in ps.items():
                    if isinstance(fdef, dict):
                        payload[fname] = {
                            "type": fdef.get("type", "string"),
                            "derived_from": fdef.get("derived_from", ""),
                        }
                    else:
                        payload[fname] = {"type": str(fdef), "derived_from": ""}

            events.append({
                "event_id": evt.get("event_id", ""),
                "name": evt.get("name", ""),
                "source_service": evt.get("source_service", ""),
                "topic": evt.get("topic", ""),
                "payload": payload,
            })
    return events


def get_consumed_events_for_phase(service_boundaries, phase_id, all_seq_steps):
    """Determine which events are consumed during a phase based on sequence diagram steps."""
    consumed = []
    if not service_boundaries:
        return consumed

    phase_steps = match_sequence_steps_to_phase(all_seq_steps, phase_id)
    event_refs = set()
    for step in phase_steps:
        label = str(step.get("label", step.get("action", step.get("description", ""))))
        evts = re.findall(r'(EVT-\d{3})', label)
        event_refs.update(evts)
        # Also check for "consume" / "receives" patterns
        if any(w in label.lower() for w in ["consume", "receives", "delivered", "event bus"]):
            step_type = step.get("type", "")
            if step_type in ("async", "event"):
                evts_in_label = re.findall(r'(EVT-\d{3})', label)
                event_refs.update(evts_in_label)

    services = service_boundaries.get("services", service_boundaries.get("service_boundaries", []))
    for svc in services:
        for ce in svc.get("consumed_events", []):
            if isinstance(ce, dict):
                eid = ce.get("event_id", ce.get("id", ""))
                if eid in event_refs:
                    consumed.append({
                        "event_id": eid,
                        "name": ce.get("name", ""),
                        "consuming_service": svc.get("service_id", svc.get("id", "")),
                        "maps_to": ce.get("maps_to", {}),
                    })

    return consumed


def build_data_lineage(steps):
    """Track which fields produced at step N are consumed at step N+M."""
    lineage = {}
    produced_fields = {}  # field_name → step_index where first produced

    for i, step in enumerate(steps):
        # Fields produced by events at this step
        for evt in step.get("data_flow", {}).get("events_published", []):
            for fname in evt.get("payload", {}).keys():
                if fname not in produced_fields:
                    produced_fields[fname] = {
                        "produced_at_step": step["phase_id"],
                        "produced_by_event": evt.get("name", ""),
                    }

        # Fields produced by API responses at this step
        for api in step.get("data_flow", {}).get("api_calls_matched", []):
            for fname in api.get("response_fields", {}).keys():
                if fname not in produced_fields:
                    produced_fields[fname] = {
                        "produced_at_step": step["phase_id"],
                        "produced_by_api": f"{api.get('method', '')} {api.get('path', '')}",
                    }

    # Now check which consumed events / API requests use previously produced fields
    for i, step in enumerate(steps):
        step_lineage = []
        for evt in step.get("data_flow", {}).get("events_consumed", []):
            maps_to = evt.get("maps_to", {})
            if isinstance(maps_to, dict):
                fm = maps_to.get("field_mapping", {})
                for source_field in fm.keys():
                    if source_field in produced_fields:
                        step_lineage.append({
                            "field": source_field,
                            "from": produced_fields[source_field],
                            "to": f"consumed by {evt.get('consuming_service', '')} at {step['phase_id']}",
                        })

        for api in step.get("data_flow", {}).get("api_calls_matched", []):
            for fname in api.get("request_fields", {}).keys():
                if fname in produced_fields:
                    step_lineage.append({
                        "field": fname,
                        "from": produced_fields[fname],
                        "to": f"sent to {api.get('method', '')} {api.get('path', '')} at {step['phase_id']}",
                    })

        if step_lineage:
            lineage[step["phase_id"]] = step_lineage

    return lineage


def generate_manifest(journey_slug, entity_map):
    journey_dir = MODELS / journey_slug

    detail = load_json(journey_dir / "journey-detail.json")
    if not detail:
        return None

    data_model = load_json(journey_dir / "data-model.json")
    event_catalogue = load_json(journey_dir / "events" / "event-catalogue.json") or {}
    service_boundaries = load_json(journey_dir / "service-boundaries.json")
    participant_interaction = load_json(journey_dir / "participant-interaction.json")

    # Load all sequence diagram steps
    all_seq_steps = []
    seq_dir = journey_dir / "sequence-diagrams"
    if seq_dir.exists():
        for sf in seq_dir.glob("*.json"):
            sd = load_json(sf)
            if sd:
                all_seq_steps.extend(sd.get("steps", sd.get("interactions", [])))

    # Load API schemas
    api_schemas = extract_api_schemas(journey_dir / "api-contracts")

    phases = detail.get("phases", [])
    manifest = {
        "journey_id": detail.get("journey_id", ""),
        "journey_name": detail.get("name", ""),
        "generated_from": "journey-detail + data-model + event-catalogue + service-boundaries + api-contracts + participant-interaction + sequence-diagrams",
        "steps": [],
    }

    for phase in phases:
        phase_id = phase.get("id", phase.get("phase_id", ""))
        phase_name = phase.get("name", "")

        # Sequence steps for this phase
        phase_seq_steps = match_sequence_steps_to_phase(all_seq_steps, phase_id)

        # Extract data mentioned in sequence step labels
        seq_fields = set()
        seq_apis = []
        for seq_step in phase_seq_steps:
            label = str(seq_step.get("label", seq_step.get("action", seq_step.get("description", ""))))
            fields, apis = extract_data_from_step_label(label)
            seq_fields.update(fields)
            seq_apis.extend(apis)

        # Match API calls to full schemas
        api_calls_matched = []
        seen_keys = set()
        for api_ref in seq_apis:
            method = api_ref["method"]
            path = api_ref["path"]
            # Try exact match then normalised match
            key = f"{method} {path}"
            if key in api_schemas and key not in seen_keys:
                api_calls_matched.append(api_schemas[key])
                seen_keys.add(key)
            else:
                norm_path = re.sub(r'\{[^}]+\}', '{id}', path)
                for ak, av in api_schemas.items():
                    norm_ak = re.sub(r'\{[^}]+\}', '{id}', ak)
                    if f"{method} {norm_path}" == norm_ak and ak not in seen_keys:
                        api_calls_matched.append(av)
                        seen_keys.add(ak)
                        break
                else:
                    api_calls_matched.append(api_ref)

        # Events published
        phase_events = get_events_for_phase(event_catalogue, phase_id)

        # Events consumed
        consumed_events = get_consumed_events_for_phase(service_boundaries, phase_id, all_seq_steps)

        # Participant data
        participant_data = extract_participant_data(participant_interaction, phase_id)

        # Entities modified — from events and service boundaries
        entities_modified = []
        if service_boundaries:
            services = service_boundaries.get("services", service_boundaries.get("service_boundaries", []))
            for evt in phase_events:
                for svc in services:
                    sid = svc.get("service_id", svc.get("id", ""))
                    if sid == evt.get("source_service", ""):
                        for ent_id in svc.get("owned_entities", []):
                            clean = re.match(r'(ENT-\d{3})', str(ent_id))
                            if clean and clean.group(1) not in entities_modified:
                                entities_modified.append(clean.group(1))

        # Entity field details for modified entities
        entity_details = {}
        for eid in entities_modified:
            if eid in entity_map:
                entity_details[eid] = {
                    "name": entity_map[eid]["name"],
                    "field_count": len(entity_map[eid]["fields"]),
                    "fields": entity_map[eid]["fields"],
                }

        step = {
            "phase_id": phase_id,
            "phase_name": phase_name,
            "description": phase.get("description", ""),
            "actors": phase.get("actors", []),
            "governance_rules": phase.get("governance_rules", []),
            "data_flow": {
                "participant_input": {
                    pid: pdata.get("actions_permitted", [])
                    for pid, pdata in participant_data.items()
                } if participant_data else {},
                "participant_output": {
                    pid: pdata.get("data_visible", [])
                    for pid, pdata in participant_data.items()
                } if participant_data else {},
                "participant_notifications": {
                    pid: pdata.get("notifications", [])
                    for pid, pdata in participant_data.items()
                } if participant_data else {},
                "api_calls_matched": api_calls_matched,
                "events_published": phase_events,
                "events_consumed": consumed_events,
                "entities_modified": entities_modified,
                "entity_field_details": entity_details,
                "data_fields_in_sequence": list(seq_fields) if seq_fields else [],
            },
        }

        manifest["steps"].append(step)

    # Build data lineage across steps
    manifest["data_lineage"] = build_data_lineage(manifest["steps"])

    # Summary stats
    total_apis = sum(len(s["data_flow"]["api_calls_matched"]) for s in manifest["steps"])
    total_events_pub = sum(len(s["data_flow"]["events_published"]) for s in manifest["steps"])
    total_events_con = sum(len(s["data_flow"]["events_consumed"]) for s in manifest["steps"])
    total_entities = len(set(e for s in manifest["steps"] for e in s["data_flow"]["entities_modified"]))
    apis_with_req = sum(1 for s in manifest["steps"] for a in s["data_flow"]["api_calls_matched"] if a.get("request_fields"))
    apis_with_resp = sum(1 for s in manifest["steps"] for a in s["data_flow"]["api_calls_matched"] if a.get("response_fields"))

    manifest["summary"] = {
        "total_steps": len(manifest["steps"]),
        "total_api_calls": total_apis,
        "apis_with_request_schema": apis_with_req,
        "apis_with_response_schema": apis_with_resp,
        "total_events_published": total_events_pub,
        "total_events_consumed": total_events_con,
        "total_entities_modified": total_entities,
        "data_lineage_connections": sum(len(v) for v in manifest["data_lineage"].values()),
    }

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

    entity_map = build_entity_map()

    print(f"\n{'='*60}")
    print(f"Generating step manifests ({len(entity_map)} entities indexed)")
    print(f"{'='*60}\n")

    generated = 0
    for slug in journeys:
        m = generate_manifest(slug, entity_map)
        if m:
            s = m["summary"]
            print(f"  {GREEN}OK{RESET}: {slug} — {s['total_steps']} steps, "
                  f"{s['total_api_calls']} APIs ({s['apis_with_request_schema']} req/{s['apis_with_response_schema']} resp), "
                  f"{s['total_events_published']} events pub, {s['total_events_consumed']} consumed, "
                  f"{s['data_lineage_connections']} lineage links")
            generated += 1

    print(f"\n{'='*60}")
    print(f"Generated {generated} step manifests")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
