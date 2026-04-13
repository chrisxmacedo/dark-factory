// Initialise OpenTelemetry BEFORE any other imports
import "./lib/otel";

import { startHealthServer } from "./health";
import { prisma } from "./lib/prisma";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";
import { loadTemplates } from "./lib/templates";
import { resolveChannels } from "./lib/preferences";
import type { Channel } from "./lib/preferences";
import { hasBeenProcessed, recordDelivery } from "./lib/delivery-tracker";
import * as emailChannel from "./channels/email";
import * as smsChannel from "./channels/sms";
import * as pushChannel from "./channels/push";
import * as inAppChannel from "./channels/in-app";
import { createJobLogger } from "./lib/logger";

const SHUTDOWN_TIMEOUT_MS = parseInt(
  process.env.SHUTDOWN_TIMEOUT_MS ?? "30000",
  10,
);

let isShuttingDown = false;

/**
 * Notification request payload — the event consumed from the queue.
 */
export interface NotificationRequest {
  notificationId: string;
  userId: string;
  templateName: string;
  channels: Channel[];
  data: Record<string, unknown>;
  /** Recipient details — resolved per channel */
  recipients: {
    email?: string;
    phone?: string;
    deviceToken?: string;
  };
}

/**
 * Process a single notification request.
 * Resolves preferences, renders template, delivers to allowed channels.
 */
export async function processNotification(
  request: NotificationRequest,
): Promise<void> {
  const log = createJobLogger(request.notificationId, request.userId);

  // Idempotency check
  const alreadyProcessed = await hasBeenProcessed(request.notificationId);
  if (alreadyProcessed) {
    log.info("Notification already processed — skipping (idempotent)");
    return;
  }

  // Resolve user preferences
  const { allowed, suppressed } = await resolveChannels(
    request.userId,
    request.channels,
  );

  // Record suppressed channels
  for (const { channel, reason } of suppressed) {
    log.warn({ channel, reason }, "Channel suppressed");
    await recordDelivery(request.notificationId, channel, "suppressed");
  }

  if (allowed.length === 0) {
    log.info("No channels to deliver — all suppressed");
    return;
  }

  // Deliver to each allowed channel (in parallel — channels are independent)
  const deliveryPromises = allowed.map(async (channel) => {
    switch (channel) {
      case "email": {
        if (!request.recipients.email) {
          log.warn("No email address — skipping email channel");
          return;
        }
        // TODO: Render template. Replace with actual renderTemplate call
        // once templates are set up:
        // const rendered = renderTemplate(request.templateName, request.data);
        await emailChannel.send({
          notificationId: request.notificationId,
          userId: request.userId,
          to: request.recipients.email,
          subject: `{SUBJECT_PLACEHOLDER}`,
          html: `{HTML_PLACEHOLDER}`,
          text: `{TEXT_PLACEHOLDER}`,
        });
        break;
      }
      case "sms": {
        if (!request.recipients.phone) {
          log.warn("No phone number — skipping SMS channel");
          return;
        }
        await smsChannel.send({
          notificationId: request.notificationId,
          userId: request.userId,
          to: request.recipients.phone,
          body: `{SMS_BODY_PLACEHOLDER}`,
        });
        break;
      }
      case "push": {
        if (!request.recipients.deviceToken) {
          log.warn("No device token — skipping push channel");
          return;
        }
        await pushChannel.send({
          notificationId: request.notificationId,
          userId: request.userId,
          deviceToken: request.recipients.deviceToken,
          title: `{PUSH_TITLE_PLACEHOLDER}`,
          body: `{PUSH_BODY_PLACEHOLDER}`,
        });
        break;
      }
      case "in_app": {
        await inAppChannel.send({
          notificationId: request.notificationId,
          userId: request.userId,
          title: `{IN_APP_TITLE_PLACEHOLDER}`,
          body: `{IN_APP_BODY_PLACEHOLDER}`,
          data: request.data,
        });
        break;
      }
    }
  });

  await Promise.allSettled(deliveryPromises);
  log.info({ channels: allowed }, "Notification delivery complete");
}

async function main(): Promise<void> {
  logger.info("Starting notification service");

  // Connect to dependencies
  await prisma.$connect();
  logger.info("Database connected");

  await redis.ping();
  logger.info("Redis connected");

  // Load notification templates
  loadTemplates();

  // Start health endpoint
  const healthServer = startHealthServer();

  // TODO: Start your notification consumer here.
  // e.g. consume from a Redis queue, Kafka topic, or HTTP webhook endpoint.
  // Each message should be parsed into a NotificationRequest and passed
  // to processNotification().

  logger.info("Notification service started");

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    if (isShuttingDown) return;
    isShuttingDown = true;
    logger.info({ signal }, "Shutdown signal received — draining");

    const forceExit = setTimeout(() => {
      logger.error("Shutdown timeout exceeded — forcing exit");
      process.exit(1);
    }, SHUTDOWN_TIMEOUT_MS);

    try {
      // TODO: Stop consumers — stop accepting new notifications, await current delivery

      healthServer.close();
      await redis.quit();
      await prisma.$disconnect();
      logger.info("Shutdown complete");
      clearTimeout(forceExit);
      process.exit(0);
    } catch (err) {
      logger.error({ err }, "Error during shutdown");
      clearTimeout(forceExit);
      process.exit(1);
    }
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

export { isShuttingDown };

main().catch((err) => {
  logger.fatal({ err }, "Notification service failed to start");
  process.exit(1);
});
