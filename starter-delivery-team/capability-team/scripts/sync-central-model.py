#!/usr/bin/env python3
"""
Deterministic central model sync. Copies entities from a journey's
data-model.json to central-model/entities/, appends events to the
central event catalogue, and merges service boundaries into the
central service map.

Replaces the agent's manual central model updates — the most common
source of silent failures.

six-field spec
  inputs         argv[1]=journey-slug; reads artefacts/models/<slug>/{data-model,
                 service-boundaries,events/event-catalogue}.json
  outputs        writes artefacts/central-model/entities/*.json;
                 updates central-model/event-catalogue.json and service-map.json
  preconditions  journey artefacts exist and are schema-valid
  postconditions every entity from the journey is present in central-model/entities/;
                 events appended with journey_origin attribution; service map updated
  idempotency    idempotent on entities (merge by id); append-only on events
                 (duplicates rejected by name match); idempotent on service map
  audit events   {script:"sync-central-model", args, exit_code, meta:{entities,
                 events, service_updates}}
"""

import json
import re
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def pascal_to_kebab(name):
    """Convert PascalCase to kebab-case, handling acronyms."""
    kebab = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', name)
    kebab = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '-', kebab)
    return kebab.lower()


def sync_entities(journey_dir, journey_id):
    """Copy new entities from journey data-model to central-model/entities/."""
    dm_path = journey_dir / "data-model.json"
    if not dm_path.exists():
        print(f"  {YELLOW}SKIP{RESET}: No data-model.json")
        return 0

    dm = json.load(open(dm_path))
    entities = dm.get("entities", dm.get("new_entities", []))
    entities_dir = CENTRAL / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for ent in entities:
        name = ent.get("name", "")
        if not name:
            continue

        kebab = pascal_to_kebab(name)
        path = entities_dir / f"{kebab}.json"

        # Add source_journeys tracking
        central_ent = dict(ent)
        existing_journeys = central_ent.get("source_journeys", [])
        if journey_id not in existing_journeys:
            existing_journeys.append(journey_id)
        central_ent["source_journeys"] = existing_journeys

        if path.exists():
            # Merge: update source_journeys, keep existing content
            existing = json.load(open(path))
            ej = existing.get("source_journeys", [])
            if journey_id not in ej:
                ej.append(journey_id)
                existing["source_journeys"] = ej
                with open(path, "w") as f:
                    json.dump(existing, f, indent=2)
                print(f"  {GREEN}UPDATED{RESET}: {kebab}.json (added {journey_id})")
                count += 1
            else:
                print(f"  {YELLOW}EXISTS{RESET}: {kebab}.json (already has {journey_id})")
        else:
            with open(path, "w") as f:
                json.dump(central_ent, f, indent=2)
            print(f"  {GREEN}CREATED{RESET}: {kebab}.json")
            count += 1

    return count


def sync_events(journey_dir, journey_id):
    """Append journey events to central event catalogue."""
    evt_path = journey_dir / "events" / "event-catalogue.json"
    if not evt_path.exists():
        print(f"  {YELLOW}SKIP{RESET}: No events/event-catalogue.json")
        return 0

    journey_events = json.load(open(evt_path))
    event_list = journey_events.get("events", [])

    # Try nested keys if events array is empty
    if not event_list:
        for k, v in journey_events.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and ("event_id" in v[0] or "name" in v[0]):
                event_list = v
                break

    if not event_list:
        print(f"  {YELLOW}SKIP{RESET}: No events found in catalogue")
        return 0

    catalogue_path = CENTRAL / "event-catalogue.json"
    if catalogue_path.exists():
        catalogue = json.load(open(catalogue_path))
    else:
        catalogue = {"name": "Central Event Catalogue", "events": []}

    # Check which events are already present
    catalogue_str = json.dumps(catalogue)
    new_events = []
    for evt in event_list:
        evt_name = evt.get("name", "")
        evt_id = evt.get("event_id", "")
        if evt_name and evt_name not in catalogue_str:
            new_events.append(evt)
        elif evt_id and evt_id not in catalogue_str:
            new_events.append(evt)

    if new_events:
        key = f"jrn{journey_id.replace('JRN-', '').lstrip('0')}_events"
        catalogue[key] = new_events
        with open(catalogue_path, "w") as f:
            json.dump(catalogue, f, indent=2)
        print(f"  {GREEN}ADDED{RESET}: {len(new_events)} events to central catalogue as {key}")
    else:
        print(f"  {YELLOW}EXISTS{RESET}: All events already in central catalogue")

    return len(new_events)


