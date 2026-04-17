/*
 * C4 workspace — Structurizr DSL
 *
 * Single source of truth for all C4 diagrams. Grows across phases:
 *   Phase B step 5: L1 System Context + L2 Container
 *   Phase C post-journey: L2 refinement + L3 Component per capability
 *
 * Every element must trace to a JSON artefact. See
 * context/best-practices/c4-workspace.md.
 */

workspace "{PROJECT_NAME}" "Capability architecture model" {

    model {
        // Personas — traces to foundation/personas/*.json
        // customer = person "Customer" "..."

        // External systems
        // regulator = softwareSystem "Regulator reporting endpoint" "External" "External System"

        system = softwareSystem "{PROJECT_NAME}" "Headless capability platform" {

            // Capabilities — one container per capability, traces to capabilities/*.json
            // cap001 = container "CAP-001 — Account Opening" "..." "Capability"

            // Platform containers — traces to architecture/service-catalogue.json
            // eventBus = container "Event Bus" "Async integration fabric" "Platform"
            // schemaRegistry = container "Schema Registry" "" "Platform"
            // observability = container "Observability" "" "Platform"
            // audit = container "Audit Pipeline" "" "Platform"
            // auth = container "Auth" "" "Platform"
            // cache = container "Cache" "" "Platform"
        }

        // Relationships — only the four valid paths:
        //   Channel -> Capability API (sync REST)
        //   Capability -> EventBus (publish/consume)
        //   Capability -> Platform (dependency)
        //   External -> System boundary
        //
        // NEVER draw capability -> capability synchronous arrows.
    }

    views {
        systemContext system "L1" {
            include *
            autolayout lr
        }

        container system "L2" {
            include *
            autolayout lr
        }

        // Component views (L3) are added per capability as journeys
        // refine them. Example:
        //
        // component cap001 "L3-CAP001" {
        //     include *
        //     autolayout lr
        // }

        styles {
            element "Capability" {
                background "#1168bd"
                color "#ffffff"
            }
            element "Platform" {
                background "#999999"
                color "#ffffff"
            }
            element "External System" {
                background "#cccccc"
            }
        }
    }
}
