import { NextRequest, NextResponse } from 'next/server';
import { getSessionFromCookie } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';

export async function POST(req: NextRequest) {
  try {
    const { type, data } = await req.json();
    if (!type) {
      return new NextResponse(null, { status: 400 });
    }

    const cookie = req.headers.get('cookie');
    const session = getSessionFromCookie(cookie);
    const email = session?.email ?? 'anonymous';

    await logEvent(type, email, data || {});
    return new NextResponse(null, { status: 204 });
  } catch {
    return new NextResponse(null, { status: 500 });
  }
}
