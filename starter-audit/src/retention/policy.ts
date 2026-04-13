/**
 * Retention policy definitions per audit event type.
 *
 * This service defines the policies but does NOT enforce them.
 * Enforcement (archival to cold storage, eventual purge) is handled
 * by starter-batch as a scheduled job.
 *
 * Duration format: number + unit (d = days, m = months, y = years)
 */

export interface RetentionPolicy {
  /** Event action prefix to match (e.g. "financial." matches "financial.transaction") */
  actionPrefix: string;
  /** How long to keep events in the primary store */
  retentionDuration: string;
  /** Human-readable description of why this retention period applies */
  reason: string;
}

const DEFAULT_RETENTION_DAYS = parseInt(
  process.env.DEFAULT_RETENTION_DAYS ?? "365",
  10,
);

/**
 * Default retention policies. Extend this list per project requirements.
 *
 * TODO: Replace these with your project's actual event types and
 * regulatory requirements.
 */
export const retentionPolicies: RetentionPolicy[] = [
  {
    actionPrefix: "financial.",
    retentionDuration: "7y",
    reason: "SOX/PCI DSS compliance — financial records retained 7 years",
  },
  {
    actionPrefix: "access.",
    retentionDuration: "1y",
    reason: "Access logs retained 1 year for security review",
  },
  {
    actionPrefix: "auth.",
    retentionDuration: "2y",
    reason: "Authentication events retained 2 years",
  },
  {
    actionPrefix: "admin.",
    retentionDuration: "5y",
    reason: "Administrative actions retained 5 years for accountability",
  },
];

/**
 * Parse a duration string into days.
 */
export function parseDurationToDays(duration: string): number {
  const match = duration.match(/^(\d+)(d|m|y)$/);
  if (!match) {
    return DEFAULT_RETENTION_DAYS;
  }

  const value = parseInt(match[1], 10);
  const unit = match[2];

  switch (unit) {
    case "d":
      return value;
    case "m":
      return value * 30;
    case "y":
      return value * 365;
    default:
      return DEFAULT_RETENTION_DAYS;
  }
}

/**
 * Find the retention policy that applies to a given action.
 * Returns the matching policy, or a default policy if no match is found.
 */
export function getRetentionForAction(action: string): RetentionPolicy {
  const match = retentionPolicies.find((policy) =>
    action.startsWith(policy.actionPrefix),
  );

  return (
    match ?? {
      actionPrefix: "",
      retentionDuration: `${DEFAULT_RETENTION_DAYS}d`,
      reason: "Default retention policy",
    }
  );
}

/**
 * Calculate the expiry date for an event based on its action type.
 */
export function getExpiryDate(action: string, eventTimestamp: Date): Date {
  const policy = getRetentionForAction(action);
  const days = parseDurationToDays(policy.retentionDuration);
  const expiry = new Date(eventTimestamp);
  expiry.setDate(expiry.getDate() + days);
  return expiry;
}
