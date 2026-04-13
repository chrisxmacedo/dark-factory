# Git Conventions

Read by: Team Lead, all agent teams (cross-cutting)

## Commit messages

Format: `{PROJECT_KEY}-{key}: {description}`

- Use imperative present tense ("Add parser", not "Added parser")
- First line under 72 characters
- Add a blank line and body paragraph for complex changes explaining
  why the change was made, not just what changed
- Every commit message must include the Deliverable Jira ID

Example:
```
HIN-208: T3: Add COinS metadata parser

Extract COinS spans from HTML pages and convert embedded key-value
pairs into structured citation objects. Required for the bibliography
import pipeline.
```

## Commit granularity

- One commit per logical change — never batch unrelated changes
- Commit after every file change, then push immediately to origin
- Each commit must be independently understandable
- Never commit generated files: `node_modules/`, `dist/`, `.next/`,
  `__pycache__/`, `coverage/`, compiled output

## PR conventions

- PR title must include the ticket key (e.g. `HIN-208: Add COinS parser`)
- PR description must cover:
  - **What** changed and why
  - **Why** this approach was chosen
  - **How to test** the change locally
- The Implementer opens PRs targeting `ci` as a signal that work is
  complete — the Implementer does not merge the PR
- The Team Lead merges the PR after the completion gate passes and
  local tests confirm the feature works
- PRs always target `ci`, never `main` — main only receives merges
  from release branches

## Code review signals

The Devil's Advocate reviews continuously during development, not as a
post-hoc gate. Findings are sent via inbox as they arise:

```
CRITIQUE [low|medium|high]: {issue} — {file:line if known} — {suggestion}
```

- **low** — style nit, minor improvement, advisory only
- **medium** — potential bug or missed edge case, should be addressed
- **high** — mandatory fix: security flaw, data loss risk, violated
  pattern, missing transaction, untestable code

High-severity critiques must be addressed or explicitly acknowledged
with rationale before the completion gate can pass. The Devil's
Advocate sends a `FINAL REVIEW: [pass|concerns]` summary when the
Implementer signals completion.

## Merge strategy

All merges preserve history. Never squash. Never fast-forward. Never
delete branches.

- **Feature branch into ci**: rebase the feature branch onto ci first
  to linearise development work, then merge with `--no-ff` to preserve
  the integration point
- **Release candidate into main**: merge with `--no-ff` — the merge
  commit marks the release point
- **Main back into ci**: merge with `--no-ff` immediately after the
  RC-to-main merge so ci picks up the release commit
- Shared branches (`ci`, `main`, release branches) are never rebased —
  only feature branches are rebased
- Branches are never deleted after merge — retained permanently for
  audit trail

## What not to commit

These paths must never be committed. Add them to `.gitignore`:

- `.env`, `.env.*` — secrets and environment-specific config
- `node_modules/` — installed dependencies
- `__pycache__/`, `*.pyc` — Python bytecode
- `.next/` — Next.js build cache
- `dist/`, `build/` — compiled output
- `coverage/` — test coverage reports
- `.DS_Store` — macOS filesystem metadata

If any of these are already tracked, remove them from tracking with
`git rm --cached` and add to `.gitignore` before proceeding.

## Pre-push hooks

The repository uses `.githooks/pre-push` to enforce branch protection:

- Direct pushes to `main` and `ci` are blocked
- Only merge commits are allowed on protected branches
- All developers must configure the hooks directory:
  `git config core.hooksPath .githooks`

If the pre-push hook rejects a push, do not bypass it. Fix the
underlying issue (e.g. commit to a feature branch instead, or ensure
the push contains a merge commit from the Team Lead).

## Tagging

- Version tags are created exclusively by `pipelinectl merge-rc`
  during the release process
- Never create version tags manually
- Tags follow semantic versioning: `v{major}.{minor}.{patch}`
- The tag is applied to the merge commit on `main` when the release
  candidate is merged

## Git notes

`pipelinectl` uses `git notes` to annotate branch-off points and merge commits.
This creates a queryable record of branch relationships without relying on
parent hash inference.

- **Branch-off notes** are added to the ci commit where a feature or RC diverged
- **Merge notes** are added to the merge commit on the target branch
- Notes are pushed to the remote via `refs/notes/commits`
- The environment dashboard reads notes to render branch/merge lines between tracks

Agents do NOT need to create git notes manually — `pipelinectl` handles this
automatically during `merge-to-ci`, `cut-rc`, and `merge-rc` operations.

To query notes:
```bash
git log --show-notes --oneline -20   # Show notes alongside log
git notes show {commit_hash}         # Show note on a specific commit
```

---

NEVER:
- Squash commits — history must be preserved for audit
- Fast-forward merge — all merges use `--no-ff`
- Delete any branch — feature, release, or otherwise
- Commit directly to `main` — main only receives merges from release branches
- Commit secrets, credentials, or environment files
- Create version tags manually — only `pipelinectl merge-rc` tags releases
- Bypass the pre-push hook with `--no-verify`
