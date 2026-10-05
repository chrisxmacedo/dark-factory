#!/usr/bin/env python3
"""
Validate a journey model's internal consistency, format compliance,
cross-capability communication rules, and central model alignment.

Usage: python3 validate-journey.py <journey-dir-name>

six-field spec
  inputs         argv[1]=journey-slug; reads artefacts/models/<slug>/** and
                 artefacts/schemas/*.schema.json and artefacts/central-model/**
  outputs        stdout verdict with per-check OK/WARN/ERROR; exit 0 pass / 1 fail
  preconditions  journey directory exists with required artefact files plus
                 at least one API contract and paired .json/.mmd sequence diagrams
  postconditions stdout is a reproducible verdict for the current tree;
                 audit line records exit_code + errors/warnings counts
  idempotency    idempotent — repeated runs on an unchanged tree yield the same verdict
  audit events   {script:"validate-journey", args, exit_code, blockers=errors,
                 warnings, meta:{slug}}
"""

import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import validate as json_validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"
FOUNDATION = ARTEFACTS / "foundation"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

errors = []
warnings = []


def error(msg):
    errors.append(msg)
    print(f"  {RED}ERROR{RESET}: {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  {YELLOW}WARN{RESET}: {msg}")


def ok(msg):
    print(f"  {GREEN}OK{RESET}: {msg}")


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        error(f"Missing file: {path.name}")
        return None
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in {path.name}: {e}")
        return None


# ---------- CHECK 1: Required files ----------

def check_required_files(d):
    print("\n[1] Required files")
    required = [
        "journey-detail.json", "participant-interaction.json", "nfr.json",
        "data-model.json", "service-boundaries.json", "events/event-catalogue.json",
    ]
    for f in required:
        if (d / f).exists():
            ok(f)
        else:
            error(f"Missing: {f}")

    api_dir = d / "api-contracts"
    contracts = list(api_dir.glob("*.json")) if api_dir.exists() else []
    if contracts:
        ok(f"API contracts: {len(contracts)} files")
    else:
        error("No API contracts found")

    seq_dir = d / "sequence-diagrams"
    if seq_dir.exists():
        jsons = {p.stem for p in seq_dir.glob("*.json")}
        mmds = {p.stem for p in seq_dir.glob("*.mmd")}
        paired = jsons & mmds
        if paired:
            ok(f"Sequence diagram pairs: {len(paired)}")
        if jsons - mmds:
            error(f"JSON without Mermaid: {jsons - mmds}")
        if mmds - jsons:
            error(f"Mermaid without JSON: {mmds - jsons}")
    else:
        error("Missing: sequence-diagrams/")


# ---------- CHECK 2: ID format compliance ----------

def check_id_formats(d):
    print("\n[2] ID format compliance")

    # Phase IDs must be PH-NNN
    detail = load_json(d / "journey-detail.json")
    if detail:
        phases = detail.get("phases", [])
        for ph in phases:
            pid = ph.get("id", ph.get("phase_id", ""))
            if not re.match(r'^PH-\d{3}$', pid):
                error(f"Phase ID '{pid}' does not match PH-NNN format")
        if phases and not errors:
            ok(f"Phase IDs: {len(phases)} phases, all PH-NNN")

    # Entity IDs must be ENT-NNN
    dm = load_json(d / "data-model.json")
    if dm:
        entities = dm.get("entities", dm.get("new_entities", []))
        for ent in entities:
            eid = ent.get("id", ent.get("entity_id", ""))
            if not re.match(r'^ENT-\d{3}$', eid):
                error(f"Entity ID '{eid}' does not match ENT-NNN format")
        if entities and not any("Entity ID" in e for e in errors):
            ok(f"Entity IDs: {len(entities)} entities, all ENT-NNN")

    # Event IDs must be EVT-NNN
    evt = load_json(d / "events" / "event-catalogue.json")
    if evt:
        events = evt.get("events", [])
        if not events:
            for k, v in evt.items():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "event_id" in v[0]:
                    events = v
                    break
        for ev in events:
            evid = ev.get("event_id", ev.get("id", ""))
            if not re.match(r'^EVT-\d{3}$', evid):
                error(f"Event ID '{evid}' does not match EVT-NNN format")
        if events and not any("Event ID" in e for e in errors):
            ok(f"Event IDs: {len(events)} events, all EVT-NNN")


# ---------- CHECK 3: Format compliance (no annotations in IDs) ----------

