import { prisma } from "./prisma";
import { logger } from "./logger";
import type { Channel } from "./preferences";

export type DeliveryStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "failed"
  | "bounced"
  | "suppressed";

export interface DeliveryRecord {
  notificationId: string;
  channel: Channel;
  status: DeliveryStatus;
  externalId?: string;
  errorMessage?: string;
  attemptCount: number;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Record a delivery attempt for a notification on a specific channel.
 */
export async function recordDelivery(
  notificationId: string,
  channel: Channel,
  status: DeliveryStatus,
  options: {
    externalId?: string;
    errorMessage?: string;
    attemptCount?: number;
  } = {},
): Promise<void> {
  // TODO: Replace with actual Prisma upsert against your delivery_log table.
  // Example:
  //   await prisma.deliveryLog.upsert({
  //     where: {
  //       notificationId_channel: { notificationId, channel },
  //     },
  //     create: {
  //       notificationId,
  //       channel,
  //       status,
  //       externalId: options.externalId,
  //       errorMessage: options.errorMessage,
  //       attemptCount: options.attemptCount ?? 1,
  //     },
  //     update: {
  //       status,
  //       externalId: options.externalId,
  //       errorMessage: options.errorMessage,
  //       attemptCount: options.attemptCount ?? 1,
  //       updatedAt: new Date(),
  //     },
  //   });

  void prisma; // reference to avoid unused lint error in skeleton

  logger.info(
    {
      notificationId,
      channel,
      status,
      externalId: options.externalId,
      attemptCount: options.attemptCount,
    },
    "Delivery status recorded",
  );
}

/**
 * Update delivery status from a provider webhook callback.
 * Called when Resend/Twilio/FCM reports delivery, bounce, or failure.
 */
export async function updateDeliveryStatus(
  externalId: string,
  status: DeliveryStatus,
  errorMessage?: string,
): Promise<void> {
  // TODO: Replace with actual Prisma update.
  // Example:
  //   await prisma.deliveryLog.updateMany({
  //     where: { externalId },
  //     data: { status, errorMessage, updatedAt: new Date() },
  //   });

  void prisma; // reference to avoid unused lint error in skeleton

  logger.info(
    { externalId, status, errorMessage },
    "Delivery status updated from webhook",
  );
}

/**
 * Check if a notification has already been processed (idempotency check).
 */
export async function hasBeenProcessed(
  notificationId: string,
): Promise<boolean> {
  // TODO: Replace with actual Prisma query.
  // Example:
  //   const existing = await prisma.deliveryLog.findFirst({
  //     where: { notificationId },
  //   });
  //   return existing !== null;

  void prisma; // reference to avoid unused lint error in skeleton
  void notificationId;

  return false;
}
