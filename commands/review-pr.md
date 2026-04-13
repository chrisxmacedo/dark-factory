---
description: Self-review the current PR via a sub-agent before human review
---

# Review PR: $ARGUMENTS

Perform a thorough self-review of the open pull request for the current branch.
This runs as a sub-agent — read everything fresh, with no assumptions.

---

## Step 1 — Identify the PR

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
BRANCH=$(git branch --show-current)

PR=$(gh pr view "$BRANCH" --repo "$REPO" \
  --json number,title,body,baseRefName,headRefName,url)
```

If no open PR exists for this branch, say so and stop.

---

## Step 2 — Read the linked issue

Extract the issue number from the PR body (look for `Closes #N`).

```bash
gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json title,body
```

Read the full acceptance criteria carefully. This is the definition of done.

---

## Step 3 — Read the diff

```bash
gh pr diff "$PR_NUMBER" --repo "$REPO"
```

Read every changed file in full. Do not skim.

---

## Step 4 — Read context files

Read the following if they exist:
- `CLAUDE.md` — project conventions
- `PRD.md` — product requirements
- Any files adjacent to the changed files that provide context

---

## Step 5 — Evaluate against criteria

Check each acceptance criterion from the issue. For each one, determine:
- ✓ Met — with a brief explanation of where/how
- ✗ Not met — with a specific explanation of what's missing
- ⚠ Partial — met in some cases but not all

---

## Step 6 — Code quality checks

Run these locally:

```bash
# Linting and formatting
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src/

# Tests
uv run pytest --tb=short
```

Report results. If any fail, fix them before proceeding.

---

## Step 7 — Review checklist

Check each of the following:

**Correctness**
- [ ] All acceptance criteria met
- [ ] No obvious logic errors
- [ ] Edge cases handled (empty inputs, missing data, auth failures)
- [ ] Error responses use consistent JSON shape

**Code quality**
- [ ] Type annotations on all functions and return values
- [ ] Pydantic schemas for all request/response bodies
- [ ] No hardcoded values that should be config/env vars
- [ ] No commented-out code or TODO comments
- [ ] No unused imports

**Tests**
- [ ] New code has test coverage
- [ ] Tests are meaningful (not just asserting 200 OK)
- [ ] Tests cover error/edge cases

**Conventions**
- [ ] Follows patterns established in existing codebase
- [ ] Consistent naming with rest of project
- [ ] CLAUDE.md conventions followed

---

## Step 8 — Output the review

Format:

```
PR Review — #{pr_number} {title}

Acceptance Criteria
  ✓ {criterion}
  ✓ {criterion}
  ✗ {criterion} — {what's missing}

CI Checks
  ✓ ruff check
  ✓ ruff format
  ✓ mypy
  ✓ pytest (42 passed)

Code Quality
  {any issues found, or "No issues found"}

Verdict
  {APPROVED — ready for human review}
  {CHANGES NEEDED — list specific items to fix}
```

If changes are needed, fix them immediately, push to the branch, and re-run
this review from Step 3.

If approved, say:

> "PR is ready for human review. Run `gh pr view --web` to open it."
