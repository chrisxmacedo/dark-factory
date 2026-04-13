# starter-notification

Starter template for multi-channel notification delivery services.

## What this is for

Services that receive notification requests (from other services via API or
event queue), resolve user delivery preferences, render templates, and deliver
via one or more channels:

- **Email** — Resend, Amazon SES
- **SMS** — Twilio
- **Push** — Firebase Cloud Messaging (FCM), Apple Push Notification Service (APNS)
- **In-app** — Database write + WebSocket push to connected clients

The service tracks delivery status per channel (sent, delivered, failed,
bounced) and handles per-channel retry with backoff.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Generic background job processing | starter-worker |
| HTTP API serving requests | starter-api |
| Notification dispatch + delivery tracking | **starter-notification** |
| Real-time WebSocket server | starter-realtime |

## Compatible starters

- **starter-worker** — notification service consumes events produced by workers
- **starter-api** — exposes a preference management API for end users
- **starter-realtime** — pushes in-app notifications via WebSocket

## Key characteristics

- **Multi-channel delivery** — email, SMS, push, in-app from a single request
- **User preferences** — respects channel opt-ins, quiet hours, frequency caps
- **Template rendering** — Handlebars templates with variable substitution
- **Idempotent** — duplicate notification IDs are safely ignored
- **Per-channel retry** — each channel retries independently with backoff
- **Delivery tracking** — sent, delivered, failed, bounced per notification per channel
- **Circuit breakers** — external providers degrade gracefully under failure
- **Observability** — structured logging, OpenTelemetry traces, health endpoint

## Tech stack

Node.js 22, TypeScript (strict), Prisma, ioredis, Pino, OpenTelemetry,
Handlebars, Resend, Twilio, Firebase Admin, Jest

## Market applications

### Banking & Finance
- Transaction alerts (debit, credit, large amount)
- Statement ready notifications
- Payment due reminders
- Fraud alerts (immediate multi-channel: SMS + push + email)

### Legal
- Case status updates
- Deadline and filing reminders
- Document ready for review
- Hearing schedule changes

### Healthcare
- Appointment reminders (SMS + email, configurable lead time)
- Test results available
- Prescription ready for pickup
- Care plan follow-up prompts

### E-commerce
- Order confirmation and receipt
- Shipping and delivery updates
- Review and feedback requests
- Back-in-stock alerts

### SaaS
- Onboarding email sequences
- Usage threshold alerts (approaching plan limits)
- Billing and invoice notifications
- Feature announcements and changelog digests

### Insurance
- Claim status updates
- Policy renewal reminders
- Premium payment due
- Policy change confirmations
