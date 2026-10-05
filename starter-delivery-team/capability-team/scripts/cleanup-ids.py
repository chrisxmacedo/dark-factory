#!/usr/bin/env python3
"""
Deterministic post-write cleanup. Strips annotations from ID fields
in service-boundaries.json (owned_entities, published_events, etc.)

Runs after the agent writes files, before validation.

six-field spec
  inputs         argv[1]=journey-slug; reads artefacts/models/<slug>/service-boundaries.json
  outputs        rewrites service-boundaries.json with annotations stripped; stdout summary
  preconditions  journey directory exists; service-boundaries.json is valid JSON
  postconditions no string in owned_entities / published_events / consumed_events_ids
                 contains "(" or whitespace annotations
  idempotency    idempotent — second run is a no-op
  audit events   {script:"cleanup-ids", args, exit_code:0, meta:{fixed}}
"""

import json
import re
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def clean_id_string(s):
    """Extract plain ID from annotated string like 'ENT-012 (Name)' or 'EVT-020 (EventName)'."""
    if not isinstance(s, str):
        return s
    # Match ENT-NNN, EVT-NNN, SVC-NNN, PH-NNN patterns
    match = re.match(r'^((?:ENT|EVT|SVC|PH)-\d{3})', s)
    if match:
        return match.group(1)
    return s


def clean_array(arr):
    """Clean all strings in an array."""
    return [clean_id_string(item) if isinstance(item, str) else item for item in arr]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cleanup-ids.py <journey-dir-name>")
        sys.exit(1)

    journey_slug = sys.argv[1]
    journey_dir = MODELS / journey_slug

    sb_path = journey_dir / "service-boundaries.json"
    if not sb_path.exists():
        print("No service-boundaries.json found")
        sys.exit(0)

    sb = json.load(open(sb_path))
    fixed = 0

    services = sb.get("services", sb.get("service_boundaries", []))
    for svc in services:
        for field in ["owned_entities", "published_events", "consumed_events_ids"]:
            if field in svc and isinstance(svc[field], list):
                original = svc[field][:]
                svc[field] = clean_array(svc[field])
                if svc[field] != original:
                    fixed += len(original) - sum(1 for a, b in zip(original, svc[field]) if a == b)

    if fixed > 0:
        with open(sb_path, "w") as f:
            json.dump(sb, f, indent=2)
        print(f"{GREEN}CLEANED{RESET}: {fixed} annotated IDs in {sb_path.name}")
    else:
        print(f"{GREEN}OK{RESET}: No annotated IDs found")

    audit.log_event("cleanup-ids", sys.argv[1:], 0, 0, 0, {"fixed": fixed})


if __name__ == "__main__":
    main()
