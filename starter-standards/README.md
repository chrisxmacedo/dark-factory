# starter-standards

Reference library of **non-regulatory** standards that a project may
choose (or be contractually required) to adhere to. Distinct from
`starter-regulations/` — these are voluntary frameworks published by
standards bodies (ISO, W3C, NIST, AICPA, etc.). Consumed by the
capability team's Discovery Team for quality, accessibility, and
architectural targets.

## Files

| File | Scope |
|------|-------|
| `accessibility.json` | WCAG, ATAG, WAI-ARIA, EN 301 549 |
| `information-security.json` | ISO 27001/27002/27017/27018, NIST CSF 2.0, NIST 800-53, NIST 800-63, CIS Controls, CSA CCM |
| `service-organization-controls.json` | SOC 1 / SOC 2 / SOC 3 (AICPA) |
| `quality-management.json` | ISO 9001, ISO 13485, ISO/IEC 25010 |

## Schema

Each file is a JSON object with:

- `category` — the standards domain (accessibility, security, etc.)
- `issuing_bodies` — list of organisations that publish the standards
- `standards` — list of standards, each with `applicable_countries`,
  `issuing_body`, `scope_applicability`, `key_principles`, and a
  `reference_url`

Standards are mostly global by nature. `applicable_countries: ["GLOBAL"]`
is the default. Where a standard is referenced as mandatory by
regulation in specific markets, that is called out in
`referenced_in_regulation` on the standard itself (see WCAG 2.2 for an
example).

Country code conventions match `../starter-regulations/README.md`.

See the first entry of any file for the full shape.

## Standards vs regulations

| Trait            | Regulation                     | Standard                                |
|------------------|--------------------------------|-----------------------------------------|
| Source           | Legislature / regulator        | Standards body (ISO, W3C, AICPA, NIST)  |
| Compliance       | Mandatory                      | Voluntary (unless contractually/regulatorily referenced) |
| Enforcement      | Fines, sanctions, licence loss | Certification, contract default          |
| Examples         | GDPR, DORA, HIPAA              | WCAG, ISO 27001, SOC 2                   |

Some standards **become** regulation when referenced by law (e.g. WCAG
is mandated for public sector websites in the EU via the Web
Accessibility Directive). In those cases, list the regulation in the
relevant market file and reference the standard here.

## How the capability team uses these

- **Phase A step 3 (governance mapping)** — Discovery Team references
  these when a capability has non-regulatory quality obligations
  (accessibility, ISO certification commitments).
- **Phase B step 5 (security model)** — architects reference
  `information-security.json` when choosing baseline controls.
- **Phase C step 9 (NFRs)** — NFR artefacts may set accessibility
  targets drawn from `accessibility.json`.

## Accuracy

Starter templates. Verify `reference_url` and `last_reviewed` before
using as authoritative.
