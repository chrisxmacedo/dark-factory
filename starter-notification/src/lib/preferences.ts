import { prisma } from "./prisma";
import { logger } from "./logger";

export type Channel = "email" | "sms" | "push" | "in_app";

export interface UserPreferences {
  userId: string;
  channels: Record<Channel, boolean>;
  quietHours: {
    enabled: boolean;
    /** IANA timezone, e.g. "Europe/London" */
    timezone: string;
    /** Start hour in 24h format (e.g. 22 for 10pm) */
    startHour: number;
    /** End hour in 24h format (e.g. 8 for 8am) */
    endHour: number;
  };
  frequencyCaps: Record<Channel, {
    /** Max notifications per window */
    maxCount: number;
    /** Window size in minutes */
    windowMinutes: number;
  }>;
}

/**
 * Load user notification preferences from the database.
 * Returns default preferences (all channels enabled, no quiet hours)
 * if the user has no stored preferences.
 */
export async function getUserPreferences(
  userId: string,
): Promise<UserPreferences> {
  // TODO: Replace with actual Prisma query against your preferences table.
  // Example:
  //   const row = await prisma.notificationPreference.findUnique({
  //     where: { userId },
  //   });
  //   if (row) return deserializePreferences(row);

  void prisma; // reference to avoid unused lint error in skeleton

  logger.debug({ userId }, "Loading user preferences");

  // Default: all channels enabled, no quiet hours, generous frequency caps
  return {
    userId,
    channels: { email: true, sms: true, push: true, in_app: true },
    quietHours: {
      enabled: false,
      timezone: "UTC",
      startHour: 22,
      endHour: 8,
    },
    frequencyCaps: {
      email: { maxCount: 50, windowMinutes: 60 },
      sms: { maxCount: 10, windowMinutes: 60 },
      push: { maxCount: 30, windowMinutes: 60 },
      in_app: { maxCount: 100, windowMinutes: 60 },
    },
  };
}

/**
 * Check whether the user is currently in quiet hours.
 */
export function isInQuietHours(prefs: UserPreferences): boolean {
  if (!prefs.quietHours.enabled) return false;

  const now = new Date();
  // Get current hour in the user's timezone
  const formatter = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    hour12: false,
    timeZone: prefs.quietHours.timezone,
  });
  const currentHour = parseInt(formatter.format(now), 10);

  const { startHour, endHour } = prefs.quietHours;

  // Handle overnight quiet hours (e.g. 22:00 - 08:00)
  if (startHour > endHour) {
    return currentHour >= startHour || currentHour < endHour;
  }

  return currentHour >= startHour && currentHour < endHour;
}

/**
 * Check whether the user has exceeded their frequency cap for a channel.
 * Uses Redis to track recent notification counts.
 */
export async function isFrequencyCapExceeded(
  userId: string,
  channel: Channel,
  prefs: UserPreferences,
): Promise<boolean> {
  // TODO: Implement frequency cap checking against Redis.
  // Use a sliding window counter keyed by `freq:{userId}:{channel}`.
  // Example:
  //   const key = `freq:${userId}:${channel}`;
  //   const count = await redis.get(key);
  //   return count !== null && parseInt(count, 10) >= prefs.frequencyCaps[channel].maxCount;

  void userId;
  void channel;
  void prefs;

  return false;
}

/**
 * Resolve which channels should receive this notification for the given user.
 * Filters by: channel opt-in, quiet hours, frequency caps.
 */
export async function resolveChannels(
  userId: string,
  requestedChannels: Channel[],
): Promise<{ allowed: Channel[]; suppressed: Array<{ channel: Channel; reason: string }> }> {
  const prefs = await getUserPreferences(userId);
  const allowed: Channel[] = [];
  const suppressed: Array<{ channel: Channel; reason: string }> = [];

  for (const channel of requestedChannels) {
    // Check channel opt-in
    if (!prefs.channels[channel]) {
      suppressed.push({ channel, reason: "channel_opt_out" });
      continue;
    }

    // Check quiet hours (in-app is exempt from quiet hours)
    if (channel !== "in_app" && isInQuietHours(prefs)) {
      suppressed.push({ channel, reason: "quiet_hours" });
      continue;
    }

    // Check frequency caps
    const capExceeded = await isFrequencyCapExceeded(userId, channel, prefs);
    if (capExceeded) {
      suppressed.push({ channel, reason: "frequency_cap" });
      continue;
    }

    allowed.push(channel);
  }

  if (allowed.length === 0 && requestedChannels.length > 0) {
    logger.warn(
      { userId, requestedChannels, suppressed },
      "All channels suppressed for notification",
    );
  }

  return { allowed, suppressed };
}
