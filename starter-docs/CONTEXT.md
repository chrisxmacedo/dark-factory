# starter-docs

Starter template for document generation and storage services.

## What this is for

Services that generate documents (PDF, DOCX) from templates and data, store
them in S3/MinIO, and provide retrieval APIs. Handles template management,
variable substitution, versioning, and bulk generation.

- Accept a template identifier + data payload, produce a rendered document
- Store generated documents in S3/MinIO with metadata in the database
- Provide signed URLs for secure, time-limited downloads
- Support bulk generation (e.g. end-of-month statements for all customers)
- Version documents — regenerate when data changes, keep history

## Compatible with

| Template | Integration |
|----------|------------|
| starter-api | Serves document download endpoints to end users |
| starter-batch | Bulk document generation (monthly statements, annual reports) |
| starter-notification | Sends generated documents as email attachments |

## Market applications

### Banking
Account statements, transaction receipts, loan agreements, regulatory reports,
KYC/AML compliance letters, wire transfer confirmations.

### Legal
Contracts, court filings, client letters, case summaries, engagement letters,
NDAs, settlement agreements, billing statements.

### Healthcare
Patient reports, lab results, discharge summaries, insurance claims,
referral letters, consent forms, prescription summaries.

### Insurance
Policy documents, claim forms, certificates of insurance, renewal notices,
endorsement schedules, loss run reports.

### HR
Offer letters, payslips, employment contracts, compliance reports,
performance reviews, termination letters, benefits summaries.

### E-commerce
Invoices, receipts, shipping labels, return forms, packing slips,
credit notes, warranty certificates.

## Key characteristics

- **Template-driven** — Handlebars templates define document structure and layout
- **Multi-format** — PDF (via Puppeteer/Chromium) and DOCX output
- **Storage abstraction** — S3/MinIO via AWS SDK, works in local dev and production
- **Signed URLs** — time-limited download links, no direct storage access
- **Versioned** — every generation creates a new version, previous versions retained
- **Stateless generation** — receives data, produces files, no business logic
- **Queue-ready** — bulk generation integrates with Redis queues

## Tech stack

Node.js 22, TypeScript (strict), Puppeteer, Handlebars, AWS SDK v3, Prisma,
ioredis, Pino, OpenTelemetry, Jest
