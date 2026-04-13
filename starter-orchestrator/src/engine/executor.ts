/**
 * Workflow executor — loads a workflow instance from the database, advances
 * its state by executing steps and evaluating transitions, persists every
 * state change, and handles timeouts.
 */

import { trace, SpanStatusCode } from "@opentelemetry/api";
import { prisma } from "../lib/prisma";
import { redis } from "../lib/redis";
import { createWorkflowLogger } from "../lib/logger";
import {
  WorkflowDefinition,
  WorkflowContext,
  StepResult,
  resolveTransition,
  applyTransition,
  isTerminal,
} from "./state-machine";
import { runCompensation } from "./compensation";

const WORKFLOW_EVENT_CHANNEL =
  process.env.WORKFLOW_EVENT_CHANNEL ?? "{project-name}:workflow:events";

const STEP_DEFAULT_TIMEOUT_MS = parseInt(
  process.env.STEP_DEFAULT_TIMEOUT_MS ?? "300000",
  10,
);

const WORKFLOW_DEFAULT_MAX_DURATION_MS = parseInt(
  process.env.WORKFLOW_DEFAULT_MAX_DURATION_MS ?? "86400000",
  10,
);

const tracer = trace.getTracer("{project-name}-orchestrator");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface WorkflowInstance {
  id: string;
  type: string;
  state: string;
  context: WorkflowContext;
  completedSteps: string[];
  createdAt: Date;
  updatedAt: Date;
}

// ---------------------------------------------------------------------------
// Registry — map workflow type names to their definitions
// ---------------------------------------------------------------------------

const workflowRegistry = new Map<string, WorkflowDefinition>();

export function registerWorkflow(definition: WorkflowDefinition): void {
  workflowRegistry.set(definition.name, definition);
}

export function getWorkflowDefinition(
  type: string,
): WorkflowDefinition | undefined {
  return workflowRegistry.get(type);
}

// ---------------------------------------------------------------------------
// Persistence helpers
// ---------------------------------------------------------------------------

/**
 * Load a workflow instance from the database.
 * Replace with your actual Prisma model queries.
 */
