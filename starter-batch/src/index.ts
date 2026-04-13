import { v4 as uuidv4 } from "uuid";
import { createJobLogger } from "./lib/logger";
import { prisma } from "./lib/prisma";
import { exampleJob } from "./jobs/example-job";

// --- Job registry ---
// Add new jobs here. Each entry maps a job name to its handler function.
const jobs: Record<string, (runId: string) => Promise<void>> = {
  example: exampleJob,
  // reconcile: reconcileJob,
  // report: reportJob,
};

async function main(): Promise<void> {
  const jobName = process.argv[2] || process.env.JOB_NAME;
  const runId = process.env.RUN_ID || uuidv4();
  const timeoutMs = Number(process.env.JOB_TIMEOUT_MS) || 300_000;

  if (!jobName) {
    console.error(
      "Usage: node dist/index.js <job-name>\n" +
        "   or: JOB_NAME=<job-name> node dist/index.js\n\n" +
        `Available jobs: ${Object.keys(jobs).join(", ")}`
    );
    process.exit(1);
  }

  const jobFn = jobs[jobName];
  if (!jobFn) {
    console.error(
      `Unknown job: "${jobName}". Available jobs: ${Object.keys(jobs).join(", ")}`
    );
    process.exit(1);
  }

  const logger = createJobLogger(jobName, runId);
  logger.info({ timeoutMs }, "Job starting");

  // Enforce maximum runtime
  const timeout = setTimeout(() => {
    logger.error("Job exceeded maximum runtime, forcing exit");
    process.exit(1);
  }, timeoutMs);
  timeout.unref();

  try {
    await jobFn(runId);
    logger.info("Job completed successfully");
  } catch (err) {
    logger.error({ err }, "Job failed");
    process.exit(1);
  } finally {
    clearTimeout(timeout);
    await prisma.$disconnect();
  }

  process.exit(0);
}

main();
