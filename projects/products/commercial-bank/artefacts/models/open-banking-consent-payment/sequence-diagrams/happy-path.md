# JRN-010: Open Banking Consent and Payment Initiation — Happy Path Sequence Diagram

## Participants
- **TPP** — Third Party Provider (PER-006), FCA-authorised PISP
- **Customer** — Personal Customer (PER-001)
- **SVC-017** — Digital Channels (Channel — Open Banking API surface, outside system boundary)
- **SVC-100** — Identity & Access Management (IAM / Authorisation Server)
- **SVC-001** — Retail Banking Core (CAP-001)
- **SVC-051** — Sanctions Screening Service (CAP-005)
- **SVC-013** — Fraud Detection (CAP-004)
- **SVC-009** — Domestic Payments (CAP-003)
- **SVC-053** — Notification Service (CAP-007)
- **SVC-103** — Event Bus / Audit Pipeline
- **Vocalink FPS** — External FPS scheme infrastructure

---

## PH-035: TPP Registration and Discovery (one-time)

```
TPP          →  SVC-017    : GET /.well-known/openid-configuration
SVC-017      →  TPP        : 200 OK (issuer, endpoints, supported_scopes)

TPP          →  SVC-017    : POST /register
                             {software_statement: "<OBIE-signed SSA JWT>",
                              redirect_uris: [...], grant_types: ["authorization_code"],
                              scope: "openid payments"}
SVC-017      →  SVC-100    : Validate SSA signature (OBIE Directory public key)
SVC-100      →  SVC-017    : SSA valid; FCA PISP authorisation confirmed
SVC-017      →  SVC-001    : Create ENT-031 TPPRegistration
                             {tpp_id, obie_org_id, fca_reference_number,
                              software_statement_id, redirect_uris, status=active}
SVC-001      →  SVC-017    : ENT-031 created OK
SVC-017      →  TPP        : 201 Created
                             {client_id: "<tpp_id>", client_secret: "<secret>",
                              token_endpoint, authorization_endpoint}
```

---

## PH-036: Consent Request

```
TPP          →  SVC-017    : POST /domestic-payment-consents
                             Authorization: Basic <client_credentials>
                             Body: {Data: {Initiation: {
                               InstructedAmount: {Amount: "150.00", Currency: "GBP"},
                               CreditorAccount: {SchemeName: "UK.OBIE.SortCodeAccountNumber",
                                                  Identification: "20-00-00/12345678",
                                                  Name: "Jane Smith"},
                               RemittanceInformation: {Reference: "INV-2024-001"}}},
                               Risk: {}}
SVC-017      →  SVC-001    : POST /open-banking-consents [SYNC]
                             {tpp_id, amount=150.00, currency=GBP,
                              payee_sort_code="200000",
                              payee_account_number="12345678",
                              payee_name="Jane Smith",
                              payment_reference="INV-2024-001"}
SVC-001      →  SVC-001    : Validate TPP (ENT-031 status=active)
                             Create ENT-030 OpenBankingConsent
                             {consent_id=<UUID>, status=awaiting_auth,
                              expires_at=now+24h}
SVC-001      →  SVC-103    : Publish EVT-058 ConsentRequested [ASYNC]
SVC-001      →  SVC-017    : 201 Created {consent_id}
SVC-017      →  TPP        : 201 Created
                             {Data: {ConsentId: "<consent_id>",
                                     Status: "AwaitingAuthorisation",
                                     CreationDateTime: "<ISO8601>",
                                     ExpirationDateTime: "<ISO8601>"},
                              Links: {Self: "/domestic-payment-consents/<consent_id>"}}

TPP          →  Customer   : Redirect browser to bank authorisation URL
                             {client_id, response_type=code,
                              scope="openid payments",
                              state=<nonce>,
                              request=<signed JAR JWT containing consent_id>}
```

---

## PH-037: Customer Authentication and Consent Confirmation

