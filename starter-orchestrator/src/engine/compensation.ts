/**
 * Compensation handler — runs rollback functions for completed steps in
 * reverse order when a workflow step fails.
 *
 * Compensation functions are best-effort: failures are logged but do not
 * prevent subsequent compensations from running.
 */

import { createWorkflowLogger } from "../lib/logger";
import { WorkflowDefinition, WorkflowContext } from "./state-machine";

/**
 * Run compensation for all completed steps in reverse order.
 *
 * @param definition  The workflow definition containing compensate functions
 * @param completedSteps  List of state names that completed successfully (in order)
 * @param ctx  Current workflow context
 * @param workflowId  For logging
 */
export async function runCompensation(
  definition: WorkflowDefinition,
  completedSteps: string[],
  ctx: WorkflowContext,
  workflowId: string,
): Promise<void> {
  const log = createWorkflowLogger(workflowId);
  const reversed = [...completedSteps].reverse();

  log.warn(
    { stepsToCompensate: reversed },
    "Starting compensation — rolling back completed steps",
  );

  for (const stepName of reversed) {
    const stateDef = definition.states[stepName];
    if (!stateDef?.compensate) {
      log.info({ stepName }, "No compensation function — skipping");
      continue;
    }

    const stepLog = createWorkflowLogger(workflowId, stepName);

    try {
      stepLog.info("Running compensation");
      await stateDef.compensate(ctx);
      stepLog.info("Compensation completed");
    } catch (err) {
      // Best-effort: log and continue with remaining compensations
      stepLog.error({ err }, "Compensation failed — continuing with remaining steps");
    }
  }

  log.info("Compensation sequence finished");
}
