import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie } from '@/lib/auth';
import { getEvents } from '@/lib/analytics';

export async function GET(req: NextRequest) {
  // Auth gate
  const cookie = req.headers.get('cookie');
  const session = getSessionFromCookie(cookie);
  if (!session || !session.email.endsWith('@humbleteam.com')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const url = new URL(req.url);
  const limit = parseInt(url.searchParams.get('limit') || '100', 10);
  const type = url.searchParams.get('type') || undefined;
  const email = url.searchParams.get('email') || undefined;

  const events = await getEvents({ limit: Math.min(limit, 1000), type, email });
  return NextResponse.json(events);
}
