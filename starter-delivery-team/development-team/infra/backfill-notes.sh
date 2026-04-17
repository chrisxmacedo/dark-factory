#!/usr/bin/env bash
# backfill-notes.sh — annotate historical merges and branch-offs with git notes.
# Safe to re-run — clears all notes first, then rebuilds.
#
# Walks ci --first-parent to find:
#   - Feature merges (subject: "Merge feature/...")
#   - Back-merges (subject: "Back-merge main...")
# Walks main --first-parent to find:
#   - RC merges (subject: "Merge release-rc-...")
# Annotates branch-off points (the ci commit BEFORE each merge/back-merge)

set -euo pipefail
cd "$(dirname "$0")"
PROJECT_ROOT="$(cd .. && pwd)"

REPOS=()
for d in "$PROJECT_ROOT"/*/; do
  [ -d "$d/.git" ] && REPOS+=("$d")
done

total_notes=0

for repo in "${REPOS[@]}"; do
  name=$(basename "$repo")
  echo "=== $name ==="
  cd "$repo"
  count=0

  # Clear existing notes
  git notes list 2>/dev/null | while read blob hash; do
    git notes remove "$hash" 2>/dev/null || true
  done

  # Get full ci first-parent log (oldest first)
  ci_commits=()
  ci_subjects=()
  ci_parents=()
  while IFS='|' read -r hash subject parents; do
    [ -z "$hash" ] && continue
    ci_commits+=("$hash")
    ci_subjects+=("$subject")
    ci_parents+=("$parents")
  done < <(git log ci --first-parent --format="%H|%s|%P" --reverse 2>/dev/null)

  # Annotate the first ci commit: branch-off from main
  if [ "${#ci_commits[@]}" -gt 0 ]; then
    git notes append -m "branch-off: ci from main" "${ci_commits[0]}" 2>/dev/null || true
    count=$((count + 1))
  fi

  # Walk ci commits in order
  for i in "${!ci_commits[@]}"; do
    hash="${ci_commits[$i]}"
    subject="${ci_subjects[$i]}"
    parents="${ci_parents[$i]}"
    prev_hash=""
    [ "$i" -gt 0 ] && prev_hash="${ci_commits[$((i-1))]}"

    # Feature or fix merge into ci
    if echo "$subject" | grep -qE "^Merge (feature|fix)/"; then
      branch=$(echo "$subject" | sed -n 's/^Merge \([^ ]*\) into ci.*/\1/p')
      if [ -n "$branch" ] && [ -n "$prev_hash" ]; then
        git notes append -m "branch-off: $branch from ci" "$prev_hash" 2>/dev/null || true
        git notes append -m "merge: $branch into ci" "$hash" 2>/dev/null || true
        count=$((count + 2))
      fi
    fi

    # Back-merge main into ci
    if echo "$subject" | grep -q "^Back-merge main"; then
      git notes append -m "merge: $subject" "$hash" 2>/dev/null || true
      count=$((count + 1))

      # The RC was cut from the previous ci commit
      # Find which RC by looking at what was merged into main just before this back-merge
      # The second parent of this back-merge is the main merge commit
      second_parent=$(echo "$parents" | awk '{print $2}')
      if [ -n "$second_parent" ] && [ -n "$prev_hash" ]; then
        rc_name=$(git log --format="%s" -1 "$second_parent" 2>/dev/null | sed -n 's/^Merge \(release-rc-[^ ]*\) into main.*/\1/p' || true)
        if [ -n "$rc_name" ]; then
          git notes append -m "branch-off: $rc_name from ci" "$prev_hash" 2>/dev/null || true
          count=$((count + 1))
        fi
      fi
    fi
  done

  # Annotate main merge commits (RC merges)
  while IFS='|' read -r hash subject; do
    [ -z "$hash" ] && continue
    rc_name=$(echo "$subject" | sed -n 's/^Merge \(release-rc-[^ ]*\) into main.*/\1/p')
    if [ -n "$rc_name" ]; then
      ticket=$(echo "$subject" | grep -o '[A-Z]*-[0-9]*' | tail -1 || true)
      suffix=""
      [ -n "$ticket" ] && suffix=" — $ticket"
      git notes append -m "merge: $rc_name into main${suffix}" "$hash" 2>/dev/null || true
      count=$((count + 1))
    fi
  done < <(git log main --first-parent --format="%H|%s" --reverse 2>/dev/null | grep "Merge release-rc")

  # Push notes
  git push origin refs/notes/commits -f 2>/dev/null || true
  echo "  $count notes added."
  total_notes=$((total_notes + count))
  cd "$PROJECT_ROOT"
done

echo ""
echo "Done. $total_notes notes added across ${#REPOS[@]} repos."
