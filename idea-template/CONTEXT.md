# idea-template/

Product & Architecture Blueprint template. Merges product vision with
technical architecture using a consistent framework.

## Framework hierarchy

```
Category (domain grouping)
  └─► Capability (stable business ability, tech-agnostic)
        └─► Journey (persona goal across touchpoints)
              └─► Step (single touchpoint, uses a capability)
        └─► Technical Service (deployable boundary, team-owned)
              └─► Container (C2 deployable)
                    └─► Component (C3 internal)
  └─► Initiative (timeboxed change effort)
        └─► Deliverable (pipeline unit)
              └─► Task (small testable unit)
```

## Key relationships

- Journey steps USE Capabilities
- Capabilities ARE REALISED BY Technical Services
- Technical Services ARE IMPLEMENTED AS Containers (C2)
- Initiatives DELIVER increments to Journeys/Capabilities VIA Technical Services

## How it feeds the pipeline

1. Product owner fills Problem + Vision + Journeys
2. Solution Architect fills Capabilities + Technical Services + C4 Model
3. `/create-project` creates Initiatives + Deliverables from this template
4. Refinement Team reads this template + REPO_MAP.md to create Tasks
5. Development Team implements Tasks

## Files

- **TEMPLATE.md** — the full template with all 12 sections (Markdown)
- **blueprint/** — the same framework as a single-file, 10-tab interactive HTML
  blueprint (`template-blueprint.html`, tokens in `TOKENS.md`), plus the
  capability-driven design methodology page
- **design-system/** — the stylesheet `/idea` builds its HTML pages on
  (`styles.css`) and a complete worked example (`example-vr-pipeline/`) to copy
  structure and CSS classes from. Never edit the example; copy it.

Ideas themselves (one folder per product) live outside the toolkit, in
`$IDEAS_DIR` from `~/.config/pipeline-toolkit/config.env`.
