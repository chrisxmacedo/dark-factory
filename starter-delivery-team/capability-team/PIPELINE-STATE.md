# Pipeline State — {PROJECT_NAME}

The Capability Lead updates this file after every agent signal, every
script run, and every gate transition. It is the crash-recovery source
of truth — if the session is compacted or restarted, this file (plus
the contents of `artefacts/`) is enough to resume.

**Do not commit this file** — it is ephemeral pipeline state.

**Read by the Programme Lead** (`../PIPELINE.md`) — the Programme Lead
polls this file to detect `GATE 1 PASSED`, `GATE 2 PASSED`, and
`FIX EXHAUSTED` signals. Keep the "Signals received" checkboxes and
"Last action" current so the handoff is not missed.

## Current phase

- **Phase:** {Phase A — Discovery | Phase B — Framing | Phase C — Analytical Modelling}
- **Gate passed:** {none | Gate 1 | Gate 2 — last for {journey-slug}}
- **Last updated:** {ISO timestamp}

## Active journey (Phase C only)

- **Journey ID:** {JRN-NNN}
- **Slug:** {journey-slug}
- **Status:** {scaffolded | in modelling | in review | stable}
- **Scaffold timestamp:** {ISO timestamp}
- **Next-available IDs at scaffold:** {PH-NNN, ENT-NNN, EVT-NNN}

## Signals received (for the active journey)

- [ ] SCAFFOLD COMPLETE — {timestamp}
- [ ] JOURNEY MODEL COMPLETE — {timestamp}
- [ ] CLEANUP-IDS RAN — {timestamp}
- [ ] SYNC-CENTRAL-MODEL RAN — {timestamp}
- [ ] REVIEW COMPLETE (Stage 1) — {verdict} — {timestamp}
- [ ] REVIEW COMPLETE (Stage 2) — {verdict} — {timestamp}
- [ ] GATE 2 PASSED — {timestamp}

## Last action

{One sentence describing the last thing the Capability Lead did or spawned.
Example: "Spawned journey-modelling-team for JRN-003 account-opening. Waiting
for JOURNEY MODEL COMPLETE signal."}

## Open refinement tickets (cross-journey)

| Refinement ID | Source journey | Target journey/entity | Status |
|---------------|----------------|------------------------|--------|
|               |                |                        |        |

## Phase A/B state (set once)

- [ ] Step 1 Capabilities — baselined
- [ ] Step 2 Technical services — baselined
- [ ] Step 3 Governance — baselined
- [ ] Step 4 Personas — baselined
- [ ] Step 5 Visual architecture + C4 L1/L2 — baselined
- [ ] Step 5 Service dependencies + catalogue — baselined
- [ ] Step 5 Observability model — baselined
- [ ] Step 5 Security model — baselined
- [ ] Step 5 Environment spec — baselined
- [ ] Step 6 Journey inventory — prioritised
- [ ] Gate 1 passed

## Recent journeys (most recent first)

| Journey ID | Slug | Gate 2 passed | Entities added | Events added |
|------------|------|---------------|-----------------|---------------|
|            |      |               |                 |               |
