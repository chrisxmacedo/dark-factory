# Finance drop

Save the month's actuals as `actuals.csv` in this folder. Columns:

```
category,item,amount,committed_on,term_months
software,Example tracker,1200,2026-10-01,1
cloud,Example platform,8000,2026-10-01,1
consultant,Example workshop,26000,2026-10-01,4
headcount,Open role,90000,2026-10-01,12
```

`category` is `software`, `cloud`, `consultant`, `workshop`, `headcount`, or `other`. Amounts are numbers in `SPEND_CURRENCY`, with no symbol. `term_months` is for consultants. Headcount rows are always flagged for a human.
