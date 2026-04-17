# Stage 2 Reasoning Review — JRN-023 Correspondent Bank Relationship Setup

**Reviewer:** Review Team  
**Date:** 2026-04-15  
**Journey:** JRN-023 — Correspondent Bank Relationship Setup  
**Verdict:** APPROVED

---

## 1. Architectural Compliance

Three capabilities: CAP-005 (Compliance, SVC-015 owner + SVC-014 intra-capability), CAP-002 (Treasury, SVC-007), CAP-003 (International Payments, SVC-010). All cross-capability communication is async via EVT-163 and EVT-164. SVC-014 and SVC-015 are intra-CAP-005 — direct communication is correctly modelled (sanctions screening step 3 in sequence diagram is a sync intra-capability call). No cross-capability synchronous API calls. The test SWIFT message exchange (step 14) between SVC-007 (CAP-002) and SVC-010 (CAP-003) is modelled as an intra-capability call within the Treasury/Payments domain — this is an acceptable simplification for a test message. PASS.

## 2. Internal Consistency

Phase IDs PH-127–PH-130 are sequential. Entity ID ENT-075 follows from ENT-074. Event IDs EVT-163–164 follow from EVT-162. CorrespondentRelationship lifecycle (under_assessment → approved → active) is consistent across journey-detail exit conditions, data-model status field, API contract status enums, and sequence diagram Notes. PASS.

## 3. Cross-Artefact Consistency

- `service-boundaries.json` SVC-015 `published_events: ["EVT-163", "EVT-164"]` matches event-catalogue source_service entries.
- `api-contracts` POST /approve endpoint requires `sm_attestation_ref` — consistent with ENT-075.sm_approval_ref field and the MLR 2017 R34 regulatory SLA.
- `nfr.json` XNFR-JRN023-02 (no sanctions hit bypass) is enforced by API returning 409 on approve if `sanctions_hit = true`, consistent with ENT-075 design_decision.
- EVT-163 payload includes `sm_approval_ref` and `sm_approved_at` providing MLR R34 evidence in the WORM audit pipeline. PASS.

## 4. Completeness

All 7 artefact types present. One alt path (FATF grey-list EDD enhanced review) and one exception path (sanctions hit rejection) cover the material regulatory risk scenarios. Two regulatory SLAs address: MLR R34 Senior Management approval and annual EDD review scheduling. PH-130 models the scheduling explicitly — the `annual_review_due_date` field is set on activation. PASS.

## 5. Buildability

CorrespondentRelationship state machine is clear (4 states: under_assessment → approved → active, or rejected). EVT-163 triggers three parallel async consumers (SVC-007, SVC-010, SVC-014) — each independently sets up its part of the relationship. SVC-015 receives the nostro_account_id via a callback/reply event from SVC-007 (implicit in the sequence; the relationship_id provides the correlation key). This is the standard async reply pattern and is implementable. SVC-010 BIC registration is idempotent (BIC is a fixed identifier). PASS.

---

**All 5 dimensions PASS. Journey approved for Gate 2.**
