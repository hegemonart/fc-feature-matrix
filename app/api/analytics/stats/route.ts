import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { db } from '@/lib/db';
import { events } from '@/lib/db/schema';
import { desc, gte, sql } from 'drizzle-orm';
import { env } from '@/lib/env';

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

/** Deterministic mock stats payload for local preview when DATABASE_URL
 *  isn't wired. Shape matches the production response. Dev-only. */
function mockStatsPayload(days: number) {
  const dailySeries = [];
  // Seeded pseudo-random so reloads don't jitter the chart.
  let seed = 42;
  const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  let totalVisitors = 0;
  let totalPageViews = 0;
  let totalEvents = 0;
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400_000);
    const date = d.toISOString().slice(0, 10);
    const visitors = Math.floor(8 + rand() * 22);
    const pageViews = Math.floor(visitors * (2 + rand() * 3));
    const total = pageViews + Math.floor(rand() * 15);
    totalVisitors += visitors;
    totalPageViews += pageViews;
    totalEvents += total;
    dailySeries.push({
      date,
      label: d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
      visitors,
      pageViews,
      total,
    });
  }
  return {
    days,
    totalVisitors,
    totalPageViews,
    totalEvents,
    dailySeries,
    topEvents: [
      { type: 'page_view',     count: totalPageViews, visitors: 47 },
      { type: 'tab_click',     count: 312,            visitors: 41 },
      { type: 'feature_click', count: 187,            visitors: 33 },
      { type: 'login',         count: 96,             visitors: 58 },
      { type: 'product_click', count: 74,             visitors: 22 },
    ],
    topUsers: [
      { email: 'sergey@humbleteam.com',   count: 128 },
      { email: 'alice@humbleteam.com',    count:  94 },
      { email: 'marco@fcbarcelona.com',   count:  71 },
      { email: 'kim@liverpoolfc.com',     count:  52 },
      { email: 'research@humbleteam.com', count:  38 },
      { email: 'jamie@bayern.com',        count:  24 },
    ],
    topFeatures: [
      { name: 'Hero Carousel',              count: 68 },
      { name: 'Next-Match Block',           count: 54 },
      { name: 'Login / Account',            count: 47 },
      { name: 'Homepage Video Block',       count: 41 },
      { name: 'News Rich Structure',        count: 33 },
      { name: 'Interactive Fan Voting',     count: 27 },
      { name: 'Sponsor Lockup in Header',   count: 19 },
    ],
  };
}

export async function GET(req: NextRequest) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const url = new URL(req.url);
  const days = Math.min(parseInt(url.searchParams.get('days') || '14', 10), 90);

  // Dev-mode fallback — serve fixture data when no Neon is wired.
  if (!env.DATABASE_URL) {
    return NextResponse.json(mockStatsPayload(days));
  }

  const since = new Date(Date.now() - days * 86400_000);

  // All events in window
  const rows = await db
    .select()
    .from(events)
    .where(gte(events.createdAt, since))
    .orderBy(desc(events.createdAt))
    .limit(5000);

  // ── Daily series ──
  const dayMap = new Map<string, { visitors: Set<string>; pageViews: number; total: number }>();
  // Pre-populate all days so chart has no gaps
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400_000);
    const key = d.toISOString().slice(0, 10);
    dayMap.set(key, { visitors: new Set(), pageViews: 0, total: 0 });
  }

  for (const row of rows) {
    const key = row.createdAt.toISOString().slice(0, 10);
    const bucket = dayMap.get(key);
    if (!bucket) continue;
    if (row.userEmail) bucket.visitors.add(row.userEmail);
    if (row.type === 'page_view') bucket.pageViews++;
    bucket.total++;
  }

  const dailySeries = Array.from(dayMap.entries()).map(([date, b]) => ({
    date,
    label: new Date(date + 'T12:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
    visitors: b.visitors.size,
    pageViews: b.pageViews,
    total: b.total,
  }));

  // ── Totals ──
  const uniqueVisitors = new Set(rows.filter(r => r.userEmail).map(r => r.userEmail)).size;
  const totalPageViews = rows.filter(r => r.type === 'page_view').length;
  const totalEvents = rows.length;

  // ── Top event types ──
  const typeMap = new Map<string, { count: number; visitors: Set<string> }>();
  for (const row of rows) {
    const b = typeMap.get(row.type) ?? { count: 0, visitors: new Set() };
    b.count++;
    if (row.userEmail) b.visitors.add(row.userEmail);
    typeMap.set(row.type, b);
  }
  const topEvents = Array.from(typeMap.entries())
    .map(([type, b]) => ({ type, count: b.count, visitors: b.visitors.size }))
    .sort((a, b) => b.count - a.count);

  // ── Top users ──
  const userMap = new Map<string, number>();
  for (const row of rows) {
    if (row.userEmail) userMap.set(row.userEmail, (userMap.get(row.userEmail) ?? 0) + 1);
  }
  const topUsers = Array.from(userMap.entries())
    .map(([email, count]) => ({ email, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // ── Top features (from tab_click / feature_view data JSON) ──
  const featureMap = new Map<string, number>();
  for (const row of rows) {
    const rowType = row.type as string;
    if ((rowType === 'tab_click' || rowType === 'feature_view') && row.data) {
      try {
        const d = JSON.parse(row.data) as Record<string, unknown>;
        const name = (d.tab ?? d.feature ?? d.name) as string | undefined;
        if (name) featureMap.set(name, (featureMap.get(name) ?? 0) + 1);
      } catch { /* skip */ }
    }
  }
  const topFeatures = Array.from(featureMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return NextResponse.json({
    days,
    totalVisitors: uniqueVisitors,
    totalPageViews,
    totalEvents,
    dailySeries,
    topEvents,
    topUsers,
    topFeatures,
  });
}
