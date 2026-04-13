# CLAUDE.md — {project-name}-realtime

This file covers coding conventions for this real-time service. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

---

## Stack

- **Node.js 22**, TypeScript (strict), ws, ioredis, Pino
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Type checking:** tsc --noEmit
- **Testing:** Jest + ts-jest

---

## Project structure

```
src/
├── index.ts              # Entry point: init OTel, start HTTP server
│                         #   with WebSocket upgrade, start Redis subscriber,
│                         #   register shutdown handlers
├── server.ts             # WebSocket server: connection handling, auth on
│                         #   upgrade, route to room manager
├── health.ts             # HTTP health endpoint at /healthz
├── rooms/
│   ├── manager.ts        # Room management: join, leave, broadcast, list members
│   └── presence.ts       # Presence tracking: who's in which room, last seen,
│                         #   broadcast presence changes
├── handlers/
│   └── message.ts        # Incoming message handler: validate schema, route
│                         #   to appropriate room action
└── lib/
    ├── otel.ts           # OpenTelemetry SDK init
    ├── redis.ts          # ioredis singleton + pub/sub subscriber for
    │                     #   cross-instance broadcasting
    ├── logger.ts         # Pino logger + createConnectionLogger(connId, userId?)
    └── auth.ts           # JWT validation for WebSocket upgrade requests
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode — no `any`, no implicit returns
- Never use `console.log` — use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from environment variables
- Never commit `.env` — use `.env.example` as the reference

### WebSocket with SSE fallback
- Primary transport is WebSocket via the `ws` library
- For environments that block WebSocket (corporate proxies, some CDNs),
  fall back to Server-Sent Events (SSE) on `GET /events`
- SSE is read-only (server to client) — clients send actions via REST
  when using SSE fallback
- Both transports deliver the same event format

### Room/channel pattern
- Clients subscribe to rooms by sending a `join` message with the room ID
- Messages are broadcast to all members of a room
- A client can be in multiple rooms simultaneously
- Room state is local to the instance — Redis pub/sub distributes events
  across instances so all room members receive broadcasts regardless of
  which instance they connect to

### Presence
- Track connected users per room with last-seen timestamps
- Broadcast `presence:join` and `presence:leave` events to room members
- Presence state stored in Redis (sorted sets) for cross-instance visibility
- Stale presence entries cleaned up on heartbeat timeout

### Authentication
- Validate JWT once on the WebSocket upgrade request (via query param or
  `Authorization` header) — do NOT re-authenticate per message
- Reject upgrade with 401 if token is invalid or expired
- Attach decoded user context to the connection object for use in handlers
- Token source: starter-gateway issues JWTs; this service validates them

### Redis pub/sub for horizontal scaling
- Each instance subscribes to Redis channels matching active rooms
- When a message is broadcast to a room, it is published to Redis so all
  instances deliver it to their local connections
- Use a separate ioredis client for pub/sub (pub/sub clients cannot run
  other commands)

### Heartbeat / ping-pong
- Server sends WebSocket ping frames at a configurable interval
- If no pong is received within the timeout, consider the connection dead
  and clean up (leave rooms, update presence)
- Heartbeat interval and timeout are configurable via environment variables

### Message schema validation
- All incoming client messages must be validated before processing
- Define expected schemas for each message type (join, leave, broadcast)
- Reject malformed messages with an error frame — never trust client input
- Keep the schema simple: `{ type: string, payload: object }`

### Backpressure
- If a client's send buffer exceeds a threshold, drop subsequent messages
  for that client rather than buffering indefinitely
- Log dropped messages at warn level
- The client is responsible for reconnecting and catching up if it falls behind

### No business logic
- This service is a routing layer — it receives events from Redis pub/sub
  and forwards them to connected clients
- Business logic belongs in starter-worker or starter-api
- This service should not query databases or call external APIs
  (other than Redis)

### Logging
- Use structured logging with Pino
- Every log line for a connection must include `connId` and `userId`
  (when available) — use `createConnectionLogger()` for this
- Log at these levels:
  - `info` — connection opened, connection closed, room joined/left
  - `warn` — message dropped (backpressure), heartbeat timeout, malformed message
  - `error` — auth failure, Redis pub/sub disconnect, unexpected error

### Graceful shutdown
- On SIGTERM/SIGINT: stop accepting new connections, send close frames to
  all connected clients, unsubscribe from Redis pub/sub, close Redis
  connections, then exit
- Shutdown timeout: if connections do not close within N seconds, force
  exit with a non-zero code
- The health endpoint must return unhealthy during shutdown

### Health endpoint
- Serve `/healthz` on the same HTTP server used for WebSocket upgrade
- Check: Redis pub/sub connectivity, connection count, room count
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability
- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Add span attributes: `ws.connection_id`, `ws.room`, `ws.user_id`
- Track metrics: active connections, rooms, messages/sec, dropped messages

### Testing
- Test message handler routing and schema validation
- Test room manager join/leave/broadcast logic
- Mock WebSocket connections and Redis pub/sub in tests
- Tests must not depend on each other or on execution order

---

## Common commands

```bash
npm install                    # Install dependencies
npm run dev                    # Start with tsx watch (hot reload)
npm run build                  # Compile TypeScript
npm start                      # Run compiled output
npm test                       # Run tests
npm run lint                   # Lint
npm run format                 # Format
npx tsc --noEmit               # Type check
```

---

## Before writing code

- Read existing files in the area being modified before generating any code
- If modifying an existing module, read the current implementation first
- Verify you are in the correct repo: `pwd && git remote get-url origin`

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npx tsc --noEmit && npm run lint && npm test
```
