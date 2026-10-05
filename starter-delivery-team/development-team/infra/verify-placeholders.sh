#!/usr/bin/env bash
# verify-placeholders.sh — check for unreplaced {PLACEHOLDER} patterns
# Run after /create-project to verify all templates were customised.
#
# Usage: ./verify-placeholders.sh
# Returns: exit 0 if clean, exit 1 if placeholders remain
#
# six-field spec (per .claude/context/process-spec.md)
#   inputs         no argv; scans dev-team root recursively for known patterns
#   outputs        stdout list of offending files; exit 0 clean / 1 placeholders remain
#   preconditions  dev-team root has been populated from the starter template
#   postconditions verdict is reproducible; one audit line per invocation
#   idempotency    idempotent — read-only
#   audit events   {script:"verify-placeholders", args, exit_code, blockers=patterns found}

set -euo pipefail
_INFRA_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$_INFRA_DIR/.."

# shellcheck source=audit.sh
source "$_INFRA_DIR/audit.sh"
audit_capture_args "$@"
trap 'code=$?; audit_log "verify-placeholders" "$code" "${found:-0}" 0 "{}"; exit $code' EXIT

echo "Scanning for unreplaced placeholders..."

# Known patterns that should have been replaced
PATTERNS=(
  '{PROJECT_KEY}'
  '{PROJECT_NAME}'
  '{PROJECT_SLUG}'
  '{JIRA_SITE}'
  '{CLOUD_ID}'
  '{SERVICE_REPOS}'
  '{service-1}'
  '{service-2}'
  '{WEB_PORT}'
  '{TBC}'
  '{T_BACKLOG}'
  '{T_REFINE}'
  '{T_DEV}'
  '{T_LOCAL}'
  '{T_INTEG}'
  '{T_E2E}'
  '{T_REGRESS}'
  '{T_RELEASE}'
  '{T_DONE}'
  '{T_TASK_INPROGRESS}'
  '{T_TASK_DONE}'
  '{PRIMARY_SERVICE}'
  '{BUILD_COMMAND}'
  '{MIGRATION_COMMAND}'
  '{UNIT_TEST_COMMAND}'
)

found=0
for pattern in "${PATTERNS[@]}"; do
  # Search .claude/, infra/, and root-level files
  matches=$(grep -rl "$pattern" \
    .claude/ infra/ \
    ARCHITECTURE.md AGENT-CONTEXT.md PIPELINE-STATE.md workflow-improvements.md \
    2>/dev/null | grep -v "verify-placeholders.sh" || true)
  if [ -n "$matches" ]; then
    echo ""
    echo "  ✗ $pattern found in:"
    echo "$matches" | while read f; do
      count=$(grep -c "$pattern" "$f" 2>/dev/null || true)
      echo "      $f ($count occurrences)"
    done
    found=$((found + 1))
  fi
done

echo ""
if [ "$found" -eq 0 ]; then
  echo "✓ All placeholders replaced. Project is ready."
  exit 0
else
  echo "✗ $found placeholder pattern(s) still present. Replace them before starting the pipeline."
  exit 1
fi
