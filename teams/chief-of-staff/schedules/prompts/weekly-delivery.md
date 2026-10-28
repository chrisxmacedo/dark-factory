Produce this week's delivery status for the CTO and tech leadership.

The metric files are already on disk. Read them and do not recompute them:

- outputs/raw/delivery.json
- outputs/raw/dora.json
- outputs/raw/cycle-time.json

Write the report to outputs/weekly/YYYY-MM-DD-delivery-status.md using today's office date. One page of narrative, then the figures with the definitions that are already in the JSON. Name risks, dependencies, and decisions needed. Where a figure is null, say it is not available and why. Do not invent a number.

You may read pull requests, workflow runs, and tickets through the configured MCP servers when a title in the JSON needs a sentence of context. Do not change code, review or merge a pull request, transition a ticket, or change priority. Decisions that are not already in config/positions.md go to drafts/for-cto/ as a draft, not as a decision.
