# starter-regulations

Reference library of regulations **grouped by sector** (finance,
healthcare, cybersecurity, etc.). Each regulation lists the countries
required to apply it. Consumed by the capability team's Discovery Team
during Phase A step 1 (market research) and step 3 (governance
mapping).

## Files

| File | Sector / theme |
|------|----------------|
| `finance.json` | Banking prudential, securities conduct, corporate governance, market infrastructure |
| `financial-crime.json` | AML, CFT, sanctions — spans finance, real-estate, legal, gambling, crypto |
| `payments-and-open-finance.json` | Payment services, instant payments, open banking / open finance |
| `crypto-assets.json` | Virtual asset service providers, stablecoins |
| `data-protection.json` | Privacy and personal data laws |
| `cybersecurity-and-resilience.json` | Cybersecurity, operational resilience, critical infrastructure |
| `health-and-clinical-trials.json` | Clinical trials, health data, pharma, genetic information |
| `ai-governance.json` | AI-specific regulation |

## Schema

Each file is a JSON object with:

- `sector` — identifier for the theme
- `description` — what this sector covers
- `regulatory_bodies` — supervising authorities across countries
- `regulations` — list of regulations

Each regulation entry has:

| Field | Meaning |
|-------|---------|
| `id` | Global identifier, format `{SECTOR}-{SHORTNAME}` |
| `name` | Full legal name |
| `abbreviation` | Common short name (e.g. GDPR, FSMA) |
| `applicable_countries` | Countries that must apply this regulation. ISO-style units: `US`, `UK`, `EU`, `CA`, `AU`, `SG`, `CH`, `AE`, `BR`. For free-zone specifics: `AE-DIFC`, `AE-ADGM`. `US-CA` for California-only. |
| `extra_territorial` | `true` if the regulation reaches beyond its listed countries (e.g. GDPR, OFAC) |
| `category` | Thematic sub-category within the sector |
| `issuing_body` | Who enacted it (legislature or supranational body) |
| `enforcing_bodies` | IDs referencing the `regulatory_bodies` list |
| `sector_applicability` | Which sub-sectors are in scope (e.g. `banking`, `insurance`) |
| `summary` | One-paragraph description |
| `key_requirements` | Bullet list of what an organisation must do |
| `effective_from` | ISO date |
| `reference_url` | Canonical source |

## Country codes used

| Code | Meaning |
|------|---------|
| `UK` | United Kingdom |
| `EU` | European Union (all member states) |
| `US` | United States (federal) |
| `US-CA` | US — California only |
| `US-NY` | US — New York only |
| `CA` | Canada |
| `CA-QC` | Canada — Quebec only |
| `AU` | Australia |
| `SG` | Singapore |
| `CH` | Switzerland |
| `AE` | United Arab Emirates (mainland / federal) |
| `AE-DIFC` | UAE — DIFC free zone |
| `AE-ADGM` | UAE — ADGM free zone |
| `BR` | Brazil |
| `GLOBAL` | No single issuing jurisdiction; adopted widely (e.g. FATF, Basel, ICH) |

## How the capability team uses these

During Phase A step 1 (market research), the Discovery Team cross-refs
the capability under design with these sector files to find regulations
applicable to the organisation's target countries.

During Phase A step 3 (governance mapping), each `governance.rules[]`
entry in `artefacts/foundation/governance/*.json` must reference the
regulation's `id` in `source.reference`.

## Accuracy

Starter templates. Regulations are amended; dates and URLs change.
Verify against each regulator's site before relying on any entry.
Agents MUST flag when `last_reviewed` is older than 12 months.

## Extending

- **New regulation** — append to the relevant sector file. Choose `id`
  prefix matching the filename.
- **New sector** — create `{sector}.json` following the same schema
  and add to the table above.
- **New country** — add to the country codes table; update
  `applicable_countries` on affected regulations.

## Related

- `../starter-standards/` — non-regulatory standards (accessibility, ISO)
- `../starter-delivery-team/capability-team/` — the pipeline that
  consumes these files
