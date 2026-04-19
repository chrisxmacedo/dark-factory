# Agentic Above, Deterministic Below

The principle: make every workflow as deterministic as possible.
Agents provide the reasoning layer on top — handling ambiguity,
novel situations, output composition, multi-step planning, and
self-critique. Everything that can be scripted, validated, or
templated is pushed down into the deterministic layer. The agent
operates in the space that remains.

## The two layers

### The deterministic layer (below)

This is code. It runs the same way every time. It does not reason,
interpret, or improvise. It either passes or fails.

Examples from the capability pipeline:

| Task | Script | What it guarantees |
|------|--------|--------------------|
| ID assignment | `scaffold-journey.py` | Globally sequential, no collisions |
| ID cleanup | `cleanup-ids.py` | No annotated IDs in output |
| Central model sync | `sync-central-model.py` | Entity files exist, events catalogued |
| File validation | `validate-journey.py` | Required files present, schema compliant |
| Architectural rules | `validate-sequences.py` | No sync cross-capability calls |
| Data traceability | `validate-data-integrity.py` | All field references resolve |
| Schema generation | `generate-event-schemas.py` | Avro from event catalogue |
| Data manifests | `generate-step-manifest.py` | Per-step I/O from artefacts |

These scripts encode decisions that were made once and should never
be revisited. The ID format is `PH-NNN`. The communication rule is
async events only between capabilities. The entity file goes in
`central-model/entities/`. These are not judgment calls — they are
rules. Rules belong in code, not in prompts.

### The agentic layer (above)

This is reasoning. It handles the parts of the workflow where the
answer is not predetermined — where context, judgment, and domain
knowledge are required.

Examples from the capability pipeline:

| Task | Why it needs an agent |
|------|----------------------|
| Market research | Requires synthesising competitive landscape, regulatory horizon, and build-vs-buy signals from unstructured sources |
| Capability decomposition | Requires judgment about what constitutes a business domain boundary |
| Promotion decisions | Requires weighing 4 criteria against market evidence — the criteria are fixed but the assessment is not |
| Journey design | Requires understanding what happens in each phase, what the actors do, what the exception paths are |
| Data model design | Requires deciding which entities exist, which fields they have, what the relationships are |
| Sequence diagram design | Requires reasoning about the order of operations, error handling, and data flow |
| Cross-artefact review | Requires checking whether the journey contradicts the governance rules, whether the entity names are consistent, whether the specification is buildable |

These tasks cannot be scripted because the answer depends on the
domain. A script cannot decide whether Mortgages should be promoted
to a standalone capability. A script cannot design the exception
path for a sanctions hit on a payment. A script cannot assess whether
a data model entity has the right fields for a developer to implement.

## The boundary between layers

The boundary is not fixed. It moves as the pipeline matures:

1. **First run**: almost everything is agentic. The agent creates
   capabilities, journeys, entities, events from scratch. The
   deterministic layer is just the scaffold script.

2. **After the first run**: patterns emerge. The agent keeps making
   the same mistakes (annotated IDs, missing entity files, wrong key
   names). Each recurring mistake becomes a script. The deterministic
   layer grows.

3. **After 30 journeys**: ~40% of the workflow is deterministic.
   ID assignment, cleanup, sync, validation, schema generation, and
   manifest creation are all scripted. The agent focuses on the 60%
   that requires reasoning.

4. **For the next project**: the deterministic layer is inherited.
   The scripts, schemas, templates, and validation rules carry forward.
   The agent starts with a tighter harness and produces consistent
   output from journey 1, not journey 15.

## Why this matters for AI development teams

Traditional software development has the same split — developers
reason about design while CI pipelines validate deterministically.
But with AI agents, the split is more critical because:

1. **Agents drift.** A human developer learns from code review and
   doesn't repeat the same structural mistake 30 times. An agent
   will produce `ENT-F001` in one session and `ENT-043` in the next,
   with no memory of which convention was agreed. Scripts prevent this.

2. **Agents can't self-validate.** An agent asked to check its own
   work will often confirm it is correct even when it isn't. External
   validation scripts are the only reliable quality gate.

3. **Agents are stateless across sessions.** The Programme Lead agent
   can't persist across 30 journeys — it hits context limits after
   2-3. Each re-spawn starts fresh. The deterministic layer provides
   continuity: the scaffold reads the artefact directory to know what
   IDs are taken, not the agent's memory.

4. **Agents are expensive.** Every token of reasoning costs money and
   time. If a task can be done by a 50-line Python script in 200ms,
   running it through an agent that takes 60 seconds and 50K tokens
   is waste. Push deterministic work down; reserve agent reasoning
   for the problems that need it.

## The design principle

When designing a workflow for AI agents:

1. **Start with the agent doing everything.** Let it produce output
   freely. Observe what it gets right and what it gets wrong.

2. **Identify the recurring failures.** These are the tasks that
   feel like reasoning but are actually rules. Annotated IDs, missing
   files, wrong key names, format drift — these are not judgment
   calls. They are conventions that the agent cannot reliably follow.

3. **Script the recurring failures.** Write a deterministic check or
   fix for each one. Add it to the pipeline.

4. **Validate, don't instruct.** Instead of adding more instructions
   to the agent prompt ("please use PH-NNN format"), add a validator
   that rejects non-compliant output. Instructions are suggestions.
   Validators are enforcement.

5. **Measure the split.** Track what percentage of the workflow is
   deterministic vs agentic. If it's below 30%, you're relying too
   much on agent consistency. If it's above 70%, you've probably
   over-constrained the agent and lost the reasoning value.

6. **Evolve the boundary.** After each run, review what the agent
   got wrong. If the mistake is structural (format, convention,
   reference integrity), script it. If the mistake is substantive
   (wrong capability boundary, missing journey phase, incorrect
   entity relationship), improve the instructions.

The goal is not to eliminate the agent. The goal is to give the agent
the smallest possible surface area of genuinely ambiguous decisions,
supported by the largest possible foundation of deterministic
guarantees.

Agentic above. Deterministic below.

See also: [ai-harness](ai-harness.md), [strategic](strategic.md),
[operational](operational.md)
