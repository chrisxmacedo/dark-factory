# Development team

The build and design pipeline stays at `starter-delivery-team/`.

`/create-project` copies `starter-delivery-team/development-team` into a product repo and renames `PIPELINE.md` to `.claude/CLAUDE.md`. The full design-and-build pipeline is the whole `starter-delivery-team/` directory. Those paths are what existing projects already use, so this folder does not move them.

That template is a Claude Code team: a lead prompt, specialist prompts under `.claude/agents/`, slash commands in `commands/`, and `config/permissions.baseline.json`. Its leads read the specialist files as their prompts. Those files are left as they are.

The chief of staff is a separate team. It may read this team's outputs where they show up in GitHub, Jira, Linear, or CI, and it may raise an issue or chase a deadline. It must not change this team's code, tickets, or order of work, and a chief-of-staff install does not include this template.
