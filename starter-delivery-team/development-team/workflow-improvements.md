# Workflow improvements — {PROJECT_NAME} (development-team)

Append a retrospective entry after every Deliverable reaches Done,
after each Diagnostics cycle, and after each pipeline stage that had
friction. The Team Lead writes the entry; any specialist team may
contribute.

**Scope:** build-pipeline learnings only. Cross-pipeline learnings
(design ↔ build handoff) go in `../workflow-improvements.md` at the
delivery-team root. Service-specific code/test patterns go in each
service repo's own `workflow-improvements.md`.

**Format per entry:**

```
## {DEV-key} — {stage or event} — {YYYY-MM-DD}

**What happened:**
- {one line}

**Root cause or insight:**
- {one line}

**What to do differently:**
- {one concrete action}

**Candidate for automation / pipelinectl check:**
- {if the issue could be caught by a script or pipeline gate}
```

---

<!-- Entries below, most recent first -->
