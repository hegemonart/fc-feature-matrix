import { NextRequest, NextResponse } from 'next/server';
import { clearSessionCookieHeader, getSessionFromCookie } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';

export async function POST(req: NextRequest) {
  const cookie = req.headers.get('cookie');
  const session = getSessionFromCookie(cookie);
  if (session) {
    logEvent('logout', session.email, {}).catch(() => {});
  }

  const res = NextResponse.json({ ok: true });
  res.headers.set('Set-Cookie', clearSessionCookieHeader());
  return res;
}
