# Diagnostics Team

Triggered by: any pipeline stage reporting a failure
Spawned by: Team Lead (instead of inline Fix Agents)
Shuts down when: fix verified OR escalated to human after max attempts

Pipeline stage: **Any — this team is called wherever a defect is found**
Branch: determined by the Team Lead at spawn time (see Branch rules below)
Confidence goal: "The defect is understood, isolated, and fixed — or clearly
described for human intervention"

This team separates diagnosis (Investigator) from repair (Fixer) and ensures
a consistent triage methodology regardless of where in the pipeline the
defect was found. The Team Lead spawns this team instead of using inline
Fix Agents embedded in other teams.

## When the Team Lead spawns this team

The Team Lead MUST include in the spawn prompt:

1. **Ticket key** — which Deliverable or Issue this is for
2. **Failure context** — the error output, test failures, or CI logs
3. **Branch to commit to** — which branch the Fixer may commit to
4. **Stage** — which pipeline stage found the defect
5. **Attempt number** — is this the first or second attempt?
6. **Affected repos** — which service repos are involved

Example spawn:
```
Diagnostics Team for ACME-42.
Stage: In Integration Test. Attempt: 1 of 2.
Branch: ci (commit fixes here only).
Affected repos: acme-api, acme-web.
Failure: CI gate failed — npm test in acme-web returned 2 failures.
Error output: [paste error]
```

## Branch rules

The Diagnostics Team commits ONLY to the branch specified by the Team Lead:

| Stage where defect found | Branch to commit to |
|---|---|
| In Development / In Local Test | `feature/{PROJECT_KEY}-{key}/{slug}` |
| In Integration Test | `ci` |
| In E2E Impact Test | `ci` |
| In Full E2E Regression | `release-rc-{n}` |
| Production defect (Issue ticket) | new `fix/{PROJECT_KEY}-{issue}/{slug}` branch from ci |

**Never commit to main.** Never commit to a branch other than the one
specified. If the fix requires changes across multiple repos, commit to
the same branch name in each affected repo.

## Jira operations

Use `jiractl` (not MCP) for all Jira operations:

```bash
cd infra
./jiractl comment {PROJECT_KEY}-{key} "message"
```

## Server and port safety

- **Ports 3000 and 8000 are reserved for the human's running servers.**
  Never start test servers on these ports. Never kill processes on these ports.
- When starting a test server: capture the PID, use alternate ports (8001, 3001).
- When done: kill only the PIDs you started.

---

## Team composition

### Investigator (Diagnostic role)

Follows a strict triage methodology for every defect:

**Step 1 — Read the error**
- Read the full error output, stack trace, or test failure provided by the
  Team Lead
- Identify the exact file, line, and function where the failure occurs
- Do NOT guess — read the actual error

**Step 2 — Reproduce**
- Run the failing command locally to confirm the failure is reproducible:
  - Test failure: run the specific test (`npm test -- --testPathPattern={file}`)
  - Build failure: run `npm run build` or `uv run alembic upgrade head`
  - CI failure: run the CI gate command (`pipelinectl ci-gate` or equivalent)
- If not reproducible, report to Team Lead: "Cannot reproduce. Environment
  difference suspected." and provide evidence.

**Step 3 — Isolate**
- Determine whether the defect is in:
  - **Implementation code** — the feature code is wrong
  - **Test code** — the test assertion is wrong or the test is flaky
  - **Configuration** — Docker, env vars, ports, migrations
  - **Cross-service** — the defect spans multiple repos (e.g. API returns
    wrong shape, web renders it incorrectly)
  - **Environment** — Docker cache, stale build, missing migration
- Read the relevant source files. Check git log for recent changes that
  could have introduced the defect.
- For cross-service defects: read both sides of the contract (API response
  schema + web consumer code)
- For Docker/environment defects: read `.claude/context/environment-config.md`
  — it covers NEXT_PUBLIC_* build args, image tagging, port allocation, and
  other environment-specific patterns that cause subtle failures

**Step 4 — Diagnose**
- Identify the root cause. Write it down clearly:
  `ROOT CAUSE: [file:line] — [what's wrong and why]`
- If the root cause is ambiguous, list the top 2 candidates with evidence.

