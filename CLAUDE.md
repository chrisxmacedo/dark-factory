# pipeline-toolkit — working on the toolkit itself

This repo holds templates, not products. These instructions apply when
editing the toolkit; the rules that agents follow inside a *project* live in
the templates (`starter-delivery-team/development-team/.claude/context/`), so
every new project inherits them.

## Rules

- **No machine- or client-specific values in the repo.** Paths, Atlassian
  sites, GitHub orgs and preferences come from
  `~/.config/pipeline-toolkit/config.env` (written by `install.sh`). In slash
  commands use `$TOOLKIT_DIR`, `$PROJECTS_DIR`, `$IDEAS_DIR`, `$ATLASSIAN_SITE`,
  `$JIRA_URL`, `$CONFLUENCE_URL`, `$MC_*`; in templates use `{PLACEHOLDER}`s.
  Check before committing:
  `grep -rn "/Users/\|atlassian.net" commands/ starter-*/ | grep -v example`
- **`commands/` is live.** `~/.claude/commands/*.md` are symlinks to these
  files, so an edit here changes the command immediately on this machine.
- **New template placeholder → add it to
  `starter-delivery-team/development-team/infra/verify-placeholders.sh`** and to
  the placeholder tables in `commands/create-project.md`. Never write a shell
  variable as `${NAME}` when `{NAME}` is also a placeholder — replacement
  would mangle it (use `$NAME`).
- **A lesson learned on a live project goes into the template** (agent-rules,
  best-practices, infra scripts), not just that project's notes, so the next
  project gets it.
- **Test script changes in a scratch copy**, never in a live project: copy the
  team folder somewhere temporary, fill placeholders, stub `docker`/`curl`/
  `jiractl` on `PATH` where needed. Capability validators can be checked
  against `~/Projects/products/commercial-bank/artefacts`.
- **Keep the README in step** with any change to how something is installed
  or run.