```
Customer     →  SVC-017    : GET /authorise
                             (consent screen loads)
SVC-017      →  SVC-001    : GET /open-banking-consents/{consent_id} [SYNC]
SVC-001      →  SVC-017    : ENT-030 {amount=150.00, payee_name="Jane Smith",
                                       payee_sort_code="200000",
                                       payee_account_number="12345678",
                                       payment_reference="INV-2024-001"}
SVC-017      →  SVC-001    : CoP check on payee details [SYNC]
SVC-001      →  SVC-017    : cop_result = match
SVC-017      →  Customer   : Display consent screen
                             "Jane Smith is about to receive £150.00 from your account.
                              Reference: INV-2024-001. Payee verified (CoP: match).
                              [Confirm] [Decline]"

Customer     →  SVC-017    : SCA initiation (clicks Confirm)
SVC-017      →  SVC-100    : Initiate SCA challenge
                             {customer_id, sca_method=biometric_mobile,
                              dynamic_link: {amount=150.00,
                                            payee_sort_code="200000",
                                            payee_account_number="12345678"}}
SVC-100      →  Customer   : Push notification to registered mobile: "Confirm £150.00 to Jane Smith"
Customer     →  SVC-100    : Biometric confirmation (Face ID / Touch ID)
SVC-100      →  SVC-017    : SCA verified; dynamic linking confirmed

SVC-017      →  SVC-001    : PATCH /open-banking-consents/{consent_id}
                             {status=authorised, customer_id=<UUID>,
                              account_id=<UUID>, sca_completed=true,
                              sca_method=biometric_mobile,
                              cop_result=match,
                              authorised_at=<ISO8601>,
                              expires_at=now+90min}
SVC-001      →  SVC-001    : Atomic update: ENT-030 status → authorised
SVC-001      →  SVC-103    : Publish EVT-059 ConsentAuthorised [ASYNC]
SVC-103      →  SVC-053    : Route EVT-059 to Notification Service
SVC-053      →  Customer   : Push: "You've authorised a payment of £150.00 to Jane Smith via [TPP Name]"

SVC-001      →  SVC-017    : 200 OK {status=authorised}
SVC-100      →  SVC-017    : Issue authorisation code {code=<auth_code>, state=<nonce>}
SVC-017      →  Customer   : 302 Redirect → TPP redirect_uri
                             ?code=<auth_code>&state=<nonce>
Customer     →  TPP        : Browser follows redirect (delivers auth code to TPP)
```

---

## PH-038: Payment Initiation

```
TPP          →  SVC-100    : POST /token
                             {grant_type=authorization_code,
                              code=<auth_code>,
                              client_id=<tpp_id>,
                              client_secret=<secret>}
SVC-100      →  TPP        : 200 OK {access_token, token_type=Bearer, expires_in=300}

TPP          →  SVC-017    : POST /domestic-payments
                             Authorization: Bearer <access_token>
                             Body: {Data: {ConsentId: "<consent_id>",
                                           Initiation: {<same as consent>}},
                                     Risk: {}}
SVC-017      →  SVC-100    : Token introspection {access_token}
SVC-100      →  SVC-017    : {active=true, scope="payments",
                               consent_id="<consent_id>", sub="<tpp_id>"}
SVC-017      →  SVC-001    : POST /payments [SYNC]
                             {consent_id, amount=150.00, currency=GBP,
                              payee_sort_code, payee_account_number,
                              payee_name, payment_reference,
                              origination_channel=open_banking,
                              tpp_id}
SVC-001      →  SVC-001    : Validate ENT-030 (status=authorised, sca_completed=true,
                              not expired, payment details match consent)
                             Validate ENT-004 Account (status=active,
                              available_balance >= 150.00, daily_limit not exceeded)
SVC-001      →  SVC-001    : BEGIN TRANSACTION
                             Create ENT-008 PaymentIntent
                             {payment_intent_id=<UUID>, consent_id,
                              account_id, customer_id, amount=150.00,
                              currency=GBP, payee_sort_code, payee_account_number,
                              payee_name, payment_reference,
                              origination_channel=open_banking, tpp_id,
                              status=pending_screening, created_at}
                             Update ENT-030 status=consumed, consumed_at=now,
                             open_banking_payment_id=<payment_intent_id>
                             COMMIT TRANSACTION
SVC-001      →  SVC-103    : Publish EVT-179 PaymentIntentCreated [ASYNC]
SVC-001      →  SVC-103    : Publish EVT-061 OpenBankingPaymentInitiated [ASYNC]
SVC-103      →  SVC-053    : Route EVT-061 → Notification Service
SVC-053      →  Customer   : Push: "Your Open Banking payment of £150.00 to Jane Smith is being processed"

SVC-001      →  SVC-017    : 201 Created {payment_intent_id}
SVC-017      →  TPP        : 201 Created
                             {Data: {DomesticPaymentId: "<payment_intent_id>",
                                     ConsentId: "<consent_id>",
                                     Status: "AcceptedSettlementInProcess",
                                     CreationDateTime: "<ISO8601>",
                                     Initiation: {<payment details>}},
                              Links: {Self: "/domestic-payments/<payment_intent_id>"}}
```

---

## PH-039: Payment Execution (JRN-002 event-driven pattern reused)

