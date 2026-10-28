#!/usr/bin/env python3
"""Load the office config file.

The file is KEY=value lines. It is not sourced as a shell script, so a value
cannot run a command. Existing environment variables win: put secrets in the
environment, not in the file.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def office_root() -> Path:
    env = os.environ.get("OFFICE_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    # Flat export: <office>/scripts/office_env.py
    if (here.parent / "config").is_dir() or (here.parent / "CLAUDE.md").is_file():
        return here.parent
    return here.parent


def config_path(root: Path | None = None) -> Path:
    return (root or office_root()) / "config" / "ara.env"


def parse_env_file(text: str, source: str = "ara.env") -> dict[str, str]:
    values: dict[str, str] = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ASSIGNMENT.match(line)
        if not match:
            raise ValueError(f"{source}:{lineno}: expected KEY=value")
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if "$(" in value or "`" in value or "\n" in value:
            raise ValueError(f"{source}:{lineno}: values cannot run commands")
        values[key] = value
    return values


def load_config(root: Path | None = None) -> dict[str, str]:
    """Return file values that do not override the real environment."""
    path = config_path(root)
    file_values: dict[str, str] = {}
    if path.is_file():
        file_values = parse_env_file(path.read_text(encoding="utf-8"), str(path))
    # The environment wins, so secrets stay out of the file.
    result = dict(os.environ)
    for key, value in file_values.items():
        result.setdefault(key, value)
    return result


def shell_exports(root: Path | None = None) -> str:
    path = config_path(root)
    if not path.is_file():
        return ""
    values = parse_env_file(path.read_text(encoding="utf-8"), str(path))
    lines = []
    for key, value in values.items():
        if key in os.environ:
            continue
        lines.append(f"export {key}={shlex.quote(value)}")
    return "\n".join(lines)


def require(config: dict[str, str], *keys: str) -> dict[str, str]:
    missing = [key for key in keys if not config.get(key)]
    if missing:
        raise SystemExit(
            "Missing office config: "
            + ", ".join(missing)
            + ". Copy config/ara.env.example to config/ara.env and set them there, "
            "or export them in the environment. Do not put tokens in git."
        )
    return {key: config[key] for key in keys}


def main() -> None:
    if "--shell" in sys.argv:
        sys.stdout.write(shell_exports())
        if shell_exports():
            sys.stdout.write("\n")
        return
    root = office_root()
    print(f"office_root={root}")
    path = config_path(root)
    print(f"config={'present' if path.is_file() else 'absent'} {path}")


if __name__ == "__main__":
    main()
