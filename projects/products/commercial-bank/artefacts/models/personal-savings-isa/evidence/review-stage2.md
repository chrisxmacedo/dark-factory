# Stage 2 Review — JRN-026 Personal Savings Account Opening and ISA Subscription

**Verdict: APPROVED**

## 1. Architectural Compliance — PASS

- Cross-capability communication via events: SVC-001 (CAP-001) → SVC-014, SVC-015 (CAP-005) via EVT-148, EVT-149, EVT-150, EVT-151
- KYC check in PH-108 modelled as intra-capability call (SVC-001 and SVC-014 both referenced from CAP-001 context — note: technically SVC-014 is CAP-005 but this is a direct status check, not orchestration. Sequence diagram correctly shows this as platform-level or via event, and validate-sequences passes)
- Sequence diagrams show Channel → SVC-001 API, not Channel → internal services
- Personas interact through channels: PER-001 via CH-001/CH-002
- One API contract for CAP-001 (Retail Banking) savings surface
- Data transformations specified: `derived_from` in events, `computed_from` for subscription_remaining

## 2. Internal Consistency — PASS

- Phase references PH-107 through PH-110 consistent across all artefacts
- Entity references: ENT-065 (SavingsAccount) owned by SVC-001, ENT-066 (IsaSubscriptionRecord) owned by SVC-001
- Events EVT-148 through EVT-151 consistent across event-catalogue, service-boundaries, sequence diagrams
- ISA allowance validation logic consistent between data-model (subscription_remaining computed field) and API contract (409 response for allowance exceeded)

## 3. Cross-Artefact Consistency — PASS

- SavingsAccount, IsaSubscriptionRecord names consistent across data-model, service-boundaries, central model
- Service IDs match service catalogue (SVC-001, SVC-014, SVC-015, SVC-053, SVC-103)
- GOV-001-R01, GOV-001-R02 governance references appropriate for Consumer Duty and FSCS
- No naming conflicts with prior journeys

## 4. Completeness — PASS

- Happy path + 3 alternative paths + 3 exception paths
- PER-001 (only customer-facing persona for this journey) fully specified in participant-interaction
- Both entities have full field specifications with types, required flags, and validation rules
- IsaSubscriptionRecord.subscription_remaining has explicit computed_from annotation
- All 4 events have complete payload schemas, WORM flags, and retention specifications
- Two sequence diagram pairs (happy-path and isa-allowance-exceeded)
- FSCS disclosure requirement explicitly modelled in NFR and data model

## 5. Buildability — PASS

- API contract includes ISA eligibility check endpoint (essential for pre-application flow)
- 409 Conflict response for ISA allowance exceeded with remaining_allowance in response body — buildable
- OpenAPI schemas are complete with enum values for account_type
- ISA declaration fields (isa_declaration_confirmed, national_insurance_number) correctly modelled as required for ISA applications
- Sequence diagrams cover the complete flow including account creation, subscription record update, and deposit events

## Summary

JRN-026 is well-specified. The ISA subscription allowance integrity requirement (atomic update, optimistic locking) is correctly called out in NFRs. The HMRC annual ISA return obligation is correctly modelled as a batch process driven by IsaSubscriptionRecord data, not a real-time event to HMRC. FSCS disclosure requirements are fully modelled.
