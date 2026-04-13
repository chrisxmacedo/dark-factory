# starter-audit

Starter template for immutable audit log and compliance services.

## What this is for

Services that provide an immutable, append-only audit trail:
- Receive audit events from all other services via a message queue
- Store events in an append-only log with tamper-detection hash chain
- Provide query and search capabilities over the audit history
- Enforce configurable retention policies per event type
- Export filtered event data for regulatory and compliance requests

Events are never modified or deleted -- only appended. This is the core
invariant of the service.

## Compatible starters

| Starter | Role |
|---------|------|
| starter-worker | Consumes audit events from queue |
| starter-api | Exposes query endpoints |
| starter-batch | Generates compliance reports, enforces retention policies |
| starter-docs | Produces audit report PDFs |

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Immutable event log with hash chain integrity | **starter-audit** |
| Regulatory query/export (who did what, when) | **starter-audit** |
| Generic background job processing | starter-worker |
| General-purpose REST/GraphQL API | starter-api |
| Scheduled report generation (not audit-specific) | starter-batch |

## Market applications

### Banking
Transaction audit trail, access logs, regulatory reporting (SOX, PCI DSS),
fraud investigation support. Every account action, approval, and transfer
is recorded with actor, timestamp, and outcome.

### Legal
Case activity log, document access tracking, chain of custody for evidence,
billing audit. Tracks who viewed, modified, or shared privileged documents
and when.

### Healthcare
Patient record access logging (HIPAA), medication administration records,
consent tracking, clinical decision audit. Demonstrates compliance with
access controls and data handling requirements.

### Insurance
Claims handling audit, underwriting decision trail, policy change history,
adjuster activity logs. Provides evidence for dispute resolution and
regulatory examination.

### Government
Public records management, decision audit trails, freedom of information
compliance, procurement activity logs. Supports transparency and
accountability requirements.

### Any regulated industry
Who did what, when, to what data, from where. If your industry requires
proof that actions were logged, tamper-evident, and retrievable on demand --
this is the starting point.

## Key characteristics

- **Append-only** -- no UPDATE, no DELETE on audit events. Ever.
- **Hash chain** -- each event includes a cryptographic hash of the previous
  event, enabling tamper detection across the entire log
- **Configurable retention** -- per event type (e.g. financial: 7 years,
  access logs: 1 year). Retention enforcement runs via starter-batch.
- **Query API** -- filter by actor, action, resource, time range with
  pagination
- **Export** -- CSV and JSON export for regulatory requests
- **No business logic** -- receives events, stores them, serves queries

## Tech stack

Node.js 22, TypeScript (strict), Prisma, ioredis, Pino, OpenTelemetry, Zod, Jest
