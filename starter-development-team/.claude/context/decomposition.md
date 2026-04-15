# Deliverable decomposition rules

Read by: Team Lead when creating Deliverables, Solution Architect during planning

## Journey-first, not component-first

Decompose by **user journey** first, technical capability second. The first
question for every feature Initiative is: "what page does the user see?"

**Wrong** (component-first):
- Build the canvas renderer
- Implement thread linking
- Add group management
- Result: isolated components and API routes, no page to put them on

**Right** (journey-first):
- App Shell — layout, navigation, auth redirect (ALWAYS FIRST)
- User can see inbox and select a thread → tree view renders
- User can link threads → visual connectors appear
- User can manage groups → sidebar shows groups
- Result: every Deliverable adds visible functionality to the app

## App Shell must be the first feature Deliverable

After the Infrastructure Setup Initiative, the **first Deliverable** in the
first feature Initiative MUST be the **App Shell**:

- Authenticated layout (redirect unauthenticated users to sign-in)
- Sidebar navigation (core sections of the app)
- Main content area where feature components will be composed
- Wire in the first feature component so the app is immediately usable
- Responsive (mobile sidebar collapses)

Without the app shell, every feature Deliverable produces code that is
invisible to users. The pipeline passes, tests pass, but nobody can see
what was built.

## The component-first trap

Agent teams faithfully build what is specified. If specifications describe
isolated capabilities ("build the renderer", "implement linking"), the teams
will build exactly that — with no page to compose them.

The solution is not better agents — it's better Deliverable decomposition.
Every Deliverable should answer: "what can the user do after this is done
that they couldn't do before?"

## Deliverable ordering rules

1. Infrastructure Setup (pipeline, Docker, CI/CD)
2. App Shell (layout, navigation, auth, first page)
3. Core data flow (the primary user journey end-to-end)
4. Feature Deliverables (each adds to the shell)
5. Polish Deliverables (performance, analytics, edge cases)
