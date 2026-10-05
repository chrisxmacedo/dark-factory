#!/usr/bin/env python3
"""
Audit helper — emits one JSONL line per named-process invocation.

Every script in the capability-team pipeline SHOULD import this and
call `log_event` on entry/exit. The file that results
(`artefacts/_audit.jsonl`) is the authoritative record of what the
pipeline actually did — non-bypassable because the script writes it,
not the agent.

See `.claude/context/process-spec.md` for the six-field contract this
implements.

six-field spec
  inputs         pipeline, script, args (list[str]), exit_code, blockers, warnings, meta
  outputs        one line appended to artefacts/_audit.jsonl
  preconditions  artefacts/ directory exists (created if missing)
  postconditions _audit.jsonl contains one new JSON object with a UTC timestamp
  idempotency    non-idempotent (one line per call; that is the point)
  audit events   this IS the audit event — do not recurse
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PIPELINE = "capability-team"
AUDIT_PATH = Path(__file__).resolve().parent.parent / "artefacts" / "_audit.jsonl"


def log_event(
    script: str,
    args: list[str] | None = None,
    exit_code: int = 0,
    blockers: int = 0,
    warnings: int = 0,
    meta: dict[str, Any] | None = None,
) -> None:
    """Append one JSONL line describing a named-process invocation.

    Called from the script itself (not from an agent) so the record
    cannot be silently skipped. Failures here are intentionally
    non-fatal — auditing must not take down a pipeline run — but a
    warning is emitted to stderr.
    """
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline": PIPELINE,
        "script": script,
        "args": args or [],
        "exit_code": exit_code,
        "blockers": blockers,
        "warnings": warnings,
        "pid": os.getpid(),
        "meta": meta or {},
    }
    try:
        with AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError as exc:
        print(f"audit: WARNING: could not write {AUDIT_PATH}: {exc}", file=sys.stderr)


def wrap(script: str):
    """Decorator that wraps a main() function and logs its outcome.

    Usage:
        @audit.wrap("validate-completeness")
        def main() -> int:
            ...
            return 0 if ok else 1

    Captures exit_code; callers can still pass blockers/warnings via
    the returned value being a tuple (exit_code, blockers, warnings).
    """
    def _decorator(fn):
        def _inner(*args, **kwargs):
            result = fn(*args, **kwargs)
            if isinstance(result, tuple):
                code, blockers, warnings = (list(result) + [0, 0])[:3]
            else:
                code, blockers, warnings = int(result or 0), 0, 0
            log_event(
                script=script,
                args=sys.argv[1:],
                exit_code=code,
                blockers=blockers,
                warnings=warnings,
            )
            return code
        return _inner
    return _decorator
