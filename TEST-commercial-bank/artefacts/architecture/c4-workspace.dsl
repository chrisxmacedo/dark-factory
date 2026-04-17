/*
 * C4 Model Workspace — UK Commercial Bank
 * document_version: 0.1.0
 * status: Draft
 *
 * Scope: System Context and Container views only.
 * Component views are deferred to Phase C (detailed design).
 *
 * People included: external runtime personas only (PER-001 to PER-012).
 * Internal personas (employees, AI agents, developers) are excluded
 * from this runtime architecture view.
 *
 * Container naming convention:
 *   Domain services:      SVC-001 to SVC-017
 *   Cross-cutting:        SVC-050 to SVC-055
 *   Foundation platform:  SVC-100 to SVC-106
 *   Observability:        SVC-107 to SVC-113 (added here for completeness)
 *
 * Data store naming convention: DS-<SVC-ID> (one store per domain service)
 * plus DS-AUDIT (WORM audit store) and DS-EVENTS (Kafka topics).
 */

workspace "UK Commercial Bank" "Architecture model for a UK-regulated commercial bank covering retail, commercial, payment, risk, compliance, wealth, and digital channels capabilities." {

    model {

        /* ─────────────────────────────────────────────
         * EXTERNAL PERSONAS (runtime actors only)
         * ───────────────────────────────────────────── */

        personalCustomer = person "Personal Customer" "An individual consumer holding retail banking products: current account, savings, debit card, personal loan, credit card, or mortgage. Regulated under FCA Consumer Duty and FSCS. PER-001." "ExternalPersona"

        businessCustomerSME = person "Business Customer (SME)" "A small or medium enterprise (sole trader to £25m turnover) holding a business current account, lending, or acquiring facility. Open Banking API integrations with accounting software. PER-002." "ExternalPersona"

        corporateClient = person "Corporate Client" "A large company (£25m+ turnover) with cash management, lending, FX, trade finance, and treasury products. Uses corporate banking portal and ERP host-to-host API. PER-003." "ExternalPersona"

        hnwClient = person "High Net Worth (HNW) Client" "An individual with investable assets above £250k holding a discretionary or advisory portfolio alongside private banking services. Subject to MiFID II suitability and SDR ESG labels. PER-004." "ExternalPersona"

        mortgageApplicant = person "Mortgage Applicant" "An individual applying for a residential mortgage via digital channel, broker, or branch. Subject to MCOB affordability assessment and Consumer Duty. PER-005." "ExternalPersona"

        thirdPartyProvider = person "Third Party Provider (TPP)" "An FCA-authorised AISP or PISP accessing Open Banking APIs under PSD2/PSR 2017. Examples: TrueLayer, Yapily, Volt. Also covers commercial VRP providers. PER-006." "ExternalPersona"

        merchant = person "Merchant" "A business customer accepting card payments through the bank's acquiring service. Interacts via terminal provisioning, dispute management, and settlement reporting. PER-007." "ExternalPersona"

        correspondentBank = person "Correspondent Bank" "A foreign or domestic financial institution holding a nostro/vostro account relationship for SWIFT cross-border payment settlement. Requires EDD under MLR 2017. PER-008." "ExternalPersona"

        regulator = person "Regulator (FCA / PRA)" "The Financial Conduct Authority and Prudential Regulation Authority as supervisory authorities. Receives regulatory returns, supervisory data requests, and material incident notifications. PER-009." "ExternalPersona"

        cardNetwork = person "Card Network (Visa / Mastercard)" "Visa and Mastercard as four-party scheme operators. The bank complies with scheme rules, PCI DSS v4.0, and interchange obligations. PER-010." "ExternalPersona"

        insuranceUnderwriter = person "Insurance Underwriter" "An insurance company or Lloyd's syndicate underwriting retail/commercial insurance products distributed through the bank under ICOBS. PER-011." "ExternalPersona"

        esgRatingAgency = person "ESG Rating Agency" "Provides ESG ratings and data (MSCI ESG, Sustainalytics, CDP) consumed by the bank for SDR-labelled wealth portfolios and corporate lending ESG assessment. PER-012." "ExternalPersona"


        /* ─────────────────────────────────────────────
         * EXTERNAL SYSTEMS
         * ───────────────────────────────────────────── */

        fps = softwareSystem "Faster Payments Service (FPS)" "Pay.UK / Vocalink real-time gross settlement rail for domestic GBP payments up to £1m. Direct scheme participation via Form3 or Bottomline PTX. ISO 20022 native (IPS)." "ExternalSystem"

        bacs = softwareSystem "BACS (Pay.UK)" "Bulk Automated Clearing and Settlement: 3-day BACS Direct Credit and Direct Debit. Used for payroll, supplier runs, and standing orders. Pay.UK operated, Vocalink processing." "ExternalSystem"

        chapsRtgs = softwareSystem "CHAPS / Bank of England RTGS" "Same-day high-value sterling settlement. Bank of England operated RT2 RTGS system. CHAPS ISO 20022 enhanced data mandatory from November 2026 (LEIs, structured addresses)." "ExternalSystem"

        swift = softwareSystem "SWIFT Network" "Society for Worldwide Interbank Financial Telecommunication. Cross-border payment messaging (CBPR+ ISO 20022 mandatory November 2025). GPI in-flight tracking. MT700-series for trade finance." "ExternalSystem"

        cardNetworks = softwareSystem "Card Networks (Visa / Mastercard)" "Four-party card scheme authorisation, clearing, and settlement networks. PCI DSS compliance, BIN management, dispute and chargeback rules." "ExternalSystem"

        companiesHouse = softwareSystem "Companies House" "UK company registry providing company registration data, filed accounts, and person of significant control (PSC) records for corporate KYB and beneficial ownership determination." "ExternalSystem"

        creditBureaus = softwareSystem "Credit Bureaus (Experian / Equifax / TransUnion)" "UK credit reference agencies providing consumer and commercial credit data, credit scores, and credit report services under RBUA data agreements. Used by SVC-052 credit decisioning." "ExternalSystem"

        hmrc = softwareSystem "HMRC" "HM Revenue and Customs. Receives mandatory FATCA/CRS reporting (Common Reporting Standard) for international account holders. Provides Making Tax Digital (MTD) API for business customer integration." "ExternalSystem"

        bankOfEngland = softwareSystem "Bank of England" "Prudential Regulation Authority supervisor. Receives COREP, FINREP, PRA 110, statistical returns, and ICAAP submissions. Holds the bank's RTGS settlement account." "ExternalSystem"

        fcaConnect = softwareSystem "FCA Connect (FCA Regulatory Portal)" "FCA's regulatory reporting portal for FCA returns, gabriel (GABRIEL replaced by RegData), REP-CRIM, Product Sales Data, and incident notifications." "ExternalSystem"

        obieDirectory = softwareSystem "OBIE Directory (Open Banking)" "Open Banking Implementation Entity / Open Finance operated trust framework directory. TPP certificate validation, eIDAS/FAPI registration, and Open Banking ecosystem participant registry." "ExternalSystem"


        /* ─────────────────────────────────────────────
         * THE BANKING SYSTEM
         * ───────────────────────────────────────────── */

        bankingSystem = softwareSystem "The Banking System" "The UK commercial bank's complete system landscape: retail banking, commercial banking, payments, risk management, compliance, wealth management, digital channels, and supporting platform services." {

            /* ── CHANNEL CONTAINERS ── */

            webPortal = container "Web Portal" "React/Next.js responsive web application for authenticated retail and SME customers. Serves online banking, product applications, and statement download. Delegates all API calls to SVC-017 and SVC-101." "React / TypeScript / Next.js" "WebBrowser"

            mobileApp = container "Mobile App" "iOS and Android native applications for personal and SME customers. Biometric SCA (FaceID, fingerprint), push notifications, Open Banking consent management, card controls." "Swift / Kotlin" "MobileApp"

            openBankingGateway = container "Open Banking Gateway" "OBIE-compliant FAPI 1.0 Advanced API endpoint for AISP/PISP TPP access. Validates TPP eIDAS certificates against OBIE Directory. Issues OAuth 2.0 PKCE authorisation codes. Routes to SVC-009 (PISP) and SVC-001/SVC-005 (AISP)." "Node.js / Nginx / FAPI" "APIGatewayContainer"

            branchTerminal = container "Branch Terminal" "In-branch teller workstation application for assisted service. Access to customer accounts, payments initiation, document scanning for KYC. Connects to SVC-001, SVC-005, SVC-054 via internal APIs." "Electron / React" "DesktopClient"

            corporateAPIPortal = container "Corporate API Portal" "REST and ISO 20022 XML API portal for corporate treasury clients: bulk payment file submission, account information, FX rates, SWIFT message status. Connects to SVC-009, SVC-010, SVC-007." "Java / Spring Boot" "APIGatewayContainer"


            /* ── DOMAIN SERVICE CONTAINERS (SVC-001 to SVC-017) ── */

            /* Retail Banking */
            retailBankingCore = container "SVC-001 Retail Banking Core" "Retail customer ledger: current accounts, savings, personal loans, overdrafts, FSCS eligibility, CASS switching. Core banking platform (Thought Machine Vault / Mambu). Realises CAP-001.01–003." "Java / Thought Machine Vault" "DomainService"

            mortgageService = container "SVC-002 Mortgage Service" "End-to-end residential mortgage lifecycle: AIP, full application, MCOB underwriting, HM Land Registry, legal completion, arrears, redemption. Realises CAP-001.04." "Java / Spring Boot" "DomainService"

            creditCardService = container "SVC-003 Credit Card Service" "Personal credit card lifecycle: application, issuance, real-time authorisation, clearing/settlement with Visa/Mastercard, S75 liability, rewards. PCI DSS CDE scoped. Realises CAP-001.05." "Java / Spring Boot" "DomainService"

            insuranceDistributionService = container "SVC-004 Insurance Distribution Service" "FCA-authorised insurance intermediary for retail insurance products (home, travel, life, packaged account). ICOBS, IDD. Quote/bind/renew workflows. Realises CAP-001.06." "Python / FastAPI" "DomainService"

            /* Commercial Banking */
            commercialBankingCore = container "SVC-005 Commercial Banking Core" "Commercial customer ledger: business current accounts, overdrafts, revolving credit, term loans. RM workflow, covenant monitoring. nCino on Salesforce integration. Realises CAP-002.01–002." "Java / Salesforce / nCino" "DomainService"

            tradeFinanceService = container "SVC-006 Trade Finance Service" "Letters of credit, documentary collections, standby LCs, trade guarantees, supply chain finance. SWIFT MT700-series, UCP 600, ETDA 2023 electronic documents. Realises CAP-002.03." "Java / Finastra Trade Innovation" "DomainService"

            treasuryService = container "SVC-007 Treasury Service" "Cash management, notional pooling, physical sweeping, IRS/FX hedging, ISDA/CSA management, EMIR margin, MiFID II suitability for derivatives. Corporate treasury portal (Kyriba). Realises CAP-002.04." "Java / Spring Boot / Kyriba" "DomainService"

            merchantAcquiringService = container "SVC-008 Merchant Acquiring Service" "Card acquiring: Visa/MC/Amex acceptance, POS/online payment gateway, chargeback management, T+1–T+3 settlement. Bureau model (Worldpay). PCI DSS CDE scoped. Realises CAP-002.05." "Java / Spring Boot" "DomainService"

            /* Payment Operations */
            domesticPaymentsService = container "SVC-009 Domestic Payments Service" "FPS, BACS, CHAPS origination and settlement. Direct scheme participation via Form3. Confirmation of Payee. Payment policy engine. Intraday settlement monitoring. Realises CAP-003.01–03, 06." "Java / Form3 / ISO 20022" "DomainService"

            internationalPaymentsService = container "SVC-010 International Payments Service" "SWIFT cross-border payments (CBPR+ ISO 20022, mandatory Nov 2025). Correspondent bank management, nostro account management, FX execution. FATF travel rule. GPI tracking. Realises CAP-003.04." "Java / SWIFT SAA Cloud / Volante" "DomainService"

            cardProcessingService = container "SVC-011 Card Processing Service" "Debit and commercial card issuing: BIN management, sub-100ms authorisation via Visa/MC networks, clearing/settlement, dispute management. Marqeta or GPS/Thredd. PCI DSS CDE. Realises CAP-003.05." "Java / Marqeta" "DomainService"

            /* Risk Management */
            riskEngineService = container "SVC-012 Risk Engine Service" "IRB PD/LGD/EAD models, IFRS 9 ECL provisioning, FRTB market risk, Basel 3.1 output floor, ICAAP/Pillar 2, PRA model inventory (SS1/23). SAS Risk Intelligence Suite. Realises CAP-004.01–03, 05." "SAS / Python / R" "DomainService"

            fraudDetectionService = container "SVC-013 Fraud Detection Service" "Real-time APP fraud, card fraud (CNP/CP), identity fraud, internal fraud detection. ML scoring (Featurespace ARIC). PSR mandatory reimbursement case management. Sub-100ms for card auth path. Realises CAP-004.04." "Python / Featurespace ARIC" "DomainService"

            /* Compliance & Regulatory */
            kycAmlService = container "SVC-014 KYC/AML Service" "Perpetual KYC: CDD/EDD, UBO determination, PEP/adverse media screening, client risk scoring, SAR reporting to NCA UKFIU. MLRO accountability. Realises CAP-005.01 (promoted)." "Java / Spring Boot / ComplyAdvantage" "DomainService"

            complianceCoreService = container "SVC-015 Compliance Core Service" "COREP, FINREP, PRA 110, FCA returns. Consumer Duty outcomes monitoring. SM&CR accountability map. UK GDPR (ROPA, DPIAs, SARs). AxiomSL regulatory reporting. Realises CAP-005.02–05." "Java / AxiomSL / OneTrust" "DomainService"

            /* Wealth Management */
            wealthPlatformService = container "SVC-016 Wealth Platform Service" "Discretionary/advisory portfolio management, MiFID II suitability, private banking, financial planning, SDR ESG labels. FNZ custody, Wealth Dynamix CRM. Realises CAP-006.01–04." "Java / FNZ / Wealth Dynamix" "DomainService"

            /* Digital Channels */
            digitalChannelsService = container "SVC-017 Digital Channels Service" "iOS/Android/web experience layer, OBIE Open Banking API programme (AISP/PISP/VRP), TPP consent lifecycle, customer communications orchestration. Realises CAP-007.01–04." "TypeScript / Node.js / React Native" "DomainService"


            /* ── CROSS-CUTTING SERVICE CONTAINERS (SVC-050 to SVC-055) ── */

            customerOnboardingService = container "SVC-050 Customer Onboarding Service" "Authoritative cross-capability onboarding: KYC/CDD, beneficial ownership (Encompass), PEP screening (ComplyAdvantage), client risk scoring, SAR pre-check. Sync (retail <1s) and async (corporate EDD multi-day) modes. Publishes KYCClearanceGranted. SSC-001." "Java / Spring Boot / Onfido / Encompass" "CrossCuttingService"

            sanctionsScreeningService = container "SVC-051 Sanctions Screening Service" "Real-time sanctions screening against OFSI, OFAC, EU, UN lists. Name-matching, fuzzy matching, beneficial ownership chain traversal. Blocking payment API (<200ms). Batch rescreening on list update. 99.99% availability. SSC-002." "Java / ComplyAdvantage / Refinitiv World-Check" "CrossCuttingService"

            creditDecisionService = container "SVC-052 Credit Decision Service" "Cross-capability credit decisioning: PD/LGD/EAD scoring (Experian PowerCurve), credit bureau integration, credit appetite policy, IFRS 9 staging. Sync (retail <1s) and async (SME >£250k committee). Versioned model API. SSC-003." "Java / Experian PowerCurve" "CrossCuttingService"

            notificationService = container "SVC-053 Notification Service" "Cross-capability customer communications: push (iOS/Android), SMS, in-app, email, WhatsApp Business. GDPR consent state, PECR, regulated communications (MCOB, CONC, BCOBS) delivery regardless of marketing opt-out. Twilio delivery infrastructure. SSC-004." "Node.js / Twilio" "CrossCuttingService"

            documentManagementService = container "SVC-054 Document Management Service" "Authoritative document storage: KYC/EDD documents, mortgage legal papers, trade finance bills, insurance policies, regulated credit agreements. ETDA 2023 electronic trade documents. Retention policy enforcement. AWS S3 + Macie. SSC-005." "Python / FastAPI / AWS S3" "CrossCuttingService"

            workflowEngine = container "SVC-055 Workflow Engine" "Durable orchestration for long-running multi-step processes: corporate EDD, mortgage origination, trade LC issuance, commercial credit committee. Maker-checker, SLA monitoring, escalation. Temporal or Camunda. SSC-006." "Go / Temporal" "CrossCuttingService"


            /* ── FOUNDATION PLATFORM CONTAINERS (SVC-100 to SVC-106) ── */

            identityAccessManagement = container "SVC-100 Identity & Access Management" "Customer SCA (PSD2 RTS, biometric), employee SSO, service account identity, OAuth 2.0 / OIDC token issuance, RBAC/ABAC, TPP certificate validation (OBIE), DIATF relying party. ForgeRock / Okta. 99.99% availability." "ForgeRock Identity Platform" "FoundationService"

            apiGateway = container "SVC-101 API Gateway" "Edge API management: rate limiting, TLS termination, API versioning, TPP FAPI validation, usage analytics, developer portal for fintech partners. Apigee / Kong. CMA Open Banking performance reporting." "Apigee / Kong Gateway" "FoundationService"

            eventBus = container "SVC-102 Event Bus" "Durable event streaming: Kafka (Confluent Cloud), CloudEvents 1.0 envelopes, schema registry, consumer group management, dead letter queues, event sourcing support. Schema version 2-version backward compat required. 99.99% availability." "Apache Kafka / Confluent Cloud" "MessageBroker"

            auditLogging = container "SVC-103 Audit & Logging" "Immutable audit logging, SIEM (Splunk Enterprise Security), structured log aggregation, 5–7 year retention, SM&CR evidence, Consumer Duty outcomes, FCA/PRA supervisory data delivery. PCI DSS scoped." "Splunk Enterprise Security / ELK" "FoundationService"

            dataPlatform = container "SVC-104 Data Platform" "Enterprise data lake and warehouse: Databricks Lakehouse, feature store (fraud ML, credit ML, AML TM), ML model serving, COREP/FINREP data aggregation, ROPA support, cross-domain analytics. PCI DSS scoped." "Databricks / Apache Spark / Delta Lake" "FoundationService"

            secretsManagement = container "SVC-105 Secrets Management" "HSM-backed cryptographic key storage, automatic secrets rotation, dynamic database credentials (Vault DB engine, 1-hour TTL), SPIFFE/SPIRE certificate issuance integration. HashiCorp Vault Enterprise. PCI DSS Req 3.6. 99.99%." "HashiCorp Vault Enterprise" "FoundationService"

            serviceMesh = container "SVC-106 Service Mesh" "mTLS enforcement (STRICT mode), zero-trust deny-all AuthorizationPolicy, Envoy sidecar proxies, distributed tracing (OTel W3C TraceContext), circuit breaking, retry, service discovery. Istio / Linkerd. Zero plaintext in RC/Prod." "Istio / Envoy Proxy" "FoundationService"


            /* ── OBSERVABILITY CONTAINERS (SVC-107 to SVC-113) ── */

            otelCollector = container "SVC-107 OTel Collector" "Sole telemetry ingestion point. OTLP/gRPC and OTLP/HTTP receivers. PII scrubbing processor (regex-redaction + HMAC pseudonymisation). Fan-out exporters to Log Store, Trace Store, Metrics Store, Audit Store. Sidecar + gateway deployment." "OpenTelemetry Collector" "ObservabilityService"

            logStore = container "SVC-108 Log Store" "Operational log aggregation: 90-day hot retention, tiered to cold after 30 days. SRE and service-owner read access. Post-scrubbing — no raw PII. Structured JSON. OTel log format." "Grafana Loki / OpenSearch" "LogDatabase"

            traceStore = container "SVC-109 Trace Store" "Distributed trace storage: 30-day retention. W3C TraceContext propagated. Pseudonymised correlation IDs only. Used for latency analysis, regression detection, and inter-service call analysis." "Grafana Tempo / Jaeger" "TraceDatabase"

            metricsStore = container "SVC-110 Metrics Store" "Long-term metrics: 13-month retention for SLO tracking, capacity planning, CMA Open Banking availability reporting, FCA operational resilience self-assessment evidence. Prometheus/Mimir." "Prometheus / Grafana Mimir" "MetricsDatabase"

            auditStore = container "SVC-111 Audit Store" "WORM (Write Once Read Many) audit log storage: 7-year retention. Cryptographically sealed (SHA-256 HMAC, HSM-backed key via SVC-105). Auditor-only access (two-person control). MLR 2017, POCA 2002, PCI DSS Req 10." "AWS S3 Object Lock (Compliance)" "AuditDatabase"

            observabilityDashboards = container "SVC-112 Observability Dashboards" "Grafana dashboards: service RED metrics, SLO tracking, Kafka consumer lag, secret expiry countdown, CVE exposure badges, blast radius visualiser, mTLS coverage, data freshness contracts (FRS-001 to FRS-007)." "Grafana" "ObservabilityService"

            securitySIEM = container "SVC-113 Security SIEM" "Real-time security event correlation and alerting (Splunk Enterprise Security). Brute-force detection, lateral movement alerts, PCI DSS compliance dashboards, SM&CR conduct surveillance, FCA operational resilience incident evidence." "Splunk Enterprise Security" "ObservabilityService"


            /* ── SERVICE-SPECIFIC DATA STORES ── */

            dsRetailBanking = container "DS-SVC-001 Retail Ledger DB" "Authoritative retail customer ledger: account balances, transaction history, FSCS eligibility flags. DC-4. PostgreSQL / Thought Machine native store." "PostgreSQL" "Database"

            dsMortgage = container "DS-SVC-002 Mortgage DB" "Mortgage origination records, repayment schedules, HM Land Registry submissions, MCOB evidence. DC-4." "PostgreSQL" "Database"

            dsCreditCard = container "DS-SVC-003 Credit Card DB" "Tokenised PAN storage, statement data, transaction records. PCI DSS CDE. DC-5." "PostgreSQL (PCI CDE)" "Database"

            dsInsurance = container "DS-SVC-004 Insurance DB" "Policy records, IPID documents, renewal schedules, underwriter relationships. DC-4." "PostgreSQL" "Database"

            dsCommercialBanking = container "DS-SVC-005 Commercial Ledger DB" "Commercial account balances, lending facilities, covenant tracking, RM workflow state. DC-4." "PostgreSQL" "Database"

            dsTradeFinance = container "DS-SVC-006 Trade Finance DB" "LC records, documentary collections, SWIFT message logs, ETDA 2023 electronic documents. DC-3." "PostgreSQL" "Database"

            dsTreasury = container "DS-SVC-007 Treasury DB" "ISDA agreements, derivative positions, EMIR trade reports, notional pool structures. DC-3." "PostgreSQL" "Database"

            dsMerchantAcquiring = container "DS-SVC-008 Merchant Acquiring DB" "Merchant records, acquiring transactions, chargeback lifecycle, settlement records. PCI DSS CDE. DC-5." "PostgreSQL (PCI CDE)" "Database"

            dsDomesticPayments = container "DS-SVC-009 Payments DB" "FPS/BACS/CHAPS payment instructions, settlement positions, CoP results, scheme acknowledgements. DC-4." "PostgreSQL" "Database"

            dsInternationalPayments = container "DS-SVC-010 International Payments DB" "SWIFT messages (ISO 20022 MX), nostro account positions, FX rates, GPI status records. DC-4." "PostgreSQL" "Database"

            dsCardProcessing = container "DS-SVC-011 Card Processing DB" "BIN configuration, tokenised card records, authorisation history, dispute lifecycle. PCI DSS CDE. DC-5." "PostgreSQL (PCI CDE)" "Database"

            dsRiskEngine = container "DS-SVC-012 Risk Engine DB" "IRB model inputs/outputs, IFRS 9 ECL data, COREP calculation workspace, ICAAP evidence. DC-3." "PostgreSQL" "Database"

            dsFraudDetection = container "DS-SVC-013 Fraud DB" "Fraud case records, ML feature store snapshots, Cifas FNIF submissions, PSR reimbursement cases. DC-4." "PostgreSQL" "Database"

            dsKycAml = container "DS-SVC-014 KYC/AML DB" "CDD/EDD records, client risk scores, SAR data (POCA protected), NCA UKFIU submissions. DC-6. Isolated SAR store with separate access controls." "PostgreSQL (SAR-isolated)" "Database"

            dsCompliance = container "DS-SVC-015 Compliance DB" "Regulatory return data, SM&CR accountability map, GDPR ROPA/DPIAs, ICO breach records. DC-6." "PostgreSQL" "Database"

            dsWealthPlatform = container "DS-SVC-016 Wealth DB" "Portfolio positions, MiFID II suitability records, SDR ESG labels, private banking relationship data. DC-4." "PostgreSQL" "Database"

            dsDigitalChannels = container "DS-SVC-017 Digital Channels DB" "Session tokens, Open Banking consent records, TPP registrations, push notification preferences. DC-4." "PostgreSQL" "Database"

            dsCustomerOnboarding = container "DS-SVC-050 Onboarding DB" "Onboarding journey state, KYC clearance records, UBO determination outcomes. DC-6." "PostgreSQL" "Database"

            dsSanctionsScreening = container "DS-SVC-051 Sanctions DB" "Sanctions screening decisions (CLEAR/BLOCKED/REVIEW), OFSI licence workflow, rescreening job state. DC-6." "PostgreSQL" "Database"

            dsCreditDecision = container "DS-SVC-052 Credit Decision DB" "Credit decision records with model version, bureau data snapshots, IFRS 9 staging at origination. DC-4." "PostgreSQL" "Database"

            dsNotification = container "DS-SVC-053 Notification DB" "Communication preferences, consent state, delivery confirmations, regulated message audit trail. DC-4." "PostgreSQL" "Database"

            dsDocumentManagement = container "DS-SVC-054 Document Store" "ETDA 2023 electronic trade documents, KYC identity documents, mortgage legal papers, regulated credit agreements. DC-4. S3 + Macie." "AWS S3 + Macie" "FileStorage"

            dsWorkflowEngine = container "DS-SVC-055 Workflow DB" "Durable workflow state, human task queue, approval chain records, SLA timers. DC-3." "PostgreSQL" "Database"

            dsAuditWorm = container "DS-AUDIT WORM Audit Store" "Immutable 7-year WORM audit log storage. Cryptographically sealed. Auditor-only access. MLR 2017, POCA 2002, PCI DSS Req 10. S3 Object Lock Compliance mode." "AWS S3 Object Lock" "AuditDatabase"

        }
        /* End bankingSystem */


        /* ─────────────────────────────────────────────
         * RELATIONSHIPS — Person → System
         * ───────────────────────────────────────────── */

        personalCustomer -> bankingSystem "Uses online and mobile banking, applies for products, makes payments" "HTTPS / Mobile App"
        businessCustomerSME -> bankingSystem "Manages business accounts, submits payments, uses Open Banking API integrations" "HTTPS / Open Banking API"
        corporateClient -> bankingSystem "Uses corporate banking portal, submits bulk payment files, accesses FX and treasury services" "HTTPS / ISO 20022 API / SWIFT"
        hnwClient -> bankingSystem "Manages investment portfolio, accesses private banking services, receives suitability reviews" "HTTPS / Mobile App"
        mortgageApplicant -> bankingSystem "Submits mortgage application, tracks status, receives MCOB communications" "HTTPS / Branch"
        thirdPartyProvider -> bankingSystem "Accesses customer account data (AISP) and initiates payments (PISP) via Open Banking APIs with customer consent" "HTTPS / FAPI 1.0 Advanced"
        merchant -> bankingSystem "Receives card settlement, manages disputes and chargebacks, accesses acquiring reports" "HTTPS / API"
        correspondentBank -> bankingSystem "Receives and sends SWIFT cross-border payment messages, manages nostro/vostro positions" "SWIFT / CBPR+ ISO 20022"
        regulator -> bankingSystem "Receives regulatory returns (COREP, FINREP, FCA), supervisory data requests, material incident notifications" "Regulatory Portal / XBRL"
        cardNetwork -> bankingSystem "Exchanges card authorisation, clearing, and settlement messages; enforces scheme compliance" "Card Network / ISO 8583"
        insuranceUnderwriter -> bankingSystem "Provides insurance products for distribution; receives policy binding requests and claims referrals" "API / Email"
        esgRatingAgency -> bankingSystem "Provides ESG rating data for corporate lending and SDR-labelled wealth portfolios" "API / Data Feed"


        /* ─────────────────────────────────────────────
         * RELATIONSHIPS — System → External Systems
         * ───────────────────────────────────────────── */

        bankingSystem -> fps "Originates and settles domestic sterling FPS payments" "Form3 / ISO 20022 IPS"
        bankingSystem -> bacs "Submits BACS Direct Credit and Direct Debit bulk payment files" "BACS bureau / Bottomline PTX"
        bankingSystem -> chapsRtgs "Originates CHAPS same-day high-value sterling payments; participates in Bank of England RT2 RTGS" "ISO 20022 / CHAPS Rules"
        bankingSystem -> swift "Sends and receives SWIFT messages for cross-border payments, trade finance LC messaging, GPI tracking" "SWIFT CBPR+ ISO 20022 / MT700"
        bankingSystem -> cardNetworks "Card authorisation, clearing, settlement, dispute messages; BIN management; PCI DSS compliance" "ISO 8583 / HSM / Visa/MC API"
        bankingSystem -> companiesHouse "Queries company registration data and PSC records for corporate KYB and UBO determination" "Companies House API (REST)"
        bankingSystem -> creditBureaus "Requests credit scores, credit reports, and affordability data under RBUA agreements" "Experian / Equifax / TransUnion API"
        bankingSystem -> hmrc "Submits FATCA/CRS regulatory reports; integrates Making Tax Digital API for business customers" "HMRC API / XBRL"
        bankingSystem -> bankOfEngland "Submits COREP, FINREP, PRA 110, ICAAP; maintains RTGS settlement account" "PRA RegData / Bank of England RTGS"
        bankingSystem -> fcaConnect "Submits FCA returns (RegData), REP-CRIM, Product Sales Data, incident notifications, Consumer Duty evidence" "FCA Connect / RegData API"
        bankingSystem -> obieDirectory "Validates TPP eIDAS/FAPI certificates; registers as Open Banking participant; checks TPP authorisation status" "OBIE Directory API"


        /* ─────────────────────────────────────────────
         * RELATIONSHIPS — Container to Container
         * (Abbreviated to key cross-cutting paths; mesh enforces all)
         * ───────────────────────────────────────────── */

        /* Channel → Platform Edge */
        personalCustomer -> webPortal "Logs in, views accounts, makes payments" "HTTPS"
        personalCustomer -> mobileApp "Biometric authentication, push notifications, card controls" "HTTPS / Push"
        businessCustomerSME -> webPortal "Business banking portal" "HTTPS"
        businessCustomerSME -> corporateAPIPortal "API integrations with accounting software (Xero, QuickBooks)" "HTTPS / Open Banking"
        corporateClient -> corporateAPIPortal "Bulk payment submission, FX rates, account information" "HTTPS / ISO 20022"
        thirdPartyProvider -> openBankingGateway "AISP account information and PISP payment initiation with customer consent" "HTTPS / FAPI 1.0"
        mortgageApplicant -> webPortal "Mortgage application, status tracking" "HTTPS"
        mortgageApplicant -> branchTerminal "Branch-assisted mortgage application" "Internal"
        hnwClient -> webPortal "Portfolio view, investment instructions" "HTTPS"
        hnwClient -> mobileApp "Mobile wealth access" "HTTPS"

        webPortal -> apiGateway "All API calls routed through edge gateway" "HTTPS/TLS 1.3"
        mobileApp -> apiGateway "All API calls routed through edge gateway" "HTTPS/TLS 1.3"
        openBankingGateway -> apiGateway "FAPI-validated requests forwarded to backend" "HTTPS/TLS 1.3"
        branchTerminal -> apiGateway "Teller API calls via internal gateway" "HTTPS/TLS 1.3"
        corporateAPIPortal -> apiGateway "Corporate API calls via gateway" "HTTPS/TLS 1.3"

        apiGateway -> identityAccessManagement "Token validation, TPP certificate verification" "HTTPS / OIDC (mTLS)"
        apiGateway -> digitalChannelsService "Forwards authenticated customer requests" "HTTPS / OTLP (mTLS)"
        apiGateway -> auditLogging "Logs all inbound API calls, rate limit events, auth failures" "OTLP/gRPC (mTLS)"

        /* Digital Channels → Domain Services */
        digitalChannelsService -> retailBankingCore "Account balance, transaction history" "gRPC / OTLP (mTLS)"
        digitalChannelsService -> domesticPaymentsService "Payment initiation (PISP, FPS)" "gRPC (mTLS)"
        digitalChannelsService -> notificationService "Customer communication triggers" "Kafka (CloudEvents)"
        digitalChannelsService -> dsDigitalChannels "Session, consent, TPP data" "JDBC"

        /* Core Domain Service → Data Stores */
        retailBankingCore -> dsRetailBanking "Ledger read/write" "JDBC (dynamic secret)"
        mortgageService -> dsMortgage "Mortgage lifecycle data" "JDBC (dynamic secret)"
        creditCardService -> dsCreditCard "Card data (tokenised PAN)" "JDBC (dynamic secret, PCI CDE)"
        insuranceDistributionService -> dsInsurance "Policy data" "JDBC (dynamic secret)"
        commercialBankingCore -> dsCommercialBanking "Commercial ledger" "JDBC (dynamic secret)"
        tradeFinanceService -> dsTradeFinance "Trade finance records" "JDBC (dynamic secret)"
        treasuryService -> dsTreasury "Derivative and pool positions" "JDBC (dynamic secret)"
        merchantAcquiringService -> dsMerchantAcquiring "Merchant and transaction data" "JDBC (dynamic secret, PCI CDE)"
        domesticPaymentsService -> dsDomesticPayments "Payment state" "JDBC (dynamic secret)"
        internationalPaymentsService -> dsInternationalPayments "SWIFT messages, FX" "JDBC (dynamic secret)"
        cardProcessingService -> dsCardProcessing "Card and auth data" "JDBC (dynamic secret, PCI CDE)"
        riskEngineService -> dsRiskEngine "Model data, COREP workspace" "JDBC (dynamic secret)"
        fraudDetectionService -> dsFraudDetection "Fraud cases, ML features" "JDBC (dynamic secret)"
        kycAmlService -> dsKycAml "CDD, SAR, risk scores" "JDBC (dynamic secret)"
        complianceCoreService -> dsCompliance "Regulatory returns, ROPA" "JDBC (dynamic secret)"
        wealthPlatformService -> dsWealthPlatform "Portfolio, suitability records" "JDBC (dynamic secret)"

        /* Cross-Cutting Services → Data Stores */
        customerOnboardingService -> dsCustomerOnboarding "Onboarding journey state, KYC clearance" "JDBC (dynamic secret)"
        sanctionsScreeningService -> dsSanctionsScreening "Screening decisions, rescreening jobs" "JDBC (dynamic secret)"
        creditDecisionService -> dsCreditDecision "Decision records with model version" "JDBC (dynamic secret)"
        notificationService -> dsNotification "Preferences, consent, delivery confirmations" "JDBC (dynamic secret)"
        documentManagementService -> dsDocumentManagement "Document store (S3 + Macie)" "AWS SDK / S3 API"
        workflowEngine -> dsWorkflowEngine "Workflow state, task queue, approvals" "JDBC (dynamic secret)"

        /* Hard-blocking synchronous dependencies (key paths) */
        domesticPaymentsService -> sanctionsScreeningService "Sanctions clearance (blocking, <200ms SLA)" "gRPC (mTLS)"
        domesticPaymentsService -> fraudDetectionService "APP fraud scoring (blocking, <100ms SLA)" "gRPC (mTLS)"
        internationalPaymentsService -> sanctionsScreeningService "Cross-border beneficiary screening" "gRPC (mTLS)"
        cardProcessingService -> fraudDetectionService "Card fraud score in authorisation path" "gRPC (mTLS)"
        creditCardService -> fraudDetectionService "CNP fraud in card authorisation" "gRPC (mTLS)"
        retailBankingCore -> customerOnboardingService "Blocks account creation on KYCClearanceGranted" "Kafka (CloudEvents)"
        commercialBankingCore -> customerOnboardingService "Blocks business account creation on KYCClearanceGranted" "Kafka (CloudEvents)"
        mortgageService -> creditDecisionService "MCOB affordability and credit decision" "gRPC (mTLS)"
        retailBankingCore -> creditDecisionService "Overdraft limit setting and personal loan origination" "gRPC (mTLS)"

        /* Platform → Event Bus (publish) */
        retailBankingCore -> eventBus "Publishes AccountOpened, BalanceUpdated, LoanOriginated" "Kafka Producer (mTLS)"
        commercialBankingCore -> eventBus "Publishes FacilityApproved, DrawdownCompleted" "Kafka Producer (mTLS)"
        domesticPaymentsService -> eventBus "Publishes PaymentSettled, PaymentRejected" "Kafka Producer (mTLS)"
        fraudDetectionService -> eventBus "Publishes FraudAlertGenerated" "Kafka Producer (mTLS)"
        customerOnboardingService -> eventBus "Publishes KYCClearanceGranted, CustomerRiskScoreAssigned" "Kafka Producer (mTLS)"
        sanctionsScreeningService -> eventBus "Publishes SanctionsListUpdated" "Kafka Producer (mTLS)"
        creditDecisionService -> eventBus "Publishes CreditDecisionMade, LimitApproved" "Kafka Producer (mTLS)"

        /* Platform → Event Bus (subscribe) */
        riskEngineService -> eventBus "Subscribes to LoanOriginated, FacilityApproved for IFRS 9/COREP" "Kafka Consumer (mTLS)"
        kycAmlService -> eventBus "Subscribes to PaymentReceived, CustomerRiskTrigger for perpetual KYC" "Kafka Consumer (mTLS)"
        notificationService -> eventBus "Subscribes to PaymentSettled, FraudAlertGenerated, LoanApproved for customer comms" "Kafka Consumer (mTLS)"
        dataPlatform -> eventBus "Ingests all domain events for analytics and ML feature store" "Kafka Consumer (mTLS)"

        /* Foundation → Foundation dependencies */
        secretsManagement -> identityAccessManagement "Service identity (machine identity) verification before granting secrets" "mTLS / OIDC"
        serviceMesh -> identityAccessManagement "SPIFFE/SPIRE certificate issuance coordination" "mTLS / PKI"
        apiGateway -> identityAccessManagement "Delegates token validation and TPP certificate verification" "OIDC / mTLS"
        workflowEngine -> identityAccessManagement "Human task identity (maker-checker, credit committee)" "OIDC (mTLS)"

        /* Observability pipeline */
        otelCollector -> logStore "Exports structured logs (post-PII-scrubbing)" "OTLP/gRPC"
        otelCollector -> traceStore "Exports distributed traces" "OTLP/gRPC"
        otelCollector -> metricsStore "Exports metrics" "OTLP/gRPC"
        otelCollector -> dsAuditWorm "Exports immutable audit events (encrypted pipeline)" "OTLP/gRPC (encrypted)"
        observabilityDashboards -> logStore "Queries logs for dashboards and alerts" "Loki API"
        observabilityDashboards -> traceStore "Queries traces for latency analysis" "Tempo API"
        observabilityDashboards -> metricsStore "Queries metrics for SLO dashboards" "PromQL"
        securitySIEM -> logStore "Ingests security events for correlation" "Loki / Kafka"
        securitySIEM -> dsAuditWorm "Reads audit evidence for compliance investigations" "Vault-controlled read"

        /* Services → Audit Logging */
        retailBankingCore -> auditLogging "Audit trail for account operations" "OTLP via OTel Collector"
        creditCardService -> auditLogging "PCI DSS access logs, card operation audit" "OTLP via OTel Collector"
        kycAmlService -> auditLogging "MLR 2017 CDD audit, SAR trail" "OTLP via OTel Collector"
        sanctionsScreeningService -> auditLogging "OFSI screening decisions (CLEAR/BLOCKED)" "OTLP via OTel Collector"
        complianceCoreService -> auditLogging "SM&CR conduct evidence, GDPR ROPA records" "OTLP via OTel Collector"
        identityAccessManagement -> auditLogging "Authentication events, access grants, denials" "OTLP via OTel Collector"
        secretsManagement -> auditLogging "Every secret access event (PCI DSS Req 3.6)" "OTLP via OTel Collector"

        /* Services → External Systems */
        domesticPaymentsService -> fps "FPS payment submission and settlement" "Form3 / ISO 20022"
        domesticPaymentsService -> bacs "BACS bulk payment file submission" "BACS bureau"
        domesticPaymentsService -> chapsRtgs "CHAPS high-value payment submission" "ISO 20022 / RT2"
        internationalPaymentsService -> swift "SWIFT cross-border payment messages" "CBPR+ ISO 20022"
        tradeFinanceService -> swift "SWIFT MT700-series LC and trade messages" "SWIFT MT/MX"
        cardProcessingService -> cardNetworks "Card authorisation, clearing, settlement" "ISO 8583 / Visa/MC"
        merchantAcquiringService -> cardNetworks "Acquiring settlement and dispute messages" "Visa/MC scheme"
        customerOnboardingService -> companiesHouse "Company registration and PSC data for corporate KYB" "Companies House REST API"
        creditDecisionService -> creditBureaus "Credit scores and reports (Experian, Equifax, TransUnion)" "Experian PowerCurve / RBUA"
        complianceCoreService -> bankOfEngland "COREP, FINREP, PRA 110, ICAAP submissions" "PRA RegData / XBRL"
        complianceCoreService -> fcaConnect "FCA regulatory returns, REP-CRIM, Consumer Duty evidence" "FCA Connect / RegData"
        complianceCoreService -> hmrc "FATCA/CRS reports" "HMRC API / XBRL"
        digitalChannelsService -> obieDirectory "TPP certificate validation" "OBIE Directory API"
        wealthPlatformService -> esgRatingAgency "Consumes ESG rating data for SDR-labelled portfolios" "API / Data Feed"

    }
    /* End model */


    /* ─────────────────────────────────────────────
     * VIEWS
     * ───────────────────────────────────────────── */

    views {

        systemContext bankingSystem "SystemContext" "System context view showing all external personas, the banking system, and connected external systems." {
            include *
            autoLayout lr
            description "Level 1 — System Context: all external actors, the Banking System, and external systems. PSD2 TPPs, card networks, payment rails, regulatory supervisors."
        }

        container bankingSystem "ContainerView" "Container view of the UK Commercial Bank: channel containers, all domain and cross-cutting service containers, platform and observability containers, and data stores." {
            include *
            autoLayout lr
            description "Level 2 — Container: channel layer, 17 domain services (SVC-001 to SVC-017), 6 cross-cutting services (SVC-050 to SVC-055), 7 foundation platform services (SVC-100 to SVC-106), 7 observability containers (SVC-107 to SVC-113), and per-service data stores. Component views deferred to Phase C."
        }


        /* ── STYLES ── */

        styles {

            element "Person" {
                shape Person
                background "#1168bd"
                color "#ffffff"
                fontSize 14
            }

            element "ExternalPersona" {
                shape Person
                background "#0a5fa8"
                color "#ffffff"
            }

            element "Software System" {
                background "#1168bd"
                color "#ffffff"
                fontSize 13
            }

            element "ExternalSystem" {
                background "#999999"
                color "#ffffff"
            }

            element "Container" {
                background "#438dd5"
                color "#ffffff"
                fontSize 12
            }

            element "WebBrowser" {
                shape WebBrowser
                background "#549dd5"
                color "#ffffff"
            }

            element "MobileApp" {
                shape MobileDeviceLandscape
                background "#4da0d0"
                color "#ffffff"
            }

            element "APIGatewayContainer" {
                shape Hexagon
                background "#2f6ea5"
                color "#ffffff"
            }

            element "DesktopClient" {
                shape Component
                background "#5b9bd5"
                color "#ffffff"
            }

            element "DomainService" {
                shape RoundedBox
                background "#2e6eb0"
                color "#ffffff"
            }

            element "CrossCuttingService" {
                shape RoundedBox
                background "#6b7db0"
                color "#ffffff"
            }

            element "FoundationService" {
                shape RoundedBox
                background "#406a8f"
                color "#ffffff"
            }

            element "ObservabilityService" {
                shape RoundedBox
                background "#5a7a5a"
                color "#ffffff"
            }

            element "MessageBroker" {
                shape Pipe
                background "#6b4f99"
                color "#ffffff"
            }

            element "Database" {
                shape Cylinder
                background "#438dd5"
                color "#ffffff"
            }

            element "FileStorage" {
                shape Folder
                background "#438dd5"
                color "#ffffff"
            }

            element "LogDatabase" {
                shape Cylinder
                background "#5a7a5a"
                color "#ffffff"
            }

            element "TraceDatabase" {
                shape Cylinder
                background "#6b7a4f"
                color "#ffffff"
            }

            element "MetricsDatabase" {
                shape Cylinder
                background "#5a6b7a"
                color "#ffffff"
            }

            element "AuditDatabase" {
                shape Cylinder
                background "#8b3333"
                color "#ffffff"
            }

        }
        /* End styles */

    }
    /* End views */

}
/* End workspace */
