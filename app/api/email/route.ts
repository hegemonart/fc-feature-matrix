import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { accessRequests } from '@/lib/db/schema';

function getResend() {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { Resend } = require('resend') as typeof import('resend');
  return new Resend(process.env.RESEND_API_KEY);
}

/* Simple in-memory rate limit: max 5 requests per IP per minute */
const rateMap = new Map<string, number[]>();
const RATE_LIMIT = 5;
const RATE_WINDOW = 60_000;

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const hits = (rateMap.get(ip) || []).filter(t => now - t < RATE_WINDOW);
  if (hits.length >= RATE_LIMIT) return true;
  hits.push(now);
  rateMap.set(ip, hits);
  return false;
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get('x-forwarded-for') || 'unknown';
  if (isRateLimited(ip)) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
  }

  let body: { feature?: string; source?: string; email?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const feature = body.feature || 'Unknown';
  const source = body.source || 'unknown';
  const requesterEmail = body.email || null;

  // Persist access request for admin triage (before Resend — row survives even if email fails)
  db.insert(accessRequests)
    .values({
      email: requesterEmail ?? feature,
      source: source || null,
      ip: ip !== 'unknown' ? ip : null,
      userAgent: req.headers.get('user-agent') || null,
    })
    .catch((err) => console.error('[email] Failed to persist access request:', err));

  try {
    const resend = getResend();
    await resend.emails.send({
      from: 'FC Benchmark <noreply@humbleteam.com>',
      to: ['hi@humbleteam.com'],
      ...(requesterEmail ? { replyTo: requesterEmail } : {}),
      subject: `FC Benchmark — Access request${requesterEmail ? ` from ${requesterEmail}` : ''}: ${feature}`,
      text: [
        `New access request for FC Benchmark.`,
        ``,
        ...(requesterEmail ? [`From: ${requesterEmail}`, ``] : []),
        `View requested: ${feature}`,
        `Source: ${source}`,
        `Time: ${new Date().toISOString()}`,
        `IP: ${ip}`,
      ].join('\n'),
    });

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error('Email send failed:', err);
    return NextResponse.json({ error: 'Failed to send email' }, { status: 500 });
  }
}
