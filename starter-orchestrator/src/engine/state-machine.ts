/**
 * Core state machine — defines the shape of workflow definitions and
 * executes state transitions.
 *
 * Workflow definitions are pure data. The state machine evaluates guards
 * and resolves the next state without side effects.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Result of executing a step. */
export type StepResult = "success" | "failure" | "pending";

/** Context carried through the workflow — accumulates step outputs. */
export type WorkflowContext = Record<string, unknown>;

/** Guard predicate — evaluated to decide if a transition is allowed. */
export type GuardFn = (ctx: WorkflowContext) => boolean;

/** Action function — executed when a transition fires (side-effect free logging, context mutation). */
export type ActionFn = (ctx: WorkflowContext) => WorkflowContext;

/** Step execution function — the actual work performed in a state. */
export type StepFn = (ctx: WorkflowContext) => Promise<{
  result: StepResult;
  ctx: WorkflowContext;
}>;

/** Compensation function — undo work performed by a step. */
export type CompensateFn = (ctx: WorkflowContext) => Promise<void>;

/** A single transition between states. */
export interface Transition {
  from: string;
  to: string;
  event: string;
  guard?: GuardFn;
  action?: ActionFn;
}

/** Definition of a single state within a workflow. */
export interface StateDefinition {
  /** Step function to execute when entering this state. Omit for terminal states. */
  execute?: StepFn;
  /** Compensation function to undo this step's work on rollback. */
  compensate?: CompensateFn;
  /** Maximum time (ms) the step may run before timing out. */
  timeoutMs?: number;
}

/** Complete workflow definition — pure data, no I/O. */
export interface WorkflowDefinition {
  name: string;
  initialState: string;
  terminalStates: { success: string[]; failure: string[] };
  states: Record<string, StateDefinition>;
  transitions: Transition[];
  /** Maximum total duration (ms) for the entire workflow. */
  maxDurationMs?: number;
}

// ---------------------------------------------------------------------------
// State machine logic
// ---------------------------------------------------------------------------

/**
 * Find all transitions that match the given (currentState, event) pair
 * and whose guard (if any) passes against the context.
 */
export function findTransitions(
  definition: WorkflowDefinition,
  currentState: string,
  event: string,
  ctx: WorkflowContext,
): Transition[] {
  return definition.transitions.filter(
    (t) =>
      t.from === currentState &&
      t.event === event &&
      (t.guard ? t.guard(ctx) : true),
  );
}

/**
 * Resolve the next state for a given (currentState, event, context).
 * Returns the first matching transition, or null if none match.
 */
export function resolveTransition(
  definition: WorkflowDefinition,
  currentState: string,
  event: string,
  ctx: WorkflowContext,
): Transition | null {
  const matches = findTransitions(definition, currentState, event, ctx);
  return matches.length > 0 ? matches[0] : null;
}

/**
 * Apply a transition: run the action (if any) and return the new state + context.
 * Does NOT execute the step — that is the executor's responsibility.
 */
export function applyTransition(
  transition: Transition,
  ctx: WorkflowContext,
): { state: string; ctx: WorkflowContext } {
  const newCtx = transition.action ? transition.action(ctx) : ctx;
  return { state: transition.to, ctx: newCtx };
}

/**
 * Check whether a state is terminal (success or failure).
 */
export function isTerminal(
  definition: WorkflowDefinition,
  state: string,
): boolean {
  return (
    definition.terminalStates.success.includes(state) ||
    definition.terminalStates.failure.includes(state)
  );
}

/**
 * Check whether a state is a success terminal state.
 */
export function isSuccess(
  definition: WorkflowDefinition,
  state: string,
): boolean {
  return definition.terminalStates.success.includes(state);
}
