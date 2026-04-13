/**
 * Workflow API routes — trigger, status, and signal endpoints.
 *
 * - POST /workflows         — trigger a new workflow instance
 * - GET  /workflows/:id     — get workflow status
 * - POST /workflows/:id/signal — send a signal (approval, rejection, etc.)
 */

import http from "node:http";
import { logger } from "../lib/logger";
import { startWorkflow, signalWorkflow, getWorkflowDefinition } from "../engine/executor";
import { prisma } from "../lib/prisma";

const API_PORT = parseInt(process.env.API_PORT ?? "3000", 10);

// ---------------------------------------------------------------------------
// Request helpers
// ---------------------------------------------------------------------------

function parseBody(req: http.IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString()) as Record<string, unknown>;
        resolve(body);
      } catch {
        reject(new Error("Invalid JSON body"));
      }
    });
    req.on("error", reject);
  });
}

function sendJson(
  res: http.ServerResponse,
  statusCode: number,
  data: unknown,
): void {
  res.writeHead(statusCode, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

function extractPathParam(url: string, pattern: RegExp): string | null {
  const match = url.match(pattern);
  return match?.[1] ?? null;
}

// ---------------------------------------------------------------------------
// Route handlers
// ---------------------------------------------------------------------------

/**
 * POST /workflows
 * Body: { type: string, context: Record<string, unknown> }
 */
async function handleTrigger(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  const body = await parseBody(req);
  const type = body.type as string | undefined;
  const context = (body.context as Record<string, unknown>) ?? {};

  if (!type) {
    sendJson(res, 400, { error: "Missing required field: type" });
    return;
  }

  const definition = getWorkflowDefinition(type);
  if (!definition) {
    sendJson(res, 400, { error: `Unknown workflow type: ${type}` });
    return;
  }

  const instance = await startWorkflow(type, context);
  sendJson(res, 201, { id: instance.id, type: instance.type, state: instance.state });
}

/**
 * GET /workflows/:id
 */
async function handleStatus(
  _req: http.IncomingMessage,
  res: http.ServerResponse,
  workflowId: string,
): Promise<void> {
  // TODO: Replace with actual Prisma query
  const rows = await prisma.$queryRaw<
    Array<{ id: string; type: string; state: string; context: unknown; createdAt: Date; updatedAt: Date }>
  >`
    SELECT * FROM "{WORKFLOW_INSTANCES_TABLE}" WHERE "id" = ${workflowId} LIMIT 1
  `;

  if (rows.length === 0) {
    sendJson(res, 404, { error: "Workflow not found" });
    return;
  }

  const instance = rows[0];
  sendJson(res, 200, {
    id: instance.id,
    type: instance.type,
    state: instance.state,
    context: instance.context,
    createdAt: instance.createdAt,
    updatedAt: instance.updatedAt,
  });
}

/**
 * POST /workflows/:id/signal
 * Body: { event: string, payload?: Record<string, unknown> }
 */
async function handleSignal(
  req: http.IncomingMessage,
  res: http.ServerResponse,
  workflowId: string,
): Promise<void> {
  const body = await parseBody(req);
  const event = body.event as string | undefined;
  const payload = (body.payload as Record<string, unknown>) ?? {};

  if (!event) {
    sendJson(res, 400, { error: "Missing required field: event" });
    return;
  }

  try {
    await signalWorkflow(workflowId, event, payload);
    sendJson(res, 200, { ok: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    sendJson(res, 422, { error: message });
  }
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

async function router(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  const url = req.url ?? "";
  const method = req.method ?? "";

  try {
    // POST /workflows
    if (method === "POST" && url === "/workflows") {
      await handleTrigger(req, res);
      return;
    }

    // POST /workflows/:id/signal
    const signalId = extractPathParam(url, /^\/workflows\/([^/]+)\/signal$/);
    if (method === "POST" && signalId) {
      await handleSignal(req, res, signalId);
      return;
    }

    // GET /workflows/:id
    const statusId = extractPathParam(url, /^\/workflows\/([^/]+)$/);
    if (method === "GET" && statusId) {
      await handleStatus(req, res, statusId);
      return;
    }

    sendJson(res, 404, { error: "Not found" });
  } catch (err) {
    logger.error({ err, url, method }, "Unhandled API error");
    sendJson(res, 500, { error: "Internal server error" });
  }
}

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------

export function startApiServer(): http.Server {
  const server = http.createServer((req, res) => {
    router(req, res).catch((err) => {
      logger.error({ err }, "Router error");
      sendJson(res, 500, { error: "Internal server error" });
    });
  });

  server.listen(API_PORT, () => {
    logger.info({ port: API_PORT }, "API server listening");
  });

  return server;
}
