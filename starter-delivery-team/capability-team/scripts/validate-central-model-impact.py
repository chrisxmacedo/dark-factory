#!/usr/bin/env python3
"""
Check whether a journey's central-model contributions affect previously
stable journeys.

When journey N adds fields to an entity or changes a service's owned
entities, prior journeys' API contracts, sequence diagrams, and event
catalogues may now be inconsistent. This script lists the affected
prior-journey artefacts so the Capability Lead can open a refinement
ticket in PIPELINE-STATE.md.

This is a DETECTION tool. It does not modify artefacts. It does not
block a gate — cross-journey refinements are scheduled, not blocking
(see defect-handling.md).

Usage: python3 validate-central-model-impact.py <journey-slug>

Exit codes:
    0 — no impact detected
    0 — impact detected (still 0; this is informational, not a gate)
    2 — usage / inputs missing
"""

import json
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"


def load_journey_data_model(slug):
    path = MODELS / slug / "data-model.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_journey_service_boundaries(slug):
    path = MODELS / slug / "service-boundaries.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def affected_prior_journeys(current_slug, touched_entity_ids, touched_event_ids):
    """List prior journeys whose artefacts reference the touched IDs."""
    impacts = []
    if not MODELS.exists():
        return impacts
    for journey_dir in sorted(MODELS.iterdir()):
        if not journey_dir.is_dir():
            continue
        if journey_dir.name == current_slug:
            continue
        # Scan all JSON files in the journey for references
        hits = {"entities": [], "events": []}
        for f in journey_dir.rglob("*.json"):
            try:
                text = f.read_text()
            except UnicodeDecodeError:
                continue
            for eid in touched_entity_ids:
                if f'"{eid}"' in text:
                    hits["entities"].append((eid, str(f.relative_to(ARTEFACTS))))
            for evid in touched_event_ids:
                if f'"{evid}"' in text:
                    hits["events"].append((evid, str(f.relative_to(ARTEFACTS))))
        if hits["entities"] or hits["events"]:
            impacts.append((journey_dir.name, hits))
    return impacts


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate-central-model-impact.py <journey-slug>")
        sys.exit(2)

    slug = sys.argv[1]
    journey_dir = MODELS / slug
    if not journey_dir.exists():
        print(f"Journey directory not found: {journey_dir}")
        sys.exit(2)

    dm = load_journey_data_model(slug) or {}
    sb = load_journey_service_boundaries(slug) or {}

    # Entities this journey touches (new + extended)
    touched_entities = set()
    for e in dm.get("new_entities", []):
        if e.get("id"):
            touched_entities.add(e["id"])
    for e in dm.get("entity_extensions", []):
        if e.get("entity_id"):
            touched_entities.add(e["entity_id"])

    # Events this journey publishes
    touched_events = set()
    for svc in sb.get("services", []):
        for ev in svc.get("published_events", []):
            if isinstance(ev, str):
                touched_events.add(ev)

    if not touched_entities and not touched_events:
        print(f"[{slug}] No entity or event touches detected. No impact check needed.")
        return

    impacts = affected_prior_journeys(slug, touched_entities, touched_events)

    print(f"[{slug}] Touched entities: {sorted(touched_entities)}")
    print(f"[{slug}] Touched events:   {sorted(touched_events)}")
    print()

    if not impacts:
        print(f"[{slug}] No prior-journey references detected. Safe to sync.")
        return

    print(f"[{slug}] CROSS-JOURNEY IMPACT — {len(impacts)} prior journey(s) affected:")
    print()
    for prior_slug, hits in impacts:
        print(f"  Prior journey: {prior_slug}")
        for eid, fpath in hits["entities"]:
            print(f"    entity {eid} referenced in {fpath}")
        for evid, fpath in hits["events"]:
            print(f"    event  {evid} referenced in {fpath}")
        print()
    print("Open a refinement in PIPELINE-STATE.md linking the current")
    print("journey to each affected prior journey. This is informational —")
    print("not a Gate 2 blocker.")


if __name__ == "__main__":
    main()
