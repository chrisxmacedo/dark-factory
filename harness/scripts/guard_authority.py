#!/usr/bin/env python3
"""PreToolUse hook for the technical chief of staff.

The role may read delivery data, write its own reports and drafts, raise
issues, and comment on issues it is chasing. It may not change product code,
merge or review pull requests, transition engineering tickets, or reprioritise
another team's work.

Exit 0 and a JSON "approve" decision allow the call. Exit 2 denies it.
Both are emitted so a Claude Code build that honours either mechanism still
blocks the call.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

WRITE_ROOTS = {"outputs", "drafts"}
ALLOWED_AGENTS = {
    "weekly-delivery",
    "meeting-actions",
    "planning",
    "budget-tracker",
    "initiative",
}
ALLOWED_SCRIPTS = {
    "pull_delivery.py",
    "dora.py",
    "cycle_time.py",
    "budget_flags.py",
    "working_days.py",
    "chase_deadlines.py",
    "pending_meetings.py",
    "raid_log.py",
    "office_env.py",
}
READ_TOOLS = {
    "Read",
    "Grep",
    "Glob",
    "LS",
    "WebFetch",
    "WebSearch",
    "Skill",
    "TodoWrite",
    "ToolSearch",
    "ListMcpResources",
    "ReadMcpResource",
}
GIT_READ = {"status", "diff", "log", "show", "remote", "rev-parse"}
GH_READ = {
    ("pr", "view"),
    ("pr", "list"),
    ("pr", "status"),
    ("pr", "diff"),
    ("pr", "checks"),
    ("run", "list"),
    ("run", "view"),
    ("issue", "list"),
    ("issue", "view"),
    ("issue", "create"),
    ("issue", "comment"),
}
MCP_READ = re.compile(
    r"(^|_)(list|get|search|query|fetch|read|view|describe|find)(_|$)",
    re.IGNORECASE,
)
MCP_WRITE = re.compile(
    r"update|create|delete|archive|merge|transition|assign|priority|rank|edit|comment|push|write|save|mutation|close",
    re.IGNORECASE,
)
SHELL_READ = {"ls", "cat", "head", "tail", "wc", "find", "grep", "jq", "date", "pwd", "printf", "echo", "true", "test"}


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("OFFICE_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def decide(event: dict, root: Path | None = None) -> tuple[str, str]:
    root = (root or project_root()).resolve()
    tool = str(event.get("tool_name") or event.get("tool") or "")
    payload = event.get("tool_input") or event.get("tool_input".replace("_", "")) or {}
    if not isinstance(payload, dict):
        payload = {}

    if tool in READ_TOOLS:
        return "approve", "read"
    if tool == "Agent":
        name = str(
            payload.get("subagent_type")
            or payload.get("agent")
            or payload.get("name")
            or ""
        )
        if name in ALLOWED_AGENTS:
            return "approve", name
        return "deny", (
            f"Only these subagents are in this role: {', '.join(sorted(ALLOWED_AGENTS))}."
        )
    if tool in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
        return _decide_write(tool, payload, root)
    if tool == "Bash":
        command = str(payload.get("command") or "")
        return _decide_bash(command, root)
    if tool.startswith("mcp__") or tool.startswith("mcp_"):
        return _decide_mcp(tool)
    return "deny", f"{tool or 'unknown tool'} is outside this role's authority."


def _decide_write(tool: str, payload: dict, root: Path) -> tuple[str, str]:
    if tool == "NotebookEdit":
        return "deny", "Notebook edits are outside this role."
    paths = []
    for key in ("file_path", "path", "notebook_path"):
        if payload.get(key):
            paths.append(str(payload[key]))
    edits = payload.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict) and edit.get("file_path"):
                paths.append(str(edit["file_path"]))
    if not paths:
        return "deny", "Refusing a write with no path."
    for path in paths:
        if not _allowed_write(path, root):
            return "deny", (
                f"Refusing to write {path}. This role only writes under outputs/ and drafts/."
            )
    return "approve", "office write"


def _allowed_write(path: str, root: Path) -> bool:
    raw = Path(path)
    if ".." in raw.parts:
        return False
    candidate = raw if raw.is_absolute() else root / raw
    try:
        resolved = candidate.resolve()
        relative = resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return bool(relative.parts) and relative.parts[0] in WRITE_ROOTS


def _decide_mcp(tool: str) -> tuple[str, str]:
    leaf = tool.split("__")[-1]
    if MCP_WRITE.search(leaf):
        return "deny", (
            f"{tool} would change a tracker. Raise an issue or write a draft instead."
        )
    if MCP_READ.search(leaf):
        return "approve", "mcp read"
    return "deny", (
        f"{tool} is not a read. This role does not change tickets through MCP."
    )


def _decide_bash(command: str, root: Path) -> tuple[str, str]:
    if not command.strip():
        return "deny", "Empty command."
    try:
        segments = split_shell(command)
    except ValueError as exc:
        return "deny", str(exc)
    if not segments:
        return "deny", "Empty command."
    for segment in segments:
        verdict, reason = _decide_segment(segment, root)
        if verdict != "approve":
            return verdict, reason
    return "approve", "bash"


def _decide_segment(segment: str, root: Path) -> tuple[str, str]:
    if _unsafe_redirection(segment):
        return "deny", "Refusing a redirect outside outputs/ and drafts/."
    try:
        argv = shlex.split(segment, posix=True)
    except ValueError as exc:
        return "deny", f"Could not parse command: {exc}"
    if not argv:
        return "deny", "Empty command."
    # Drop simple env assignments (KEY=value) in front of the command.
    while argv and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0]) and "=" in argv[0]:
        if "$(" in argv[0] or "`" in argv[0]:
            return "deny", "Refusing a command substitution."
        argv = argv[1:]
    if not argv:
        return "deny", "Nothing to run."
    binary = Path(argv[0]).name
    if binary in {"sudo", "rm", "dd", "mkfs", "curl", "wget", "ssh", "scp", "docker", "kubectl"}:
        return "deny", f"{binary} is outside this role."
    if binary == "git":
        return _decide_git(argv[1:])
    if binary == "gh":
        return _decide_gh(argv[1:])
    if binary in {"python3", "python"}:
        return _decide_python(argv[1:], root)
    if binary in SHELL_READ:
        if binary == "find" and any(arg in {"-delete", "-exec", "-execdir"} for arg in argv):
            return "deny", "Refusing find that changes files."
        if binary in {"cat", "head", "tail"}:
            for arg in argv[1:]:
                if arg.startswith("-"):
                    continue
                if _sensitive(arg) or _outside_office(arg, root):
                    return "deny", "Refusing to read secrets or files outside this office."
        return "approve", binary
    if binary == "mkdir":
        targets = [arg for arg in argv[1:] if not arg.startswith("-")]
        if targets and all(_allowed_write(target, root) or _parent_allowed(target, root) for target in targets):
            return "approve", "mkdir"
        return "deny", "mkdir is only allowed under outputs/ and drafts/."
    return "deny", (
        f"'{binary}' is not something this role runs. Data pulls go through scripts/."
    )


def _parent_allowed(path: str, root: Path) -> bool:
    """Allow mkdir of a new directory whose parent is an allowed write root."""
    raw = Path(path)
    if ".." in raw.parts:
        return False
    parent = raw.parent
    if str(parent) in {"", "."}:
        return raw.parts[:1] == list(WRITE_ROOTS) or (raw.parts and raw.parts[0] in WRITE_ROOTS)
    return _allowed_write(str(parent), root) or (
        parent.parts and parent.parts[0] in WRITE_ROOTS and ".." not in parent.parts
    )


def _decide_git(args: list[str]) -> tuple[str, str]:
    if not args:
        return "deny", "git needs a read-only subcommand."
    if args[0] == "branch":
        if any(arg in {"-d", "-D", "-m", "-M", "-u"} or arg.startswith("--delete") or arg.startswith("--move") for arg in args):
            return "deny", "Refusing a git branch change."
        return "approve", "git branch"
    if args[0] in GIT_READ:
        return "approve", f"git {args[0]}"
    return "deny", (
        f"git {args[0]} would change a repository. This role does not change code."
    )


def _decide_gh(args: list[str]) -> tuple[str, str]:
    if len(args) < 2:
        return "deny", "gh is limited to reading PRs, CI, and issues, plus raising or commenting on issues."
    pair = (args[0], args[1])
    if pair in GH_READ:
        if pair == ("issue", "create") or pair == ("issue", "comment"):
            return "approve", "gh issue"
        return "approve", f"gh {' '.join(pair)}"
    return "deny", (
        f"gh {' '.join(args[:2])} is outside this role. "
        "It can raise issues and chase them. It cannot merge, review, or edit pull requests, "
        "and it cannot reprioritise another team's work."
    )


def _decide_python(args: list[str], root: Path) -> tuple[str, str]:
    if not args or args[0].startswith("-"):
        return "deny", "Only the office scripts in scripts/ may be run."
    script = Path(args[0])
    if script.name not in ALLOWED_SCRIPTS:
        return "deny", f"{script.name} is not an office script."
    if script.parts[:1] != ("scripts",) and script.parent.name != "scripts":
        return "deny", "Office scripts must be invoked from scripts/."
    for arg in args[1:]:
        if arg in {"--output", "-o"}:
            continue
        if "$(" in arg or "`" in arg or ".." in Path(arg).parts:
            return "deny", "Refusing a path that leaves the office."
    outputs = _flag_values(args[1:], "--output")
    for destination in outputs:
        if not _allowed_write(destination, root):
            return "deny", f"Script output must stay under outputs/ or drafts/: {destination}"
    return "approve", script.name


def _flag_values(args: list[str], flag: str) -> list[str]:
    values = []
    for index, arg in enumerate(args):
        if arg == flag and index + 1 < len(args):
            values.append(args[index + 1])
        elif arg.startswith(flag + "="):
            values.append(arg.split("=", 1)[1])
    return values


def _sensitive(path: str) -> bool:
    name = Path(path).name.lower()
    return name in {".env", ".env.jira", ".env.local"} or name.endswith(".pem") or "id_rsa" in name or "credentials" in name


def _outside_office(path: str, root: Path) -> bool:
    raw = Path(path)
    if ".." in raw.parts:
        return True
    candidate = raw if raw.is_absolute() else root / raw
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return True
    return False


def _unsafe_redirection(segment: str) -> bool:
    """Deny redirects other than /dev/null or outputs/ and drafts/."""
    pattern = re.compile(r"(?:^|[^>])>{1,2}\s*([^\s;|&]+)")
    for match in pattern.finditer(segment):
        target = match.group(1).strip("'\"")
        if target == "/dev/null":
            continue
        raw = Path(target)
        if ".." in raw.parts:
            return True
        if not raw.parts or raw.parts[0] not in WRITE_ROOTS:
            return True
    return False


def split_shell(command: str) -> list[str]:
    """Split a command on &&, ||, ;, and | without breaking quotes."""
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if quote:
            buf.append(char)
            if char == quote and (index == 0 or command[index - 1] != "\\"):
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            index += 1
            continue
        if char == "\n" or char == ";":
            parts.append("".join(buf).strip())
            buf = []
            index += 1
            continue
        two = command[index : index + 2]
        if two in {"&&", "||"} or char == "|":
            parts.append("".join(buf).strip())
            buf = []
            index += 2 if two in {"&&", "||"} else 1
            continue
        buf.append(char)
        index += 1
    if quote:
        raise ValueError("Unbalanced quotes.")
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [part for part in parts if part]


def emit(verdict: str, reason: str) -> int:
    if verdict == "approve":
        json.dump({"decision": "approve", "reason": reason}, sys.stdout)
        sys.stdout.write("\n")
        return 0
    payload = {"decision": "deny", "reason": reason}
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    sys.stderr.write(reason + "\n")
    return 2


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        raise SystemExit(emit("deny", "Hook received no tool call."))
    event = json.loads(raw)
    verdict, reason = decide(event)
    raise SystemExit(emit(verdict, reason))


if __name__ == "__main__":
    main()
