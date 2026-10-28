#!/usr/bin/env bash
# Run one office prompt with Claude Code in headless mode.
#
# Loads CLAUDE.md, skills, subagents, hooks, and .mcp.json (this script does
# not pass --bare). Permission prompts are denied rather than blocking a
# schedule. The authority hook still blocks anything outside the role.
#
# Usage:
#   scripts/claude-headless.sh --agent weekly-delivery --prompt-file schedules/prompts/weekly-delivery.md
#   scripts/claude-headless.sh --dry-run --agent weekly-delivery --prompt-file schedules/prompts/weekly-delivery.md

set -euo pipefail

OFFICE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$OFFICE_ROOT"

DRY=0
AGENT=""
PROMPT_FILE=""
BUDGET="${CLAUDE_MAX_BUDGET_USD:-2.00}"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --agent) AGENT="${2:?--agent needs a name}"; shift 2 ;;
    --prompt-file) PROMPT_FILE="${2:?--prompt-file needs a path}"; shift 2 ;;
    --budget) BUDGET="${2:?--budget needs an amount}"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$AGENT" ] || [ -z "$PROMPT_FILE" ]; then
  echo "Both --agent and --prompt-file are required." >&2
  exit 2
fi
if [ ! -f "$PROMPT_FILE" ]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

if [ -f "$OFFICE_ROOT/scripts/office_env.py" ] && [ -f "$OFFICE_ROOT/config/ara.env" ]; then
  eval "$(python3 "$OFFICE_ROOT/scripts/office_env.py" --shell)"
  BUDGET="${CLAUDE_MAX_BUDGET_USD:-$BUDGET}"
fi

mkdir -p "$OFFICE_ROOT/outputs/logs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OFFICE_ROOT/outputs/logs/${AGENT}-${STAMP}.json"
LOCK_DIR="$OFFICE_ROOT/outputs/logs"
LOCK="$LOCK_DIR/${AGENT}.lock"

CMD=(
  claude
  -p
  --agent "$AGENT"
  --permission-mode dontAsk
  --output-format json
  --max-budget-usd "$BUDGET"
  --allowedTools "Read,Grep,Glob,Bash,Write,Edit,Skill"
  --disallowedTools "NotebookEdit"
  --append-system-prompt-file "$OFFICE_ROOT/CLAUDE.md"
)

if [ "$DRY" -eq 1 ]; then
  printf 'dry-run agent=%s budget=%s prompt=%s\n' "$AGENT" "$BUDGET" "$PROMPT_FILE"
  printf '%q ' "${CMD[@]}"
  printf '< %q\n' "$PROMPT_FILE"
  printf 'log=%s\n' "$LOG"
  exit 0
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "claude is not on PATH. Install Claude Code, then run this again." >&2
  exit 127
fi

mkdir -p "$LOCK_DIR"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "A ${AGENT} run is already in progress ($LOCK)." >&2
  exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

set +e
"${CMD[@]}" < "$PROMPT_FILE" | tee "$LOG"
code=${PIPESTATUS[0]}
set -e
exit "$code"
