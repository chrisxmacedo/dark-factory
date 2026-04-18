# Security best practices

Read by: all teams, all starters

## Where the security requirements come from

The capability team specifies the project's security model in
`capability-team/artefacts/architecture/security-model.json` (zero-trust
policy, mTLS, data classifications, network zones, controls). That spec
is **derived** from regulations and standards — for context and for
resolving ambiguity, the underlying libraries are at:

- `../../../../starter-regulations/cybersecurity-and-resilience.json`
  (DORA, NIS 2, CPS 234, NYDFS Part 500, etc.)
- `../../../../starter-regulations/data-protection.json` (GDPR, HIPAA,
  CCPA, LGPD, etc.)
- `../../../../starter-standards/information-security.json` (ISO
  27001/27017/27018, NIST CSF, NIST 800-53, NIST 800-63, CIS Controls)
- `../../../../starter-standards/service-organization-controls.json`
  (SOC 1/2/3)

**Read the spec first.** Only consult the libraries when the spec is
ambiguous, when a regulation is cited by `id` and you need its full
requirements, or when the Diagnostics Team is tracing a control back
to its origin (see `SPEC DEFECT RAISED` in
`../defect-handling.md`).

## Input validation

- Validate at EVERY system boundary: API endpoints, queue messages, webhook payloads, file uploads
- Schema validation: Zod (TypeScript), Pydantic (Python) on every POST/PATCH/DELETE handler
- Route parameter validation: verify IDs are valid format (CUID, UUID) before querying database
- Never pass unvalidated user input to a database query, file path, or external API call

## SQL injection

- Always use parameterised queries or ORM (Prisma, SQLAlchemy)
- Never build queries with string concatenation or template literals
- Never use raw SQL unless explicitly required — and always parameterise

## Authentication

- Validate JWT/session on every request via middleware — not per-route checks
- Token storage: Keychain (iOS), EncryptedSharedPreferences (Android), httpOnly cookies (web)
- Session expiry: enforce server-side, don't trust client-side expiry
- Failed auth: return 401 with generic message — never reveal whether user exists

## Authorisation

- Check resource ownership on every request: user can only access their own data
- Row-level security or explicit `WHERE userId = ?` on every query
- Admin endpoints: separate middleware, separate rate limits, audit logged

## CORS

- Configure per environment — never allow `*` in production
- Explicitly list allowed origins, methods, and headers
- Credentials: only allow with specific origins, never with wildcard

## Rate limiting

- Enforce on every public endpoint
- Per-user (authenticated) or per-IP (unauthenticated)
- Return 429 with Retry-After header
- Defined-but-unused rate limiting is a bug — if the module exists, wire it in

## Secrets management

- Never in code, never in git, never in Docker build layers
- Use environment variables or secret managers (AWS Secrets Manager, Vault)
- Shared secrets between services: document coupling in .secrets.md
- Rotate when: team member leaves, secret exposed, quarterly schedule
- Encryption key derivation: cache at module load, don't re-derive per call

## Encryption

- At rest: AES-256-GCM for sensitive fields (tokens, PII)
- In transit: HTTPS only in production, redirect HTTP → HTTPS
- Key derivation: SHA-256 hash of secret, cached once at startup

## Error responses

- Never leak stack traces, internal paths, database structure, or query details
- Return generic error shapes: `{ error: { code: "not_found", message: "Resource not found" } }`
- Log the full error server-side with correlation ID for debugging

## File handling

- Validate file type (MIME + extension), enforce size limits
- S3 storage keys: validate userId/emailId don't contain `/` or `..` (path traversal)
- Signed URLs for secure download — time-limited (15 min default)

## Dependencies

- Run `npm audit` / `pip audit` on every CI run
- Update vulnerable packages within 48 hours of advisory
- Pin versions in lock files — review changelogs before major upgrades

NEVER:
- Use eval(), dynamic require(), Function constructor, or remote code execution
- Store secrets in .env files that are committed to git
- Trust client-side validation as the only validation
- Return detailed error messages to unauthenticated users
- Log or return full database error messages to clients
