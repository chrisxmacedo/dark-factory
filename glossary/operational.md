# Operational

The operational aspect of a company is everything that supports the
strategic function but is not itself the product. It is the machinery
that keeps the company running so that the strategic capabilities can
deliver.

Operational capabilities are the systems, teams, and processes that
every company needs regardless of what it sells. A bank needs HR,
legal, finance, facilities, and IT — but so does a hospital, a
retailer, and a logistics company. The operational capabilities are
interchangeable across industries. The strategic capabilities are not.

## Examples of operational capabilities

- **Legal & Compliance** (internal) — contract review, employment law,
  corporate governance. Not to be confused with regulatory compliance
  of the product (which is strategic — FCA conduct rules apply to the
  banking product, not to the HR department).
- **Human Resources** — recruitment, payroll, performance management,
  training. Supports all strategic capabilities but delivers nothing
  to the customer.
- **Finance & Treasury** (internal) — management accounting, budgeting,
  cash management, tax. The company's own financial operations, not
  the financial products it sells to customers.
- **Marketing & Communications** — brand, campaigns, public relations.
  Promotes the strategic product but is not the product itself.
- **Facilities & Property** — office management, branch infrastructure,
  physical security.
- **IT Operations** — infrastructure, service desk, identity
  management, network. The platform layer in the architecture is the
  technical expression of IT operations.
- **Procurement** — vendor management, contract negotiation, supply
  chain for internal consumption.
- **Corporate Strategy & Planning** — board reporting, strategic
  planning, M&A. Decides what the company should do; doesn't do it.
- **Internal Audit** — assurance over operational and strategic
  processes. An oversight function, not a delivery function.

## The distinction matters architecturally

In a capability-driven architecture, strategic capabilities are the
primary decomposition unit — they define the deployment boundaries,
the data ownership, the event contracts, and the journey flows.
Operational capabilities sit in the platform layer or outside the
system boundary entirely.

This distinction prevents a common architectural mistake: treating
internal support functions as first-class capabilities alongside
the product. When HR, Legal, and Marketing are modelled at the same
level as Retail Banking and Payment Operations, the architecture
loses focus. The journeys that matter — the ones customers experience —
are buried among internal workflows.

## How operational capabilities appear in the pipeline

Operational capabilities typically appear as:

1. **Platform services** — IT Operations becomes the platform layer
   (Event Bus, Observability, Auth, Cache). These are shared
   infrastructure, not business capabilities.

2. **External systems** — HR, Finance, and Legal often run on
   third-party SaaS (Workday, SAP, iManage). They appear on the C4
   System Context diagram as external systems, not as containers
   within the system boundary.

3. **Governance rules** — Legal and Compliance inform the governance
   constraints that the strategic capabilities must follow. They are
   inputs to the architecture, not components of it.

4. **Personas** — internal personas (Senior Manager, Compliance
   Officer) interact with strategic capabilities through internal
   portals. They are users of the system, not parts of it.

## The grey zone

Some capabilities straddle the line:

- **Regulatory Reporting** — is it strategic (the regulator is an
  external stakeholder who can shut the business down) or operational
  (it's an internal reporting function)? In most regulated industries,
  regulatory reporting is strategic because failure to report
  accurately has direct consequences for the licence to operate.

- **Fraud Detection** — is it strategic (it protects the customer) or
  operational (it protects the company)? Under APP fraud mandatory
  reimbursement, fraud detection is strategic because it directly
  affects the customer's financial outcome.

- **Treasury** (when the company IS a bank) — the company's own
  treasury function is operational (managing the balance sheet), but
  Treasury Services sold to corporate clients are strategic (a product
  the customer pays for).

The promotion test helps resolve these: if the capability has distinct
external participants, a separate regulatory framework, a distinct
lifecycle, and independent scalability — it is strategic, regardless
of whether it "feels" internal.

See also: [strategic](strategic.md), [ai-harness](ai-harness.md)
