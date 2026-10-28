# Teams

A team is a rulebook plus specialists. It can be installed without the other teams.

| Team | Template | Enable it |
|---|---|---|
| Development (design and build) | `starter-delivery-team/` | Copy that directory, or let `/create-project` install the build pipeline. See `teams/development/README.md`. |
| Technical chief of staff | `teams/chief-of-staff/` | `./harness/export-chief-of-staff.sh <empty-dir>`. This does not copy the delivery team. |

Both use Claude Code. They do not share a backlog.

The chief of staff may read the engineering organisation's pull requests, CI, tickets, and delivery metrics, and it may raise issues and chase deadlines. It reads those through GitHub, Jira, and Linear (scripts for the counts, MCP for a ticket or a pull request that needs a sentence of context). It must not change product code, merge or review pull requests, transition engineering tickets, or reprioritise the delivery team's work. It does not need the delivery template to be present.
