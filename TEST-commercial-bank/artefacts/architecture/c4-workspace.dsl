workspace "UK Commercial Bank" "C4 architecture model for a UK commercial bank." {

    model {

        # ── People ──────────────────────────────────────────────────────────
        personalCustomer    = person "Personal Customer"        "Retail banking customer."                          "External"
        businessCustomer    = person "Business Customer"        "SME or corporate banking customer."                "External"
        hnwClient           = person "High Net Worth Client"    "Private / wealth management customer."             "External"
        mortgageApplicant   = person "Mortgage Applicant"       "Customer applying for a mortgage product."         "External"
        tpp                 = person "Third Party Provider"     "FCA-authorised TPP accessing Open Banking APIs."   "External"
        merchant            = person "Merchant"                 "Business accepting card payments."                 "External"
        correspondentBank   = person "Correspondent Bank"       "Overseas bank using SWIFT / nostro services."      "External"
        regulator           = person "Regulator (FCA/PRA)"      "Financial conduct and prudential regulator."       "External"
        cardNetwork         = person "Card Network"             "Visa / Mastercard scheme operator."                "External"

        # ── External Software Systems ────────────────────────────────────────
        fasterPayments  = softwareSystem "Faster Payments Service"  "Real-time retail payment infrastructure."          "External"
        bacs            = softwareSystem "BACS"                     "Bulk credit and direct debit clearing."            "External"
        chaps           = softwareSystem "CHAPS/RTGS"               "Same-day high-value sterling settlement."          "External"
        swift           = softwareSystem "SWIFT Network"            "International interbank messaging."                "External"
        visaMastercard  = softwareSystem "Card Networks"            "Visa and Mastercard scheme networks."              "External"
        companiesHouse  = softwareSystem "Companies House"          "UK company registry for KYB verification."         "External"
        creditBureaus   = softwareSystem "Credit Bureaus"           "Experian, Equifax, TransUnion credit data."        "External"
        hmrc            = softwareSystem "HMRC"                     "Tax authority — CASS and regulatory reporting."    "External"
        bankOfEngland   = softwareSystem "Bank of England"          "Central bank — reserve accounts and reporting."    "External"
        fca             = softwareSystem "FCA Connect"              "Regulatory portal for submissions."                "External"
        obie            = softwareSystem "Open Banking Directory"   "OBIE / Open Finance register of TPPs."             "External"

        # ── The Banking System ───────────────────────────────────────────────
        bankingSystem = softwareSystem "UK Commercial Bank" "Core banking platform delivering retail, commercial, payments, risk, and wealth services." {

            # ── Channel Layer ────────────────────────────────────────────────
            group "Channel Layer" {
                webPortal           = container "Web Portal"            "Browser-based internet banking for personal and business customers."   "React / TypeScript"    "Web Application"
                mobileApp           = container "Mobile App"            "iOS and Android native mobile banking application."                    "Swift / Kotlin"        "Mobile Application"
                openBankingGateway  = container "Open Banking Gateway"  "PSD2-compliant API gateway for TPP access."                           "Node.js"               "API Application"
                branchTerminal      = container "Branch Terminal"       "In-branch staff workstation for customer-facing operations."           "Electron"              "Desktop Application"
            }

            # ── Foundation Layer ─────────────────────────────────────────────
            group "Foundation" {
                iam                 = container "Identity & Access Management"  "Authentication, authorisation, and session management."     "Keycloak / OAuth 2.0"  "Service"
                apiGateway          = container "API Gateway"                   "Central ingress, routing, rate-limiting, and auth enforcement." "Kong"              "Service"
                eventBus            = container "Event Bus"                     "Asynchronous domain-event backbone."                        "Apache Kafka"          "Message Broker"
                auditLogging        = container "Audit & Logging"               "Immutable audit trail and observability pipeline."          "Elasticsearch / Fluentd" "Service"
                dataPlatform        = container "Data Platform"                 "Analytics, reporting, and ML feature store."                "Databricks / S3"       "Database"
                secretsManagement   = container "Secrets Management"            "Centralised secrets vault and key management."              "HashiCorp Vault"       "Service"
            }

            # ── Data Stores ──────────────────────────────────────────────────
            group "Data Stores" {
                retailDb        = container "Retail Banking Database"       "Persistent store for retail accounts, mortgages, and cards."    "PostgreSQL"    "Database"
                commercialDb    = container "Commercial Banking Database"   "Persistent store for commercial accounts and trade finance."    "PostgreSQL"    "Database"
                paymentsDb      = container "Payments Database"             "Payment instructions, status, and reconciliation records."      "PostgreSQL"    "Database"
                riskDb          = container "Risk Database"                 "Risk scores, AML alerts, and compliance records."              "PostgreSQL"    "Database"
                wealthDb        = container "Wealth Database"               "Portfolio, position, and client suitability data."             "PostgreSQL"    "Database"
                auditDb         = container "Audit Store"                   "Write-once audit log and regulatory evidence store."           "OpenSearch"    "Database"
            }

            # ── Domain Services — Retail Banking ─────────────────────────────
            group "Retail Banking" {
                retailAccounts          = container "Retail Accounts Service"           "Current, savings, and ISA account management."         "Java / Spring Boot" "Service"
                mortgageService         = container "Mortgage Service"                  "Mortgage origination, servicing, and redemption."      "Java / Spring Boot" "Service"
                creditCardService       = container "Credit Card Service"               "Card issuance, limit management, and statements."      "Java / Spring Boot" "Service"
                insuranceDistribution   = container "Insurance Distribution Service"    "Bancassurance product distribution and claims."        "Java / Spring Boot" "Service"
            }

            # ── Domain Services — Commercial Banking ──────────────────────────
            group "Commercial Banking" {
                commercialAccounts  = container "Commercial Accounts Service"   "Business current accounts, overdrafts, and FX."        "Java / Spring Boot" "Service"
                tradeFinance        = container "Trade Finance Service"         "Letters of credit, guarantees, and trade instruments."  "Java / Spring Boot" "Service"
                treasuryService     = container "Treasury Service"              "Liquidity, FX, and money markets."                     "Java / Spring Boot" "Service"
                merchantAcquiring   = container "Merchant Acquiring Service"    "Merchant onboarding, settlement, and disputes."        "Java / Spring Boot" "Service"
            }

            # ── Domain Services — Payments ────────────────────────────────────
            group "Payments" {
                domesticPayments        = container "Domestic Payments Service"     "Faster Payments, BACS, and CHAPS instruction processing."  "Java / Spring Boot" "Service"
                internationalPayments   = container "International Payments Service" "Cross-border SWIFT and SEPA payment processing."          "Java / Spring Boot" "Service"
                cardProcessing          = container "Card Processing Service"       "Card authorisation, clearing, and settlement."             "Java / Spring Boot" "Service"
            }

            # ── Domain Services — Risk & Compliance ───────────────────────────
            group "Risk & Compliance" {
                riskEngine          = container "Risk Engine Service"        "Credit, market, and operational risk computation."     "Python / FastAPI"   "Service"
                fraudDetection      = container "Fraud Detection Service"    "Real-time transaction fraud scoring."                  "Python / FastAPI"   "Service"
                kycAml              = container "KYC/AML Service"            "Know Your Customer and Anti-Money Laundering checks."  "Java / Spring Boot" "Service"
                complianceService   = container "Compliance Service"         "Regulatory reporting and policy enforcement."          "Java / Spring Boot" "Service"
            }

            # ── Domain Services — Wealth ──────────────────────────────────────
            group "Wealth" {
                wealthPlatform  = container "Wealth Platform Service"   "Portfolio management, advisory, and discretionary services." "Java / Spring Boot" "Service"
            }

            # ── Cross-Cutting Services ────────────────────────────────────────
            group "Cross-Cutting" {
                customerOnboarding  = container "Customer Onboarding Service"   "Digital onboarding journey orchestration."         "Java / Spring Boot" "Service"
                sanctionsScreening  = container "Sanctions Screening Service"   "Real-time and batch sanctions list screening."     "Java / Spring Boot" "Service"
                creditDecision      = container "Credit Decision Service"       "Automated credit scoring and decisioning."         "Python / FastAPI"   "Service"
                notificationService = container "Notification Service"          "Multi-channel customer notifications (push, SMS, email)." "Node.js"    "Service"
                documentManagement  = container "Document Management Service"   "Document capture, storage, and retrieval."         "Java / Spring Boot" "Service"
                workflowEngine      = container "Workflow Engine"               "Long-running business process orchestration."      "Camunda"            "Service"
            }
        }

        # ════════════════════════════════════════════════════════════════════
        # Relationships
        # ════════════════════════════════════════════════════════════════════

        # People → Channels
        personalCustomer    -> webPortal            "Manages accounts and payments via"
        personalCustomer    -> mobileApp            "Manages accounts and payments via"
        businessCustomer    -> webPortal            "Manages business banking via"
        businessCustomer    -> mobileApp            "Manages business banking via"
        hnwClient           -> webPortal            "Accesses wealth services via"
        hnwClient           -> mobileApp            "Accesses wealth services via"
        mortgageApplicant   -> webPortal            "Submits mortgage application via"
        mortgageApplicant   -> mobileApp            "Submits mortgage application via"
        tpp                 -> openBankingGateway   "Accesses account and payment APIs via"
        merchant            -> webPortal            "Manages acquiring account via"
        correspondentBank   -> openBankingGateway   "Sends payment instructions via"
        regulator           -> openBankingGateway   "Retrieves regulatory data via"

        # Channels → API Gateway
        webPortal           -> apiGateway  "Routes all API calls through"
        mobileApp           -> apiGateway  "Routes all API calls through"
        openBankingGateway  -> apiGateway  "Forwards authenticated requests to"
        branchTerminal      -> apiGateway  "Routes all API calls through"

        # API Gateway → IAM
        apiGateway -> iam "Validates tokens and enforces access policies via"

        # API Gateway → Domain Services
        apiGateway -> retailAccounts        "Routes retail account requests to"
        apiGateway -> mortgageService       "Routes mortgage requests to"
        apiGateway -> creditCardService     "Routes card management requests to"
        apiGateway -> insuranceDistribution "Routes insurance requests to"
        apiGateway -> commercialAccounts    "Routes commercial account requests to"
        apiGateway -> tradeFinance          "Routes trade finance requests to"
        apiGateway -> treasuryService       "Routes treasury requests to"
        apiGateway -> merchantAcquiring     "Routes merchant acquiring requests to"
        apiGateway -> domesticPayments      "Routes domestic payment instructions to"
        apiGateway -> internationalPayments "Routes international payment instructions to"
        apiGateway -> cardProcessing        "Routes card transaction requests to"
        apiGateway -> wealthPlatform        "Routes wealth management requests to"
        apiGateway -> customerOnboarding    "Routes onboarding requests to"

        # Domain Services → Databases
        retailAccounts          -> retailDb     "Reads and writes account data"
        mortgageService         -> retailDb     "Reads and writes mortgage data"
        creditCardService       -> retailDb     "Reads and writes card data"
        insuranceDistribution   -> retailDb     "Reads and writes insurance data"
        commercialAccounts      -> commercialDb "Reads and writes commercial account data"
        tradeFinance            -> commercialDb "Reads and writes trade instrument data"
        treasuryService         -> commercialDb "Reads and writes treasury position data"
        merchantAcquiring       -> commercialDb "Reads and writes merchant data"
        domesticPayments        -> paymentsDb   "Reads and writes payment records"
        internationalPayments   -> paymentsDb   "Reads and writes payment records"
        cardProcessing          -> paymentsDb   "Reads and writes card transaction records"
        riskEngine              -> riskDb       "Reads and writes risk scores"
        fraudDetection          -> riskDb       "Reads and writes fraud signals"
        kycAml                  -> riskDb       "Reads and writes KYC/AML case data"
        complianceService       -> riskDb       "Reads and writes compliance records"
        wealthPlatform          -> wealthDb     "Reads and writes portfolio data"
        auditLogging            -> auditDb      "Writes immutable audit events"

        # Domain Services → Cross-Cutting
        mortgageService         -> creditDecision       "Requests credit assessment from"
        creditCardService       -> creditDecision       "Requests credit limit decision from"
        commercialAccounts      -> creditDecision       "Requests facility decision from"
        domesticPayments        -> sanctionsScreening   "Screens payment parties via"
        internationalPayments   -> sanctionsScreening   "Screens payment parties via"
        tradeFinance            -> sanctionsScreening   "Screens counterparties via"
        customerOnboarding      -> kycAml               "Initiates KYC/AML verification via"
        customerOnboarding      -> workflowEngine       "Orchestrates onboarding workflow via"
        mortgageService         -> workflowEngine       "Orchestrates mortgage process via"
        tradeFinance            -> workflowEngine       "Orchestrates trade instrument lifecycle via"
        retailAccounts          -> notificationService  "Sends account alerts via"
        commercialAccounts      -> notificationService  "Sends account alerts via"
        domesticPayments        -> notificationService  "Sends payment confirmations via"
        internationalPayments   -> notificationService  "Sends payment confirmations via"
        mortgageService         -> documentManagement   "Stores and retrieves mortgage documents via"
        tradeFinance            -> documentManagement   "Stores and retrieves trade documents via"
        customerOnboarding      -> documentManagement   "Stores identity documents via"

        # Domain Services → Foundation (event bus)
        retailAccounts          -> eventBus "Publishes account events to"
        mortgageService         -> eventBus "Publishes mortgage events to"
        commercialAccounts      -> eventBus "Publishes account events to"
        domesticPayments        -> eventBus "Publishes payment events to"
        internationalPayments   -> eventBus "Publishes payment events to"
        cardProcessing          -> eventBus "Publishes card transaction events to"
        fraudDetection          -> eventBus "Subscribes to transaction events from"
        riskEngine              -> eventBus "Subscribes to risk-relevant events from"
        auditLogging            -> eventBus "Subscribes to all domain events from"
        dataPlatform            -> eventBus "Ingests domain events from"

        # Cross-Cutting → Foundation
        customerOnboarding  -> iam              "Provisions identities in"
        workflowEngine      -> secretsManagement "Retrieves credentials from"
        notificationService -> secretsManagement "Retrieves API keys from"
        auditLogging        -> secretsManagement "Retrieves signing keys from"
        complianceService   -> dataPlatform     "Queries regulatory metrics from"
        riskEngine          -> dataPlatform     "Reads ML feature data from"

        # Domain Services → External Systems
        domesticPayments        -> fasterPayments   "Submits Faster Payment instructions to"
        domesticPayments        -> bacs             "Submits BACS bulk payment files to"
        domesticPayments        -> chaps            "Submits CHAPS high-value payments to"
        internationalPayments   -> swift            "Sends SWIFT messages to"
        cardProcessing          -> visaMastercard   "Exchanges authorisation messages with"
        kycAml                  -> companiesHouse   "Verifies company registration via"
        kycAml                  -> creditBureaus    "Retrieves credit file data from"
        creditDecision          -> creditBureaus    "Requests credit scores from"
        complianceService       -> hmrc             "Submits regulatory reports to"
        complianceService       -> bankOfEngland    "Submits prudential data to"
        complianceService       -> fca              "Submits regulatory returns via"
        openBankingGateway      -> obie             "Validates TPP certificates against"

        # Regulator read access
        complianceService   -> regulator "Provides regulatory data to"
    }

    # ════════════════════════════════════════════════════════════════════════
    # Views
    # ════════════════════════════════════════════════════════════════════════
    views {

        systemContext bankingSystem "SystemContext" "System context diagram for the UK Commercial Bank." {
            include *
            autoLayout lr
        }

        container bankingSystem "Containers" "Container diagram showing all services and data stores within the UK Commercial Bank." {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427B
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Software System" {
                background #1168BD
                color #ffffff
            }
            element "Container" {
                background #438DD5
                color #ffffff
            }
            element "Web Application" {
                shape WebBrowser
            }
            element "Mobile Application" {
                shape MobileDeviceLandscape
            }
            element "Desktop Application" {
                shape RoundedBox
            }
            element "Database" {
                shape Cylinder
                background #336791
                color #ffffff
            }
            element "Message Broker" {
                shape Pipe
                background #e67e00
                color #ffffff
            }
            element "API Application" {
                shape Hexagon
            }
            element "Service" {
                shape Component
            }
        }
    }
}
