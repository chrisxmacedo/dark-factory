import { createJobLogger } from "../lib/logger";
import { prisma } from "../lib/prisma";
import { loadCheckpoint, saveCheckpoint, clearCheckpoint } from "../lib/checkpoint";

interface ExampleCheckpoint {
  lastProcessedId: number;
  processedCount: number;
  total: number;
}

/**
 * Example batch job demonstrating the standard patterns:
 * - Idempotency (upserts, check-before-write)
 * - Resumability (checkpoint after each batch)
 * - Progress logging at regular intervals
 */
export async function exampleJob(runId: string): Promise<void> {
  const logger = createJobLogger("example", runId);
  const BATCH_SIZE = 100;

  // --- Resume from checkpoint if one exists ---
  const checkpoint = await loadCheckpoint<ExampleCheckpoint>(runId);
  let lastProcessedId = checkpoint?.lastProcessedId ?? 0;
  let processedCount = checkpoint?.processedCount ?? 0;

  if (checkpoint) {
    logger.info(
      { lastProcessedId, processedCount },
      "Resuming from checkpoint"
    );
  }

  // --- Count total work ---
  // Replace this with your actual query. The `where` clause should match
  // the records this job needs to process.
  const total = await prisma.$queryRaw<[{ count: bigint }]>`
    SELECT COUNT(*)::bigint as count FROM "User" WHERE id > ${lastProcessedId}
  `.then((rows) => Number(rows[0].count));

  logger.info({ total, alreadyProcessed: processedCount }, "Work estimated");

  // --- Process in batches ---
  let hasMore = true;

  while (hasMore) {
    // Fetch the next batch. Replace with your actual query.
    const batch = await prisma.user.findMany({
      where: { id: { gt: lastProcessedId } },
      orderBy: { id: "asc" },
      take: BATCH_SIZE,
    });

    if (batch.length === 0) {
      hasMore = false;
      break;
    }

    for (const record of batch) {
      // --- Process each record ---
      // Replace this with your actual processing logic.
      // Use upserts or check-before-write for idempotency.
      //
      // Example:
      // await prisma.processedRecord.upsert({
      //   where: { sourceId: record.id },
      //   create: { sourceId: record.id, result: computeResult(record) },
      //   update: { result: computeResult(record) },
      // });

      lastProcessedId = record.id;
      processedCount++;
    }

    // --- Checkpoint after each batch ---
    await saveCheckpoint<ExampleCheckpoint>(runId, {
      lastProcessedId,
      processedCount,
      total: processedCount + total - (processedCount - (checkpoint?.processedCount ?? 0)),
    });

    logger.info(
      { progress: `${processedCount}/${total}`, lastProcessedId },
      "Batch processed"
    );
  }

  // --- Cleanup ---
  await clearCheckpoint(runId);
  logger.info({ processedCount }, "Job finished");
}
