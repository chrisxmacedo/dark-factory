#!/usr/bin/env bash
# audit.sh — bash counterpart to capability-team/scripts/audit.py.
#
# Source this file from any infra/ script and call `audit_log` on key
# pipeline events. The resulting `_audit.jsonl` (in the dev-team root)
# is the authoritative record of what the pipeline did — non-bypassable
# because the script writes it, not the agent.
#
# See .claude/context/process-spec.md for the six-field contract.
#
# six-field spec
#   inputs         script (str), exit_code (int), blockers (int), warnings (int), meta_json (str)
#   outputs        one line appended to _audit.jsonl in the dev-team root
#   preconditions  the dev-team root (parent of infra/) is writable
#   postconditions _audit.jsonl contains one new JSON object with a UTC timestamp
#   idempotency    non-idempotent (one line per call; that is the point)
#   audit events   this IS the audit event — do not recurse

set -u

# Resolve the dev-team root from infra/ — audit lives at the dev-team root
# because pipelinectl / jiractl operate across many service repos.
_AUDIT_INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_AUDIT_PATH="$(cd "$_AUDIT_INFRA_DIR/.." && pwd)/_audit.jsonl"
_AUDIT_PIPELINE="development-team"

# audit_log <script> <exit_code> [blockers] [warnings] [meta_json]
audit_log() {
  local script="${1:-unknown}"
  local exit_code="${2:-0}"
  local blockers="${3:-0}"
  local warnings="${4:-0}"
  # NB: bash's ${5:-{}} mis-parses — the default value closer collides with
  # the ${} closer. Use a plain default instead.
  local meta="${5-}"
  [[ -z "$meta" ]] && meta='{}'
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local line
  line=$(printf '{"ts":"%s","pipeline":"%s","script":"%s","args":%s,"exit_code":%s,"blockers":%s,"warnings":%s,"pid":%s,"meta":%s}' \
    "$ts" \
    "$_AUDIT_PIPELINE" \
    "$script" \
    "$(printf '%s\n' "${_AUDIT_ARGS:-[]}")" \
    "$exit_code" \
    "$blockers" \
    "$warnings" \
    "$$" \
    "$meta")

  # Non-fatal on write failure — auditing must not break the run.
  if ! printf '%s\n' "$line" >> "$_AUDIT_PATH" 2>/dev/null; then
    echo "audit: WARNING: could not write $_AUDIT_PATH" >&2
  fi
}

# Helper: capture this invocation's argv as a JSON array for later reuse.
# Source this file then call `audit_capture_args "$@"` at the top of
# your script.
audit_capture_args() {
  if [[ $# -eq 0 ]]; then
    _AUDIT_ARGS="[]"
    return
  fi
  local out="["
  local sep=""
  for a in "$@"; do
    # Minimal JSON escaping of each arg.
    local escaped="${a//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    out+="$sep\"$escaped\""
    sep=","
  done
  out+="]"
  _AUDIT_ARGS="$out"
}

export -f audit_log
export -f audit_capture_args
