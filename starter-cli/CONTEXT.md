# starter-cli

Starter template for command-line tools (Node.js/TypeScript or Go).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

CLI tools that automate workflows, interact with APIs, or process data:
- Data migration and transformation (CSV/JSON/SQL pipelines)
- API client wrappers (authenticated CRUD against a backend)
- DevOps tooling (deploy scripts, environment management, secret rotation)
- Developer experience tools (scaffolders, linters, code generators)
- Reporting and export (fetch data, format, output to file or stdout)

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Interactive CLI tool distributed via npm or binary | **starter-cli** |
| Background job processor (long-running, queue-based) | starter-worker |
| Scheduled batch job (cron, run-and-exit) | starter-batch |
| REST API serving HTTP requests | starter-api |
| Serverless function (event-triggered, cloud-hosted) | starter-serverless |

**Rule of thumb:** if a human types a command and gets output in their
terminal, use starter-cli. If the process runs unattended in the cloud,
use worker, batch, or serverless.

## Compatible starters

- **starter-api** -- backend API the CLI authenticates against
- **starter-gateway** -- API gateway the CLI routes through
- **starter-batch** -- CLI can trigger batch jobs or share data pipeline logic
- **starter-infrastructure** -- CLI may wrap Terraform/Pulumi commands
- **starter-observability** -- CLI can emit OTel traces for long operations

## Key characteristics

- **Structured output** -- human-readable by default, `--json` flag for machine parsing
- **Stderr for logs, stdout for output** -- pipeable by design
- **Config file support** -- dotenv and/or RC file (~/.{tool}rc)
- **--verbose and --dry-run** -- standard flags on every command
- **Exit codes** -- 0 success, 1 general error, 2 usage error
- **Cross-platform** -- runs on macOS, Linux, Windows (WSL at minimum)

## Tech stack

**TypeScript variant:** Node.js 22, TypeScript (strict), Commander.js, Zod, dotenv, Jest
**Go variant:** Go 1.22+, cobra, viper, zerolog, go test, goreleaser

## Market applications

### Banking & Finance
- Data migration tools (legacy system exports, ledger reconciliation)
- Regulatory report generators (CSV/PDF from transaction data)
- Account provisioning and bulk operations

### DevOps & Platform Engineering
- Deployment orchestrators (multi-service rollouts)
- Secret rotation and environment sync tools
- Infrastructure audit and compliance checkers

### SaaS
- API CLI clients (CRUD operations, webhook management)
- Tenant provisioning and configuration tools
- Data export and backup utilities

### Data Engineering
- ETL pipeline runners (extract, transform, load to warehouse)
- Schema migration tools
- Data quality validation and profiling

### Developer Tooling
- Project scaffolders and code generators
- CI/CD helper scripts (version bumping, changelog generation)
- Local development environment managers
