import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';

export async function POST(req: NextRequest) {
  try {
    const cookie = req.headers.get('cookie');
    const session = getSessionFromCookie(cookie);

    // Require authentication — prevents anonymous event pollution (D-28)
    if (!session) {
      return new NextResponse(null, { status: 401 });
    }

    const { type, data } = await req.json();
    if (!type) {
      return new NextResponse(null, { status: 400 });
    }

    await logEvent(type, session.email, data || {});
    return new NextResponse(null, { status: 204 });
  } catch {
    return new NextResponse(null, { status: 500 });
  }
}
