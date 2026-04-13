import { prisma } from "../lib/prisma";
import { createJobLogger } from "../lib/logger";
import { withRetry } from "../lib/retry";

/**
 * Example job payload — replace with your actual schema.
 */
export interface ExampleJobPayload {
  jobId: string;
  userId: string;
  // TODO: add job-specific fields
}

export interface ExampleJobResult {
  success: boolean;
}

/**
 * Example worker handler.
 *
 * Requirements:
 * - MUST be idempotent — running with the same jobId twice produces
 *   the same result without side effects.
 * - MUST NOT manage queue consumption — that belongs in src/consumers/.
 * - External calls MUST use withRetry() and circuit breakers.
 */
export async function processExampleJob(
  payload: ExampleJobPayload,
): Promise<ExampleJobResult> {
  const log = createJobLogger(payload.jobId, payload.userId);
  log.info("Processing example job");

  // --- Idempotency check ---
  // If this job has already been processed, return early.
  // Replace with your actual idempotency lookup.
  const existing = await prisma.$queryRaw`
    SELECT 1 FROM "{JOB_RESULTS_TABLE}" WHERE "job_id" = ${payload.jobId} LIMIT 1
  `;
  if (Array.isArray(existing) && existing.length > 0) {
    log.info("Job already processed — skipping (idempotent)");
    return { success: true };
  }

  // --- Process the job ---
  // TODO: Replace with actual business logic.
  // Use withRetry for external API calls:
  //
  // const apiResult = await withRetry(
  //   () => callExternalService(payload),
  //   { maxAttempts: 3, backoffMs: 1000 },
  // );

  await withRetry(
    async () => {
      // TODO: Write result to database
      log.info("Job processed successfully");
    },
    { maxAttempts: 3, backoffMs: 500 },
  );

  return { success: true };
}
