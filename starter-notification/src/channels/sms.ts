import { withRetry } from "../lib/retry";
import { CircuitBreaker } from "../lib/circuit-breaker";
import { createJobLogger } from "../lib/logger";
import { recordDelivery } from "../lib/delivery-tracker";

// TODO: Uncomment when Twilio is configured:
// import twilio from "twilio";
// const client = twilio(
//   process.env.TWILIO_ACCOUNT_SID,
//   process.env.TWILIO_AUTH_TOKEN,
// );

const MAX_RETRIES = parseInt(process.env.MAX_RETRIES_SMS ?? "2", 10);
const RETRY_BACKOFF_MS = parseInt(process.env.RETRY_BACKOFF_MS ?? "1000", 10);

export const smsCircuitBreaker = new CircuitBreaker("sms", {
  failureThreshold: 5,
  resetTimeoutMs: 60_000,
});

export interface SmsPayload {
  notificationId: string;
  userId: string;
  to: string;
  body: string;
}

export interface DeliveryResult {
  externalId?: string;
  status: "sent" | "failed";
  errorMessage?: string;
}

/**
 * Send an SMS via Twilio with retry and circuit breaker.
 */
export async function send(payload: SmsPayload): Promise<DeliveryResult> {
  const log = createJobLogger(payload.notificationId, payload.userId);
  log.info({ to: payload.to }, "Sending SMS");

  try {
    const result = await smsCircuitBreaker.call(() =>
      withRetry(
        async () => {
          // TODO: Replace with actual Twilio call:
          // const message = await client.messages.create({
          //   body: payload.body,
          //   from: process.env.TWILIO_FROM_NUMBER,
          //   to: payload.to,
          // });
          // return { sid: message.sid };

          throw new Error(
            "SMS provider not configured — set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN",
          );
        },
        { maxAttempts: MAX_RETRIES, backoffMs: RETRY_BACKOFF_MS },
      ),
    );

    const externalId = (result as { sid?: string }).sid;

    await recordDelivery(payload.notificationId, "sms", "sent", {
      externalId,
    });

    log.info({ externalId }, "SMS sent");
    return { externalId, status: "sent" };
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : String(err);

    await recordDelivery(payload.notificationId, "sms", "failed", {
      errorMessage,
    });

    log.error({ err }, "SMS delivery failed");
    return { status: "failed", errorMessage };
  }
}

/**
 * Check SMS delivery status via Twilio API.
 */
export async function getStatus(
  externalId: string,
): Promise<string> {
  // TODO: Implement with Twilio:
  // const message = await client.messages(externalId).fetch();
  // return message.status;
  void externalId;
  return "unknown";
}
