import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const cookie = req.headers.get('cookie');
  const session = getSessionFromCookie(cookie);
  if (session) {
    return NextResponse.json({ authenticated: true, email: session.email });
  }
  return NextResponse.json({ authenticated: false });
}
