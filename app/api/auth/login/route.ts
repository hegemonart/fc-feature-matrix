import { NextRequest, NextResponse } from 'next/server';
import {
  getUserByEmail,
  verifyPassword,
  createSessionToken,
  sessionCookieHeader,
} from '@/lib/auth';
import { logEvent } from '@/lib/analytics';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq, sql } from 'drizzle-orm';

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();
    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password required' }, { status: 400 });
    }

    const user = await getUserByEmail(email);
    if (!user) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

    const valid = await verifyPassword(password, user.passwordHash);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

    // Update last_login_at
    await db
      .update(users)
      .set({ lastLoginAt: sql`now()` })
      .where(eq(users.id, user.id));

    const token = createSessionToken(user.email);
    const ua = req.headers.get('user-agent') || '';
    logEvent('login', user.email, { userAgent: ua }).catch(() => {});

    const res = NextResponse.json({ ok: true, email: user.email });
    res.headers.set('Set-Cookie', sessionCookieHeader(token));
    return res;
  } catch {
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
