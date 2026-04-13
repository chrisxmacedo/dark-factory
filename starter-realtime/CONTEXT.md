# starter-realtime

Starter template for WebSocket/SSE real-time update services.

## What this is for

Services that manage persistent connections with clients to deliver
real-time updates:
- Accept WebSocket connections (with SSE fallback)
- Authenticate connections via JWT on upgrade
- Manage room/channel subscriptions — clients join rooms, receive broadcasts
- Track presence — who is connected to each room, join/leave events
- Bridge between an event bus (Redis pub/sub) and connected clients
- Horizontally scalable — multiple instances share events via Redis pub/sub

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| HTTP REST endpoints | starter-api |
| Background job processing | starter-worker |
| Real-time push to connected clients | **starter-realtime** |
| API gateway / auth proxy | starter-gateway |
| Push notifications (email, SMS, mobile) | starter-notification |

## Key characteristics

- **Persistent connections** — WebSocket with SSE fallback for restricted environments
- **Room/channel pattern** — clients subscribe to rooms, messages broadcast to all members
- **Presence tracking** — who is in each room, join/leave event broadcasts
- **Auth on connect** — JWT validated once at connection upgrade, not per message
- **Redis pub/sub** — cross-instance event broadcasting for horizontal scaling
- **Heartbeat** — ping/pong to detect dead connections
- **Backpressure** — drop messages if a client cannot keep up, never buffer indefinitely
- **No business logic** — receives events from pub/sub, routes to connected clients
- **Graceful shutdown** — drain connections, close cleanly

## Market applications

### Banking / Trading
Live price feeds, portfolio value updates, transaction notifications,
market alerts, order execution status.

### Collaboration
Live document editing, cursor presence, real-time comments, co-editing
indicators, shared whiteboard state.

### Gaming
Game state synchronization, matchmaking status updates, leaderboard
changes, in-game chat, lobby presence.

### IoT
Device telemetry streaming, sensor dashboards, threshold alert feeds,
device status changes, fleet tracking.

### Support
Live chat between agents and customers, agent availability indicators,
typing indicators, queue position updates.

### SaaS
Dashboard live updates, deployment status, build/CI progress, usage
metric streaming, collaborative admin panels.

## Tech stack

Node.js 22, TypeScript (strict), ws, ioredis, Pino, OpenTelemetry, Jest
