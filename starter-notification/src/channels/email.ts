import { Resend } from "resend";
import { withRetry } from "../lib/retry";
import { CircuitBreaker } from "../lib/circuit-breaker";
import { createJobLogger } from "../lib/logger";
import { recordDelivery } from "../lib/delivery-tracker";

const resend = new Resend(process.env.RESEND_API_KEY);

const MAX_RETRIES = parseInt(process.env.MAX_RETRIES_EMAIL ?? "3", 10);
const RETRY_BACKOFF_MS = parseInt(process.env.RETRY_BACKOFF_MS ?? "1000", 10);

export const emailCircuitBreaker = new CircuitBreaker("email", {
  failureThreshold: 5,
  resetTimeoutMs: 60_000,
});

export interface EmailPayload {
  notificationId: string;
  userId: string;
  to: string;
  subject: string;
  html: string;
  text: string;
}

export interface DeliveryResult {
  externalId?: string;
  status: "sent" | "failed";
  errorMessage?: string;
}

/**
 * Send an email via Resend with retry and circuit breaker.
 */
export async function send(payload: EmailPayload): Promise<DeliveryResult> {
  const log = createJobLogger(payload.notificationId, payload.userId);
  log.info({ to: payload.to }, "Sending email");

  try {
    const result = await emailCircuitBreaker.call(() =>
      withRetry(
        async () => {
          const response = await resend.emails.send({
            from: `${process.env.EMAIL_FROM_NAME ?? "{FROM_NAME}"} <${process.env.EMAIL_FROM_ADDRESS ?? "{FROM_ADDRESS}"}>`,
            to: [payload.to],
            subject: payload.subject,
            html: payload.html,
            text: payload.text,
          });

          if (response.error) {
            throw new Error(response.error.message);
          }

          return response.data;
        },
        { maxAttempts: MAX_RETRIES, backoffMs: RETRY_BACKOFF_MS },
      ),
    );

    const externalId = result?.id;

    await recordDelivery(payload.notificationId, "email", "sent", {
      externalId,
    });

    log.info({ externalId }, "Email sent");
    return { externalId, status: "sent" };
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : String(err);

    await recordDelivery(payload.notificationId, "email", "failed", {
      errorMessage,
    });

    log.error({ err }, "Email delivery failed");
    return { status: "failed", errorMessage };
  }
}

/**
 * Check email delivery status via provider API.
 */
export async function getStatus(
  externalId: string,
): Promise<string> {
  // TODO: Resend does not expose a status-check endpoint in the same way
  // as transactional email providers. Status updates come via webhooks.
  // Implement webhook handler in src/api/ to call updateDeliveryStatus().
  void externalId;
  return "unknown";
}
