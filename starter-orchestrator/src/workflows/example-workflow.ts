/**
 * Example workflow definition — a simple approval flow with 4 states.
 *
 * Flow: submitted -> under_review -> approved/rejected
 *
 * The "under_review" state is an approval gate: the step returns "pending"
 * and the workflow waits for an external signal ("approve" or "reject").
 *
 * Replace this with your actual workflow definitions.
 */

import { WorkflowDefinition } from "../engine/state-machine";
import { executeSubmission } from "../steps/example-step";

export const exampleWorkflow: WorkflowDefinition = {
  name: "example-approval",

  initialState: "submitted",

  terminalStates: {
    success: ["approved"],
    failure: ["rejected"],
  },

  states: {
    submitted: {
      execute: executeSubmission,
      compensate: async (ctx) => {
        // TODO: Undo submission (e.g. release reserved resources)
        void ctx;
      },
      timeoutMs: 60_000,
    },

    under_review: {
      // No execute function — this is an approval gate.
      // The workflow waits here until a signal arrives.
      timeoutMs: 86_400_000, // 24 hours to approve
    },

    approved: {
      // Terminal success state — no step to execute.
    },

    rejected: {
      // Terminal failure state — no step to execute.
    },
  },

  transitions: [
    // After submission succeeds, move to review
    {
      from: "submitted",
      to: "under_review",
      event: "success",
    },
    // Submission failed
    {
      from: "submitted",
      to: "rejected",
      event: "failure",
    },
    // External approval signal
    {
      from: "under_review",
      to: "approved",
      event: "approve",
    },
    // External rejection signal
    {
      from: "under_review",
      to: "rejected",
      event: "reject",
    },
    // Review timed out
    {
      from: "under_review",
      to: "rejected",
      event: "timeout",
    },
  ],

  maxDurationMs: 172_800_000, // 48 hours
};
