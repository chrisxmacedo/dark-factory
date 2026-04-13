import { z } from "zod";

/**
 * Schema for incoming audit events before hash chain computation.
 * These are the fields provided by the producing service.
 */
export const auditEventInputSchema = z.object({
  id: z.string().min(1),
  timestamp: z.coerce.date(),
  actor: z.string().min(1),
  action: z.string().min(1),
  resource: z.string().min(1),
  context: z.string().min(1),
  outcome: z.enum(["success", "failure"]),
  metadata: z.record(z.unknown()).default({}),
});

export type AuditEventInput = z.infer<typeof auditEventInputSchema>;

/**
 * Full audit event including hash chain fields. This is what gets stored.
 */
export const auditEventSchema = auditEventInputSchema.extend({
  previousHash: z.string().min(1),
  hash: z.string().min(1),
});

export type AuditEvent = z.infer<typeof auditEventSchema>;