async function loadWorkflow(
  workflowId: string,
): Promise<WorkflowInstance | null> {
  // TODO: Replace with actual Prisma query
  // return prisma.workflowInstance.findUnique({ where: { id: workflowId } });
  const rows = await prisma.$queryRaw<WorkflowInstance[]>`
    SELECT * FROM "{WORKFLOW_INSTANCES_TABLE}" WHERE "id" = ${workflowId} LIMIT 1
  `;
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Persist a state transition to the database.
 */
async function persistTransition(
  workflowId: string,
  fromState: string,
  toState: string,
  event: string,
  context: WorkflowContext,
  completedSteps: string[],
): Promise<void> {
  const log = createWorkflowLogger(workflowId);

  // TODO: Replace with actual Prisma transaction
  // await prisma.$transaction([
  //   prisma.workflowInstance.update({ where: { id: workflowId }, data: { state: toState, context, completedSteps, updatedAt: new Date() } }),
  //   prisma.workflowTransition.create({ data: { workflowId, fromState, toState, event, context, timestamp: new Date() } }),
  // ]);

  log.info({ fromState, toState, event }, "State transition persisted");
}

// ---------------------------------------------------------------------------
// Core execution
// ---------------------------------------------------------------------------

/**
 * Create a new workflow instance and persist it.
 */
export async function startWorkflow(
  type: string,
  initialContext: WorkflowContext,
): Promise<WorkflowInstance> {
  const definition = getWorkflowDefinition(type);
  if (!definition) {
    throw new Error(`Unknown workflow type: ${type}`);
  }

  const id = crypto.randomUUID();
  const instance: WorkflowInstance = {
    id,
    type,
    state: definition.initialState,
    context: initialContext,
    completedSteps: [],
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  // TODO: Replace with actual Prisma create
  // await prisma.workflowInstance.create({ data: instance });

  const log = createWorkflowLogger(id);
  log.info({ type, initialState: definition.initialState }, "Workflow started");

  // Immediately try to advance
  await advanceWorkflow(id);

  return instance;
}

/**
 * Advance a workflow instance by executing its current step and applying
 * the resulting transition. Repeats until the workflow is terminal or pending.
 */
export async function advanceWorkflow(workflowId: string): Promise<void> {
  return tracer.startActiveSpan(
    "workflow.advance",
    async (span) => {
      const log = createWorkflowLogger(workflowId);

      try {
        const instance = await loadWorkflow(workflowId);
        if (!instance) {
          log.error("Workflow instance not found");
          span.setStatus({ code: SpanStatusCode.ERROR, message: "not found" });
          return;
        }

        const definition = getWorkflowDefinition(instance.type);
        if (!definition) {
          log.error({ type: instance.type }, "Workflow definition not found");
          span.setStatus({ code: SpanStatusCode.ERROR, message: "no definition" });
          return;
        }

        span.setAttributes({
          "workflow.id": workflowId,
          "workflow.type": instance.type,
          "workflow.state": instance.state,
        });

        // Check workflow-level timeout
        const maxDuration = definition.maxDurationMs ?? WORKFLOW_DEFAULT_MAX_DURATION_MS;
        const elapsed = Date.now() - instance.createdAt.getTime();
        if (elapsed > maxDuration) {
          log.warn({ elapsed, maxDuration }, "Workflow timed out");
          await handleWorkflowTimeout(instance, definition);
          return;
        }

        // If already terminal, nothing to do
        if (isTerminal(definition, instance.state)) {
          log.info({ state: instance.state }, "Workflow already terminal");
          return;
        }

        // Execute the current state's step (if any)
        const stateDef = definition.states[instance.state];
        if (!stateDef?.execute) {
          log.warn({ state: instance.state }, "No step to execute in this state");
          return;
        }

        const stepLog = createWorkflowLogger(workflowId, instance.state);
        stepLog.info("Executing step");

        const timeoutMs = stateDef.timeoutMs ?? STEP_DEFAULT_TIMEOUT_MS;
        let stepResult: { result: StepResult; ctx: WorkflowContext };

        try {
          stepResult = await Promise.race([
            stateDef.execute(instance.context),
            new Promise<never>((_, reject) =>
              setTimeout(() => reject(new Error("Step timed out")), timeoutMs),
            ),
          ]);
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err);
          if (message === "Step timed out") {
            stepLog.warn({ timeoutMs }, "Step timed out");
            stepResult = { result: "failure", ctx: { ...instance.context, _timeoutStep: instance.state } };
          } else {
            stepLog.error({ err }, "Step execution failed");
            stepResult = { result: "failure", ctx: instance.context };
          }
        }

        span.setAttribute("step.result", stepResult.result);

        // Map step result to event
        const event = stepResult.result; // "success" | "failure" | "pending"

        if (event === "pending") {
          stepLog.info("Step pending — awaiting external signal");
          return;
        }

        // Resolve and apply transition
        const transition = resolveTransition(
          definition,
          instance.state,
          event,
          stepResult.ctx,
        );

        if (!transition) {
          stepLog.error(
            { state: instance.state, event },
            "No matching transition — workflow stuck",
          );
          span.setStatus({ code: SpanStatusCode.ERROR, message: "no transition" });
          return;
        }

        const { state: newState, ctx: newCtx } = applyTransition(
          transition,
          stepResult.ctx,
        );

        const completedSteps =
          event === "success"
            ? [...instance.completedSteps, instance.state]
            : instance.completedSteps;

        await persistTransition(
          workflowId,
          instance.state,
          newState,
          event,
          newCtx,
          completedSteps,
        );

        stepLog.info({ newState }, "Transitioned");

        // If failure and compensation is configured, run it
        if (event === "failure" && completedSteps.length > 0) {
          await runCompensation(definition, completedSteps, newCtx, workflowId);
        }

        // If new state is terminal, publish completion event
        if (isTerminal(definition, newState)) {
          await publishWorkflowEvent(workflowId, instance.type, newState);
        } else {
          // Continue advancing (recursion with DB reload for crash safety)
          await advanceWorkflow(workflowId);
        }
      } catch (err) {
        log.error({ err }, "Unexpected error advancing workflow");
        span.setStatus({ code: SpanStatusCode.ERROR });
        span.recordException(err instanceof Error ? err : new Error(String(err)));
      } finally {
        span.end();
      }
    },
  );
}

/**
 * Handle an external signal (e.g. approval, rejection) for a pending workflow.
 */
export async function signalWorkflow(
  workflowId: string,
  signalEvent: string,
  signalPayload: Record<string, unknown>,
): Promise<void> {
  const log = createWorkflowLogger(workflowId);
  log.info({ signalEvent }, "Signal received");

  const instance = await loadWorkflow(workflowId);
  if (!instance) {
    throw new Error(`Workflow not found: ${workflowId}`);
  }

  const definition = getWorkflowDefinition(instance.type);
  if (!definition) {
    throw new Error(`Unknown workflow type: ${instance.type}`);
  }

  const mergedCtx: Record<string, unknown> = { ...instance.context, ...signalPayload };

  const transition = resolveTransition(
    definition,
    instance.state,
    signalEvent,
    mergedCtx,
  );

  if (!transition) {
    throw new Error(
      `No transition for signal "${signalEvent}" in state "${instance.state}"`,
    );
  }

  const { state: newState, ctx: newCtx } = applyTransition(transition, mergedCtx);
  const completedSteps = [...instance.completedSteps, instance.state];

  await persistTransition(
    workflowId,
    instance.state,
    newState,
    signalEvent,
    newCtx,
    completedSteps,
  );

  log.info({ newState }, "Signal applied — transitioned");

  if (isTerminal(definition, newState)) {
    await publishWorkflowEvent(workflowId, instance.type, newState);
  } else {
    await advanceWorkflow(workflowId);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function handleWorkflowTimeout(
  instance: WorkflowInstance,
  definition: WorkflowDefinition,
): Promise<void> {
  const log = createWorkflowLogger(instance.id);
  const failureState = definition.terminalStates.failure[0] ?? "failed";

  await persistTransition(
    instance.id,
    instance.state,
    failureState,
    "timeout",
    { ...instance.context, _timedOut: true },
    instance.completedSteps,
  );

  if (instance.completedSteps.length > 0) {
    await runCompensation(definition, instance.completedSteps, instance.context, instance.id);
  }

  await publishWorkflowEvent(instance.id, instance.type, failureState);
  log.info({ failureState }, "Workflow timed out — moved to failure state");
}

async function publishWorkflowEvent(
  workflowId: string,
  type: string,
  finalState: string,
): Promise<void> {
  const event = JSON.stringify({
    workflowId,
    type,
    finalState,
    timestamp: new Date().toISOString(),
  });
  await redis.publish(WORKFLOW_EVENT_CHANNEL, event);
}
