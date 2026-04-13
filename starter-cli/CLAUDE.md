# CLAUDE.md -- {PROJECT_NAME}-cli

This file covers coding conventions for this CLI tool. For project-wide
architecture, service providers, and secrets, see `../CLAUDE.md` and
`../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack (TypeScript variant)

- **Node.js 22**, TypeScript (strict)
- **CLI framework:** Commander.js
- **Validation:** Zod (for input/config parsing)
- **Config:** dotenv + cosmiconfig (~/.{tool}rc, .{tool}rc.json)
- **Logging:** stderr-only (never pollute stdout)
- **Output:** JSON (--json flag) or human-readable table/text
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Testing:** Jest + ts-jest
- **Distribution:** npm publish (bin field in package.json)

## Stack (Go variant)

- **Go 1.22+**
- **CLI framework:** cobra + viper (config)
- **Validation:** go-playground/validator or custom
- **Logging:** zerolog (stderr)
- **Output:** encoding/json or tablewriter
- **Testing:** go test + testify
- **Distribution:** goreleaser (cross-platform binaries, Homebrew tap)

---

## Project structure (planned)

### TypeScript

```
src/
├── index.ts              # Entry point: parse args, route to command
├── commands/             # One file per command (verb)
│   ├── init.ts           # Example: `tool init`
│   ├── sync.ts           # Example: `tool sync`
│   └── export.ts         # Example: `tool export`
├── lib/
│   ├── config.ts         # Config loading (env, RC file, CLI flags)
│   ├── output.ts         # Formatters: JSON, table, plain text
│   ├── logger.ts         # Stderr logger with --verbose support
│   ├── http.ts           # HTTP client with auth, retry, timeout
│   └── validation.ts     # Zod schemas for input validation
├── types/
│   └── index.ts          # Shared type definitions
└── __tests__/
    ├── commands/          # Command-level integration tests
    └── lib/               # Unit tests for utilities
```

### Go

```
cmd/
├── root.go               # Root cobra command, global flags
├── init.go               # `tool init` subcommand
├── sync.go               # `tool sync` subcommand
└── export.go             # `tool export` subcommand
internal/
├── config/               # Viper config loading
├── output/               # JSON / table formatters
├── client/               # HTTP client with auth and retry
└── validation/           # Input validation
pkg/                      # Public library code (if any)
main.go                   # Entry point
```

---

## Conventions

### General
- All functions must have full type annotations (TypeScript) or doc comments (Go)
- TypeScript strict mode -- no `any`, no implicit returns
- Never use `console.log` -- all user-facing output goes through `src/lib/output.ts`
- Never hardcode secrets or URLs -- read from environment or config file
- Never commit `.env` -- use `.env.example` as the reference

### Output discipline
- **stdout** is exclusively for command output (data the user or a pipe consumes)
- **stderr** is for logs, progress, warnings, errors
- Every command must support `--json` to emit machine-readable JSON to stdout
- Human-readable output is the default (tables, formatted text)
- Exit codes: 0 = success, 1 = runtime error, 2 = usage/validation error

### Command design
- One file per command in `src/commands/` (TypeScript) or `cmd/` (Go)
- Every command supports `--verbose` (detailed stderr logging) and `--dry-run`
  (show what would happen without side effects)
- Commands are composable -- avoid hidden side effects
- Use subcommands for related operations: `tool users list`, `tool users create`
- Include `--help` text with usage examples for every command

### Config loading priority (highest to lowest)
1. CLI flags (`--api-url`)
2. Environment variables (`TOOL_API_URL`)
3. Project config file (`.{tool}rc.json` in current directory)
4. User config file (`~/.{tool}rc.json`)
5. Defaults

### HTTP client
- All outbound HTTP calls go through the shared client with retry and timeout
- Support API key and OAuth token authentication
- Respect `--dry-run` -- log the request but do not send it
- Include `User-Agent: {tool}/{version}` header

### Error handling
- Never print a stack trace to the user unless `--verbose` is set
- User-facing errors must be clear and actionable ("File not found: config.json.
  Run `tool init` to create one.")
- Wrap all errors with context (TypeScript: custom error classes, Go: fmt.Errorf wrapping)

### Security
- Never log or display secrets, tokens, or passwords
- Mask sensitive values in `--verbose` output
- Support reading secrets from stdin (`echo $TOKEN | tool auth --token -`)
- Config files containing secrets must warn if world-readable

### Testing
- Every command needs at least one happy-path test and one error-path test
- Mock HTTP calls -- never hit real APIs in tests
- Test `--json` output parsing (valid JSON, correct schema)
- Test exit codes for success and failure scenarios
- Tests must not depend on each other or on execution order

---

## Common commands (planned)

### TypeScript

```bash
npm install                    # Install dependencies
npm run dev                    # Run with tsx (hot reload)
npm run build                  # Compile TypeScript
npm start -- <command>         # Run compiled CLI
npm test                       # Run tests
npm run lint                   # Lint
npm run format                 # Format
npx tsc --noEmit               # Type check
npm link                       # Link for local development
```

### Go

```bash
go build -o tool .             # Build binary
go run . <command>             # Run directly
go test ./...                  # Run all tests
golangci-lint run              # Lint
goreleaser release --snapshot  # Test release build
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (build, test, lint, type check)
- **TypeScript:** `npm publish` on tagged release (semver)
- **Go:** goreleaser on tagged release (binaries + Homebrew tap + Docker image)
- Version is sourced from `package.json` (TS) or `ldflags` (Go), never hardcoded

---

## Before opening a PR

### TypeScript

```bash
npx tsc --noEmit && npm run lint && npm test
```

### Go

```bash
golangci-lint run && go test ./...
```
