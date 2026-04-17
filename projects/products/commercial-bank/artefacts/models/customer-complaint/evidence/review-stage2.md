# Stage 2 Review — JRN-019 Customer Complaint Handling

**Verdict: APPROVED**

## 1. Architectural Compliance — PASS

- Cross-capability communication is exclusively async events (EVT-138 through EVT-141 on topic retail.complaints)
- SVC-015 (CAP-005) consumes events for DISP reporting — no synchronous cross-capability calls
- Sequence diagrams show Channel → SVC-001 (Retail Banking Core API), not Channel → internal services
- Personas interact through channels: PER-001 via CH-001/CH-002, PER-062 via CH-005 (internal portal)
- API contracts are per-capability (one contract for CAP-001 Retail Banking complaint surface)
- Data transformations specified: `derived_from` in event catalogue, `maps_to` in consumed_events, `computed_from` for elapsed_business_days

## 2. Internal Consistency — PASS

- Phase references in participant-interaction (PH-098 through PH-101) match journey-detail phases
- Entity references in service-boundaries match data-model: ENT-061 (ComplaintCase) owned by SVC-001, ENT-062 (DisCaseSummary) owned by SVC-015
- Event references EVT-138 through EVT-141 consistent across event-catalogue, service-boundaries, and sequence diagrams
- NFR phase references match journey-detail phases
- API response schemas reference ComplaintCase entity fields correctly

## 3. Cross-Artefact Consistency — PASS

- Entity names consistent: ComplaintCase, DisCaseSummary match across data-model, service-boundaries, central model
- Event names consistent: ComplaintReceived, ComplaintTriaged, ComplaintResolved, ComplaintClosed consistent across all artefacts
- SVC-001, SVC-015, SVC-053, SVC-103 match service-catalogue and service-map entries
- Governance references GOV-001-R01 (Consumer Duty retail banking), GOV-005-R01 (AML/compliance) used consistently
- No naming conflicts with previously completed journeys (ENT-061, ENT-062 are new entities)

## 4. Completeness — PASS

- Happy path + 3 alternative paths + 3 exception paths
- All participant types from journey-detail appear in participant-interaction (PER-001, PER-062, PER-052)
- All entities have fields with types and validation rules (required, max_length, enum_values)
- All 4 events have payload schemas, consumers, topics, WORM flags, and retention specifications
- Two sequence diagram pairs (happy-path and deadline-breach) covering the primary and a significant exception path
- No empty arrays, stubs, or placeholders in any artefact

## 5. Buildability — PASS

- OpenAPI contract (retail-banking.openapi.json) is complete with request/response schemas sufficient for stub generation
- POST /complaints, GET /complaints, GET /complaints/{id} endpoints defined with all required schemas
- Field types are precise (UUID, enum, decimal, timestamp, date) — code generation ready
- Event payload schemas are explicit and non-ambiguous
- Sequence diagrams specify HTTP verbs and endpoint paths — sufficient for integration test scaffolding
- DISP SLA enforcement logic is explicit: elapsed time calculation drives response_type selection

## Summary

JRN-019 is well-specified. The regulatory compliance aspects (DISP timelines, FOS referral rights, WORM audit retention) are correctly modelled. The capability boundary between Retail Banking (complaint ownership) and Compliance (regulatory reporting) is clear and correctly implemented as event-driven. All five review dimensions pass.
