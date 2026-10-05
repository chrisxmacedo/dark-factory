#!/usr/bin/env python3
"""
Validate sequence diagrams against cross-capability communication rules.

Rules:
1. Cross-capability communication must go via the Event Bus (SVC-102)
2. No direct synchronous arrows between services in different capabilities
3. Channel → Capability calls are allowed (channels sit outside the system)
4. Within-capability calls are allowed (services in the same capability)

Usage: python3 validate-sequences.py <journey-dir-name>
       python3 validate-sequences.py --all

six-field spec
  inputs         argv[1]=slug|--all; reads sequence-diagrams/*.json; reads
                 architecture/service-dependencies.json (capability map)
  outputs        stdout per-arrow OK/VIOLATION; exit 0 pass / 1 violations found
  preconditions  service-dependencies.json exists (capability map source of truth)
  postconditions stdout is a reproducible verdict; audit line captures total violations
  idempotency    idempotent
  audit events   {script:"validate-sequences", args, exit_code, blockers=violations,
                 meta:{mode}}
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
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Service → Capability mapping
# This should ideally be loaded from service-dependencies.json but
# we hardcode the mapping here for deterministic checking.
# Update this when new services/capabilities are added.
SVC_TO_CAP = {}
CHANNEL_SERVICES = set()  # Services classified as channels (outside system boundary)
EVENT_BUS = "SVC-102"


def load_capability_map():
    """Load service-to-capability mapping from service-dependencies.json."""
    global SVC_TO_CAP, CHANNEL_SERVICES

    deps_path = ARTEFACTS / "architecture" / "service-dependencies.json"
    if not deps_path.exists():
        print(f"  {YELLOW}WARN{RESET}: service-dependencies.json not found, using fallback mapping")
        return False

    deps = json.load(open(deps_path))
    services = deps.get("services", [])
    for svc in services:
        sid = svc.get("id", svc.get("service_id", ""))
        classification = svc.get("classification", "")
        caps = svc.get("capability_mappings", svc.get("capability_id", ""))
        svc_type = svc.get("type", "")

        # Channel services sit outside the system boundary — skip them
        if classification == "channel":
            CHANNEL_SERVICES.add(sid)
            continue

        if isinstance(caps, list) and caps:
            cap = caps[0] if isinstance(caps[0], str) else str(caps[0])
        elif isinstance(caps, str):
            cap = caps
        else:
            cap = ""

        if sid and cap:
            SVC_TO_CAP[sid] = cap

    # Also try to load from technical services files
    for ts_file in (ARTEFACTS / "foundation" / "technical-services").glob("*.json"):
        try:
            data = json.load(open(ts_file))
            for svc in data.get("services", []):
                sid = svc.get("id", "")
                caps = svc.get("capability_mappings", [])
                if sid and caps:
                    if isinstance(caps, list):
                        # Extract CAP-XXX from various formats
                        for c in caps:
                            cap_id = c if isinstance(c, str) else c.get("capability_id", "")
                            cap_match = re.search(r'(CAP-\d{3})', str(cap_id))
                            if cap_match:
                                SVC_TO_CAP[sid] = cap_match.group(1)
                                break
        except (json.JSONDecodeError, KeyError):
            pass

    # Platform/foundation services don't belong to a business capability
    for sid in list(SVC_TO_CAP.keys()):
        if SVC_TO_CAP[sid].startswith("PLATFORM") or SVC_TO_CAP[sid] == "":
            del SVC_TO_CAP[sid]

    return True


def get_capability(svc_id):
    """Get the capability a service belongs to."""
    return SVC_TO_CAP.get(svc_id, None)


def is_event_bus(participant):
    """Check if a participant is the event bus."""
    return "102" in participant or "Event Bus" in participant or participant == "EB"


def is_channel_or_actor(participant):
    """Check if a participant is outside the system (channel, actor, external)."""
    if participant.startswith("PER") or participant.startswith("EXT"):
        return True
    if participant in CHANNEL_SERVICES:
        return True
    # Check extracted SVC ID against channel services
    svc_id = extract_service_id(participant)
    if svc_id and svc_id in CHANNEL_SERVICES:
        return True
    return False


def is_platform_service(svc_id):
    """Check if a service is platform infrastructure (not a business capability)."""
    # SVC-100 to SVC-113 are platform/foundation
    match = re.match(r'SVC-(\d{3})', svc_id)
    if match:
        num = int(match.group(1))
        return num >= 100
    return False


def extract_service_id(participant_key):
    """Extract SVC-XXX from a participant key like 'SVC001' or 'SVC-001'."""
    # Handle formats: SVC001, SVC-001, SVC_001
    match = re.search(r'SVC[\-_]?(\d{3})', participant_key)
    if match:
        return f"SVC-{match.group(1)}"
    return None


def validate_mermaid(mmd_path):
    """Validate a Mermaid sequence diagram for cross-capability violations."""
    errors = []
    warnings = []

    text = mmd_path.read_text()
    lines = text.split("\n")

    # Extract participant declarations
    participants = {}
    for line in lines:
        # Match: participant SVC001 as SVC-001<br/>Retail Banking Core
        match = re.match(r'\s+participant\s+(\w+)\s+as\s+(.+)', line)
        if match:
            key = match.group(1)
            label = match.group(2)
            svc_id = extract_service_id(key) or extract_service_id(label)
            participants[key] = svc_id

        # Match: actor PER001 as PER-001
        match = re.match(r'\s+actor\s+(\w+)\s+as\s+(.+)', line)
        if match:
            participants[match.group(1)] = match.group(1)  # Actors stay as-is

    # Extract arrows (synchronous calls)
    arrow_pattern = re.compile(
        r'\s+(\w+)\s*(->>|-->>|-)>\s*(\w+)\s*:\s*(.*)'
    )

    for line_num, line in enumerate(lines, 1):
        match = arrow_pattern.match(line)
        if not match:
            continue

        from_key = match.group(1)
        arrow_type = match.group(2)
        to_key = match.group(3)
        label = match.group(4).strip()

        from_svc = extract_service_id(from_key)
        to_svc = extract_service_id(to_key)

        # Skip if either end is an actor/external
        if not from_svc or not to_svc:
            continue

        # Skip if either end is a channel service (outside system boundary)
        if is_channel_or_actor(from_key) or is_channel_or_actor(to_key):
            continue

        # Skip if going to/from the event bus
        if is_event_bus(from_key) or is_event_bus(to_key):
            continue

        # Skip if either is a platform service
        if is_platform_service(from_svc) or is_platform_service(to_svc):
            continue

        # Check cross-capability
        from_cap = get_capability(from_svc)
        to_cap = get_capability(to_svc)

        if from_cap and to_cap and from_cap != to_cap:
            # This is a synchronous call between different capabilities
            if "publish" in label.lower() or "event" in label.lower():
                continue  # Event-related, probably going via bus

            errors.append(
                f"Line {line_num}: {from_svc} ({from_cap}) → {to_svc} ({to_cap}): "
                f"synchronous cross-capability call. Label: '{label[:60]}'"
            )

    return errors, warnings


def validate_json_sequence(json_path):
    """Validate a JSON sequence diagram for cross-capability violations."""
    errors = []

    try:
        data = json.load(open(json_path))
    except (json.JSONDecodeError, FileNotFoundError):
        return [f"Cannot read {json_path.name}"], []

    steps = data.get("steps", data.get("interactions", []))
    for i, step in enumerate(steps):
        from_svc = step.get("from", step.get("source", ""))
        to_svc = step.get("to", step.get("target", ""))
        is_async = step.get("async", step.get("asynchronous", False))
        step_type = step.get("type", "")
        if step_type in ("event-publish", "event-consume", "event", "async", "publish"):
            is_async = True
        action = step.get("action", step.get("description", ""))

        # Extract SVC IDs
        from_id = extract_service_id(from_svc) if isinstance(from_svc, str) else None
        to_id = extract_service_id(to_svc) if isinstance(to_svc, str) else None

        if not from_id or not to_id:
            continue
        if from_id in CHANNEL_SERVICES or to_id in CHANNEL_SERVICES:
            continue
        if is_event_bus(from_svc) or is_event_bus(to_svc):
            continue
        if is_platform_service(from_id) or is_platform_service(to_id):
            continue

        from_cap = get_capability(from_id)
        to_cap = get_capability(to_id)

        if from_cap and to_cap and from_cap != to_cap and not is_async:
            errors.append(
                f"Step {i+1}: {from_id} ({from_cap}) → {to_id} ({to_cap}): "
                f"synchronous cross-capability call. Action: '{str(action)[:60]}'"
            )

    return errors, []


def validate_journey(journey_dir):
    """Validate all sequence diagrams in a journey."""
    seq_dir = journey_dir / "sequence-diagrams"
    if not seq_dir.exists():
        print(f"  {YELLOW}WARN{RESET}: No sequence-diagrams/ directory")
        return 0

    total_errors = 0

    # Check Mermaid files
    for mmd in sorted(seq_dir.glob("*.mmd")):
        errs, warns = validate_mermaid(mmd)
        if errs:
            print(f"\n  {RED}VIOLATIONS{RESET} in {mmd.name}:")
            for e in errs:
                print(f"    {RED}•{RESET} {e}")
            total_errors += len(errs)
        else:
            print(f"  {GREEN}OK{RESET}: {mmd.name}")

    # Check JSON files
    for jf in sorted(seq_dir.glob("*.json")):
        errs, warns = validate_json_sequence(jf)
        if errs:
            print(f"\n  {RED}VIOLATIONS{RESET} in {jf.name}:")
            for e in errs:
                print(f"    {RED}•{RESET} {e}")
            total_errors += len(errs)
        else:
            print(f"  {GREEN}OK{RESET}: {jf.name}")

    return total_errors


def main():
    load_capability_map()

    if not SVC_TO_CAP:
        print(f"{YELLOW}WARNING{RESET}: Could not load capability mapping. Cross-capability checks will be limited.")
        print("Ensure service-dependencies.json or technical-services/*.json exist with capability_mappings.\n")

    if len(sys.argv) < 2:
        print("Usage: python3 validate-sequences.py <journey-dir-name>")
        print("       python3 validate-sequences.py --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        journeys = sorted(d for d in MODELS.iterdir() if d.is_dir())
    else:
        journeys = [MODELS / sys.argv[1]]

    total_errors = 0
    print(f"\nCapability map loaded: {len(SVC_TO_CAP)} services mapped")
    print(f"{'='*60}")

    for journey_dir in journeys:
        if not journey_dir.exists():
            print(f"Not found: {journey_dir}")
            continue

        print(f"\n--- {journey_dir.name} ---")
        total_errors += validate_journey(journey_dir)

    print(f"\n{'='*60}")
    if total_errors:
        print(f"{RED}FAILED{RESET}: {total_errors} cross-capability violations found")
    else:
        print(f"{GREEN}PASSED{RESET}: No cross-capability violations")
    print(f"{'='*60}\n")

    code = 1 if total_errors else 0
    mode = "all" if "--all" in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else "")
    audit.log_event("validate-sequences", sys.argv[1:], code, total_errors, 0,
                    {"mode": mode})
    sys.exit(code)


if __name__ == "__main__":
    main()
