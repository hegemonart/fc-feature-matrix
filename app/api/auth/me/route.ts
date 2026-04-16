import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie } from '@/lib/auth';
import { getUserByEmail } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const cookie = req.headers.get('cookie');
  const session = getSessionFromCookie(cookie);
  if (!session) {
    return NextResponse.json({ authenticated: false });
  }

  // Look up current is_admin from DB — the session token only holds email
  const user = await getUserByEmail(session.email);
  if (!user) {
    return NextResponse.json({ authenticated: false });
  }

  return NextResponse.json({
    authenticated: true,
    email: user.email,
    isAdmin: user.isAdmin,
    isPremium: user.isPremium,
  });
}