def check_format_compliance(d):
    print("\n[3] Format compliance (strict)")

    sb = load_json(d / "service-boundaries.json")
    if not sb:
        return

    services = sb.get("services", sb.get("service_boundaries", []))
    for svc in services:
        sid = svc.get("service_id", svc.get("id", ""))

        # Check owned_entities are plain IDs
        for ent in svc.get("owned_entities", []):
            if isinstance(ent, str):
                if "(" in ent or " " in ent:
                    error(f"owned_entities in {sid}: '{ent}' has annotations. Use plain ID only.")
            elif isinstance(ent, dict):
                pass  # dict format is acceptable

        # Check published_events are plain IDs or objects
        for evt in svc.get("published_events", []):
            if isinstance(evt, str) and ("(" in evt or " " in evt):
                error(f"published_events in {sid}: '{evt}' has annotations. Use plain ID only.")

    if not any("annotations" in e for e in errors):
        ok("No annotated IDs in service-boundaries")


# ---------- CHECK 4: Entity ownership ----------

def check_entity_ownership(d):
    print("\n[4] Entity ownership")

    dm = load_json(d / "data-model.json")
    sb = load_json(d / "service-boundaries.json")
    if not dm or not sb:
        return

    entities = dm.get("entities", dm.get("new_entities", []))
    entity_ids = {e.get("id", e.get("entity_id", "")) for e in entities}

    owned = set()
    services = sb.get("services", sb.get("service_boundaries", []))
    for svc in services:
        for ent in svc.get("owned_entities", []):
            if isinstance(ent, str):
                clean = re.match(r'(ENT-\S+)', ent)
                owned.add(clean.group(1) if clean else ent)
            elif isinstance(ent, dict):
                owned.add(ent.get("entity_id", ent.get("id", "")))

    unowned = entity_ids - owned
    if unowned:
        error(f"Entities without owner: {unowned}")
    else:
        ok(f"All {len(entity_ids)} entities have owners")


# ---------- CHECK 5: Cross-capability communication rules ----------

def check_cross_capability_rules(d):
    print("\n[5] Cross-capability communication rules")

    sb = load_json(d / "service-boundaries.json")
    if not sb:
        return

    # Load service dependencies to get capability mappings
    deps = load_json(ARTEFACTS / "architecture" / "service-dependencies.json")
    if not deps:
        warn("Cannot check cross-capability rules — service-dependencies.json not found")
        return

    # Build service → capability mapping
    svc_to_cap = {}
    dep_services = deps.get("services", [])
    for svc in dep_services:
        sid = svc.get("id", svc.get("service_id", ""))
        caps = svc.get("capability_mappings", svc.get("capability_id", ""))
        if isinstance(caps, list) and caps:
            svc_to_cap[sid] = caps[0] if isinstance(caps[0], str) else str(caps[0])
        elif isinstance(caps, str):
            svc_to_cap[sid] = caps

    # Check service-boundaries for consumed_apis (synchronous cross-capability calls)
    services = sb.get("services", sb.get("service_boundaries", []))
    violations = []
    for svc in services:
        sid = svc.get("service_id", svc.get("id", ""))
        my_cap = svc_to_cap.get(sid, svc.get("capability_id", ""))

        for api in svc.get("consumed_apis", []):
            target = ""
            if isinstance(api, str):
                # Try to extract service ID
                match = re.search(r'(SVC-\d{3})', api)
                target = match.group(1) if match else ""
            elif isinstance(api, dict):
                target = api.get("service_id", api.get("target_service", ""))

            if target and target in svc_to_cap:
                target_cap = svc_to_cap[target]
                if my_cap and target_cap and my_cap != target_cap:
                    # Check if this is flagged as async/event-driven
                    protocol = api.get("protocol", "") if isinstance(api, dict) else ""
                    if protocol not in ("event", "async", "event_driven"):
                        violations.append(f"{sid} ({my_cap}) → {target} ({target_cap}): sync API call across capability boundary")

    if violations:
        for v in violations:
            warn(f"Possible cross-capability sync call: {v}")
    else:
        ok("No cross-capability synchronous API calls detected")


# ---------- CHECK 6: Central model alignment — events ----------

def check_events_in_central(d):
    print("\n[6] Central model — events")

    evt = load_json(d / "events" / "event-catalogue.json")
    central = load_json(CENTRAL / "event-catalogue.json")
    if not evt or not central:
        return

    event_list = evt.get("events", [])
    if not event_list:
        for k, v in evt.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and ("name" in v[0] or "event_id" in v[0]):
                event_list = v
                break

    j_names = {e.get("name", "") for e in event_list}
    central_str = json.dumps(central)
    missing = {n for n in j_names if n and n not in central_str}

    if missing:
        error(f"Events NOT in central catalogue: {missing}")
    else:
        ok(f"All {len(j_names)} events found in central catalogue")


# ---------- CHECK 7: Central model alignment — entities ----------

