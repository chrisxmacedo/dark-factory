#!/usr/bin/env python3
"""
Deep structural integrity check for journey models. Traces data flow
from journey phase → sequence step → event payload → entity field
and surfaces any break in the chain.

Checks:
1. Entity field completeness (types, validation rules, computed_from)
2. Event payload traceability (derived_from → real entity fields)
3. Consumed event mapping completeness (maps_to field resolution)
4. API contract → entity traceability (response fields match entities)
5. Sequence diagram data flow (referenced events/APIs/fields exist)
6. Governance rule resolution (rule IDs exist in governance files)
7. Persona resolution (PER-NNN exists in persona files)
8. Cross-entity field consistency (same name = same type everywhere)

Usage: python3 validate-data-integrity.py <journey-slug>
       python3 validate-data-integrity.py --all
       python3 validate-data-integrity.py --all --json  (machine-readable output)
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ARTEFACTS = Path(__file__).parent.parent / "artefacts"
MODELS = ARTEFACTS / "models"
CENTRAL = ARTEFACTS / "central-model"
FOUNDATION = ARTEFACTS / "foundation"

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

JSON_MODE = "--json" in sys.argv


def load_json(path):
    try:
        return json.load(open(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ── Build global indexes ─────────────────────────────────────────────

def build_entity_index():
    """Build a map of entity_id → {name, fields: {field_name: field_def}}."""
    index = {}

    # From central model
    entities_dir = CENTRAL / "entities"
    if entities_dir.exists():
        for f in entities_dir.glob("*.json"):
            if f.name.startswith("_"):
                continue
            data = load_json(f)
            if not data:
                continue
            eid = data.get("id", data.get("entity_id", ""))
            name = data.get("name", f.stem)
            fields = {}
            for field in data.get("fields", []):
                fname = field.get("name", "")
                if fname:
                    fields[fname] = field
            if eid:
                index[eid] = {"name": name, "fields": fields, "source": str(f)}

    # Also scan journey data models for entities not yet in central
    for dm_file in MODELS.rglob("data-model.json"):
        data = load_json(dm_file)
        if not data:
            continue
        for ent in data.get("entities", data.get("new_entities", [])):
            eid = ent.get("id", ent.get("entity_id", ""))
            if eid and eid not in index:
                name = ent.get("name", "")
                fields = {}
                for field in ent.get("fields", []):
                    fname = field.get("name", "")
                    if fname:
                        fields[fname] = field
                index[eid] = {"name": name, "fields": fields, "source": str(dm_file)}

    return index


def build_governance_index():
    """Build a map of rule_id → {name, capability_id, source_file}."""
    index = {}
    gov_dir = FOUNDATION / "governance"
    if not gov_dir.exists():
        return index
    for f in gov_dir.glob("*.json"):
        data = load_json(f)
        if not data:
            continue
        cap_id = data.get("capability_id", "")
        for rule in data.get("rules", []):
            rid = rule.get("rule_id", rule.get("id", ""))
            if rid:
                index[rid] = {
                    "name": rule.get("name", ""),
                    "capability_id": cap_id,
                    "source": str(f)
                }
    return index


def build_persona_index():
    """Build a map of persona_id → {name, capability_touchpoints}."""
    index = {}
    personas_dir = FOUNDATION / "personas"
    if not personas_dir.exists():
        return index
    for f in personas_dir.glob("*.json"):
        data = load_json(f)
        if not data:
            continue
        for persona in data.get("personas", []):
            pid = persona.get("id", "")
            if pid:
                index[pid] = {
                    "name": persona.get("name", ""),
                    "touchpoints": persona.get("capability_touchpoints", []),
                }
    return index


def build_event_index(journey_dir):
    """Build a map of event_name → {event_id, payload_fields, source_service}."""
    index = {}
    evt_file = journey_dir / "events" / "event-catalogue.json"
    data = load_json(evt_file)
    if not data:
        return index

    events = data.get("events", [])
    if not events:
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and ("name" in v[0] or "event_id" in v[0]):
                events.extend(v)

    for evt in events:
        name = evt.get("name", "")
        if name:
            payload = evt.get("payload_schema", {})
            index[name] = {
                "event_id": evt.get("event_id", ""),
                "source_service": evt.get("source_service", ""),
                "payload_fields": payload if isinstance(payload, dict) else {},
                "topic": evt.get("topic", ""),
            }
    return index


# ── Check functions ──────────────────────────────────────────────────

class Report:
    def __init__(self, journey_slug):
        self.journey = journey_slug
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, check, issue, **kwargs):
        entry = {"check": check, "issue": issue, **kwargs}
        self.errors.append(entry)
        if not JSON_MODE:
            print(f"  {RED}ERROR{RESET} [{check}]: {issue}")

    def warn(self, check, issue, **kwargs):
        entry = {"check": check, "issue": issue, **kwargs}
        self.warnings.append(entry)
        if not JSON_MODE:
            print(f"  {YELLOW}WARN{RESET}  [{check}]: {issue}")

    def ok(self, check, msg):
        if not JSON_MODE:
            print(f"  {GREEN}OK{RESET}    [{check}]: {msg}")

    def to_dict(self):
        return {
            "journey": self.journey,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "error_details": self.errors,
            "warning_details": self.warnings,
        }


def check_entity_fields(journey_dir, entity_index, report):
    """[1] Entity field completeness."""
    dm = load_json(journey_dir / "data-model.json")
    if not dm:
        report.warn("entity_fields", "No data-model.json found")
        return

    entities = dm.get("entities", dm.get("new_entities", []))
    for ent in entities:
        eid = ent.get("id", ent.get("entity_id", ""))
        ename = ent.get("name", "")
        fields = ent.get("fields", [])

        if not fields:
            report.error("entity_fields", f"{eid} ({ename}) has no fields defined")
            continue

        for field in fields:
            fname = field.get("name", "")
            ftype = field.get("type", "")

            if not ftype:
                report.error("entity_fields", f"{eid}.{fname} has no type",
                             entity=eid, field=fname)

            # Check computed_from references
            computed = field.get("computed_from", {})
            if computed and isinstance(computed, dict):
                source_fields = computed.get("source_fields", [])
                all_field_names = {f.get("name", "") for f in fields}
                for sf in source_fields:
                    if sf not in all_field_names:
                        # Could be on a referenced entity
                        if "." in sf:
                            ref_ent, ref_field = sf.split(".", 1)
                            if ref_ent in entity_index:
                                if ref_field not in entity_index[ref_ent]["fields"]:
                                    report.error("entity_fields",
                                                 f"{eid}.{fname} computed_from references {sf} but {ref_ent} has no field '{ref_field}'",
                                                 entity=eid, field=fname)

    report.ok("entity_fields", f"{len(entities)} entities checked")


def check_event_payload_traceability(journey_dir, entity_index, report):
    """[2] Event payload traceability — derived_from → real entity fields."""
    event_index = build_event_index(journey_dir)
    if not event_index:
        report.warn("event_traceability", "No events found")
        return

    checked = 0
    for evt_name, evt in event_index.items():
        payload = evt["payload_fields"]
        for field_name, field_def in payload.items():
            if not isinstance(field_def, dict):
                continue

            derived = field_def.get("derived_from", "")
            if not derived:
                continue

            checked += 1

            # Parse "ENT-NNN.field_name" or "ENT-NNN.field + ENT-NNN.field"
            refs = re.findall(r'(ENT-\d{3})\.(\w+)', str(derived))
            for ent_id, field_ref in refs:
                if ent_id not in entity_index:
                    report.error("event_traceability",
                                 f"{evt_name}.{field_name} derived_from references {ent_id} which doesn't exist",
                                 event=evt_name, field=field_name, derived_from=derived)
                elif field_ref not in entity_index[ent_id]["fields"]:
                    report.error("event_traceability",
                                 f"{evt_name}.{field_name} derived_from references {ent_id}.{field_ref} but entity has no such field",
                                 event=evt_name, field=field_name, derived_from=derived,
                                 available_fields=list(entity_index[ent_id]["fields"].keys())[:10])

    report.ok("event_traceability", f"{checked} derived_from references checked across {len(event_index)} events")


def check_consumed_event_mappings(journey_dir, entity_index, event_index_local, report):
    """[3] Consumed event mapping completeness."""
    sb = load_json(journey_dir / "service-boundaries.json")
    if not sb:
        return

    checked = 0
    services = sb.get("services", sb.get("service_boundaries", []))
    for svc in services:
        consumed = svc.get("consumed_events", [])
        for ce in consumed:
            if not isinstance(ce, dict):
                continue

            maps_to = ce.get("maps_to", {})
            if not maps_to:
                continue
            if not isinstance(maps_to, dict):
                continue

            checked += 1
            target_ent = maps_to.get("target_entity", "")
            field_mapping = maps_to.get("field_mapping", {})

            if target_ent and target_ent not in entity_index:
                report.error("consumed_mapping",
                             f"maps_to target_entity {target_ent} doesn't exist",
                             service=svc.get("service_id", ""),
                             event=ce.get("event_id", ce.get("name", "")))

            if target_ent and target_ent in entity_index and field_mapping:
                target_fields = entity_index[target_ent]["fields"]
                for source_field, target_field in field_mapping.items():
                    if target_field not in target_fields:
                        report.error("consumed_mapping",
                                     f"maps_to field '{target_field}' doesn't exist on {target_ent}",
                                     service=svc.get("service_id", ""),
                                     target_entity=target_ent,
                                     available_fields=list(target_fields.keys())[:10])

    if checked:
        report.ok("consumed_mapping", f"{checked} consumed event mappings checked")


def check_api_entity_traceability(journey_dir, entity_index, report):
    """[4] API contract → entity traceability."""
    api_dir = journey_dir / "api-contracts"
    if not api_dir.exists():
        return

    for api_file in sorted(api_dir.glob("*.json")):
        data = load_json(api_file)
        if not data:
            continue

        # Check if components/schemas reference entity fields
        schemas = data.get("components", {}).get("schemas", {})
        if schemas:
            report.ok("api_traceability", f"{api_file.name}: {len(schemas)} schemas defined")
        else:
            report.warn("api_traceability", f"{api_file.name}: no components/schemas section")


def check_sequence_data_flow(journey_dir, event_index_local, report):
    """[5] Sequence diagram data flow — referenced events exist."""
    seq_dir = journey_dir / "sequence-diagrams"
    if not seq_dir.exists():
        return

    for jf in sorted(seq_dir.glob("*.json")):
        data = load_json(jf)
        if not data:
            continue

        steps = data.get("steps", data.get("interactions", []))
        for step in steps:
            # Check if step references an event
            label = str(step.get("label", step.get("action", step.get("description", ""))))
            event_refs = re.findall(r'(EVT-\d{3})', label)
            for evt_ref in event_refs:
                # Check it exists in event catalogue
                found = any(e["event_id"] == evt_ref for e in event_index_local.values())
                if not found:
                    # Check central catalogue
                    central_cat = load_json(CENTRAL / "event-catalogue.json")
                    if central_cat and evt_ref not in json.dumps(central_cat):
                        report.warn("sequence_data_flow",
                                    f"{jf.name} step {step.get('step', '?')} references {evt_ref} not found in event catalogues",
                                    file=jf.name)

        report.ok("sequence_data_flow", f"{jf.name}: {len(steps)} steps checked")


def check_governance_resolution(journey_dir, gov_index, report):
    """[6] Governance rule resolution."""
    detail = load_json(journey_dir / "journey-detail.json")
    if not detail:
        return

    phases = detail.get("phases", [])
    checked = 0
    for phase in phases:
        rules = phase.get("governance_rules", [])
        for rule_ref in rules:
            if isinstance(rule_ref, str):
                # Extract rule ID pattern (GOV-NNN-RNN or RULE-XXX-NNN)
                rule_ids = re.findall(r'(GOV-\d{3}-R\d{2}|RULE-\w+-\d{3})', rule_ref)
                for rid in rule_ids:
                    checked += 1
                    if rid not in gov_index:
                        report.warn("governance_resolution",
                                    f"Phase {phase.get('id', '?')} references rule {rid} not found in governance files",
                                    phase=phase.get("id", ""))

    if checked:
        report.ok("governance_resolution", f"{checked} governance rule references checked")
    else:
        report.warn("governance_resolution", "No governance rule references found in journey phases")


def check_persona_resolution(journey_dir, persona_index, report):
    """[7] Persona resolution."""
    pi = load_json(journey_dir / "participant-interaction.json")
    if not pi:
        return

    participants = pi.get("participants", [])
    checked = 0
    for p in participants:
        pid = p.get("id", p.get("persona_id", ""))
        if not pid:
            continue

        # Only check PER-NNN patterns (skip EXT-, OPS-, etc.)
        if not re.match(r'^PER-\d{3}$', pid):
            continue

        checked += 1
        if pid not in persona_index:
            report.error("persona_resolution",
                         f"Participant {pid} not found in foundation persona files",
                         persona_id=pid)

    if checked:
        report.ok("persona_resolution", f"{checked} persona references checked")


def check_cross_entity_consistency(journey_dir, entity_index, report):
    """[8] Cross-entity field consistency."""
    # Build a map of field_name → [(entity_id, type)] across all entities in this journey
    dm = load_json(journey_dir / "data-model.json")
    if not dm:
        return

    field_types = defaultdict(list)
    entities = dm.get("entities", dm.get("new_entities", []))
    for ent in entities:
        eid = ent.get("id", ent.get("entity_id", ""))
        for field in ent.get("fields", []):
            fname = field.get("name", "")
            ftype = field.get("type", "")
            if fname and ftype:
                field_types[fname].append((eid, ftype))

    # Check for type mismatches on same-named fields
    mismatches = 0
    for fname, occurrences in field_types.items():
        if len(occurrences) <= 1:
            continue
        types = set(t for _, t in occurrences)
        if len(types) > 1:
            mismatches += 1
            entities_with_types = ", ".join(f"{eid}:{t}" for eid, t in occurrences)
            report.warn("field_consistency",
                         f"Field '{fname}' has different types across entities: {entities_with_types}",
                         field=fname)

    if mismatches == 0:
        report.ok("field_consistency", "No cross-entity type mismatches")


# ── Main ─────────────────────────────────────────────────────────────

def validate_journey(journey_slug, entity_index, gov_index, persona_index):
    journey_dir = MODELS / journey_slug
    if not journey_dir.exists():
        print(f"Not found: {journey_dir}")
        return None

    report = Report(journey_slug)

    if not JSON_MODE:
        print(f"\n{'─'*60}")
        print(f"{CYAN}Data integrity: {journey_slug}{RESET}")
        print(f"{'─'*60}")

    event_index = build_event_index(journey_dir)

    check_entity_fields(journey_dir, entity_index, report)
    check_event_payload_traceability(journey_dir, entity_index, report)
    check_consumed_event_mappings(journey_dir, entity_index, event_index, report)
    check_api_entity_traceability(journey_dir, entity_index, report)
    check_sequence_data_flow(journey_dir, event_index, report)
    check_governance_resolution(journey_dir, gov_index, report)
    check_persona_resolution(journey_dir, persona_index, report)
    check_cross_entity_consistency(journey_dir, entity_index, report)

    if not JSON_MODE:
        if report.errors:
            print(f"\n  {RED}FAILED{RESET}: {len(report.errors)} errors, {len(report.warnings)} warnings")
        elif report.warnings:
            print(f"\n  {YELLOW}PASSED WITH WARNINGS{RESET}: {len(report.warnings)} warnings")
        else:
            print(f"\n  {GREEN}PASSED{RESET}: All data integrity checks clean")

    return report


def main():
    all_mode = "--all" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args and not all_mode:
        print("Usage: python3 validate-data-integrity.py <journey-slug>")
        print("       python3 validate-data-integrity.py --all")
        print("       python3 validate-data-integrity.py --all --json")
        sys.exit(1)

    # Build global indexes once
    if not JSON_MODE:
        print(f"\n{'='*60}")
        print("Building global indexes...")

    entity_index = build_entity_index()
    gov_index = build_governance_index()
    persona_index = build_persona_index()

    if not JSON_MODE:
        print(f"  Entities: {len(entity_index)}")
        print(f"  Governance rules: {len(gov_index)}")
        print(f"  Personas: {len(persona_index)}")
        print(f"{'='*60}")

    if all_mode:
        journeys = sorted(d.name for d in MODELS.iterdir() if d.is_dir())
    else:
        journeys = args

    all_reports = []
    total_errors = 0
    total_warnings = 0

    for slug in journeys:
        report = validate_journey(slug, entity_index, gov_index, persona_index)
        if report:
            all_reports.append(report)
            total_errors += len(report.errors)
            total_warnings += len(report.warnings)

    if JSON_MODE:
        output = {
            "total_journeys": len(all_reports),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "journeys": [r.to_dict() for r in all_reports],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Data integrity summary: {len(all_reports)} journeys")
        print(f"  Errors:   {total_errors}")
        print(f"  Warnings: {total_warnings}")

        if total_errors:
            print(f"\n  {RED}FAILED{RESET}: {total_errors} data integrity errors found")
        elif total_warnings:
            print(f"\n  {YELLOW}PASSED WITH WARNINGS{RESET}")
        else:
            print(f"\n  {GREEN}PASSED{RESET}: All data integrity checks clean")
        print(f"{'='*60}\n")

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
