# AI Harness

The AI harness is the envelope that controls AI agents within a
development pipeline. It is not the agent itself — it is the
structure around the agent that constrains what it can do, validates
what it produces, and determines when it is done.

Without a harness, an AI agent is a powerful but undirected reasoning
engine. It can produce impressive output on any prompt, but there is
no guarantee that the output conforms to a schema, follows a process,
respects architectural rules, or is consistent with prior work. The
harness provides those guarantees.

## What the harness contains

### Instructions (what to do)

Agent team documents that define the role, responsibilities, inputs,
outputs, and completion signals for each agent:

- **Programme Lead** — orchestrates phases, spawns teams, enforces
  gates. Never produces artefacts.
- **Discovery Team** — researches the market, drafts capabilities,
  maps governance, identifies personas. Signals DISCOVERY COMPLETE.
- **Journey Modelling Team** — produces journey artefacts (steps 7-13),
  runs cleanup and sync scripts. Signals JOURNEY MODEL COMPLETE.
- **Review Team** — runs deterministic validation scripts, then
  applies reasoning-based review. Signals REVIEW COMPLETE with verdict.

Each team has a markdown file that the agent reads before starting
work. The file is the harness — it tells the agent what is expected,
what format to use, what rules to follow, and when to stop.

### Schemas (what shape the output must be)

Canonical JSON schemas for every artefact type. The agent produces
content; the schema constrains the structure. If the output doesn't
validate against the schema, the Review Team rejects it.

Schemas enforce:
- Field names (one canonical name per concept — `persona_id` not
  `participant_id`)
- ID formats (`PH-NNN`, `ENT-NNN`, `EVT-NNN`)
- Required fields (every entity needs `id`, `name`, `fields`)
- Type constraints (`computed_from` is an object with `formula` and
  `source_fields`, not a free-text string)

### Scripts (what can be checked mechanically)

Deterministic validation and generation scripts that replace agent
judgment with code wherever possible:

- **scaffold-journey.py** — assigns globally sequential IDs, creates
  template files with the correct structure
- **cleanup-ids.py** — strips annotations the agent adds despite
  being told not to
- **sync-central-model.py** — copies entities and events to the
  central model (the agent's most common failure mode)
- **validate-journey.py** — checks file existence, ID formats,
  entity ownership, schema conformance
- **validate-sequences.py** — enforces cross-capability async-only
  communication rule
- **validate-data-integrity.py** — traces field references from
  entities through events through API contracts
- **generate-event-schemas.py** — produces Avro schemas from event
  catalogues
- **generate-step-manifest.py** — produces per-step data manifests

These scripts are the most valuable part of the harness. They catch
errors the agent produces consistently (annotated IDs, missing entity
files, cross-capability sync calls) and remove them mechanically.

### Gates (when work can proceed)

Quality gates that block progression until conditions are met:

- **Gate 1: Modelling readiness** — all foundation artefacts baselined,
  journey inventory prioritised, first journey selected
- **Gate 2: Journey stable** — all validators pass, Review Team
  approves, central model updated

Gates are binary. They are not negotiable. An agent cannot argue its
way past a gate — the scripts either pass or they don't.

### Process improvements (what was learned)

A living document that captures generalised learnings from running
the pipeline. Each learning becomes either a script (if deterministic)
or an instruction update (if reasoning-based). The harness evolves.

## Why the harness matters

An AI agent without a harness produces work that is individually
impressive but systemically inconsistent. The first artefact is
well-structured. The fifth uses different key names. The tenth
contradicts the third. By the thirtieth, the accumulated drift
makes the output unusable without manual reconciliation.

The harness prevents this by:

1. **Constraining the output space** — schemas and templates limit
   what the agent can produce to what the pipeline can consume
2. **Validating mechanically** — scripts catch errors that the agent
   produces systematically, without relying on the agent to self-correct
3. **Enforcing process** — gates block progression until quality is
   met, preventing garbage-in-garbage-out propagation
4. **Learning from failures** — process improvements capture what
   went wrong and encode the fix as either a script or an instruction

## The harness is not the agent

The harness does not contain the agent's reasoning ability, domain
knowledge, or creative capacity. It contains the structure that makes
those abilities useful at scale. A brilliant agent in a poor harness
produces inconsistent work. A mediocre agent in a strong harness
produces reliable, validated, buildable specifications.

The goal is to make the harness as tight as possible — maximise the
deterministic envelope, minimise the space where the agent can drift —
while leaving the agent free to reason about the genuinely ambiguous
parts: market research, capability decomposition, journey design,
data model decisions, and architectural trade-offs.

See also: [strategic](strategic.md), [operational](operational.md),
[agentic-above-deterministic-below](agentic-above-deterministic-below.md)
