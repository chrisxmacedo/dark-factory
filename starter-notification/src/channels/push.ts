import { withRetry } from "../lib/retry";
import { CircuitBreaker } from "../lib/circuit-breaker";
import { createJobLogger } from "../lib/logger";
import { recordDelivery } from "../lib/delivery-tracker";

// TODO: Uncomment when Firebase is configured:
// import * as admin from "firebase-admin";
// if (!admin.apps.length) {
//   admin.initializeApp({ credential: admin.credential.applicationDefault() });
// }

const MAX_RETRIES = parseInt(process.env.MAX_RETRIES_PUSH ?? "2", 10);
const RETRY_BACKOFF_MS = parseInt(process.env.RETRY_BACKOFF_MS ?? "1000", 10);

export const pushCircuitBreaker = new CircuitBreaker("push", {
  failureThreshold: 5,
  resetTimeoutMs: 60_000,
});

export interface PushPayload {
  notificationId: string;
  userId: string;
  /** FCM device token */
  deviceToken: string;
  title: string;
  body: string;
  data?: Record<string, string>;
}

export interface DeliveryResult {
  externalId?: string;
  status: "sent" | "failed";
  errorMessage?: string;
}

/**
 * Send a push notification via FCM with retry and circuit breaker.
 */
export async function send(payload: PushPayload): Promise<DeliveryResult> {
  const log = createJobLogger(payload.notificationId, payload.userId);
  log.info({ deviceToken: payload.deviceToken }, "Sending push notification");

  try {
    const result = await pushCircuitBreaker.call(() =>
      withRetry(
        async () => {
          // TODO: Replace with actual FCM call:
          // const messageId = await admin.messaging().send({
          //   token: payload.deviceToken,
          //   notification: {
          //     title: payload.title,
          //     body: payload.body,
          //   },
          //   data: payload.data,
          // });
          // return { messageId };

          throw new Error(
            "Push provider not configured — set GOOGLE_APPLICATION_CREDENTIALS",
          );
        },
        { maxAttempts: MAX_RETRIES, backoffMs: RETRY_BACKOFF_MS },
      ),
    );

    const externalId = (result as { messageId?: string }).messageId;

    await recordDelivery(payload.notificationId, "push", "sent", {
      externalId,
    });

    log.info({ externalId }, "Push notification sent");
    return { externalId, status: "sent" };
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : String(err);

    await recordDelivery(payload.notificationId, "push", "failed", {
      errorMessage,
    });

    log.error({ err }, "Push delivery failed");
    return { status: "failed", errorMessage };
  }
}

/**
 * Check push delivery status.
 * FCM does not provide a status-check API — delivery confirmations
 * come via the FCM Data API or client-side acknowledgment.
 */
export async function getStatus(
  externalId: string,
): Promise<string> {
  void externalId;
  return "unknown";
}
