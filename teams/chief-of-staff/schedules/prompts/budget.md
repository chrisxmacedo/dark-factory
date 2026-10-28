Write the monthly tech budget tracker. Today is working day 5.

Read outputs/raw/budget-flags.json. If status is no_actuals, write outputs/budget/YYYY-MM.md that says the tracker is blocked on the finance drop, and stop. Do not invent amounts.

Otherwise write outputs/budget/YYYY-MM.md with the caps, the annual total, and each row. Rows marked within_cap can be reported as inside the configured caps. Rows marked needs_human, and an annual_decision of needs_human, are flags for the CTO. Draft the request in drafts/for-cto/ and do not approve it. Headcount is never a decision this role makes.
