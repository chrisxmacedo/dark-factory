#!/usr/bin/env bash
# Print (or install) cron lines for the office jobs.
#
# The crontab only starts scripts/run-due.sh. That script runs the data
# pulls first and starts Claude only when the job's gate is open.
#
#   scripts/install-schedule.sh --print
#   scripts/install-schedule.sh --install
#
# --install rewrites the block between the chief-of-staff markers in the
# user crontab. It does not touch other lines.

set -euo pipefail

OFFICE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$OFFICE_ROOT"
MODE="print"
case "${1:-}" in
  ""|--print) MODE="print" ;;
  --install) MODE="install" ;;
  -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
  *) echo "Unknown argument: $1" >&2; exit 2 ;;
esac

if [ -f scripts/office_env.py ] && [ -f config/ara.env ]; then
  eval "$(python3 scripts/office_env.py --shell)"
fi
TZ_NAME="${OFFICE_TZ:-UTC}"
RUNNER="$OFFICE_ROOT/scripts/run-due.sh"
BEGIN="# BEGIN technical-chief-of-staff"
END="# END technical-chief-of-staff"

block="$(python3 - "$OFFICE_ROOT" "$RUNNER" "$TZ_NAME" "$BEGIN" "$END" <<'PY'
import json, sys
root, runner, tz, begin, end = sys.argv[1:]
jobs = json.load(open(root + "/schedules/jobs.json"))["jobs"]
print(begin)
print(f"TZ={tz}")
print(f"# Office root: {root}")
for job in jobs:
    cron = job["cron"]
    print(f"{cron} {runner} --job {job['id']}  # {job['responsibility']}")
print(end)
PY
)"

printf '%s\n' "$block"
if [ "$MODE" = "print" ]; then
  exit 0
fi

current="$(crontab -l 2>/dev/null || true)"
python3 - "$current" "$block" "$BEGIN" "$END" <<'PY' | crontab -
import sys
current, block, begin, end = sys.argv[1:]
lines = current.splitlines()
kept = []
skipping = False
for line in lines:
    if line.strip() == begin:
        skipping = True
        continue
    if line.strip() == end:
        skipping = False
        continue
    if not skipping:
        kept.append(line)
while kept and kept[-1] == "":
    kept.pop()
if kept:
    kept.append("")
sys.stdout.write("\n".join(kept + block.splitlines()) + "\n")
PY
echo "Installed the chief-of-staff block into the user crontab."
