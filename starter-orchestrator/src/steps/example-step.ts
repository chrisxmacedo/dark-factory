/**
 * Example step implementation — validates a submission.
 *
 * Steps must be:
 * - Idempotent: safe to run multiple times with the same workflow instance
 * - Pure of queue logic: steps do not manage their own scheduling
 * - Return typed results: success, failure, or pending
 *
 * Replace this with your actual step implementations.
 */

import { prisma } from "../lib/prisma";
import { createWorkflowLogger } from "../lib/logger";
import { WorkflowContext, StepResult } from "../engine/state-machine";

/**
 * Execute the "submitted" step — validate the submission data.
 *
 * Returns:
 * - success: submission is valid, workflow advances
 * - failure: submission is invalid, workflow transitions to failure
 * - pending: (not used here, but available for async validation)
 */
export async function executeSubmission(
  ctx: WorkflowContext,
): Promise<{ result: StepResult; ctx: WorkflowContext }> {
  const workflowId = ctx.workflowId as string;
  const log = createWorkflowLogger(workflowId, "submitted");

  log.info("Validating submission");

  // --- Idempotency check ---
  // If this step has already been processed for this workflow, return early.
  // TODO: Replace with your actual idempotency lookup.
  const existing = await prisma.$queryRaw`
    SELECT 1 FROM "{STEP_RESULTS_TABLE}"
    WHERE "workflow_id" = ${workflowId}
    AND "step_name" = 'submitted'
    LIMIT 1
  `;
  if (Array.isArray(existing) && existing.length > 0) {
    log.info("Step already completed — returning cached result (idempotent)");
    return { result: "success", ctx };
  }

  // --- Execute step logic ---
  // TODO: Replace with actual validation / business logic.
  //
  // Example: check that required fields are present
  // const { applicantName, amount } = ctx as { applicantName?: string; amount?: number };
  // if (!applicantName || !amount) {
  //   log.warn("Missing required fields");
  //   return { result: "failure", ctx: { ...ctx, error: "Missing required fields" } };
  // }

  // TODO: Persist step result for idempotency
  // await prisma.stepResult.create({
  //   data: { workflowId, stepName: "submitted", result: "success", ... }
  // });

  log.info("Submission validated successfully");

  return {
    result: "success",
    ctx: { ...ctx, submittedAt: new Date().toISOString() },
  };
}
