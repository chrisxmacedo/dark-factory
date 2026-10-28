# starter-delivery-team

End-to-end delivery pipeline. Contains two sub-pipelines and an
orchestrating Programme Lead who moves work across them.

Sibling reference folders at the `templates/` root:
- `../starter-regulations/` — sector-indexed regulations (finance,
  data-protection, cybersecurity, etc.), each with applicable-country
  tagging. Consumed by the capability team during Phase A.
- `../starter-standards/` — non-regulatory standards (accessibility,
  information security, SOC, quality management). Consumed by both
  teams — capability team in Phase A/B (governance, security model),
  development team in build (testing against accessibility or security
  baselines where a project commits to them).

```
starter-delivery-team/
  PIPELINE.md              — Programme Lead orchestration (top-level script)
  PIPELINE-STATE.md        — Cross-pipeline state (ephemeral)
  PORTFOLIO-MAP.md         — Portfolio view: what's in design, what's in build (ephemeral)
  workflow-improvements.md — Cross-pipeline retrospective log
  CONTEXT.md               — This file
  .claude/
    context/
      project.md           — Project identity, Jira keys, team paths
      jira-lifecycle.md    — Projects, components, tickets, Sprint 0 rules, slice rules
      cross-pipeline-flow.md — How work moves design → Jira → build → live
      defect-handling.md   — Cross-pipeline escalation rules
  capability-team/         — Design pipeline (Phases A, B, C)
    PIPELINE.md            — Capability Lead orchestration
    CONTEXT.md
    …
  development-team/        — Build pipeline (Refinement → Release)
    PIPELINE.md            — Team Lead orchestration
    CONTEXT.md
    …
```

## Roles

| Role                | Scope                                              | Script                                  |
|---------------------|----------------------------------------------------|-----------------------------------------|
| **Programme Lead**  | Top-level — moves work across both pipelines        | `starter-delivery-team/PIPELINE.md`     |
| **Capability Lead** | Design pipeline — Phases A, B, C, Gates 1 and 2     | `capability-team/PIPELINE.md`           |
| **Team Lead**       | Build pipeline — feature → ci → RC → main           | `development-team/PIPELINE.md`          |

The Programme Lead NEVER produces artefacts or code. The Capability Lead
and Team Lead never orchestrate across the boundary between design and
build — that is the Programme Lead's job.

## Flow

```
[Capability pipeline]               [Jira handoff]                 [Development pipeline]
┌────────────────────┐        ┌──────────────────────┐        ┌────────────────────────┐
│ Capability Lead    │        │ Programme Lead        │        │ Team Lead              │
│                    │        │                       │        │                        │
│ Phase A Discovery  │        │ On Gate 2 pass:       │        │ Refinement Team        │
│ Phase B Framing    │  ────► │  - verify evidence/   │ ────► │ Development Team       │
│ Phase C Modelling  │        │  - create Deliverable │        │ Local / Integ / E2E    │
│ Gate 1             │        │    in DEV Jira        │        │ Regression / Release   │
│ Gate 2 (per-jrny)  │        │  - attach evidence    │        │                        │
└────────────────────┘        │  - package artefacts  │        │ Reports back:          │
                              │  - notify Team Lead   │ ◄──── │  - on Done              │
                              │                       │        │  - on FIX EXHAUSTED     │
                              │ Routes defects back   │ ────► │                        │
                              │  to Capability Lead   │        │                        │
                              │  if the artefacts are │        │                        │
                              │  the root cause       │        │                        │
                              └──────────────────────┘        └────────────────────────┘
```

## Jira projects

| Project  | Used by         | Purpose                                         |
|----------|-----------------|-------------------------------------------------|
| FOUND    | Capability Lead | Phase A/B artefact tickets                       |
| MODEL    | Capability Lead | Phase C journey epics                            |
| DEV      | Programme Lead → Team Lead | Deliverables derived from stable journeys |

Link conventions:
- FOUND artefact **enables** MODEL journey epic
- MODEL journey **Stable** → Programme Lead creates DEV Deliverable that **implements** the journey
- DEV Deliverable links back to the MODEL journey via an "implements" link

## State files (all ephemeral — not committed)

| File                              | Owned by         | Purpose                                           |
|-----------------------------------|------------------|---------------------------------------------------|
| `PIPELINE-STATE.md` (top)         | Programme Lead   | Cross-pipeline handoff state                       |
| `PORTFOLIO-MAP.md` (top)          | Programme Lead   | Portfolio-level view                               |
| `capability-team/PIPELINE-STATE.md` | Capability Lead | Active journey + signals                          |
| `capability-team/ARTEFACT-MAP.md` | Capability Lead  | Current central-model state                        |
| `development-team/PIPELINE-STATE.md` | Team Lead     | Active ticket + signals                            |
| `development-team/AGENT-CONTEXT.md` | Team Lead       | Service graph + repo map                           |

## Retrospective logs

- `starter-delivery-team/workflow-improvements.md` — cross-pipeline
  retrospectives (handoff friction, misaligned evidence, misrouted
  defects)
- `capability-team/workflow-improvements.md` — design retrospectives
- `development-team/workflow-improvements.md` — build-pipeline
  retrospectives across all Deliverables (owned by the Team Lead)
- Service repos may additionally keep their own `workflow-improvements.md`
  for code/test patterns specific to that service

## Placeholders to replace (top-level)

| Placeholder      | Replace with                    |
|------------------|---------------------------------|
| `{PROJECT_NAME}` | Full project name               |
| `{ORG_NAME}`     | Organisation name               |
| `{FOUND_KEY}`    | Jira Foundation project key     |
| `{MODEL_KEY}`    | Jira Modelling project key      |
| `{DEV_KEY}`      | Jira Development project key    |

The sub-teams have their own placeholders — see their CONTEXT.md files.

## How to kick off a new project

Before any agent runs:

1. **Human creates three Jira projects** via `/create-jira-project`
   (FOUND, MODEL, DEV). See `.claude/context/jira-lifecycle.md` §1 for
   the workflows each project needs.
2. **Human adds API credentials** to `development-team/infra/.env.jira`.
3. **Human replaces placeholders** across this folder:
   `grep -rn "{[A-Z_]\+}" .` and fill in each `{PROJECT_NAME}`,
   `{FOUND_KEY}`, `{MODEL_KEY}`, `{DEV_KEY}`, etc.
4. **Human starts the Programme Lead** pointing at this folder. The
   Programme Lead reads `PIPELINE.md` and spawns the Capability Lead.

No Jira components are needed yet — they are populated at Gate 1 (post
Phase A/B) when the service catalogue is stable. See
`.claude/context/jira-lifecycle.md` §2.

## Relationship to the chief of staff

The technical chief of staff is a separate team (`../teams/chief-of-staff/`).
It may read this team's pull requests, CI, tickets, and delivery metrics
where those appear in GitHub, Jira, or Linear, and it may raise an issue or
chase a deadline. It must not change this team's code, transition its
tickets, or reprioritise its work. Installing this directory does not
install the chief of staff, and the chief-of-staff export does not copy
this directory.
