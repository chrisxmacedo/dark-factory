# Stage 2 Reasoning Review — JRN-029 Commercial VRP Consent Setup

**Reviewer:** Review Team  
**Date:** 2026-04-15  
**Journey:** JRN-029 — Commercial VRP (Variable Recurring Payment) Consent Setup  
**Verdict:** APPROVED

---

## 1. Architectural Compliance

Three capabilities involved: CAP-007 (Digital Channels, SVC-017 — API gateway), CAP-003 (Domestic Payments, SVC-009 — consent and payment owner), CAP-004 (Fraud Detection, SVC-013 — inline scoring), CAP-001 (Retail Banking Core, SVC-001 — account debit). All cross-capability communication post-payment-execution is async via EVT-156/157/158. The inline fraud scoring (SVC-009 → SVC-013) is modelled as an internal capability pattern within PH-117's payment execution critical path per DD-029-02. The Channel→Capability API pattern is correctly applied: SVC-017 receives TPP requests and delegates to SVC-009. PASS.

## 2. Internal Consistency

Phase IDs PH-115–PH-118 are sequential and non-overlapping. Entity IDs ENT-070–071 follow from ENT-069. Event IDs EVT-156–158 follow from EVT-155. VrpConsent (ENT-070) lifecycle states (pending_authorisation → active → revoked/expired) are consistent across journey-detail, data-model, API contract, and sequence diagram. PASS.

## 3. Cross-Artefact Consistency

- `journey-detail.json` phases match event-catalogue phase labels exactly.
- `service-boundaries.json` correctly attributes ENT-070 and ENT-071 to SVC-009, not SVC-017 — consistent with DD-029-01.
- `api-contracts/open-banking-vrp.openapi.json` endpoint structure (POST /consents, GET /consents/{id}, DELETE /consents/{id}, POST /consents/{id}/payments) is consistent with sequence diagram steps 1–34.
- `PaymentRejectionResponse` covers all reject_reason values from ENT-071 field definition.
- `nfr.json` regulatory SLAs align with FCA cVRP framework obligations (consent transparency, SCA requirement, API uptime).
- EVT-158 VrpConsentRevoked covers all revocation_reason variants in ENT-070 (customer_initiated, tpp_initiated, bank_suspended, expired). PASS.

## 4. Completeness

All 7 required artefact types present. Happy path covers PH-115–117 (consent setup + first payment). PH-118 (consent lifecycle/revocation) is documented in journey-detail and has corresponding EVT-158 and API DELETE /consents/{id} endpoint. Alternative path (consent parameter breach) documented in journey-detail with 422 response schema. Exception path (fraud hold) documented. Cross-cutting NFRs address: consent record retention (5 years PSR), idempotent monthly aggregate enforcement, real-time consent dashboard visibility. PASS.

## 5. Buildability

VrpConsent (ENT-070) `current_month_aggregate` field has a clear computed_from annotation: SUM of VrpPayments in calendar month. The calendar month boundary reset is an implicit SVC-009 responsibility (monthly aggregate resets at midnight on 1st of each month). This should be a service-level implementation concern. Optimistic locking on current_month_aggregate is flagged in XNFR-JRN029-02 — implementable via compare-and-swap on PostgreSQL. The `end_to_end_id` in VrpPaymentRequest provides natural idempotency for PISP retries. All state transitions are triggered by explicit API calls or system events. PASS.

---

**All 5 dimensions PASS. Journey approved for Gate 2.**
