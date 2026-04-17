import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { db } from '@/lib/db';
import { events } from '@/lib/db/schema';
import { desc, gte, sql } from 'drizzle-orm';

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

export async function GET(req: NextRequest) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const url = new URL(req.url);
  const days = Math.min(parseInt(url.searchParams.get('days') || '14', 10), 90);
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
