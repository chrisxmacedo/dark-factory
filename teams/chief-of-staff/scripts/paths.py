"""Locate the office root for team scripts.

In the toolkit the root is teams/chief-of-staff. After the standalone export
the root is the directory that contains scripts/. OFFICE_ROOT overrides both.
"""

from __future__ import annotations

import os
from pathlib import Path


def office_root() -> Path:
    env = os.environ.get("OFFICE_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]
