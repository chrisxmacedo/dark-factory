# development-team

Build pipeline of the delivery team (`starter-delivery-team/`). The
**Team Lead** polls Jira and orchestrates specialist teams through
feature → ci → RC → main. Deliverables arrive in Backlog from the
**Programme Lead** (`../PIPELINE.md`), who sources them from the
sibling `capability-team/`.

Copy the enclosing `starter-delivery-team/` directory into a new project
workspace — it provides the Team Lead + 8 specialist agent teams +
Docker environments + CI/CD + the Programme Lead + the Capability
Lead.

## Contents

- **PIPELINE.md** — Team Lead orchestration script (rename to `.claude/CLAUDE.md` in the project)
- **ARCHITECTURE.md** — Technical architecture specification template
- **SOLUTION-ARCHITECT-INPUTS.md** — Inputs checklist for the solution architect
- **.claude/agents/** — 8 specialist team definitions (refinement, development, local-test, integration-test, e2e-impact, regression, release, diagnostics)
- **infra/** — Docker Compose environments, `envctl` (Docker management), `envwatch` (auto-rebuild), `jiractl` (Jira API without tokens), `pipelinectl` (mechanical pipeline ops without Claude), `dashboard.py` (web UI)
- **tests/** — Test infrastructure: LLM stub server (Anthropic + OpenAI compatible), fixture seeder, and directory structure for integration/e2e/smoke test suites
- **.github/workflows/** — GitHub Actions CI (feature/ci branches) and release (release-rc branches) workflow skeletons

## For agents

- Replace all `{PLACEHOLDER}` values with project-specific configuration before use.
- The infra/ Docker Compose files are stack-agnostic skeletons — add your services to base.yml and override per environment.
- The LLM stub server in tests/mocks/llm_stub/ supports both Anthropic and OpenAI API formats.
- Agent files include Docker environment sections — customize ports and commands per project.
- See `../../development-pipeline-config/development-pipeline-configuration-guide.md` (or open `../../development-pipeline-config/index.html`) for the full setup walkthrough.
