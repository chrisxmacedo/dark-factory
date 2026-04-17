# Security model best practices

Read by: Discovery Team (step 5)

The security model is a **specification** consumed by the downstream
development pipeline. This file describes what the spec must contain,
not how it is enforced at runtime.

## Zero-trust policy

- `service.yaml` is the authoritative allowed-call policy source per
  service.
- The spec must list, per service:
  - `allowed_callers` — which services may call this service
  - `allowed_callees` — which services this service may call
  - `allowed_topics_produced` and `allowed_topics_consumed`
- Policy diffs (observed calls outside the declared policy) are a
  security signal at runtime — the downstream team builds the
  enforcement; the spec just names the policy.

## mTLS

The spec declares, per service pair that communicates:
- Whether mTLS is required (it should be for all inter-service calls)
- The workload-identity field used for peer identification
- The trust root (shared across the mesh)

## Data classification

The spec assigns a classification to every data element:

| Level         | Meaning                                                |
|---------------|--------------------------------------------------------|
| public        | May be published without restriction                   |
| internal      | Visible to all employees; not external                 |
| confidential  | Restricted to named roles; audit access                |
| regulated     | Special handling required (PII, PCI, health, etc.)     |

Classification is used downstream to decide encryption, masking, audit
routing, and SIEM severity.

## Network segmentation zones

The spec names the zones and which services belong in each:

- **DMZ** — public-facing edges (API gateways, ingress)
- **Application** — capability services
- **Data** — capability data stores
- **Compliance** — audit pipeline, regulated data stores, WORM storage
- **Management** — control plane, CI/CD, secrets management

Cross-zone traffic rules are part of the spec (e.g. Application → Data
allowed; DMZ → Data disallowed).

## Secrets

Per service, the spec lists:
- Named secrets (no values)
- `rotation_days` per secret
- Owner role
- Storage backend (secrets manager / config)

## Controls (what the spec includes, not how they are built)

- Zero-trust policy map
- mTLS requirements per service pair
- Secret rotation schedule
- Blast radius visualisation (derived from `service-dependencies.json`)
- CVE exposure map (derived from `service.yaml` data classification)
- Audit log separation (physical, WORM, auditor-only access)

## Anti-patterns in the spec

- Missing `data_classification` on a service handling user data.
- Secrets listed without `rotation_days`.
- Cross-zone traffic rules left implicit.
- Audit data classified as `internal` — it must be `regulated`.
- mTLS declared optional for inter-service calls — it is not.
