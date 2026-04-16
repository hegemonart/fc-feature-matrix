import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { getEvents } from '@/lib/analytics';

export async function GET(req: NextRequest) {
  // Auth gate — must be an admin
  const cookie = req.headers.get('cookie');
  const session = getSessionFromCookie(cookie);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const user = await getUserByEmail(session.email);
  if (!user?.isAdmin) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const url = new URL(req.url);
  const limit = parseInt(url.searchParams.get('limit') || '100', 10);
  const type = url.searchParams.get('type') || undefined;
  const email = url.searchParams.get('email') || undefined;

  const analyticsEvents = await getEvents({ limit: Math.min(limit, 1000), type, email });
  return NextResponse.json(analyticsEvents);
}
