# Capability-Driven Architecture for AI Development Teams

## Architecture Specification

---

## 1. Overview

This document describes a capability-driven architecture designed for
systems built by AI development teams. The architecture applies to any
domain where a system can be decomposed into distinct business
capabilities — regulated industries, e-commerce, logistics, healthcare,
financial services, or any organisation with multiple functional areas
that need to coordinate.

The architecture has two runtime layers and one design-time layer:

- **Capability Layer** (runtime) — business domain groupings containing
  independently deployable technical services
- **Platform Layer** (runtime) — shared infrastructure that all
  capabilities depend on
- **Contract Layer** (design-time) — specification artefacts that live in
  the repository and CI pipeline, consumed by channel UIs and AI
  development agents

---

## 2. The Capability Layer

### 2.1 What a Capability Is

A capability is a business domain grouping. It represents what the
organisation does, not how the software is built. Capabilities are
identified by mapping the business domain, not by analysing the
technology.

A capability is NOT a single deployable service. It is a grouping of one
or more independently deployable technical services that together fulfil
a business domain's responsibilities.

### 2.2 What a Capability Contains

Each capability contains:

- **One or more technical services** — APIs, workers, processors,
  scheduled jobs, or any other deployment unit the domain requires.
  These are the actual running processes.
- **Its own data** — one or more databases or database schemas. Services
  within a capability may share a database or have their own. This is an
  internal decision, invisible to other capabilities.
- **Published event contracts** — the events it produces, registered in
  the platform's Schema Registry.
- **Consumed event subscriptions** — the events it listens for from other
  capabilities.
- **A REST API surface** — exposed to external consumers (channel UIs,
  internal tooling, external partners).

### 2.3 Communication Within a Capability

Services within a capability communicate by whatever means makes sense
for the domain. This is an internal technical decision. Options include:

- Synchronous REST/gRPC calls between services within the capability
- Shared database access where services read from and write to common tables
- Direct method calls if services are co-located in the same process
- Internal message queues if the domain requires async processing within
  its boundary

The architecture does not prescribe how services within a capability talk
to each other. The capability boundary is a business domain boundary, not
a technical communication boundary. The team or AI agent working on that
capability decides the internal structure.

### 2.4 Communication Across Capabilities

Communication between capabilities is exclusively asynchronous events
through the Platform Layer's Event Bus. This is the hard architectural
rule.

- A capability **never** calls another capability's API directly.
- A capability **never** reads from or writes to another capability's
  database.
- A capability **never** communicates synchronously with another
  capability.

### 2.5 Shared Data Models

Capabilities do not share data models. Each capability owns its own
representation of shared concepts.

Synchronisation happens through domain events. When a capability changes
shared data, it publishes an event. Each consuming capability updates its
own representation independently.

Reference data is published by whichever capability is authoritative and
consumed as read-only by others.

### 2.6 Journey State

User journeys are not orchestrated by a central process manager or saga.
Journey state is implicit in the data held by capabilities.

There is no separate state machine. The data IS the state.

### 2.7 Channel Interaction

Channel UIs (customer-facing apps, websites, internal tooling, partner
portals) sit outside the system boundary. They interact with capabilities
through their published REST APIs using standard stateless
request-response calls.

A channel may call multiple capabilities in sequence to assemble a user
journey. The channel orchestrates the user interaction; the event bus
orchestrates the cross-capability consequences.

---

## 3. The Platform Layer

### 3.1 What the Platform Layer Is

The Platform Layer is shared infrastructure that all capabilities depend
on. It provides technical primitives but contains no business logic. The
principle is: share the mechanism, isolate the state.

### 3.2 Platform Services

- **Event Bus** — routes domain events between capabilities. Stateless
  infrastructure; routes messages without owning business state.
- **Schema Registry** — validates event payloads at runtime during
  serialisation and deserialisation. The one element of the contract layer
  that operates at runtime.
- **Observability** — traces, metrics, and logs across all capabilities.
  One shared collector and backend.
- **Audit Pipeline** — immutable append-only audit logging. Shared
  pipeline mechanism, separate audit streams per capability.
- **Auth & Identity** — one token validation middleware, one identity
  provider.
- **Cache** — shared instance with key namespacing per capability.

### 3.3 Shared vs Isolated

- **Shared instance**: Event Bus, Observability, Auth, Schema Registry.
- **Isolated per capability**: Databases, audit streams, cache keys.

---

## 4. The Contract Layer

### 4.1 What the Contract Layer Is

The Contract Layer is a design-time concern. It consists of specification
artefacts that live in the repository and CI pipeline. They are not
runtime containers and do not appear on C4 diagrams.

