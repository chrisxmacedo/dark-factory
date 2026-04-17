# Stage 2 Reasoning Review — JRN-021 GDPR Data Subject Access Request

**Reviewer:** Review Team  
**Date:** 2026-04-15  
**Journey:** JRN-021 — GDPR Data Subject Access Request  
**Verdict:** APPROVED

---

## 1. Architectural Compliance

Three capabilities: CAP-005 (Compliance Core owner, SVC-015 and SVC-014), CAP-001 (Retail Banking, SVC-001), CAP-007 (Digital Channels, SVC-017). Cross-capability communication from SVC-001 (CAP-001) is async: SVC-001 consumes EVT-159 and publishes a data extract event back to SVC-015. SVC-014 (intra-CAP-005) communicates directly with SVC-015 per the intra-capability pattern — correctly modelled. Channel→Capability API pattern: SVC-017 calls SVC-015's SAR API; SVC-015 owns the SarCase entity. No cross-capability sync calls. PASS.

## 2. Internal Consistency

Phase IDs PH-119–PH-122 are sequential. Entity ID ENT-072 follows from ENT-071. Event IDs EVT-159–160 follow from EVT-158. SarCase lifecycle (received → under_review → response_ready → closed) is consistent across journey-detail, data-model, API contract status enum, and sequence diagram Notes. PASS.

## 3. Cross-Artefact Consistency

- `service-boundaries.json` SVC-015 `published_events: ["EVT-159", "EVT-160"]` matches event-catalogue source_service entries.
- `api-contracts/compliance-regulatory.openapi.json` POST /sar and GET /sar/{id} endpoints are used in sequence diagram steps 4 and 22. SarCaseDetail.days_remaining is a computed field consistent with data-model `days_to_close computed_from`.
- `nfr.json` REG-SLA-JRN021-01 30-day requirement is modelled in data-model `deadline_date = received_at + 30 days` and in journey-detail PH-119 exit conditions.
- `nfr.json` XNFR-JRN021-03 data minimisation requirement is directly implemented by PH-121 legal review phase with Schedule 2 exemption application.
- EVT-160 payload includes `days_to_close` enabling SVC-103 to write the ICO SLA reporting record. PASS.

## 4. Completeness

All 7 artefact types present. One alt path (extension for complex SAR) and one exception path (30-day deadline breach) documented. Both are ICO-relevant scenarios. XNFR-JRN021-02 addresses the automated day-21/day-28 alert requirement. The journey correctly references DD-021-01 explaining why SVC-001 data extraction is event-driven rather than sync. Two regulatory SLAs cover the primary UK GDPR obligations. PASS.

## 5. Buildability

SarCase state machine is simple and clear. The data extraction pattern (EVT-159 → SVC-001 extracts → publishes internal extract event → SVC-015 receives) is implementable with standard event-driven choreography. The 30-day deadline monitoring (XNFR-JRN021-02) requires a scheduled job within SVC-015 checking open SarCases — a standard operational pattern. Secure download link expiry (14 days) is a standard time-to-live pattern. The redaction workflow in PH-121 is a human task with tooling support — correctly modelled as a Notes block in the sequence diagram rather than automated service calls. PASS.

---

**All 5 dimensions PASS. Journey approved for Gate 2.**
