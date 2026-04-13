import { prisma } from "../lib/prisma";
import { createJobLogger } from "../lib/logger";
import { recordDelivery } from "../lib/delivery-tracker";

const WEBSOCKET_SERVICE_URL = process.env.WEBSOCKET_SERVICE_URL;

export interface InAppPayload {
  notificationId: string;
  userId: string;
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

export interface DeliveryResult {
  externalId?: string;
  status: "sent" | "failed";
  errorMessage?: string;
}

/**
 * Create an in-app notification (DB write) and optionally push to
 * connected WebSocket clients.
 *
 * In-app notifications are NOT retried — the DB write is local and
 * the WebSocket push is best-effort.
 */
export async function send(payload: InAppPayload): Promise<DeliveryResult> {
  const log = createJobLogger(payload.notificationId, payload.userId);
  log.info("Creating in-app notification");

  try {
    // TODO: Replace with actual Prisma create against your notifications table.
    // Example:
    //   const notification = await prisma.notification.create({
    //     data: {
    //       id: payload.notificationId,
    //       userId: payload.userId,
    //       title: payload.title,
    //       body: payload.body,
    //       data: payload.data ?? {},
    //       read: false,
    //     },
    //   });

    void prisma; // reference to avoid unused lint error in skeleton

    await recordDelivery(payload.notificationId, "in_app", "sent");
    log.info("In-app notification created");

    // Best-effort WebSocket push to connected clients
    if (WEBSOCKET_SERVICE_URL) {
      try {
        await fetch(`${WEBSOCKET_SERVICE_URL}/push`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userId: payload.userId,
            event: "notification",
            data: {
              id: payload.notificationId,
              title: payload.title,
              body: payload.body,
              data: payload.data,
            },
          }),
          signal: AbortSignal.timeout(5000),
        });
        log.info("WebSocket push sent");
      } catch (wsErr) {
        // WebSocket push is best-effort — do not fail the notification
        log.warn({ err: wsErr }, "WebSocket push failed (best-effort)");
      }
    }

    return { externalId: payload.notificationId, status: "sent" };
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : String(err);

    await recordDelivery(payload.notificationId, "in_app", "failed", {
      errorMessage,
    });

    log.error({ err }, "In-app notification failed");
    return { status: "failed", errorMessage };
  }
}

/**
 * In-app notifications do not have an external delivery status.
 * Status is managed directly in the database.
 */
export async function getStatus(
  externalId: string,
): Promise<string> {
  void externalId;
  return "delivered";
}
