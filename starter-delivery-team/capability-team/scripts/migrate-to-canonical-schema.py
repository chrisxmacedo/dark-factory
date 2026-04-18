#!/usr/bin/env python3
"""
Migrate all journey artefacts to the canonical schema structure.
Maps variant key names to the standard keys defined in the schemas.

This is a one-time migration. After running, all files conform to
the canonical schemas and the parser/generator can use single key names.

Usage: python3 migrate-to-canonical-schema.py --all
       python3 migrate-to-canonical-schema.py <journey-slug>
"""

import json
import re
import sys
from pathlib import Path
from copy import deepcopy

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def load_json(path):
    try:
        return json.load(open(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def migrate_participant_interaction(journey_dir):
    """Standardise participant-interaction.json to canonical schema."""
    path = journey_dir / "participant-interaction.json"
    data = load_json(path)
    if not data:
        return 0

    changes = 0
    canonical = {
        "journey_id": data.get("journey_id", ""),
        "document_version": data.get("document_version", data.get("version", "1.0.0")),
        "status": data.get("status", "Stable"),
        "participants": [],
    }

    participants = data.get("participants", [])
    for p in participants:
        # Standardise participant ID key
        pid = p.get("persona_id", p.get("participant_id", p.get("id", "")))
        pname = p.get("persona_name", p.get("name", pid))

        # Find phase-level data from any key variant
        phases_raw = None
        for key in ["phases", "phase_interactions", "touchpoints", "interactions_by_phase",
                     "interaction_phases", "interactions"]:
            if key in p and isinstance(p[key], list) and p[key]:
                if isinstance(p[key][0], dict):
                    phases_raw = p[key]
                    break

        # Also check for top-level projections (hnw pattern)
        top_projections = p.get("projections", [])
        top_entitlements = p.get("entitlements", [])

        canonical_phases = []

        if phases_raw:
            for pd in phases_raw:
                if not isinstance(pd, dict):
                    continue

                phase_id = pd.get("phase_id", pd.get("phase", pd.get("id", "")))
                # Normalise phase_id to PH-NNN if it's just a number reference
                if phase_id and not phase_id.startswith("PH-"):
                    match = re.search(r'PH-\d{3}', str(phase_id))
                    if match:
                        phase_id = match.group(0)

                # Handle nested interactions
                if "interactions" in pd and isinstance(pd["interactions"], list):
                    all_provided = []
                    all_received = []
                    for interaction in pd["interactions"]:
                        if isinstance(interaction, dict):
                            for v in (interaction.get("data_provided", []),):
                                if isinstance(v, list):
                                    all_provided.extend(v)
                                elif v:
                                    all_provided.append(v)
                            for v in (interaction.get("data_received", interaction.get("data_returned", [])),):
                                if isinstance(v, list):
                                    all_received.extend(v)
                                elif v:
                                    all_received.append(v)
                    data_provided = all_provided
                    data_received = all_received
                else:
                    # Extract data_provided from various keys
                    data_provided = (
                        pd.get("data_provided") or
                        pd.get("information_collected_from_participant") or
                        pd.get("entitlement") or pd.get("entitlements") or
                        pd.get("actions") or pd.get("action") or
                        pd.get("interaction") or []
                    )

                    # Extract data_received from various keys
                    data_received = (
                        pd.get("data_received") or pd.get("data_returned") or
                        pd.get("projection") or pd.get("projections") or
                        pd.get("data_visible") or pd.get("information_surfaced") or
                        pd.get("information_disclosed_to_participant") or
                        pd.get("data_exposed") or pd.get("outcome") or
                        pd.get("data_visibility_rules") or []
                    )

                # Normalise to lists
                if not isinstance(data_provided, list):
                    data_provided = [data_provided] if data_provided else []
                if not isinstance(data_received, list):
                    data_received = [data_received] if data_received else []

                # Normalise items to objects if they're strings
                def normalise_data_items(items):
                    result = []
                    for item in items:
                        if isinstance(item, dict) and "field" in item:
                            result.append(item)
                        elif isinstance(item, dict):
                            result.append(item)
                        elif isinstance(item, str):
                            result.append({"field": item, "entity": "", "type": "string"})
                    return result

                data_provided = normalise_data_items(data_provided)
                data_received = normalise_data_items(data_received)

                # Extract other fields
                actions = pd.get("actions_permitted", pd.get("permitted_actions",
                          pd.get("can_do", [])))
                if not isinstance(actions, list):
                    actions = [actions] if actions else []

                notifications = pd.get("notifications", pd.get("notification_sent",
                                pd.get("notified", pd.get("alerts", []))))
                if not isinstance(notifications, list):
                    notifications = [notifications] if notifications else []

                withheld = pd.get("data_withheld", pd.get("information_withheld",
                           pd.get("data_never_visible", [])))
                if not isinstance(withheld, list):
                    withheld = [withheld] if withheld else []

                canonical_phase = {
                    "phase_id": phase_id,
                    "data_provided": data_provided,
                    "data_received": data_received,
                    "actions_permitted": actions,
                    "notifications": notifications,
                }
                if withheld:
                    canonical_phase["data_withheld"] = withheld

                desc = pd.get("description", pd.get("interaction_type", ""))
                if desc:
                    canonical_phase["description"] = desc

                canonical_phases.append(canonical_phase)

        elif top_projections and isinstance(top_projections, list):
            # hnw pattern — projections at top level
            phases_active = p.get("phases_active", [])
            for proj in top_projections:
                if isinstance(proj, dict):
                    phase_id = proj.get("phase", proj.get("phase_id", ""))
                    canonical_phases.append({
                        "phase_id": phase_id,
                        "data_provided": [],
                        "data_received": proj.get("data_exposed", proj.get("data_visible", [])),
                        "actions_permitted": top_entitlements if isinstance(top_entitlements, list) else [],
                        "notifications": [],
                        "data_withheld": proj.get("data_withheld", []),
                    })

        canonical_participant = {
            "persona_id": pid,
            "persona_name": pname,
            "phases": canonical_phases,
        }

        # Preserve channel if present
        channel = p.get("channel", p.get("channel_access", p.get("channels", "")))
        if channel:
            canonical_participant["channel"] = channel if isinstance(channel, str) else str(channel)

        canonical["participants"].append(canonical_participant)
        if canonical_phases:
            changes += 1

    save_json(path, canonical)
    return changes


def migrate_data_model(journey_dir):
    """Standardise data-model.json — rename 'new_entities' to 'entities'."""
    path = journey_dir / "data-model.json"
    data = load_json(path)
    if not data:
        return 0

    changes = 0

    # Rename new_entities → entities
    if "new_entities" in data and "entities" not in data:
        data["entities"] = data.pop("new_entities")
        changes += 1

    # Standardise entity ID key
    for ent in data.get("entities", []):
        if "entity_id" in ent and "id" not in ent:
            ent["id"] = ent.pop("entity_id")
            changes += 1

    save_json(path, data)
    return changes


def migrate_service_boundaries(journey_dir):
    """Standardise service-boundaries.json."""
    path = journey_dir / "service-boundaries.json"
    data = load_json(path)
    if not data:
        return 0

    changes = 0

    # Rename service_boundaries → services
    if "service_boundaries" in data and "services" not in data:
        data["services"] = data.pop("service_boundaries")
        changes += 1

    for svc in data.get("services", []):
        # Standardise service_id
        if "id" in svc and "service_id" not in svc:
            svc["service_id"] = svc.pop("id")
            changes += 1

        # Ensure consumed_events items are objects
        consumed = svc.get("consumed_events", [])
        normalised = []
        for ce in consumed:
            if isinstance(ce, str):
                normalised.append({"event_id": ce})
                changes += 1
            elif isinstance(ce, dict):
                normalised.append(ce)
        svc["consumed_events"] = normalised

    save_json(path, data)
    return changes


def migrate_event_catalogue(journey_dir):
    """Standardise event-catalogue.json — ensure events are under 'events' key."""
    path = journey_dir / "events" / "event-catalogue.json"
    data = load_json(path)
    if not data:
        return 0

    changes = 0

    # If events aren't under 'events', find them
    if "events" not in data or not data["events"]:
        for k, v in list(data.items()):
            if isinstance(v, list) and v and isinstance(v[0], dict) and ("event_id" in v[0] or "name" in v[0]):
                if k != "events":
                    data["events"] = v
                    del data[k]
                    changes += 1
                break

    # Standardise event fields
    for evt in data.get("events", []):
        if "id" in evt and "event_id" not in evt:
            evt["event_id"] = evt.pop("id")
            changes += 1

        # Ensure payload_schema fields are objects
        ps = evt.get("payload_schema", {})
        if isinstance(ps, dict):
            for fname, fdef in list(ps.items()):
                if isinstance(fdef, str):
                    ps[fname] = {"type": fdef}
                    changes += 1

    save_json(path, data)
    return changes


def migrate_journey(journey_slug):
    journey_dir = MODELS / journey_slug
    if not journey_dir.exists():
        return

    print(f"\n  {journey_slug}:")
    total = 0

    c = migrate_participant_interaction(journey_dir)
    if c: print(f"    participant-interaction: {c} changes")
    total += c

    c = migrate_data_model(journey_dir)
    if c: print(f"    data-model: {c} changes")
    total += c

    c = migrate_service_boundaries(journey_dir)
    if c: print(f"    service-boundaries: {c} changes")
    total += c

    c = migrate_event_catalogue(journey_dir)
    if c: print(f"    event-catalogue: {c} changes")
    total += c

    if total == 0:
        print(f"    {GREEN}already canonical{RESET}")
    else:
        print(f"    {YELLOW}{total} total changes{RESET}")

    return total


def main():
    all_mode = "--all" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args and not all_mode:
        print("Usage: python3 migrate-to-canonical-schema.py --all")
        sys.exit(1)

    if all_mode:
        journeys = sorted(d.name for d in MODELS.iterdir() if d.is_dir())
    else:
        journeys = args

    print(f"{'='*60}")
    print(f"Migrating {len(journeys)} journeys to canonical schema")
    print(f"{'='*60}")

    total = 0
    for slug in journeys:
        total += migrate_journey(slug) or 0

    print(f"\n{'='*60}")
    print(f"Migration complete: {total} total changes across {len(journeys)} journeys")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
