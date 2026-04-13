import type http from "node:http";
import { searchEvents, parseFilters } from "./search";
import { logger } from "../lib/logger";
import type { URL } from "node:url";

const EXPORT_FIELDS = [
  "id",
  "timestamp",
  "actor",
  "action",
  "resource",
  "context",
  "outcome",
  "metadata",
  "previousHash",
  "hash",
] as const;

/**
 * Handle an export request. Streams filtered audit events as CSV or JSON.
 *
 * GET /audit/export?format=csv&actor=...&from=...&to=...
 * GET /audit/export?format=json&actor=...&from=...&to=...
 */
export async function handleExport(
  url: URL,
  res: http.ServerResponse,
): Promise<void> {
  const format = url.searchParams.get("format") ?? "json";

  if (format !== "csv" && format !== "json") {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "format must be 'csv' or 'json'" }));
    return;
  }

  const filters = parseFilters(url.searchParams);
  // Override page size for export — stream in batches
  filters.pageSize = 500;

  logger.info({ format, filters }, "Starting audit export");

  try {
    if (format === "csv") {
      await exportCsv(filters, res);
    } else {
      await exportJson(filters, res);
    }
  } catch (err) {
    logger.error({ err }, "Export failed");
    // If headers not yet sent, send error response
    if (!res.headersSent) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Export failed" }));
    } else {
      res.end();
    }
  }
}

/**
 * Stream filtered events as CSV. Writes header row followed by data rows.
 */
async function exportCsv(
  filters: ReturnType<typeof parseFilters>,
  res: http.ServerResponse,
): Promise<void> {
  res.writeHead(200, {
    "Content-Type": "text/csv",
    "Content-Disposition": "attachment; filename=audit-export.csv",
  });

  // Header row
  res.write(EXPORT_FIELDS.join(",") + "\n");

  let cursor: string | undefined = filters.cursor;

  while (true) {
    const { events, nextCursor } = await searchEvents({ ...filters, cursor });

    for (const event of events) {
      const row = EXPORT_FIELDS.map((field) => {
        const value = event[field];
        if (value === null || value === undefined) return "";
        const str = typeof value === "object" ? JSON.stringify(value) : String(value);
        // Escape CSV: wrap in quotes if contains comma, newline, or quote
        if (str.includes(",") || str.includes("\n") || str.includes('"')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      });
      res.write(row.join(",") + "\n");
    }

    if (!nextCursor) break;
    cursor = nextCursor;
  }

  res.end();
  logger.info("CSV export complete");
}

/**
 * Stream filtered events as newline-delimited JSON (NDJSON).
 * Each line is a complete JSON object for memory-efficient processing.
 */
async function exportJson(
  filters: ReturnType<typeof parseFilters>,
  res: http.ServerResponse,
): Promise<void> {
  res.writeHead(200, {
    "Content-Type": "application/x-ndjson",
    "Content-Disposition": "attachment; filename=audit-export.ndjson",
  });

  let cursor: string | undefined = filters.cursor;

  while (true) {
    const { events, nextCursor } = await searchEvents({ ...filters, cursor });

    for (const event of events) {
      res.write(JSON.stringify(event) + "\n");
    }

    if (!nextCursor) break;
    cursor = nextCursor;
  }

  res.end();
  logger.info("JSON export complete");
}
