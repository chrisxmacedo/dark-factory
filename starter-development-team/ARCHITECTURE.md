# Technical Architecture Specification

Template for Solution Architect output. Complete each section when starting a
new project. Delete sections that don't apply. Replace placeholders with
concrete decisions.

---

## Compute & Hosting

- Application hosting platform:
- Container strategy (Docker, serverless, VMs):
- Region and availability zone:
- Scaling model (horizontal, vertical, auto-scale triggers):
- CDN / edge network:

## Application Components

- API service (REST, GraphQL, gRPC):
- Web frontend (SPA, SSR, static site):
- Mobile app (native, cross-platform, PWA):
- Background workers / job queues:
- Scheduled tasks / cron jobs:
- Scrapers / data ingestion pipelines:
- Admin dashboard:

## Inter-Service Contracts

When a project has 2+ services that share data models, API contracts, or
event schemas, decide early how contracts are enforced:

- Shared types package (npm workspace, Python namespace package):
- Schema registry (for event-driven architectures):
- Generated clients from OpenAPI spec:
- Manual contract — duplicated types with integration-test validation:

If services share a secret (JWT signing key, encryption key, webhook secret),
document the coupling in `.secrets.md` under "Shared secrets" so both services
stay in sync when keys rotate.

## Data Layer

- Primary database (Postgres, MySQL, MongoDB):
- Database hosting (Supabase, PlanetScale, RDS, self-hosted):
- Caching layer (Redis, Memcached):
- Search engine (Elasticsearch, Meilisearch, Algolia):
- File / object storage (S3, R2, GCS):
- Message queue / event bus (Kafka, RabbitMQ, SQS):
- Schema management and migrations strategy:

## Authentication & Identity

- Auth provider (Supabase Auth, Auth0, Clerk, Cognito, custom):
- Auth model (JWT, session-based, API keys):
- Role and permission model (RBAC, ABAC):
- OAuth / social login providers:
- Multi-tenancy model (shared DB, schema-per-tenant, DB-per-tenant):

## Observability

- Logging platform (Axiom, Datadog, CloudWatch):
- Structured logging format:
- Error tracking (Sentry, Bugsnag):
- APM / tracing (Datadog, New Relic, OpenTelemetry):
- Uptime / synthetic monitoring (Checkly, Pingdom):
- Alerting and on-call routing (PagerDuty, Opsgenie):
- Health check endpoints:

## Source Control & Repositories

- Repository strategy (monorepo vs multi-repo):
- Repository hosting (GitHub, GitLab):
- GitHub org:
- Branching model (trunk-based, gitflow, custom):
- Code review and merge policy:
- Branch protection rules:

## CI/CD & Deployment

- CI platform (GitHub Actions, CircleCI, GitLab CI):
- Build pipeline stages:
- Test automation in CI:
- Deployment strategy (blue-green, canary, rolling):
- Environment promotion model (dev, staging, production):
- Infrastructure as code (Terraform, Pulumi, CDK):
- Secret management (Vault, Doppler, platform-native):

## Testing Strategy

- Test layers (unit, component, integration, E2E):
- Test frameworks per language/service:
- Test data management (fixtures, factories, seed scripts):
- Contract testing between services:
- Load / performance testing tooling:

## Docker Environments

- CI environment strategy (base + override, ephemeral, LLM stub):
- Test environment strategy (fixture seeding, init containers):
- Prod-parity environment strategy (persisted volumes, real APIs, OTel stack):
- Local service replacements (managed service → Docker equivalent):
- LLM/AI API stub approach (content-hash keyed fixtures):
- Infrastructure metrics exporters (postgres-exporter, redis-exporter):
- Environment variable management (.env.ci committed, .env.prod-parity gitignored):

## API Design

- API style and versioning strategy:
- API documentation (OpenAPI/Swagger, auto-generated):
- Rate limiting and throttling:
- Pagination model:
- Error response format:

## Security

- TLS / certificate management:
- CORS policy:
- Input validation strategy:
- Dependency vulnerability scanning (Dependabot, Snyk):
- Data encryption (at rest, in transit):
- GDPR / compliance posture:
- Backup and disaster recovery plan:

## Payments & Billing

- Payment processor (Stripe, Paddle, Lemon Squeezy):
- Pricing model (flat, per-seat, usage-based, freemium):
- Subscription lifecycle management:
- Invoice and receipt generation:
- Tax handling:

## Communication & Notifications

- Transactional email (Resend, Postmark, SES):
- Push notifications:
- In-app notifications:
- SMS (Twilio, MessageBird):
- Webhook system (outbound events to customers):

## Analytics & Reporting

- Product analytics (PostHog, Mixpanel, Amplitude):
- Business reporting / dashboards:
- Data warehouse (BigQuery, Snowflake, Redshift):
- ETL / data pipeline tooling:
- Customer-facing analytics / reporting:

## Domain & DNS

- Domain registrar:
- DNS provider:
- Subdomain strategy (api.x.com, app.x.com, docs.x.com):
- Email domain (transactional vs marketing):

## Documentation

- Internal technical docs (architecture, runbooks):
- External API docs:
- User-facing docs / help centre:
- Changelog:

## Project Management & Workflow

- Ticket tracking (Jira, Linear, GitHub Issues):
- Knowledge base (Confluence, Notion):
- Development workflow and status model:
- Definition of done per stage:
