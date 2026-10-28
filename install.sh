#!/usr/bin/env bash
# install.sh — set up the pipeline toolkit on this machine (or for a new client)
#
# Asks for this machine's / client's settings and working preferences, writes
# them to ~/.config/pipeline-toolkit/config.env, links the slash commands into
# ~/.claude/commands, and optionally merges baseline permissions into the
# projects workspace. Safe to re-run: current answers become the defaults.
#
# Usage:
#   ./install.sh              interactive
#   ./install.sh --defaults   accept current/default answers without asking
#
# Nothing secret is stored: Jira API tokens go in each project's
# infra/.env.jira, and the Mission Control bot token stays in your shell env
# (install.sh only records the NAME of the variable that holds it).

set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$HOME/.config/pipeline-toolkit"
CONFIG_FILE="$CONFIG_DIR/config.env"
COMMANDS_DIR="$HOME/.claude/commands"
STAMP="$(date +%Y%m%d-%H%M%S)"

INTERACTIVE=true
case "${1:-}" in
  --defaults) INTERACTIVE=false ;;
  -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
  "") ;;
  *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
esac

say()  { printf '%s\n' "$*"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# ask VAR "Question" "default" [allowed values...]
ask() {
  local var="$1" question="$2" default="$3"; shift 3
  local allowed=("$@") answer
  while true; do
    if $INTERACTIVE; then
      if [ ${#allowed[@]} -gt 0 ]; then
        read -r -p "$question [$(IFS=/; echo "${allowed[*]}")] ($default): " answer || true
      else
        read -r -p "$question ($default): " answer || true
      fi
    fi
    answer="${answer:-$default}"
    if [ ${#allowed[@]} -eq 0 ] || [[ " ${allowed[*]} " == *" $answer "* ]]; then
      printf -v "$var" '%s' "$answer"; return
    fi
    say "  Please answer one of: ${allowed[*]}"
    $INTERACTIVE || { printf -v "$var" '%s' "$default"; return; }
  done
}

# ── Current values become the defaults ──────────────────────────────────────
if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
  say "Existing config found at $CONFIG_FILE — its values are the defaults."
fi

# ── Prerequisites (warn only) ───────────────────────────────────────────────
head_ "Checking prerequisites"
check() { if command -v "$1" >/dev/null 2>&1; then say "  ✓ $1"; else say "  ✗ $1 — $2"; fi; }
check claude  "npm install -g @anthropic-ai/claude-code"
check git     "install Xcode command line tools or git"
check gh      "brew install gh"
check python3 "needed by jiractl, dashboard and capability scripts"
check uv      "brew install uv (Python starters)"
check node    "Node.js 22 (TypeScript starters)"
if v=$(docker compose version --short 2>/dev/null); then
  v="${v#v}"
  if [ "$(printf '%s\n%s\n' 2.24.4 "$v" | sort -V | head -1)" = "2.24.4" ]; then say "  ✓ docker compose $v"
  else say "  ✗ docker compose $v — need >= 2.24.4"; fi
else
  say "  ✗ docker compose — install Docker Desktop or OrbStack"
fi

# ── Questions ───────────────────────────────────────────────────────────────
head_ "Where things live"
ask CLIENT_NAME  "Label for this setup (client or 'personal')" "${CLIENT_NAME:-personal}"
ask PROJECTS_DIR "Projects folder"                            "${PROJECTS_DIR:-$(dirname "$TOOLKIT_DIR")}"
ask IDEAS_DIR    "Ideas folder (one sub-folder per product idea)" "${IDEAS_DIR:-$PROJECTS_DIR/ideas}"

head_ "Atlassian (Jira + Confluence)"
ask ATLASSIAN_SITE "Atlassian site, e.g. acme.atlassian.net"   "${ATLASSIAN_SITE:-}"
ATLASSIAN_SITE="${ATLASSIAN_SITE#https://}"; ATLASSIAN_SITE="${ATLASSIAN_SITE#http://}"; ATLASSIAN_SITE="${ATLASSIAN_SITE%/}"
ask JIRA_EMAIL     "Your Atlassian login email (used for infra/.env.jira; no token stored)" "${JIRA_EMAIL:-}"

head_ "GitHub"
ask GITHUB_ORG "Default GitHub org for new project repos (blank = ask per project)" "${GITHUB_ORG:-}"
say "  Mission Control (GitHub Projects board used by /board, /create-ticket, …)."
ask MC_ORG "  Mission Control org (blank = not used here)" "${MC_ORG:-}"
if [ -n "$MC_ORG" ]; then
  ask MC_PROJECT_NUMBER "  Project number" "${MC_PROJECT_NUMBER:-1}"
  ask MC_PROJECT_ID     "  Project node ID (gh project view N --owner ORG --format json -q .id)" "${MC_PROJECT_ID:-}"
  ask MC_TOKEN_VAR      "  Name of the env var holding the bot token (blank = use your own gh login)" "${MC_TOKEN_VAR:-}"
else
  MC_PROJECT_NUMBER=""; MC_PROJECT_ID=""; MC_TOKEN_VAR=""
fi

head_ "Working preferences (applied to each new project by /create-project)"
say "  Promotion to production: 'human' waits for \"Approve promote KEY-N\";"
say "  'auto' promotes when regression is green (failures still wait for you)."
ask PROMOTE_POLICY     "  Promote to production" "${PROMOTE_POLICY:-human}" human auto
say "  After a ticket is Done: 'auto' starts the next Backlog ticket; 'ask' stops and asks."
ask NEXT_TICKET_POLICY "  Next ticket"            "${NEXT_TICKET_POLICY:-auto}" auto ask
say "  Track work as GitHub issues too (created before work, closed on merge)?"
ask GITHUB_ISSUES      "  GitHub issues"          "${GITHUB_ISSUES:-yes}" yes no

# ── Write config ────────────────────────────────────────────────────────────
head_ "Writing $CONFIG_FILE"
mkdir -p "$CONFIG_DIR"
[ -f "$CONFIG_FILE" ] && cp "$CONFIG_FILE" "$CONFIG_FILE.bak-$STAMP" && say "  previous config saved as config.env.bak-$STAMP"
q() { printf "'%s'" "${1//\'/\'\\\'\'}"; }   # single-quote a value safely
{
  echo "# pipeline-toolkit config — written by $TOOLKIT_DIR/install.sh on $(date '+%Y-%m-%d %H:%M')"
  echo "# Re-run install.sh to change. Sourced by the slash commands."
  echo "CLIENT_NAME=$(q "$CLIENT_NAME")"
  echo "TOOLKIT_DIR=$(q "$TOOLKIT_DIR")"
  echo "PROJECTS_DIR=$(q "$PROJECTS_DIR")"
  echo "IDEAS_DIR=$(q "$IDEAS_DIR")"
  echo "ATLASSIAN_SITE=$(q "$ATLASSIAN_SITE")"
  echo "JIRA_URL=$(q "${ATLASSIAN_SITE:+https://$ATLASSIAN_SITE}")"
  echo "CONFLUENCE_URL=$(q "${ATLASSIAN_SITE:+https://$ATLASSIAN_SITE/wiki}")"
  echo "JIRA_EMAIL=$(q "$JIRA_EMAIL")"
  echo "GITHUB_ORG=$(q "$GITHUB_ORG")"
  echo "MC_ORG=$(q "$MC_ORG")"
  echo "MC_PROJECT_NUMBER=$(q "$MC_PROJECT_NUMBER")"
  echo "MC_PROJECT_ID=$(q "$MC_PROJECT_ID")"
  echo "MC_TOKEN_VAR=$(q "$MC_TOKEN_VAR")"
  echo "PROMOTE_POLICY=$(q "$PROMOTE_POLICY")"
  echo "NEXT_TICKET_POLICY=$(q "$NEXT_TICKET_POLICY")"
  echo "GITHUB_ISSUES=$(q "$GITHUB_ISSUES")"
} > "$CONFIG_FILE"
say "  ✓ written"
[ -z "$ATLASSIAN_SITE" ] && say "  ! No Atlassian site set — the Jira/Confluence commands will ask you to re-run install.sh."

# ── Link slash commands ─────────────────────────────────────────────────────
head_ "Linking slash commands into $COMMANDS_DIR"
mkdir -p "$COMMANDS_DIR"
backup_dir="$COMMANDS_DIR/.backup-$STAMP"
# True if $1's contents match any committed version of repo path $2, i.e. it's
# an old installed copy with no local edits.
is_committed_version() {
  local blob; blob=$(git -C "$TOOLKIT_DIR" hash-object "$1" 2>/dev/null) || return 1
  git -C "$TOOLKIT_DIR" log --all --format=%H -- "$2" 2>/dev/null | while read -r c; do
    [ "$(git -C "$TOOLKIT_DIR" rev-parse -q --verify "$c:$2" 2>/dev/null)" = "$blob" ] && { echo yes; break; }
  done | grep -q yes
}
linked=0; backed_up=0
for src in "$TOOLKIT_DIR"/commands/*.md; do
  name="$(basename "$src")"; dest="$COMMANDS_DIR/$name"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    continue
  elif [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ -f "$dest" ] && [ ! -L "$dest" ] && { cmp -s "$src" "$dest" || is_committed_version "$dest" "commands/$name"; }; then
      :  # same as the repo now or at some earlier commit — no local edits to keep
    else
      mkdir -p "$backup_dir"; mv "$dest" "$backup_dir/"; backed_up=$((backed_up + 1))
    fi
  fi
  ln -sfn "$src" "$dest"; linked=$((linked + 1))
done
say "  ✓ $linked command(s) linked (edits in the repo are live immediately)"
[ "$backed_up" -gt 0 ] && say "  ! $backed_up existing command(s) differed from the repo — moved to $backup_dir"

# ── Baseline permissions for the projects workspace ─────────────────────────
head_ "Permissions"
settings="$PROJECTS_DIR/.claude/settings.json"
ask MERGE_PERMS "Merge baseline permissions into $settings?" "no" yes no
if [ "$MERGE_PERMS" = "yes" ]; then
  mkdir -p "$PROJECTS_DIR/.claude"
  [ -f "$settings" ] && cp "$settings" "$settings.bak-$STAMP"
  python3 - "$TOOLKIT_DIR/config/permissions.baseline.json" "$settings" <<'PY'
import json, os, sys
base, target = sys.argv[1], sys.argv[2]
add = json.load(open(base))["permissions"]["allow"]
cur = json.load(open(target)) if os.path.exists(target) else {}
allow = cur.setdefault("permissions", {}).setdefault("allow", [])
new = [r for r in add if r not in allow]
allow.extend(new)
json.dump(cur, open(target, "w"), indent=2); open(target, "a").write("\n")
print(f"  ✓ {len(new)} rule(s) added, {len(allow)} total")
PY
else
  say "  skipped (baseline is in config/permissions.baseline.json)"
fi

# ── Done ────────────────────────────────────────────────────────────────────
head_ "Done — $CLIENT_NAME"
say "  Config    : $CONFIG_FILE"
say "  Toolkit   : $TOOLKIT_DIR"
say "  Projects  : $PROJECTS_DIR"
say "  Atlassian : ${ATLASSIAN_SITE:-not set}"
say "  Prefs     : promote=$PROMOTE_POLICY, next-ticket=$NEXT_TICKET_POLICY, github-issues=$GITHUB_ISSUES"
say ""
say "Next: connect the Atlassian MCP in Claude, then run /create-project <name>."
say "Chief of staff only (no delivery team): $TOOLKIT_DIR/harness/export-chief-of-staff.sh <empty-dir>"
