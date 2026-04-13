# starter-serverless

Starter template for serverless functions (AWS Lambda, Cloudflare Workers, Vercel Edge).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Event-driven functions that run on-demand in managed compute environments:
- Webhook receivers (Stripe, GitHub, Twilio, Shopify)
- Payment callback processors (3DS confirmations, refund notifications)
- Image/file processing (resize, thumbnail, format conversion)
- Scheduled tasks (health checks, cache warming, report triggers)
- API endpoints with minimal infrastructure (lightweight CRUD, proxies)
- Edge logic (geo-routing, A/B testing, auth at the edge)

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Stateless, event-triggered function (webhook, cron, edge) | **starter-serverless** |
| Long-running background job processor (queue consumer) | starter-worker |
| Scheduled batch job (large data sets, checkpointing) | starter-batch |
| Full REST API with middleware, auth, versioning | starter-api |
| Full-stack web application with SSR | starter-web |

**Rule of thumb:** if the function runs for under 30 seconds, has no
persistent connections, and responds to a single event, use serverless.
If it needs to stay alive, maintain state, or process queues, use worker
or batch.

## Compatible starters

- **starter-api** -- serverless functions can act as lightweight API routes or webhooks feeding into the main API
- **starter-worker** -- serverless functions can enqueue jobs for workers to process
- **starter-notification** -- serverless can trigger notification dispatch on events
- **starter-audit** -- serverless functions emit audit events for compliance tracking
- **starter-observability** -- OTel Lambda layer or Workers trace integration
- **starter-infrastructure** -- Terraform/Pulumi manages the serverless deployment

## Key characteristics

- **Stateless** -- no in-memory state between invocations
- **Cold-start optimised** -- minimal dependencies, lazy initialisation
- **Bounded runtime** -- Lambda 15 min max, Workers 30s CPU / 30s wall, Edge 30s
- **Event-driven** -- triggered by HTTP, queue, schedule, or storage events
- **Pay-per-invocation** -- cost scales to zero when idle
- **Infrastructure as config** -- deploy via SAM, SST, Wrangler, or Vercel config

## Tech stack

**Lambda variant:** Node.js 20, TypeScript, SST or SAM, AWS SDK v3, middy middleware
**Workers variant:** V8 isolate, TypeScript, Hono, Wrangler, Workers KV/D1
**Edge variant:** Vercel Edge Runtime, TypeScript, Next.js Edge API Routes

## Market applications

### Payments & Financial Services
- Payment webhook processors (Stripe, Adyen, PayPal callbacks)
- 3D Secure completion handlers
- Transaction enrichment (merchant categorisation, currency conversion)
- Fraud scoring pre-checks (sub-second response required)

### E-commerce
- Order event processors (new order, status change, refund)
- Inventory sync triggers (marketplace to warehouse)
- Dynamic pricing calculations at the edge
- Image resizing and optimisation for product catalogues

### SaaS & Developer Platforms
- Webhook relay and transformation (format conversion between services)
- OAuth callback handlers
- Usage metering and event ingestion
- Scheduled health checks and synthetic monitoring

### Media & Content
- Image/video thumbnail generation on upload
- Content moderation triggers (scan on publish)
- CDN cache invalidation handlers
- PDF generation from templates

### IoT & Event Processing
- Device telemetry ingestion (MQTT to database)
- Alert threshold evaluation
- Geo-fence entry/exit event handling
- Sensor data aggregation and forwarding
