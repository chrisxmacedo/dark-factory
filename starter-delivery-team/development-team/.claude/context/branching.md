# Branching — {PROJECT_NAME}

Read by: Team Lead, all agent teams (for commit rules)

## Branch types

The repository has four branch types. The Team Lead is the **only agent**
that creates branches or performs merges. No specialist team ever creates
or merges a branch.

```
main        ← receives only: RC merge (Team Lead, after human approval)
  │
  └─► ci    ← receives only: feature branch merges (Team Lead, after local tests pass)
                              RC back-merge (Team Lead, immediately after RC → main)
        │
        ├─► feature/{PROJECT_KEY}-{key}/{slug}  ← Development + Local Test teams commit here
        │     Implementer opens a PR as a signal only — Team Lead merges it
        │     Branch is NEVER deleted after merge — kept for audit
        │
        └─► release-rc-{n}              ← ALWAYS cut from ci HEAD, NEVER from a previous RC
              Each release branch is single-use: cut fresh from ci HEAD,
              merged to main, back-merged to ci, then done.
              Each RC is independent — NEVER branch from or base on a previous RC.
              If ci has moved on since the last RC, the new RC includes everything.
              Regression team validates this branch — Fix Agent may commit
              bug fixes here if genuine regressions are found
              Team Lead merges into main after human approval
              Team Lead back-merges into ci immediately after
              Branch is NEVER deleted after merge — kept for audit
```

## Branch deletion policy

**No branch is ever deleted.** Feature branches, release branches, and all
others are retained permanently after their merges complete. This provides a
full audit trail of every change, every release candidate, and every merge
point. Do not delete branches. Do not squash or flatten commit history.
Feature branches are rebased onto ci before merging. Shared branches (ci,
release, main) are NEVER rebased. All merges use --no-ff merge commits.

## Rebase rules

- **Rebase feature branches** onto ci before merging — this linearises dev work
- **NEVER rebase** ci, release, or main — these are shared branches whose history must be preserved
- All merges use `--no-ff` to preserve integration points in the graph

**Never delete any branch. Never squash. Never commit directly to main — main only receives merges from release branches.**

## RC skip for unchanged repos

When cutting an RC, `pipelinectl cut-rc` compares each repo's ci HEAD with
the last RC branch HEAD. If they are identical (no new commits on ci since
the last RC was cut), that repo is **skipped** — no new RC branch is created.

This means:
- Only repos with actual changes get a new RC branch
- The Docker environments use the latest existing RC image for unchanged repos
- The dashboard only shows RC nodes for repos that changed
- `merge-rc` automatically skips repos without the RC branch

## Git notes for branch tracking

`pipelinectl` annotates branch-off points and merge commits using `git notes`.
This makes branch relationships queryable without inferring them from parent
hashes.

**Notes added automatically:**

| Event | Note on | Note content |
|---|---|---|
| Feature merged into ci | The merge commit on ci | `merge: feature/{key}/{slug} into ci — {key}` |
| Feature branched from ci | The ci commit at the branch point | `branch-off: feature/{key}/{slug} from ci — {key}` |
| RC cut from ci | The ci commit at the cut point | `branch-off: release-rc-{n} from ci — {key}` |
| RC merged into main | The merge commit on main | `merge: release-rc-{n} into main — {key}` |
| Main back-merged into ci | The merge commit on ci | `merge: main (v{x}.{y}.0) back-merge into ci — {key}` |

**Querying notes:**
```bash
git notes show {commit}              # Show note on a specific commit
git log --show-notes --oneline -20   # Show notes alongside log
git notes list                       # List all annotated commits
```

Notes are pushed to the remote via `refs/notes/commits` by pipelinectl.
The environment dashboard uses these to render branch-off and merge lines
between tracks.
