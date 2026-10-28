# Initiatives

One folder per initiative the CTO has assigned, with `meta.json`:

```json
{
  "id": "example-cutover",
  "title": "Example platform cutover",
  "stage": "kickoff",
  "next_milestone": "2026-11-03",
  "close_by": ""
}
```

`stage` is `kickoff`, `plan`, or `close`. The weekday job writes a brief when stage is `kickoff` and no brief exists, a plan when `next_milestone` is today, and a closure when `close_by` is today.
