# starter-orchestrator

Starter template for workflow state machine and orchestration services.

## What this is for

Services that manage multi-step processes with:
- Branching logic (state machines with conditional transitions)
- Approval gates (workflow pauses until external signal)
- Timeouts (per-step and per-workflow maximum durations)
- Compensation (rollback of completed steps when a later step fails)

The orchestrator receives workflow trigger events, advances through states
based on transition rules and guard conditions, and coordinates with other
services at each step.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| HTTP API serving requests | starter-api |
| Background job processing | starter-worker |
| Multi-step process with state machine logic | **starter-orchestrator** |
| Notifications at workflow milestones | starter-notification (called by orchestrator) |
| Audit trail of state transitions | starter-audit (receives events from orchestrator) |

## Compatible services

- **starter-worker** — executes individual steps dispatched by the orchestrator
- **starter-notification** — sends notifications at workflow milestones
- **starter-api** — exposes workflow status endpoints to clients
- **starter-audit** — logs every state transition for compliance

## Market applications

### Banking
- **Loan approval** — application -> credit check -> underwriting -> approval/rejection -> disbursement
- **Account opening** — identity verification -> compliance screening -> account provisioning -> welcome pack
- **KYC verification** — document upload -> automated checks -> manual review -> approval/rejection
- **Wire transfer approval** — initiation -> sanctions screening -> limit checks -> dual approval -> execution

### Legal
- **Case lifecycle** — intake -> review -> filing -> discovery -> trial -> settlement/judgment
- **Document approval chains** — draft -> review -> legal review -> signoff -> execution
- **Contract management** — negotiation -> internal review -> counterparty review -> execution -> renewal

### Healthcare
- **Patient journey** — admission -> triage -> treatment plan -> treatment -> discharge -> follow-up
- **Insurance pre-authorisation** — request -> clinical review -> peer review -> approval/denial
- **Clinical trial enrollment** — screening -> consent -> eligibility -> randomisation -> monitoring

### Insurance
- **Claims processing** — submission -> initial assessment -> investigation -> adjudication -> approval -> payment
- **Policy underwriting** — application -> risk assessment -> pricing -> approval -> issuance
- **Fraud investigation** — flagging -> assignment -> investigation -> determination -> resolution

### HR
- **Employee onboarding** — offer acceptance -> background check -> IT setup -> training -> probation review
- **Leave approval** — request -> manager review -> HR review -> approval/denial
- **Performance review** — self-assessment -> manager review -> calibration -> feedback delivery

### E-commerce
- **Order fulfillment** — payment confirmed -> picking -> packing -> shipping -> delivery confirmation
- **Return processing** — request -> approval -> shipping label -> receipt -> inspection -> refund
- **Subscription lifecycle** — signup -> trial -> conversion -> renewal -> cancellation/retention

## Key characteristics

- **State machine core** — workflows defined as states, transitions, guards, and actions
- **Idempotent steps** — every step can be safely retried
- **Compensation/rollback** — failed workflows undo completed steps in reverse order
- **Approval gates** — workflows pause and resume on external signals
- **Timeout handling** — per-step and per-workflow maximum durations
- **Event-driven** — receives trigger events, emits completion/failure events
- **Full audit trail** — every state transition persisted with timestamp

## Tech stack

Node.js 22, TypeScript (strict), Prisma, ioredis, Pino, OpenTelemetry, Jest
