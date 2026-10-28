#!/usr/bin/env bash
# Copy the harness core and the chief-of-staff team into an empty directory.
#
# The destination is a Claude Code project you can open at work. It does not
# contain the delivery team, service starters, or the toolkit slash commands.
#
#   ./harness/export-chief-of-staff.sh /path/to/empty-dir

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEAM="$ROOT/teams/chief-of-staff"
DEST="${1:-}"

if [ -z "$DEST" ] || [ "$DEST" = "-h" ] || [ "$DEST" = "--help" ]; then
  sed -n '2,8p' "$0"
  exit 0
fi

if [ -e "$DEST" ] && [ -n "$(find "$DEST" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  echo "Destination is not empty: $DEST" >&2
  exit 1
fi
mkdir -p "$DEST"

copy_tree() {
  local src="$1" target="$2"
  mkdir -p "$target"
  # Trailing slash copies the contents. Exclude bytecode so a previous test
  # run cannot leak into a work checkout.
  tar -C "$src" --exclude '__pycache__' --exclude '*.pyc' -cf - . | tar -C "$target" -xf -
}

mkdir -p "$DEST/scripts" "$DEST/.claude/agents" "$DEST/.claude/skills" \
  "$DEST/outputs" "$DEST/drafts"

cp "$TEAM/CLAUDE.md" "$DEST/CLAUDE.md"
cp "$TEAM/CONTEXT.md" "$DEST/CONTEXT.md"
cp "$TEAM/STANDALONE.md" "$DEST/README.md"
cp "$ROOT/harness/README.md" "$DEST/HARNESS.md"
cp "$ROOT/harness/escalation.md" "$DEST/escalation.md"
cp "$ROOT/harness/claude/settings.json" "$DEST/.claude/settings.json"
cp "$ROOT/harness/mcp/mcp.json" "$DEST/.mcp.json"
cp "$ROOT/harness/scripts/guard_authority.py" "$DEST/scripts/guard_authority.py"
cp "$ROOT/harness/scripts/office_env.py" "$DEST/scripts/office_env.py"
cp "$ROOT/harness/scripts/claude-headless.sh" "$DEST/scripts/claude-headless.sh"
cp "$ROOT/harness/scripts/install-schedule.sh" "$DEST/scripts/install-schedule.sh"
copy_tree "$ROOT/harness/skills" "$DEST/.claude/skills"
copy_tree "$TEAM/.claude/agents" "$DEST/.claude/agents"
copy_tree "$TEAM/.claude/skills" "$DEST/.claude/skills"
copy_tree "$TEAM/config" "$DEST/config"
copy_tree "$TEAM/scripts" "$DEST/scripts"
copy_tree "$TEAM/schedules" "$DEST/schedules"
copy_tree "$TEAM/inbox" "$DEST/inbox"
copy_tree "$TEAM/tests" "$DEST/tests"
: > "$DEST/outputs/.gitkeep"
: > "$DEST/drafts/.gitkeep"

# Agent hooks in the template point at the toolkit layout. The work checkout
# keeps the guard next to the other office scripts.
python3 - "$DEST" <<'PY'
import pathlib, sys
dest = pathlib.Path(sys.argv[1])
old = 'python3 "$CLAUDE_PROJECT_DIR/../../harness/scripts/guard_authority.py"'
new = 'python3 "$CLAUDE_PROJECT_DIR/scripts/guard_authority.py"'
for path in dest.rglob("*"):
    if path.suffix not in {".md", ".json"} or not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
PY

cat > "$DEST/.gitignore" <<'EOF'
config/ara.env
config/positions.md
config/holidays.txt
outputs/**
!outputs/.gitkeep
drafts/**
!drafts/.gitkeep
.claude/settings.local.json
__pycache__/
*.pyc
EOF

chmod +x "$DEST/scripts/claude-headless.sh" "$DEST/scripts/install-schedule.sh" "$DEST/scripts/run-due.sh"

if grep -R -n -e "starter-delivery-team" -e "pipelinectl" -e "jiractl" -e "/Users/" -e "atlassian.net" "$DEST" >/dev/null; then
  echo "Export contains delivery-team paths or machine-specific values." >&2
  grep -R -n -e "starter-delivery-team" -e "pipelinectl" -e "jiractl" -e "/Users/" -e "atlassian.net" "$DEST" >&2 || true
  exit 1
fi

echo "Exported the chief of staff to $DEST"
echo "Next: follow $DEST/README.md"
