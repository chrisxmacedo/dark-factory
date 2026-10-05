#!/usr/bin/env python3
"""
Completeness validator — checks the specification is implementable.

Runs across the full `artefacts/` tree and enforces structural completeness
as the capability team produces documentation. It does not check semantic
correctness (other validators handle that) — it checks that every required
artefact exists, that every reference resolves, and that known gaps
(stubs, TODOs, placeholders) are visibly flagged.

six-field spec
  inputs         argv: [--strict]; reads artefacts/**
  outputs        stdout verdict; exit 0 (complete) | 1 (blockers) | 2 (warnings)
  preconditions  artefacts/ exists; REQUIREMENTS list matches pipeline version
  postconditions one line appended to artefacts/_audit.jsonl
  idempotency    idempotent — re-running on an unchanged tree yields the same verdict
  audit events   {script:"validate-completeness", args, exit_code, blockers, warnings}

Projects with stronger regulatory duties should promote warn → blocker
for the artefacts their regulator requires (e.g. UK banking: promote
COMPLY-EVIDENCE to blocker).
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AR = ROOT / "artefacts"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402


# ── Requirement definitions ──────────────────────────────────────────
#
# Severity:
#   "blocker" → fails the validator (exit 1)
#   "warn"    → surfaced only (exit 2, or exit 1 under --strict)
#
# To add a new required artefact: append a dict and bump the relevant
# PIPELINE.md gate to call this script. Never silently relax severity.

REQUIREMENTS = [
    # Foundation — Phase A/B outputs
    {"id": "FOUNDATION-CAPS",    "severity": "blocker", "description": "At least one capability artefact",    "check": "glob", "pattern": "foundation/capabilities/*.json",       "min": 1},
    {"id": "FOUNDATION-PERSONAS","severity": "blocker", "description": "Personas file",                        "check": "glob", "pattern": "foundation/personas/*.json",           "min": 1},
    {"id": "FOUNDATION-GOV",     "severity": "blocker", "description": "Governance file(s)",                   "check": "glob", "pattern": "foundation/governance/*.json",         "min": 1},
    {"id": "FOUNDATION-SVC",     "severity": "blocker", "description": "Technical services catalogue",         "check": "glob", "pattern": "foundation/technical-services/*.json", "min": 1},
    {"id": "FOUNDATION-INV",     "severity": "blocker", "description": "Journey inventory",                    "check": "exists", "path": "foundation/journey-inventory.json"},

    # Architecture — design-time
    {"id": "ARCH-C4-DSL",        "severity": "blocker", "description": "C4 workspace DSL",                     "check": "exists", "path": "architecture/c4-workspace.dsl"},
    {"id": "ARCH-CHANNEL",       "severity": "blocker", "description": "Channel model",                        "check": "exists", "path": "architecture/channel-model.json"},
    {"id": "ARCH-SVCCAT",        "severity": "blocker", "description": "Service catalogue",                    "check": "exists", "path": "architecture/service-catalogue.json"},
    {"id": "ARCH-SVCDEPS",       "severity": "blocker", "description": "Service dependencies",                 "check": "exists", "path": "architecture/service-dependencies.json"},
    {"id": "ARCH-OBS",           "severity": "blocker", "description": "Observability model",                  "check": "exists", "path": "architecture/observability-model.json"},
    {"id": "ARCH-SEC",           "severity": "blocker", "description": "Security model",                       "check": "exists", "path": "architecture/security-model.json"},
    {"id": "ARCH-ENV",           "severity": "blocker", "description": "Environment spec",                     "check": "exists", "path": "architecture/environment-spec.json"},
    {"id": "ARCH-VISUAL",        "severity": "warn",    "description": "Visual architecture",                  "check": "exists", "path": "architecture/visual-architecture.json"},

    # Architecture — runtime contracts (cross-cutting, universally required)
    {"id": "ARCH-ERROR-MODEL",   "severity": "blocker", "description": "Cross-cutting error model",            "check": "exists", "path": "architecture/error-model.json"},
    {"id": "ARCH-RUNTIME-CONV",  "severity": "blocker", "description": "Runtime conventions (IDs, idempotency, auth)", "check": "exists", "path": "architecture/runtime-conventions.json"},
    {"id": "ARCH-RBAC",          "severity": "blocker", "description": "RBAC matrix",                          "check": "exists", "path": "architecture/rbac-matrix.json"},
    {"id": "ARCH-DEPLOY",        "severity": "blocker", "description": "Deployment topology",                  "check": "exists", "path": "architecture/deployment-topology.json"},
    {"id": "ARCH-SLO",           "severity": "blocker", "description": "SLO catalogue",                        "check": "exists", "path": "architecture/slo-catalogue.json"},
    {"id": "ARCH-CONFIG",        "severity": "blocker", "description": "Config schema",                        "check": "exists", "path": "architecture/config-schema.json"},
    {"id": "ARCH-RETENTION",     "severity": "blocker", "description": "Data retention policy",                "check": "exists", "path": "architecture/data-retention-policy.json"},

    # Central model
    {"id": "CENTRAL-ENTS",       "severity": "blocker", "description": "Central-model entities",               "check": "glob", "pattern": "central-model/entities/*.json", "min": 1},
    {"id": "CENTRAL-SVCMAP",     "severity": "warn",    "description": "Service map",                          "check": "exists", "path": "central-model/service-map.json"},
    {"id": "CENTRAL-EVCAT",      "severity": "warn",    "description": "Central event catalogue",              "check": "exists", "path": "central-model/event-catalogue.json"},

    # Runtime / operational
    {"id": "RUN-RUNBOOKS",       "severity": "warn",    "description": "At least one oncall runbook",          "check": "glob", "pattern": "runtime/runbooks/*.md", "min": 1},
    {"id": "RUN-DASH",           "severity": "warn",    "description": "Observability dashboards",             "check": "exists", "path": "runtime/observability-dashboards.json"},
    {"id": "RUN-COST",           "severity": "warn",    "description": "Cost model",                           "check": "exists", "path": "runtime/cost-model.json"},
    {"id": "RUN-VENDOR",         "severity": "warn",    "description": "Vendor notes",                         "check": "exists", "path": "runtime/vendor-notes.json"},
    {"id": "RUN-MIGRATION",      "severity": "warn",    "description": "Migration plan",                       "check": "exists", "path": "runtime/migration-plan.json"},
    {"id": "RUN-IAC",            "severity": "warn",    "description": "IaC starter",                          "check": "exists", "path": "runtime/iac/README.md"},

    # Compliance — projects with a named regulator should promote this to blocker
    {"id": "COMPLY-EVIDENCE",    "severity": "warn",    "description": "Compliance evidence trail (promote to blocker if regulated)", "check": "exists", "path": "compliance-evidence-trail.json"},

    # Test fixtures
    {"id": "TEST-FIXTURES",      "severity": "warn",    "description": "Test fixtures present",                "check": "exists", "path": "test-fixtures/README.md"},

    # Deviations report (auto-generated at build)
    {"id": "DEV-REPORT",         "severity": "warn",    "description": "Architectural deviations report",      "check": "exists", "path": "_architectural-deviations.md"},
]


# ── Per-journey deep checks ─────────────────────────────────────────

JOURNEY_SEQ_PATHS = {
    "happy": re.compile(r"happy", re.IGNORECASE),
    "alt":   re.compile(r"\b(alt|alternative)\b", re.IGNORECASE),
    "exc":   re.compile(r"\b(exception|error|fail|exceeded|rejected|block|denied|declined|refuse)\b", re.IGNORECASE),
}

DEEP_CHECKS = {
    "entity-primary-key":    {"severity": "blocker", "description": "Every entity declares a primary key"},
    "event-payload-schema":  {"severity": "blocker", "description": "Every event has a payload_schema"},
    "journey-has-happy":     {"severity": "blocker", "description": "Every journey has a happy-path sequence diagram"},
    "journey-has-alt":       {"severity": "warn",    "description": "Every journey has an alternative-path sequence (stub acceptable)"},
    "journey-has-exc":       {"severity": "warn",    "description": "Every journey has an exception-path sequence (stub acceptable)"},
    "stub-tracking":         {"severity": "warn",    "description": "Stub / TODO markers are surfaced"},
}


# ── Runners ─────────────────────────────────────────────────────────

def check_requirement(req):
    if req["check"] == "exists":
        p = AR / req["path"]
        return (p.exists(), f"missing file: artefacts/{req['path']}")
    if req["check"] == "glob":
        matches = list(AR.glob(req["pattern"]))
        ok = len(matches) >= req.get("min", 1)
        return (ok, f"found {len(matches)} / needed ≥ {req.get('min', 1)} for pattern {req['pattern']}")
    return (False, "unknown check type")


def has_pk(fields):
    def is_id_type(t):
        t = str(t).upper()
        return t.startswith("UUID") or t.startswith("ULID") or t == "KSUID"
    return any(x.get("primary_key") or x.get("pk") or
               (is_id_type(x.get("type", "")) and str(x.get("name", "")).endswith("_id"))
               for x in fields)


def deep_checks():
    results = {k: {"fails": [], "info": v} for k, v in DEEP_CHECKS.items()}

    # Entity primary keys
    ent_dir = AR / "central-model/entities"
    if ent_dir.exists():
        for f in sorted(ent_dir.glob("*.json")):
            try:
                e = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            eid = e.get("entity_id") or e.get("id") or f.stem
            if e.get("fields") and not has_pk(e["fields"]):
                results["entity-primary-key"]["fails"].append(eid)

    # Event payload schemas
    for f in sorted((AR / "models").glob("*/events/event-catalogue.json")):
        try:
            cat = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        journey = f.parts[-3]
        for e in cat.get("events", []):
            if not (e.get("payload_schema") or e.get("schema") or e.get("payload")):
                eid = e.get("event_id") or e.get("id") or "?"
                results["event-payload-schema"]["fails"].append(f"{journey}::{eid}")

    # Per-journey sequence coverage
    models = AR / "models"
    if models.exists():
        for jdir in sorted(models.iterdir()):
            if not jdir.is_dir():
                continue
            seq_dir = jdir / "sequence-diagrams"
            files = [f.name for f in seq_dir.glob("*.mmd")] if seq_dir.exists() else []
            for kind, regex in JOURNEY_SEQ_PATHS.items():
                has = any(regex.search(n) for n in files)
                if not has:
                    results[f"journey-has-{kind}"]["fails"].append(jdir.name)

    # Stub / TODO markers — surfaced only
    stub_pattern = re.compile(r"\b(TODO|STUB|x-status.*stub|PLACEHOLDER|tbd)\b", re.IGNORECASE)
    for root in [AR / "architecture", AR / "models", AR / "runtime", AR / "central-model"]:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if f.is_file() and f.suffix in (".json", ".md", ".mmd", ".dsl"):
                try:
                    if stub_pattern.search(f.read_text()):
                        results["stub-tracking"]["fails"].append(str(f.relative_to(AR)))
                except (UnicodeDecodeError, PermissionError):
                    pass

    return results


def xref_checks():
    """Cross-artefact reference resolution."""
    issues = []

    personas = set()
    for p in (AR / "foundation/personas").glob("*.json"):
        try:
            for x in json.loads(p.read_text()).get("personas", []):
                personas.add(x.get("id"))
        except json.JSONDecodeError:
            continue

    services = set()
    for p in (AR / "foundation/technical-services").glob("*.json"):
        try:
            for x in json.loads(p.read_text()).get("services", []):
                services.add(x.get("id"))
        except json.JSONDecodeError:
            continue

    cap_file = AR / "architecture/service-catalogue.json"
    if cap_file.exists():
        try:
            for s in json.loads(cap_file.read_text()).get("services", []):
                services.add(s.get("id"))
        except json.JSONDecodeError:
            pass

    # Entity owning_service resolves
    for f in (AR / "central-model/entities").glob("*.json"):
        try:
            e = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        ow = e.get("owning_service")
        if ow and services and ow not in services:
            issues.append(f"entity {e.get('entity_id') or e.get('id')}: owning_service {ow} not in service catalogue")

    # Journey triggering_persona resolves
    for jd in (AR / "models").glob("*/journey-detail.json"):
        try:
            j = json.loads(jd.read_text())
        except json.JSONDecodeError:
            continue
        tp = j.get("triggering_persona")
        if tp and personas and tp not in personas:
            issues.append(f"journey {jd.parts[-2]}: triggering_persona {tp} not in personas")

    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Warnings become blockers")
    args = ap.parse_args()

    print("═" * 68)
    print("  Completeness validator")
    print("═" * 68)

    blockers = []
    warnings = []

    print("\n— Required artefacts —")
    for req in REQUIREMENTS:
        ok, detail = check_requirement(req)
        mark = "✓" if ok else ("✗" if req["severity"] == "blocker" else "!")
        print(f"  {mark} {req['id']:25s} {req['description']}")
        if not ok:
            msg = f"{req['id']}: {detail}"
            (blockers if req["severity"] == "blocker" else warnings).append(msg)

    print("\n— Deep structural checks —")
    deep = deep_checks()
    for key, info in deep.items():
        fails = info["fails"]
        sev = info["info"]["severity"]
        desc = info["info"]["description"]
        mark = "✓" if not fails else ("✗" if sev == "blocker" else "!")
        print(f"  {mark} {key:25s} {desc}")
        if fails:
            shown = fails[:5]
            more = f" (+{len(fails) - 5} more)" if len(fails) > 5 else ""
            print(f"      {len(fails)} failure(s): {', '.join(shown)}{more}")
            msg = f"{key}: {len(fails)} failures — {', '.join(shown)}{more}"
            (blockers if sev == "blocker" else warnings).append(msg)

    print("\n— Cross-reference resolution —")
    xissues = xref_checks()
    if not xissues:
        print("  ✓ all cross-references resolve")
    else:
        for i in xissues:
            print(f"  ✗ {i}")
            blockers.append(f"xref: {i}")

    print("\n" + "═" * 68)
    if args.strict:
        blockers = blockers + warnings
        warnings = []

    if blockers:
        print(f"  RESULT: {len(blockers)} blocker(s), {len(warnings)} warning(s)")
        print("\nBlockers:")
        for b in blockers[:20]:
            print(f"  • {b}")
        if len(blockers) > 20:
            print(f"  … +{len(blockers) - 20} more")
        audit.log_event("validate-completeness", sys.argv[1:], 1, len(blockers), len(warnings),
                        {"strict": args.strict})
        sys.exit(1)
    elif warnings:
        print(f"  RESULT: 0 blockers, {len(warnings)} warning(s) — surface-only")
        print("\nWarnings:")
        for w in warnings[:20]:
            print(f"  • {w}")
        if len(warnings) > 20:
            print(f"  … +{len(warnings) - 20} more")
        audit.log_event("validate-completeness", sys.argv[1:], 2, 0, len(warnings),
                        {"strict": args.strict})
        sys.exit(2)
    else:
        print("  RESULT: ✓ complete. Specification is ready for implementation.")
        audit.log_event("validate-completeness", sys.argv[1:], 0, 0, 0,
                        {"strict": args.strict})
        sys.exit(0)


if __name__ == "__main__":
    main()