def sync_service_map(journey_dir, journey_id):
    """Merge service boundaries into central service map."""
    sb_path = journey_dir / "service-boundaries.json"
    if not sb_path.exists():
        print(f"  {YELLOW}SKIP{RESET}: No service-boundaries.json")
        return 0

    sb = json.load(open(sb_path))
    services = sb.get("services", sb.get("service_boundaries", []))

    map_path = CENTRAL / "service-map.json"
    if map_path.exists():
        smap = json.load(open(map_path))
    else:
        smap = {"services": [], "document_version": "0.1.0"}

    smap_str = json.dumps(smap)
    count = 0

    for svc in services:
        sid = svc.get("service_id", svc.get("id", ""))
        if not sid:
            continue

        if sid in smap_str:
            # Service exists — add journey to source_journeys
            # Find the service in the map (could be nested in various ways)
            additions_key = f"jrn{journey_id.replace('JRN-', '').lstrip('0')}_additions"
            if additions_key not in smap_str:
                smap[additions_key + "_" + sid] = {
                    "service_id": sid,
                    "journey": journey_id,
                    "new_owned_entities": svc.get("owned_entities", []),
                    "new_published_events": svc.get("published_events", []),
                }
                count += 1
                print(f"  {GREEN}EXTENDED{RESET}: {sid} with {journey_id} additions")
            else:
                print(f"  {YELLOW}EXISTS{RESET}: {sid} already has {journey_id} additions")
        else:
            # New service — add full entry
            svc_entry = {
                "service_id": sid,
                "service_name": svc.get("service_name", svc.get("name", "")),
                "source_journeys": [journey_id],
                "owned_entities": svc.get("owned_entities", []),
                "published_events": svc.get("published_events", []),
            }
            if "services" not in smap:
                smap["services"] = []
            smap["services"].append(svc_entry)
            count += 1
            print(f"  {GREEN}ADDED{RESET}: {sid} to service map")

    if count > 0:
        with open(map_path, "w") as f:
            json.dump(smap, f, indent=2)

    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sync-central-model.py <journey-dir-name>")
        sys.exit(1)

    journey_slug = sys.argv[1]
    journey_dir = MODELS / journey_slug

    if not journey_dir.exists():
        print(f"Not found: {journey_dir}")
        sys.exit(1)

    # Derive journey ID from manifest or journey-detail
    manifest_path = journey_dir / "_manifest.json"
    if manifest_path.exists():
        manifest = json.load(open(manifest_path))
        journey_id = manifest.get("journey_id", "UNKNOWN")
    else:
        detail_path = journey_dir / "journey-detail.json"
        if detail_path.exists():
            detail = json.load(open(detail_path))
            journey_id = detail.get("journey_id", "UNKNOWN")
        else:
            journey_id = "UNKNOWN"

    print(f"\n{'='*50}")
    print(f"Syncing central model: {journey_slug} ({journey_id})")
    print(f"{'='*50}")

    print(f"\n[Entities]")
    ent_count = sync_entities(journey_dir, journey_id)

    print(f"\n[Events]")
    evt_count = sync_events(journey_dir, journey_id)

    print(f"\n[Service Map]")
    svc_count = sync_service_map(journey_dir, journey_id)

    print(f"\n{'='*50}")
    print(f"Sync complete: {ent_count} entities, {evt_count} events, {svc_count} service updates")
    print(f"{'='*50}\n")

    audit.log_event("sync-central-model", sys.argv[1:], 0, 0, 0, {
        "entities": ent_count,
        "events": evt_count,
        "service_updates": svc_count,
    })


if __name__ == "__main__":
    main()
