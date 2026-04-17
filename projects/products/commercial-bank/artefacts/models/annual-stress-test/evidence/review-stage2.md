# Stage 2 Reasoning Review — JRN-022 Annual Stress Test Participation (PRA)

**Reviewer:** Review Team  
**Date:** 2026-04-15  
**Journey:** JRN-022 — Annual Stress Test Participation (PRA)  
**Verdict:** APPROVED

---

## 1. Architectural Compliance

Two capabilities: CAP-004 (Risk Management, SVC-012) and CAP-005 (Compliance, SVC-015). Cross-capability communication is exclusively async via EVT-161 and EVT-162. No customer-facing channels involved — this is an internal SMF-triggered journey per DD-022-02. The CRO interacts with SVC-012 via internal REST API (Channel→Capability API pattern applied to internal users). No synchronous cross-capability calls detected. SVC-015 consumes events to maintain its RegulatorySubmission tracking record — consistent with the principle that SVC-015 is the system of record for regulatory submissions while SVC-012 owns model outputs. PASS.

## 2. Internal Consistency

Phase IDs PH-123–PH-126 are sequential. Entity IDs ENT-073–074 follow from ENT-072. Event IDs EVT-161–162 follow from EVT-160. StressTestExercise status lifecycle (pending → in_progress → projections_complete → approved_for_submission → submitted) is consistent across journey-detail, data-model, API contract responses, and sequence diagram Notes. PASS.

## 3. Cross-Artefact Consistency

- `service-boundaries.json` SVC-012 `published_events: ["EVT-161", "EVT-162"]` matches event-catalogue.
- `api-contracts/risk-management.openapi.json` POST /stress-tests, GET /stress-tests/{id}, POST /stress-tests/{id}/confirm-submission map exactly to sequence diagram steps 1, 11, and 15.
- `ConfirmSubmissionRequest` requires both `pra_submission_ref` and `cro_attestation_ref` — consistent with StressTestExercise.cro_attestation_ref data-model field.
- `nfr.json` REG-SLA-JRN022-02 (SS1/23 model validation) addressed by `model_validation_sign_off_ref` field on ENT-073 and Step 12 returning it in GET response.
- `EVT-162` payload includes `projected_stressed_cet1_y1/y2/y3` providing the audit trail of the submitted capital trajectory. PASS.

## 4. Completeness

All 7 artefact types present. One alt path (model validation failure, rerun required) and one exception path (submission deadline breach) cover the regulatory risk scenarios. ENT-074 (RegulatorySubmission) is designed as a reusable entity for future regulatory submission journeys (ICAAP, RMAR), documented in DD-022-01. Both regulatory SLAs are addressed: PRA submission deadline and SS1/23 model validation requirement. PASS.

## 5. Buildability

StressTestExercise state machine is clear and implementable. The batch compute workload (PH-124 model projections < 24h) is modelled as internal processing within SVC-012, not as synchronous API calls — appropriate. The PATCH status pattern for Board approval (step 13) could be split into a dedicated endpoint for auditability, but the confirmation-submission endpoint (step 15) captures the material approval evidence (cro_attestation_ref, board_approved_at). RegulatorySubmission (ENT-074) is intentionally generic to avoid creating journey-specific regulatory tracking entities. PASS.

---

**All 5 dimensions PASS. Journey approved for Gate 2.**
