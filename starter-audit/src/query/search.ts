import http from "node:http";
import { URL } from "node:url";
import { prisma } from "../lib/prisma";
import { logger } from "../lib/logger";

const QUERY_PORT = parseInt(process.env.QUERY_PORT ?? "3000", 10);
const DEFAULT_PAGE_SIZE = parseInt(
  process.env.QUERY_DEFAULT_PAGE_SIZE ?? "100",
  10,
);
const MAX_PAGE_SIZE = parseInt(
  process.env.QUERY_MAX_PAGE_SIZE ?? "1000",
  10,
);

export interface SearchFilters {
  actor?: string;
  action?: string;
  resource?: string;
  outcome?: string;
  from?: Date;
  to?: Date;
  cursor?: string;
  pageSize?: number;
}

/**
 * Parse query string parameters into typed search filters.
 */
export function parseFilters(params: URLSearchParams): SearchFilters {
  const pageSize = Math.min(
    parseInt(params.get("pageSize") ?? String(DEFAULT_PAGE_SIZE), 10),
    MAX_PAGE_SIZE,
  );

  return {
    actor: params.get("actor") ?? undefined,
    action: params.get("action") ?? undefined,
    resource: params.get("resource") ?? undefined,
    outcome: params.get("outcome") ?? undefined,
    from: params.get("from") ? new Date(params.get("from")!) : undefined,
    to: params.get("to") ? new Date(params.get("to")!) : undefined,
    cursor: params.get("cursor") ?? undefined,
    pageSize,
  };
}

/**
 * Execute a filtered, cursor-paginated query against the audit event table.
 *
 * TODO: Replace raw SQL with Prisma model queries once the schema is defined.
 */
export async function searchEvents(filters: SearchFilters): Promise<{
  events: Array<Record<string, unknown>>;
  nextCursor: string | null;
}> {
  const conditions: string[] = [];
  const values: unknown[] = [];
  let paramIndex = 1;

  if (filters.actor) {
    conditions.push(`actor = $${paramIndex++}`);
    values.push(filters.actor);
  }
  if (filters.action) {
    conditions.push(`action = $${paramIndex++}`);
    values.push(filters.action);
  }
  if (filters.resource) {
    conditions.push(`resource = $${paramIndex++}`);
    values.push(filters.resource);
  }
  if (filters.outcome) {
    conditions.push(`outcome = $${paramIndex++}`);
    values.push(filters.outcome);
  }
  if (filters.from) {
    conditions.push(`timestamp >= $${paramIndex++}`);
    values.push(filters.from);
  }
  if (filters.to) {
    conditions.push(`timestamp <= $${paramIndex++}`);
    values.push(filters.to);
  }
  if (filters.cursor) {
    conditions.push(`id < $${paramIndex++}`);
    values.push(filters.cursor);
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
  const limit = filters.pageSize ?? DEFAULT_PAGE_SIZE;

  // TODO: Replace with Prisma model query once schema is defined
  const events = await prisma.$queryRawUnsafe<Array<Record<string, unknown>>>(
    `SELECT * FROM {AUDIT_EVENTS_TABLE} ${where} ORDER BY timestamp DESC, id DESC LIMIT ${limit + 1}`,
    ...values,
  );

  const hasMore = events.length > limit;
  if (hasMore) {
    events.pop();
  }

  const nextCursor = hasMore && events.length > 0
    ? String(events[events.length - 1].id)
    : null;

  return { events, nextCursor };
}

/**
 * Start the query API HTTP server.
 */
export function startQueryServer(): http.Server {
  const server = http.createServer(async (req, res) => {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end();
      return;
    }

    const url = new URL(req.url ?? "/", `http://localhost:${QUERY_PORT}`);

    if (url.pathname === "/audit/search") {
      try {
        const filters = parseFilters(url.searchParams);
        const result = await searchEvents(filters);

        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(result));
      } catch (err) {
        logger.error({ err }, "Search query failed");
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Internal server error" }));
      }
      return;
    }

    res.writeHead(404);
    res.end();
  });

  server.listen(QUERY_PORT, () => {
    logger.info({ port: QUERY_PORT }, "Query API server listening");
  });

  return server;
}
