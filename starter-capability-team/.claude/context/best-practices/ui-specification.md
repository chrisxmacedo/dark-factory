# UI specification best practices

Read by: Capability Team (Phase D)

## Screen specification rules

Every screen must address **six states**:
1. **Loading** — data is being fetched
2. **Empty** — no data exists yet (first-time user)
3. **Happy path** — normal data, expected behaviour
4. **Partial data** — some API calls succeeded, some failed
5. **Error** — service unavailable
6. **Forbidden** — user lacks entitlement for this screen

A screen spec that only describes the happy path is incomplete.

## Field-level specification

Every field on a screen must reference:
- The data model entity and field it displays
- The projection rule (from participant interaction model) — what does this participant type see?
- The action entitlement — can this participant edit this field?
- The validation rule (from data model) — applied client-side

Do NOT invent fields that don't exist in the data model. If the screen
needs a field that doesn't exist, create a Model feedback ticket.

## Task flow specification

Task flows translate system-level sequence diagrams into user-level
interaction sequences:
- What the user clicks
- What they see in response
- Where they navigate next
- What happens on error

Every journey that passes through a portal must have a task flow.

## Form specification

Forms reference the data model for field types and validation:
- Field grouping and ordering are UX decisions (designer)
- Field types, validation, and constraints come from the data model
- Conditional logic (show/hide fields based on state) must reference
  governance rules or entity state
- Every form must handle: validation errors, server errors, partial
  submission (save draft)

## Portal-first, not screen-first

Design one portal at a time, not one screen at a time:
- Start with the information architecture (step 14)
- Then specify all screens within that portal
- Then task flows across those screens
- Then forms within those screens
- Finally, the design system for the portal

This ensures navigation, layout, and patterns are consistent within
a portal.

## Model feedback loop

When a screen spec reveals a gap in the analytical model:
1. Document the gap precisely: which entity, which field, why it's needed
2. Create a "Model feedback" ticket in the MODEL project
3. Link it to the UXSPEC screen spec
4. Mark the affected screen as "Pending model update"
5. Continue with other screens — do NOT block

The Programme Lead prioritises model feedback in the Phase C backlog.

## Design system

The design system captures reusable patterns across screens:
- Component patterns (tables, forms, status indicators, notifications)
- Layout patterns (page structure, navigation, responsive behaviour)
- Interaction patterns (confirmation dialogs, inline editing, bulk actions)
- Error patterns (how errors are displayed, recovery actions)

Define these once per portal, reference from individual screen specs.

NEVER:
- Specify screens without referencing the data model
- Invent fields that don't exist in the central model
- Skip the six-state requirement for any screen
- Design screens in isolation without the portal's information architecture
- Block on model feedback — create a ticket and continue
