#!/usr/bin/env bash
# Entry point used by cron. See scripts/run_due.py for the gates.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/run_due.py "$@"
