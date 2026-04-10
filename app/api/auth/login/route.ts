import { NextRequest, NextResponse } from 'next/server';
import { loadUsers, verifyPassword, createSessionToken, sessionCookieHeader } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();
    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password required' }, { status: 400 });
    }

    const users = loadUsers();
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());
    if (!user) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

    const valid = await verifyPassword(password, user.passwordHash);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

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