### 4.2 Contract Artefact Types

- **API Contracts** — OpenAPI specs per capability (not per service).
  Each capability exposes one API surface to channels. Internal service
  routing is an implementation detail. Validation at runtime is performed
  by the application framework, not by referencing the spec file.
- **Event Contracts** — schemas registered in the Schema Registry. The
  schema definitions live in the repository; the Schema Registry enforces
  them at runtime.
- **Journey Contracts** — process specifications defining how capabilities
  compose for a given user outcome. Nothing reads them at runtime.
- **Regulatory or Domain Constraints** — compliance rules implemented as
  validation logic within capabilities. At runtime, they are just code.

### 4.3 Who Consumes the Contract Layer

- Channel developers use API contracts and journey contracts.
- AI development agents use the full contract layer as navigation aid.
- CI pipelines use contracts for contract testing and schema validation.

---

## 5. Communication Summary

There are exactly four valid communication paths:

### 5.1 Channel → Capability API (synchronous REST)

Channels (web portal, mobile app, internal tooling, branch terminal,
partner portal) call the capability's published REST API. The capability
routes internally to whatever service handles the request. The channel
never addresses a service directly — it only sees the capability's API
surface. A persona (customer, analyst, officer) always interacts through
a channel, never directly with a service or capability.

Example: A credit analyst uses the internal portal (channel) which calls
`GET /loan-applications/{id}/credit-assessment` on the Commercial
Banking capability API. The capability routes to its internal credit
assessment service.

### 5.2 Event Bus → Capability (asynchronous events)

A capability publishes a domain event to the Event Bus. Other
capabilities consume it independently. The consuming capability routes
internally to the right service. This is the sole mechanism for
cross-capability communication. No synchronous cross-capability calls.

Example: Commercial Banking publishes LoanApproved; Risk Management
consumes it to update exposure calculations.

### 5.3 Service → Service within a capability (internal)

Services within the same capability communicate by whatever means the
capability decides — direct method calls, shared database, internal
REST/gRPC, internal queues. This is an internal implementation detail,
invisible outside the capability boundary.

Example: The mortgage underwriting service calls the affordability
calculation service; both are within the Retail Banking capability.

### 5.4 Service → Platform service (infrastructure)

Any service can call platform infrastructure (IAM, Audit, Observability,
Cache, Schema Registry, Notifications). These are shared mechanisms
that sit below the capability layer.

No other communication paths exist. Services are never directly
addressable from outside their capability.

---

## 6. C4 Mapping

### 6.1 L1 — System Context

Shows the system boundary and its users. People: actual users. External
systems: regulators, payment providers, industry infrastructure. AI
agents do not appear — development concern, not system user.

### 6.2 L2 — Container Diagram

Shows only what runs in production. Two boundary groupings:

- **Capabilities boundary** — capability containers with async event
  arrows between them.
- **Platform boundary** — infrastructure containers below capabilities.
  Dependency arrows flow downward.

The Contract Layer does not appear on L2.

### 6.3 L3 — Component Diagram

Zooms into a single capability: internal services, inbound/outbound
ports, API controllers, data stores, platform adapters. No design-time
artefacts.

---

## 7. AI Agent Context Boundaries

An AI agent working on a capability loads:

1. The capability's internal services and components
2. The event contracts it publishes and consumes
3. The API contract it exposes
4. The platform adapter interfaces it uses
5. The journey contracts that describe this capability's role

It never sees inside other capabilities — only their published schemas
and API specs.

### 7.1 Context Budget

Each capability should maintain a target maximum size in tokens. A
capability that exceeds its context budget is a candidate for
decomposition — not because of team structure (Conway's Law), but
because of cognitive structure: the AI agent can no longer reason about
the whole capability at once.

---

## 8. Key Architectural Principles

1. **Capabilities are business domain groupings, not deployment units.**
   A capability contains one or more independently deployable services.
2. **Cross-capability communication is exclusively asynchronous events.**
   No synchronous calls between capabilities.
3. **Share the mechanism, isolate the state.** Platform infrastructure is
   shared; business data is isolated per capability.
4. **Each capability owns its own data representations.** No shared data
   models. Synchronisation through domain events.
5. **Journey state is implicit in capability data.** No central
   orchestrator or saga.
6. **The Contract Layer is design-time, not runtime.** The Schema
   Registry is the sole runtime manifestation.
7. **C4 diagrams show only what runs in production.**
8. **Capabilities are sized to fit within an AI agent's context window.**
   This is the primary decomposition constraint.