def check_entities_in_central(d):
    print("\n[7] Central model — entities")

    dm = load_json(d / "data-model.json")
    if not dm:
        return

    entities = dm.get("entities", dm.get("new_entities", []))
    central_dir = CENTRAL / "entities"
    if not central_dir.exists():
        error("central-model/entities/ missing")
        return

    central_files = {p.stem for p in central_dir.glob("*.json")}

    for ent in entities:
        name = ent.get("name", "")
        # PascalCase → kebab-case (handles acronyms like TPP, SAR, KYC)
        # Insert hyphen before: lowercase→uppercase, uppercase→uppercase+lowercase
        kebab = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', name)
        kebab = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '-', kebab)
        kebab = kebab.lower()
        if kebab in central_files:
            ok(f"{name} → {kebab}.json")
        else:
            error(f"{name} not in central-model/entities/ (expected {kebab}.json)")


# ---------- CHECK 8: Central model — service map ----------

def check_service_map(d):
    print("\n[8] Central model — service map")

    sb = load_json(d / "service-boundaries.json")
    smap = load_json(CENTRAL / "service-map.json")
    if not sb or not smap:
        return

    services = sb.get("services", sb.get("service_boundaries", []))
    smap_str = json.dumps(smap)

    for svc in services:
        sid = svc.get("service_id", svc.get("id", ""))
        if sid and sid in smap_str:
            ok(f"{sid} in service map")
        elif sid:
            error(f"{sid} NOT in service map")


# ---------- CHECK: JSON Schema validation ----------

SCHEMA_MAP = {
    "journey-detail.json": "journey-detail.schema.json",
    "participant-interaction.json": "participant-interaction.schema.json",
    "data-model.json": "data-model.schema.json",
    "service-boundaries.json": "service-boundaries.schema.json",
    "nfr.json": "nfr.schema.json",
}

def check_json_schemas(d):
    """Validate artefact files against their canonical JSON schemas."""
    print("\n[9] JSON schema validation")

    if not HAS_JSONSCHEMA:
        warn("jsonschema package not installed — skipping schema validation (pip install jsonschema)")
        return

    schemas_dir = ARTEFACTS / "schemas"
    validated = 0
    schema_errors = 0

    for filename, schema_name in SCHEMA_MAP.items():
        filepath = d / filename
        schema_path = schemas_dir / schema_name

        if not filepath.exists():
            continue
        if not schema_path.exists():
            warn(f"Schema {schema_name} not found in {schemas_dir}")
            continue

        try:
            data = json.load(open(filepath))
            schema = json.load(open(schema_path))
            json_validate(instance=data, schema=schema)
            ok(f"{filename} conforms to {schema_name}")
            validated += 1
        except ValidationError as e:
            # Extract the most useful part of the error
            path = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            msg = str(e.message)[:120]
            error(f"{filename} schema violation at {path}: {msg}")
            schema_errors += 1
        except Exception as e:
            warn(f"{filename} schema check failed: {e}")

    # Also validate event catalogue
    evt_path = d / "events" / "event-catalogue.json"
    evt_schema = schemas_dir / "event-catalogue.schema.json"
    if evt_path.exists() and evt_schema.exists():
        try:
            data = json.load(open(evt_path))
            schema = json.load(open(evt_schema))
            json_validate(instance=data, schema=schema)
            ok(f"events/event-catalogue.json conforms to schema")
            validated += 1
        except ValidationError as e:
            path = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            msg = str(e.message)[:120]
            error(f"events/event-catalogue.json schema violation at {path}: {msg}")
            schema_errors += 1
        except Exception as e:
            warn(f"events/event-catalogue.json schema check failed: {e}")

    if validated and not schema_errors:
        ok(f"{validated} files validated against schemas")


# ---------- MAIN ----------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate-journey.py <journey-dir-name>")
        sys.exit(1)

    name = sys.argv[1]
    d = MODELS / name
    if not d.exists():
        print(f"Not found: {d}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Validating: {name}")
    print(f"{'='*60}")

    check_required_files(d)
    check_id_formats(d)
    check_format_compliance(d)
    check_entity_ownership(d)
    check_cross_capability_rules(d)
    check_events_in_central(d)
    check_entities_in_central(d)
    check_service_map(d)
    check_json_schemas(d)

    print(f"\n{'='*60}")
    if errors:
        print(f"{RED}FAILED{RESET}: {len(errors)} errors, {len(warnings)} warnings")
    elif warnings:
        print(f"{YELLOW}PASSED WITH WARNINGS{RESET}: {len(warnings)} warnings")
    else:
        print(f"{GREEN}PASSED{RESET}: All checks clean")
    print(f"{'='*60}\n")

    code = 1 if errors else 0
    audit.log_event("validate-journey", sys.argv[1:], code, len(errors), len(warnings),
                    {"slug": name})
    sys.exit(code)


if __name__ == "__main__":
    main()
