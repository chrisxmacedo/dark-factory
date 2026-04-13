# CLAUDE.md — {project-name}-orchestrator

This file covers coding conventions for this orchestrator service. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

---

## Stack

- **Node.js 22**, TypeScript (strict), Prisma, ioredis, Pino
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Type checking:** tsc --noEmit
- **Testing:** Jest + ts-jest

---

## Project structure

```
src/
├── index.ts              # Entry point: init OTel, start API server,
│                         #   start workflow consumer, register shutdown handlers
├── health.ts             # HTTP health endpoint at /healthz
├── engine/
│   ├── state-machine.ts  # Core state machine: define states, transitions,
│   │                     #   guards, execute transitions
│   ├── executor.ts       # Workflow executor: load definition, advance state,
│   │                     #   handle timeouts, dispatch steps
│   └── compensation.ts   # Compensation handler: run rollback steps in
│                         #   reverse order on failure
├── workflows/            # Workflow definitions (one file per workflow type)
│   └── example-workflow.ts  # Example: approval flow with 4 states
├── steps/                # Step implementations (one file per step)
│   └── example-step.ts   # Example: idempotent step returning success/failure/pending
├── api/
│   └── workflows.ts      # HTTP routes: trigger, status, signal (approval/rejection)
└── lib/
    ├── prisma.ts         # Prisma client singleton with lazy connect
    ├── redis.ts          # ioredis singleton with retry strategy
    ├── logger.ts         # Pino logger + createWorkflowLogger(workflowId, stepName?)
    └── otel.ts           # OpenTelemetry SDK initialisation
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode — no `any`, no implicit returns
- Never use `console.log` — use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from environment variables
- Never commit `.env` — use `.env.example` as the reference

### Workflow definitions (src/workflows/)
- One file per workflow type in `src/workflows/`
- Each workflow exports a `WorkflowDefinition` containing:
  - States (with metadata: timeout, compensation function, etc.)
  - Transitions (source state, target state, event, guard condition)
  - Initial state and terminal states (success + failure)
- Workflow definitions are pure data — no side effects, no I/O
- Guard functions are pure predicates on workflow context

### Step implementations (src/steps/)
- One file per step in `src/steps/`
- Every step MUST be idempotent — safe to run multiple times with the
  same workflow instance. Check for existing results before executing.
- Steps return a `StepResult`: `success`, `failure`, or `pending`
  - `success` — step completed, workflow advances
  - `failure` — step failed, trigger compensation if configured
  - `pending` — step awaiting external signal (approval gate, webhook)
- Steps receive the workflow context and return an updated context
- Steps must not manage their own state persistence — the executor does that

### Approval gates
- A step returning `pending` pauses the workflow
- The workflow resumes when an external signal arrives via
  `POST /workflows/:id/signal`
- Signal payloads are validated against the expected signal schema
- Approval gates have timeouts — if no signal arrives, the workflow
  transitions to a timeout state

### Timeouts
- Each step definition includes an optional `timeoutMs`
- The workflow definition includes an optional `maxDurationMs`
- The executor checks timeouts on each poll/advance cycle
- Timed-out steps trigger the configured timeout transition

### Compensation (rollback)
- Each step definition includes an optional `compensate` function
- If a step fails after previous steps succeeded, the compensation handler
  runs compensate functions for completed steps in reverse order
- Compensation functions are best-effort — they log failures but do not
  throw (the workflow is already in a failed state)
- Compensation functions must also be idempotent

### State persistence
- Every state transition is stored in the database with:
  - workflow ID, from-state, to-state, event, timestamp, context snapshot
- The executor loads the current state from DB on every advance
  (crash recovery: restart from last persisted state)
- Use database transactions when updating workflow state and step results

### Event-driven architecture
- Workflows are triggered by events arriving on a Redis queue
- On completion/failure, the orchestrator publishes an event to Redis
- Events include: workflow ID, type, final state, result summary

### Logging
- Use structured logging with Pino
- Every log line inside a workflow must include `workflowId` and
  `stepName` (when available) — use `createWorkflowLogger()` for this
- Log at these levels:
  - `info` — workflow started, step completed, workflow completed, signal received
  - `warn` — step timeout, compensation started, retry attempt
  - `error` — workflow failed, compensation failed, unrecoverable error

### Graceful shutdown
- On SIGTERM/SIGINT: complete the current step, do not start new steps,
  close DB and Redis connections, then exit
- Shutdown timeout: if current step does not finish within N seconds,
  force exit with a non-zero code
- The health endpoint must return unhealthy during shutdown

### Health endpoint
- Serve `/healthz` on a configurable port (default 8080)
- Check: database connectivity, Redis connectivity, executor status
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability
- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Traces should span the entire workflow execution (one root span per workflow)
- Each step gets a child span under the workflow span
- Add span attributes: `workflow.type`, `workflow.id`, `workflow.state`,
  `step.name`, `step.result`

### Testing
- Every step needs at least one test for the happy path and one for
  idempotency (running the same step twice produces the same result)
- Workflow definitions need tests for transition logic (given state + event,
  assert next state)
- Compensation logic needs tests (given failure at step N, assert steps
  N-1..1 are compensated in order)
- Mock external services — never call real APIs in tests
- Tests must not depend on each other or on execution order

---

## Common commands

```bash
npm install                    # Install dependencies
npm run dev                    # Start with tsx watch (hot reload)
npm run build                  # Compile TypeScript
npm start                      # Run compiled output
npm test                       # Run tests
npm run lint                   # Lint
npm run format                 # Format
npx tsc --noEmit               # Type check
npx prisma generate            # Regenerate Prisma client
npx prisma db push             # Push schema to database
```

---

## Before writing code

- Read existing files in the area being modified before generating any code
- If modifying an existing module, read the current implementation first
- Verify you are in the correct repo: `pwd && git remote get-url origin`

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npx tsc --noEmit && npm run lint && npm test
```