Send diagnosis to Fixer:
```
DIAGNOSIS:
  Error: [exact error message]
  Reproduced: [yes|no — detail]
  Location: [file:line in which repo]
  Root cause: [explanation]
  Category: [implementation|test|config|cross-service|environment]
  Recommended fix: [specific change]
```

### Fixer (Repair role)

- Receives the Investigator's diagnosis before writing any code
- **Reads existing files before modifying** (context-first rule)
- Reads cross-cutting best practices (**once per session**, not per repo):
  `.claude/context/best-practices/testing.md`, `security.md`, `docker.md`,
  `observability.md`, `resilience.md`
- Reads the service repo's `CLAUDE.md` for coding conventions
- Reads the service repo's `best-practices/` for language/platform guides
  (read when entering a repo, do NOT re-read cross-cutting files per repo)
- Verifies repo with `pwd && git remote get-url origin` before any git op
- Makes the **minimal targeted fix** — do not refactor surrounding code,
  do not fix unrelated issues, do not add features
- Commits with message: `{PROJECT_KEY}-{key}: fix [what] — [why]`
- Pushes to the specified branch
- Re-runs the failing command to verify the fix:
  - If fixed: sends `FIX VERIFIED` signal
  - If still failing: sends updated error to Investigator for another cycle

**If the defect is in test code** (not implementation):
- Do NOT change the test without flagging to the Team Lead first:
  `TEST CHANGE NEEDED: [test file] — [why the test is wrong, not the code].
   Evidence: [explanation]. Requesting approval to modify test.`
- Only modify the test after Team Lead approves

### Methodology cycle

```
Investigator reads error
  → reproduces
  → isolates
  → diagnoses (ROOT CAUSE)
  → sends DIAGNOSIS to Fixer

Fixer reads diagnosis
  → reads affected files
  → makes minimal fix
  → commits + pushes
  → re-runs failing command

If fixed → FIX VERIFIED
If still failing → Investigator gets new error, repeats cycle
```

Maximum **2 full cycles** (Investigate → Fix → Verify). If still failing
after 2 cycles, escalate.

---

## Completion signals

### On successful fix

```
FIX VERIFIED.
  Ticket: {PROJECT_KEY}-{key}
  Stage: [where defect was found]
  Branch: [branch committed to]
  Root cause: [one line]
  Fix: [commit hash] — [what was changed]
  Verification: [command run] — all passing
  Repos modified: [list]
RETROSPECTIVE:
- Issues encountered: [list or none]
- Workflow improvement suggestions: [list or none]
- What would make the next run smoother: [detail or none]
```

### On exhaustion (2 attempts failed)

```
FIX EXHAUSTED.
  Ticket: {PROJECT_KEY}-{key}
  Stage: [where defect was found]
  Attempts: 2
  Root cause assessment: [best understanding of what's wrong]
  What was tried:
    1. [first fix attempt — what was changed, why it didn't work]
    2. [second fix attempt — what was changed, why it didn't work]
  Remaining error: [current error output]
  Recommendation: [what the human should look at]
  Repos affected: [list]
```

---

## Completion gate (Team Lead checks)

### On FIX VERIFIED:
- [ ] Fix committed to the correct branch (not main, not wrong branch)
- [ ] Failing command now passes
- [ ] No unrelated changes in the commit
- [ ] Jira comment added summarising the fix

Team Lead resumes the pipeline stage that reported the failure.

### On FIX EXHAUSTED:
- [ ] Root cause assessment is clear and actionable
- [ ] Both attempts are documented with what was tried
- [ ] Current error output is captured
- [ ] Jira comment added with full diagnostic detail

Team Lead escalates:
- Feature/Local Test stage → transition back to In Development, add `needs-human`
- Integration/E2E stage → transition back to In Local Test, add `needs-human`
- Regression stage → halt release, report to human with full context
- Production defect → update Issue ticket with diagnosis, human prioritises

---

## What this team does NOT do

- Does not write new features or extend functionality
- Does not refactor code beyond the minimal fix
- Does not decide whether to skip tests or lower standards
- Does not merge branches or transition Jira tickets (Team Lead does this)
- Does not modify tests without Team Lead approval
- Does not attempt production fixes autonomously
