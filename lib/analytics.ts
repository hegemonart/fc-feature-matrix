import { Redis } from '@upstash/redis';

const EVENTS_KEY = 'analytics:events';
const MAX_EVENTS = 10_000;

// ── Redis client (lazy init) ──

let redis: Redis | null = null;

function getRedis(): Redis | null {
  if (redis) return redis;
  const url = process.env.KV_REST_API_URL;
  const token = process.env.KV_REST_API_TOKEN;
  if (!url || !token) return null;
  redis = new Redis({ url, token });
  return redis;
}

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
  const event: AnalyticsEvent = {
    type,
    email,
    timestamp: new Date().toISOString(),
    ...data,
  };

  const kv = getRedis();
  if (!kv) {
    // Local dev fallback
    console.log('[analytics]', JSON.stringify(event));
    return;
  }

  try {
    await kv.lpush(EVENTS_KEY, JSON.stringify(event));
    await kv.ltrim(EVENTS_KEY, 0, MAX_EVENTS - 1);
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
  const kv = getRedis();
  if (!kv) return [];

  const { limit = 100, type, email } = opts;

  try {
    // Fetch more than needed if filtering, to ensure we get enough results
    const fetchCount = (type || email) ? Math.min(limit * 5, MAX_EVENTS) : limit;
    const raw: string[] = await kv.lrange(EVENTS_KEY, 0, fetchCount - 1);

    let events: AnalyticsEvent[] = raw.map(r =>
      typeof r === 'string' ? JSON.parse(r) : r as AnalyticsEvent,
    );

    if (type) events = events.filter(e => e.type === type);
    if (email) events = events.filter(e => e.email === email);

    return events.slice(0, limit);
  } catch (err) {
    console.error('[analytics] Failed to read events:', err);
    return [];
  }
}
