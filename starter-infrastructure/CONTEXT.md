# starter-infrastructure

Starter template for Infrastructure as Code (Terraform/Pulumi).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Declarative infrastructure definitions for production deployments:
- Cloud resource provisioning (VPC, compute, databases, caches, CDN)
- Environment management (dev, staging, prod with shared modules)
- Compliance-auditable infrastructure (change history, drift detection)
- Security-hardened setups (encryption at rest, least-privilege IAM, network isolation)
- Multi-service platform infrastructure (supporting all other starters)

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Provision and manage cloud infrastructure | **starter-infrastructure** |
| Deploy serverless functions | starter-serverless (uses this for underlying infra) |
| Application code and business logic | starter-api, starter-web, starter-worker, etc. |
| Observability stack configuration | starter-observability (uses this for collector/storage infra) |
| Docker Compose local environments | starter-delivery-team/development-team (infra/ directory) |

**Rule of thumb:** if you are defining what cloud resources exist and how
they are configured, use starter-infrastructure. If you are writing
application code that runs on those resources, use the appropriate service
starter.

## Compatible starters

- **All service starters** -- infrastructure provisions the compute, database, cache, and storage that services run on
- **starter-delivery-team** -- pipeline orchestration deploys to infrastructure managed by this starter
- **starter-observability** -- infrastructure provisions the collector, storage, and dashboards
- **starter-serverless** -- Lambda/Workers infrastructure defined here, function code in serverless starter

## Key characteristics

- **Declarative** -- desired state, not imperative scripts
- **Modular** -- reusable modules for common patterns (VPC, RDS, ECS, etc.)
- **Environment parity** -- same modules, different variables per environment
- **Remote state** -- S3 + DynamoDB locking (no local state files)
- **Security first** -- encryption, least-privilege, and compliance scanning built in
- **Plan before apply** -- all changes are reviewed as plans before execution
- **Tagging policy** -- every resource tagged for cost allocation and ownership

## Tech stack

Terraform (HCL) preferred, AWS provider, S3 backend, tflint, checkov,
GitHub Actions for plan-on-PR / apply-on-merge

## Market applications

### Banking & Finance (PCI-DSS, SOX)
- Payment processing infrastructure (isolated VPC, encrypted databases, WAF)
- Audit-compliant environments with immutable logging
- Multi-region failover for high-availability transaction processing
- Network segmentation between cardholder data and public zones

### Healthcare (HIPAA)
- Encrypted-at-rest databases and storage for PHI
- VPN-only access to sensitive environments
- Audit logging with tamper-proof retention
- BAA-eligible service selection and configuration

### Insurance (SOX, state regulations)
- Claims processing infrastructure with data residency controls
- Disaster recovery with defined RPO/RTO targets
- Segregated environments for actuarial and customer-facing systems

### SaaS & Multi-tenant
- Tenant isolation patterns (shared infra with logical separation or dedicated VPCs)
- Auto-scaling compute for variable workloads
- CDN and edge distribution for global user base
- Zero-downtime deployment infrastructure (blue/green, canary)

### Government & Public Sector
- GovCloud-compliant infrastructure
- FedRAMP boundary definitions
- Air-gapped environment provisioning
- Data sovereignty and residency enforcement

### Any Production Deployment
- Standard three-tier architecture (CDN -> compute -> database)
- CI/CD infrastructure (runners, artifact storage, deployment pipelines)
- Monitoring and alerting infrastructure
- Cost management (tagging, budgets, reserved capacity)