```
NOTE: EVT-179 consumed concurrently by SVC-051 and SVC-013 (parallel fan-out)

SVC-103      →  SVC-051    : Route EVT-179 PaymentIntentCreated
SVC-103      →  SVC-013    : Route EVT-179 PaymentIntentCreated

--- Concurrent ---
SVC-051      →  SVC-051    : Sanctions screen payee (OFSI, UN, EU, OFAC lists)
                             [Result: clear]
SVC-051      →  SVC-103    : Publish EVT-180 SanctionsScreeningCompleted
                             {payment_intent_id, outcome=clear}

SVC-013      →  SVC-013    : ML fraud scoring (features include tpp_id, consent_id,
                              payee, amount, customer behaviour)
                             [Result: risk_level=low]
SVC-013      →  SVC-103    : Publish EVT-181 FraudScoreCompleted
                             {payment_intent_id, risk_level=low}
--- End Concurrent ---

SVC-103      →  SVC-001    : Route EVT-180 (outcome=clear)
SVC-103      →  SVC-001    : Route EVT-181 (risk_level=low)
SVC-001      →  SVC-001    : Both results received — PaymentIntent status=pending_screening
                             Both clear: Update PaymentIntent status=processing
SVC-001      →  SVC-103    : Publish EVT-182 PaymentCleared
                             {payment_intent_id, account_id, amount=150.00,
                              payee_sort_code, payee_account_number}

SVC-103      →  SVC-009    : Route EVT-182 PaymentCleared
SVC-009      →  SVC-009    : Create ENT-009 PaymentExecution
                             {execution_id=<UUID>, payment_intent_id,
                              status=fps_submitted}
                             Construct ISO 20022 pacs.008
                             {UETR=<UUID>, InstrAmt=150.00, currency=GBP,
                              Cdtr: {Nm="Jane Smith",
                                     Acct={Id={Othr={Id="200000/12345678"}}}}}
SVC-009      →  Vocalink    : Submit pacs.008 to FPS
Vocalink     →  SVC-009    : pacs.002 ACCP (Accepted)
                             {FpsReference=<FPS_REF>, TxSts=ACCP}
SVC-009      →  SVC-009    : Update ENT-009 status=settled, fps_reference=<FPS_REF>
SVC-009      →  SVC-103    : Publish EVT-183 PaymentExecuted
                             {payment_intent_id, execution_id,
                              fps_reference=<FPS_REF>, settled_at}

SVC-103      →  SVC-001    : Route EVT-183 PaymentExecuted
SVC-001      →  SVC-001    : Atomic debit: Account.available_balance -= 150.00
                             Update Account.daily_payment_total
                             Update PaymentIntent.status=completed, completed_at=now
SVC-001      →  SVC-103    : Publish EVT-184 AccountDebited [ASYNC]
SVC-001      →  SVC-103    : Publish EVT-062 OpenBankingPaymentCompleted [ASYNC]
                             {payment_intent_id, consent_id, tpp_id,
                              fps_reference=<FPS_REF>, amount=150.00,
                              payee_name="Jane Smith", completed_at}

SVC-103      →  SVC-017    : Route EVT-062 → SVC-017 status cache
SVC-017      →  SVC-017    : Update payment status cache:
                             DomesticPaymentId → AcceptedSettlementCompleted
SVC-103      →  SVC-053    : Route EVT-062 → Notification Service
SVC-053      →  Customer   : Push: "Payment of £150.00 to Jane Smith was successful.
                              FPS Ref: <FPS_REF>"
```

---

## PH-040: Status Polling and Confirmation

```
TPP          →  SVC-017    : GET /domestic-payments/<payment_intent_id>
                             Authorization: Bearer <access_token>
SVC-017      →  SVC-017    : Read status cache (AcceptedSettlementCompleted)
SVC-017      →  TPP        : 200 OK
                             {Data: {DomesticPaymentId: "<payment_intent_id>",
                                     ConsentId: "<consent_id>",
                                     Status: "AcceptedSettlementCompleted",
                                     CreationDateTime: "<ISO8601>",
                                     CompletionDateTime: "<ISO8601>",
                                     Initiation: {<payment details>}},
                              Links: {Self: "/domestic-payments/<payment_intent_id>"}}
```

---

## Key Design Notes

1. **SVC-017 is a CHANNEL service** — it sits outside the system boundary and may call SVC-001 synchronously. It holds no persistent domain state (ENT-030, ENT-031 live in SVC-001).

2. **Single synchronous cross-boundary call** — SVC-017 → SVC-001 POST /payments is the only synchronous channel-to-capability call. All subsequent processing is async event-driven (JRN-002 pattern).

3. **Atomic consent consumption** — ENT-030.status = consumed and ENT-008 creation are a single transaction in SVC-001. No partial state is possible.

4. **Dynamic linking** — SCA at PH-037 binds the customer's authentication to the specific amount (£150.00) and payee account (20-00-00/12345678). Any deviation is a mandatory rejection.

5. **Fraud/sanctions non-disclosure** — EVT-185/P08 failure reasons are mapped to generic OBIE error codes before being returned to the TPP in EVT-063.
