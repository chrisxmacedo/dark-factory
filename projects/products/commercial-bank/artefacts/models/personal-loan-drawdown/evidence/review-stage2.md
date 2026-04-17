# Stage 2 Reasoning Review — JRN-027 Personal Loan Application and Drawdown

**Reviewer:** Review Team  
**Date:** 2026-04-15  
**Journey:** JRN-027 — Personal Loan Application and Drawdown  
**Verdict:** APPROVED

---

## 1. Architectural Compliance

All cross-capability communication is exclusively async via SVC-102 (Event Bus). Three capabilities are involved:
- CAP-001 (Retail Banking Core, owner) — SVC-001
- CAP-004 (Risk Engine) — SVC-012 publishes EVT-153 (CreditAssessmentCompleted) back to CAP-001 via Event Bus
- CAP-005 (Compliance/KYC) — SVC-015 and SVC-014 consume events

EVT-153 is correctly modelled as the only event in this journey published by a non-CAP-001 service (SVC-012 in CAP-004). CAP-003 (Payments, SVC-009) receives EVT-154 to execute the drawdown transfer — correctly async. No synchronous cross-capability calls detected. The Channel→CAP-001 API pattern is used throughout. PASS.

## 2. Internal Consistency

Phase IDs PH-111–PH-114 are sequential and non-overlapping with other journeys. Entity IDs ENT-067–069 are sequential. Event IDs EVT-152–155 follow from EVT-151 (last ISA event). Service-boundaries.json aligns exactly with event-catalogue.json producers/consumers. API contract endpoints match sequence diagram actions. PASS.

## 3. Cross-Artefact Consistency

- `journey-detail.json` PH-111–PH-114 phases match phase labels in nfr.json, event-catalogue.json, and sequence diagram steps.
- `data-model.json` entities (ENT-067/068/069) appear correctly in service-boundaries.json `owned_entities`.
- `service-boundaries.json` published_events and consumed_events are plain ID strings (no annotations) — confirmed by cleanup-ids.py passing clean.
- `sequence-diagrams/happy-path.json` step count (31) covers all 4 phases with SCA validations, async event flows, and compliance consumers.
- `api-contracts/retail-banking.openapi.json` schemas (LoanApplicationRequest, AcceptOfferRequest) contain all fields referenced in sequence diagram actions.
- `nfr.json` regulatory SLAs (SECCI pre-contractual, 14-day withdrawal, CONC affordability) are addressed by SECCI acknowledgement field in LoanApplicationRequest and `withdrawal_right_days: 14` in LoanApplicationDetail.
- UK GDPR Article 22 automated decision disclosure covered by `decline_reason` and `human_review_available` boolean in LoanApplicationDetail. PASS.

## 4. Completeness

All 7 required artefact types present. Two journey scenarios (happy-path; no explicit declined/referred scenario — covered by alt_paths in journey-detail). All 4 events catalogued with CloudEvents types, data classifications, retention periods, and WORM flags. EVT-155 `worm_audit_pipeline: false` is acceptable — drawdown completion is not a legally binding instrument (agreement execution EVT-154 is). Cross-cutting NFRs address: CCA 1974 6-year retention, GDPR Article 22 disclosure, single hard search per application. PASS.

## 5. Buildability

SVC-001 has clear state transitions: LoanApplication(submitted → approved → offer_presented) → LoanAgreement(executed) → LoanAccount(pending_disbursement → active). Each state transition is triggered by a consumed event or API call. SCA assertion references are stored on both LoanAgreement entity and EVT-154 payload providing a complete audit chain. The polling pattern (202 Accepted + poll_url) is implementable and avoids long-held HTTP connections. Disbursement is idempotent by design (SVC-009 receives EVT-154 containing agreement_id as natural idempotency key). PASS.

---

**All 5 dimensions PASS. Journey approved for Gate 2.**
