# Capability decomposition best practices

Read by: Discovery Team (Phase A)

See `context/architecture-specification.md` for the authoritative definition.
This file captures the working rules for drafting capabilities and
sub-capabilities during Phase A.

## What a capability is

- A **capability** is a business domain grouping containing one or more
  independently deployable technical services. It is NOT a single service.
- A capability owns its data — one or more databases or schemas,
  invisible to other capabilities.
- Capabilities are stable over decades — they change only when the
  mandate changes.
- Technology choices are derived from capability requirements, never
  the reverse.
- **Capabilities are sized to fit an AI agent's context window.** This
  is the primary decomposition constraint.

## Research before drafting

The agent must research the market landscape for each capability domain
before producing artefacts. A capability list derived only from the org
chart produces a shallow architecture.

Research captures:
- **Competitive landscape** — who does what, what's being unbundled or
  re-bundled
- **Regulatory horizon** — what's coming in 2-3 years
- **Build-vs-buy assessment** — what platforms exist, what must be in-house
- **Sub-capability boundary evidence** — market structure informs the
  promotion test

Each capability artefact includes a `market_context` section capturing
the research findings that informed its design.

## Sub-capability promotion test

Every sub-capability must be evaluated against four criteria:

1. Distinct external participants?
2. Separate regulatory framework?
3. Distinct lifecycle (end-to-end phases that don't map onto the parent)?
4. Independent scalability requirements?

If 3+ criteria met → **promote** to a separate service within the
capability. Document the decision in the artefact.

- **Retained** sub-capabilities are implemented as internal modules
  within an existing service — shared database, direct method calls.
- **Promoted** sub-capabilities become their own service (own repo, own
  deployment unit) but remain inside the capability boundary. They may
  share databases with other services in the same capability or have
  their own — this is an internal decision.

Promotion does NOT mean leaving the capability. A promoted sub-capability
is still part of its parent capability. It becomes a separate service,
not a separate capability. Cross-capability communication rules do not
apply within the capability boundary.

The market research from Step 1 provides evidence for promotion:
- Specialist providers exist → evidence for distinct participants and
  independent scalability
- Separate regulation governs it → evidence for separate regulatory
  framework
- The market treats it as a distinct product → evidence for distinct
  lifecycle

## Shared sub-capabilities

When a sub-capability appears in more than one capability:

- Record in `foundation/shared-sub-capabilities.json`
- Document the architectural resolution: **share contracts, not
  implementations**
- Each capability owns its own representation of shared concepts (e.g.
  Billing has BillingCustomer, not a shared Customer model)
- Reference data is published by whichever capability is authoritative
  and consumed as read-only by others via domain events
- This decision has downstream implications for service boundaries

## Anti-patterns

- A capability that is "just a service" — too narrow, no business domain
  grouping.
- A capability that spans unrelated regulatory regimes — too wide, will
  be split later.
- A sub-capability promoted without evidence — adds services without
  justification.
- A shared data model across capabilities — violates the capability
  boundary. Use event projections instead.
