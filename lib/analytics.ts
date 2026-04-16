import { db } from './db';
import { events } from './db/schema';
import { desc, eq, and, lt, gt } from 'drizzle-orm';

// ── Event types ──

export interface AnalyticsEvent {
  type: string;
  email: string;
  timestamp: string;
  [key: string]: unknown;
}

// ── Log an event ──

export async function logEvent(
  type: string,
  email: string,
  data: Record<string, unknown> = {},
): Promise<void> {
  if (!process.env.DATABASE_URL) {
    // Dev fallback when DB is not configured
    console.log('[analytics]', JSON.stringify({ type, email, timestamp: new Date().toISOString(), ...data }));
    return;
  }

  try {
    await db.insert(events).values({
      userEmail: email || null,
      // type cast — DB enum values match the strings callers already use
      type: type as typeof events.$inferInsert['type'],
      data: Object.keys(data).length > 0 ? JSON.stringify(data) : null,
      userAgent: typeof data.userAgent === 'string' ? data.userAgent : null,
    });
  } catch (err) {
    console.error('[analytics] Failed to log event:', err);
  }
}

// ── Read events ──

export async function getEvents(opts: {
  limit?: number;
  type?: string;
  email?: string;
} = {}): Promise<AnalyticsEvent[]> {
  if (!process.env.DATABASE_URL) return [];

  const { limit = 100, type, email } = opts;

  try {
    const conditions = [];
    if (type) conditions.push(eq(events.type, type as typeof events.$inferInsert['type']));
    if (email) conditions.push(eq(events.userEmail, email));

    const rows = await db
      .select()
      .from(events)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(desc(events.createdAt))
      .limit(Math.min(limit, 1000));

    return rows.map((row) => {
      let extra: Record<string, unknown> = {};
      if (row.data) {
        try { extra = JSON.parse(row.data) as Record<string, unknown>; } catch { /* ignore */ }
      }
      return {
        type: row.type,
        email: row.userEmail ?? '',
        timestamp: row.createdAt.toISOString(),
        ...extra,
      };
    });
  } catch (err) {
    console.error('[analytics] Failed to read events:', err);
    return [];
  }
}
