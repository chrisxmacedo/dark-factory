#!/usr/bin/env python3
"""
Generate placeholder sequence-diagram JSON stubs that pair with the
alt-path.mmd / exception-path.mmd Mermaid stubs previously seeded.

validate-journey.py requires every .mmd in sequence-diagrams/ to have
a matching .json. These JSON stubs carry x-status: "stub" so the
completeness validator flags them for the review team to refine.

Idempotent: only writes files that do not already exist.

six-field spec
  inputs         no argv; reads every journey's sequence-diagrams/*.mmd
  outputs        writes matching sequence-diagrams/<stem>.json stub where missing;
                 stdout per-file summary + totals
  preconditions  artefacts/models/ exists
  postconditions every .mmd file has a paired .json file (stubbed if it did not)
  idempotency    idempotent — only creates missing files
  audit events   {script:"generate-sequence-json-stubs", args, exit_code:0,
                 meta:{created, skipped}}
"""

import json
import sys
from pathlib import Path

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402


def journey_id_from_detail(detail_path: Path) -> str:
    if not detail_path.exists():
        return "JRN-000"
    try:
        d = json.load(detail_path.open())
        # Various shapes observed across models
        jid = d.get("journey_id") or d.get("id") or ""
        if not jid and isinstance(d.get("journey"), dict):
            jid = d["journey"].get("id") or d["journey"].get("journey_id") or ""
        return jid or "JRN-000"
    except Exception:
        return "JRN-000"


def stub_payload(stem: str, journey_id: str, journey_slug: str) -> dict:
    kind = {
        "alt-path": "Alternative Path",
        "exception-path": "Exception Path",
    }.get(stem, "Path")

    seq_prefix = {
        "alt-path": "ALT",
        "exception-path": "EXC",
    }.get(stem, "STUB")

    return {
        "$schema": "sequence-diagram-schema-v1",
        "id": f"SEQ-{journey_id.replace('JRN-', '')}-{seq_prefix}-STUB",
        "name": f"{journey_id} — {journey_slug}: {kind} (STUB — review team to complete)",
        "journey_id": journey_id,
        "journey_phase": "TBD",
        "x-status": "stub",
        "x-todo": (
            "Review team to replace placeholder actors with real "
            "PER-XXX / CAP-XXX / SVC-XXX IDs, flesh out the step narrative, "
            "and remove x-status:stub once complete."
        ),
        "description": (
            f"Placeholder {kind.lower()} for {journey_id}. The paired Mermaid "
            f"stub outlines the shape; this JSON must be authored by the "
            f"capability team responsible for the journey."
        ),
        "participants": [
            {"id": "PER-XXX", "name": "Persona (TBD)", "type": "actor"},
            {"id": "SVC-XXX", "name": "Channel Service (TBD)", "type": "service"},
            {"id": "SVC-XXX", "name": "Capability Service (TBD)", "type": "service"},
            {"id": "SVC-102", "name": "Event Bus", "type": "infrastructure"},
        ],
        "steps": [
            {
                "step": 1,
                "phase": "TBD",
                "from": "PER-XXX",
                "to": "SVC-XXX",
                "action": f"Initiate {kind.lower()} (TBD)",
                "description": (
                    "STUB — replace with the specific trigger and payload "
                    "for this variant."
                ),
                "async": False,
            }
        ],
        "notes": [
            f"STUB file — pairs with {stem}.mmd.",
            "Not yet architecturally reviewed.",
            "Will be picked up by the capability team owning this journey.",
        ],
    }


def main() -> int:
    created = 0
    skipped = 0

    for journey_dir in sorted(MODELS.iterdir()):
        if not journey_dir.is_dir():
            continue
        seq_dir = journey_dir / "sequence-diagrams"
        if not seq_dir.exists():
            continue

        journey_slug = journey_dir.name
        journey_id = journey_id_from_detail(journey_dir / "journey-detail.json")

        for mmd in sorted(seq_dir.glob("*.mmd")):
            paired_json = mmd.with_suffix(".json")
            if paired_json.exists():
                skipped += 1
                continue
            payload = stub_payload(mmd.stem, journey_id, journey_slug)
            paired_json.write_text(json.dumps(payload, indent=2) + "\n")
            created += 1
            print(f"created: {paired_json.relative_to(ARTEFACTS.parent)}")

    print(f"\nCreated {created} stub JSON files; {skipped} already existed.")
    audit.log_event("generate-sequence-json-stubs", sys.argv[1:], 0, 0, 0, {
        "created": created,
        "skipped": skipped,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
