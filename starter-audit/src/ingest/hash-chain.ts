import { createHash } from "node:crypto";
import type { AuditEventInput } from "./schema";

const GENESIS_HASH =
  process.env.GENESIS_HASH ??
  "0000000000000000000000000000000000000000000000000000000000000000";

/**
 * Compute a SHA-256 hash for an audit event, incorporating the previous
 * event's hash to form an unbroken chain. If any stored event is modified
 * after the fact, the chain breaks and tampering is detectable.
 *
 * The hash is computed over a deterministic JSON representation of the
 * event fields plus the previous hash.
 */
export function computeEventHash(
  event: AuditEventInput,
  previousHash: string | null,
): { hash: string; previousHash: string } {
  const prev = previousHash ?? GENESIS_HASH;

  const payload = JSON.stringify({
    id: event.id,
    timestamp: event.timestamp.toISOString(),
    actor: event.actor,
    action: event.action,
    resource: event.resource,
    context: event.context,
    outcome: event.outcome,
    metadata: event.metadata,
    previousHash: prev,
  });

  const hash = createHash("sha256").update(payload).digest("hex");

  return { hash, previousHash: prev };
}

/**
 * Verify that a sequence of stored events has an unbroken hash chain.
 * Returns the index of the first broken link, or -1 if the chain is valid.
 */
export function verifyChain(
  events: Array<{ hash: string; previousHash: string } & AuditEventInput>,
): number {
  for (let i = 0; i < events.length; i++) {
    const event = events[i];
    const expectedPrev = i === 0 ? GENESIS_HASH : events[i - 1].hash;

    if (event.previousHash !== expectedPrev) {
      return i;
    }

    const { hash: recomputed } = computeEventHash(event, event.previousHash);
    if (event.hash !== recomputed) {
      return i;
    }
  }

  return -1;
}
