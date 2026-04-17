# Artefact Map — {PROJECT_NAME}

Quick-reference map of the current state of `artefacts/`. The Capability Lead
regenerates this after every Gate 2 pass so the next journey's modelling
team can orient without re-reading the full tree.

**Do not commit this file** — it is a local working document regenerated
from `artefacts/` contents.

**Regenerate with:**
```bash
python3 scripts/summarise-central-model.py > ARTEFACT-MAP.md
```
(If the script does not yet exist, update this file by hand after each Gate 2.)

## Foundation (Phase A + B — baselined once)

| Artefact | Count | Notes |
|----------|-------|-------|
| Capabilities | {N} | {list IDs} |
| Sub-capabilities (promoted) | {N} | {list} |
| Sub-capabilities (retained) | {N} | {list} |
| Shared sub-capabilities | {N} | {list} |
| Technical services | {N} | {N domain, N cross-cutting, N foundation} |
| Governance rules | {N} | {across N capabilities} |
| Personas | {N internal, N external} | {list} |
| Channels | {N} | {list} |

## Architecture

| Artefact | State |
|----------|-------|
| Visual architecture | {layers, N channels} |
| C4 workspace | L1 + L2 baselined; L3 diagrams for {N} containers |
| Service dependencies | {N services across T0-T4, N build phases} |
| Service catalogue | {N services} |
| Observability model | {N log categories, N instrumentation items} |
| Security model | {N data classifications, N zones} |
| Environment spec | CI / RC / prod-parity defined |

## Central model

| Aggregation | Count | Most recent change |
|-------------|-------|---------------------|
| Entities | {N} | {journey that last changed} |
| Services | {N} | {journey} |
| Events | {N} | {journey} |

## Journey status

| Journey ID | Slug | Status | Capabilities touched | Entities added | Events added |
|------------|------|--------|-----------------------|-----------------|---------------|
|            |      |        |                       |                 |               |

## Open cross-journey refinements

| ID | Source | Impact | Status |
|----|--------|--------|--------|
|    |        |        |        |

## Known conflicts / watchlist

- {Any entities with naming collisions flagged but not resolved}
- {Any sub-capability promotion decisions still pending review}
- {Any cross-capability integration points flagged for Architect review}
