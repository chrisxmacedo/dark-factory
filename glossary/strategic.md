# Strategic

The strategic aspect of a company is the part that creates and delivers
a product or service to market. It is the reason the company exists.

A bank's strategic function is banking — taking deposits, making loans,
processing payments, managing risk. An energy supplier's strategic
function is buying wholesale energy and selling it to customers. A
hospital's strategic function is treating patients.

Strategic capabilities are the capabilities that directly produce the
thing the customer pays for. They are what makes this company different
from every other company. They are the source of competitive advantage,
the subject of regulation, and the focus of the capability-driven
architecture.

In the capability pipeline, the strategic capabilities are identified
in Phase A (Discovery) by asking: "What does this organisation do?"
The answer is never "it runs an HR department" or "it has a legal team."
The answer is the product. Everything else is operational.

## How to identify strategic capabilities

1. **Would a customer notice if this capability disappeared?** If yes,
   it is strategic. If a bank stopped processing payments, customers
   would notice immediately. If the bank's internal legal team
   disappeared, customers would not notice for months.

2. **Is this capability regulated because of what it does to
   customers?** Financial conduct regulation (FCA BCOBS, MCOB, CONC)
   targets strategic capabilities. Employment law targets operational
   functions. The regulatory framework tells you which capabilities
   are strategic.

3. **Does this capability differentiate the company from competitors?**
   Retail banking products, lending criteria, payment speed, wealth
   advisory — these are competitive differentiators. Payroll processing,
   office management, and corporate communications are not.

4. **Is revenue directly attributable to this capability?** Net interest
   margin on lending, interchange on card payments, advisory fees on
   wealth management — these are strategic revenue lines. The IT
   department has a cost, not a revenue line.

## Strategic capabilities in the capability pipeline

The capability pipeline treats strategic capabilities as the primary
decomposition unit. Each strategic capability becomes a deployment
boundary — a self-contained domain with its own data, logic, contracts,
events, and test suite. The architecture is organised around these
capabilities because they are stable over decades (they change only
when the mandate changes) and they represent the irreducible complexity
of the business.

The journeys modelled in Phase C flow through strategic capabilities.
The data model is derived from journeys. The event contracts define
how strategic capabilities coordinate. The entire specification is
structured around what the organisation strategically does.

## Relationship to operational

Strategic capabilities depend on operational capabilities for support,
but the dependency is one-directional. Retail Banking needs Legal for
contract review, but Legal does not need Retail Banking to function.
The strategic capability is the customer-facing domain; the operational
capability is the internal support function.

In architectural terms, operational capabilities are often shared
services or platform services — they provide mechanisms that multiple
strategic capabilities consume. The principle "share the mechanism,
isolate the state" applies: the HR system is shared infrastructure,
but each strategic capability owns its own domain data.

See also: [operational](operational.md), [ai-harness](ai-harness.md)
