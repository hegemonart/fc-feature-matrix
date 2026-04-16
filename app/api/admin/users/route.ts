import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSessionFromCookie, getUserByEmail, hashPassword } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

const createSchema = z.object({
  email: z.string().email(),
  name: z.string().optional(),
  password: z.string().min(12, 'Password must be at least 12 characters'),
});

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

export async function POST(req: NextRequest) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }

  const parsed = createSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const { email, name, password } = parsed.data;
  const passwordHash = await hashPassword(password);

  try {
    const [user] = await db
      .insert(users)
      .values({ email: email.toLowerCase(), name: name ?? null, passwordHash, isAdmin: false })
      .returning({
        id: users.id,
        email: users.email,
        name: users.name,
        isAdmin: users.isAdmin,
        createdAt: users.createdAt,
        lastLoginAt: users.lastLoginAt,
      });

    logEvent('admin_user_created', admin.email, { target_email: email }).catch(() => {});

    return NextResponse.json({
      user: {
        ...user,
        createdAt: user.createdAt.toISOString(),
        lastLoginAt: user.lastLoginAt?.toISOString() ?? null,
      },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes('unique')) return NextResponse.json({ error: 'Email already exists' }, { status: 409 });
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
