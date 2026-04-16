import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSessionFromCookie, getUserByEmail, hashPassword } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq, sql } from 'drizzle-orm';

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

const patchSchema = z.object({
  isAdmin: z.boolean().optional(),
  isPremium: z.boolean().optional(),
  newPassword: z.string().min(12).optional(),
});

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id } = await params;

  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }

  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });

  const { isAdmin, isPremium, newPassword } = parsed.data;

  // Toggle is_admin with last-admin guardrail (atomic single-statement UPDATE)
  if (isAdmin === false) {
    const result = await db.execute(
      sql`UPDATE users SET is_admin = false WHERE id = ${id}
          AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
          RETURNING id`
    );
    if ((result.rowCount ?? 0) === 0) {
      return NextResponse.json({ error: 'Cannot demote the last admin' }, { status: 409 });
    }
    return NextResponse.json({ ok: true });
  }

  if (isAdmin === true) {
    await db.update(users).set({ isAdmin: true }).where(eq(users.id, id));
    return NextResponse.json({ ok: true });
  }

  if (isPremium !== undefined) {
    await db.update(users).set({ isPremium }).where(eq(users.id, id));
    return NextResponse.json({ ok: true });
  }

  if (newPassword) {
    const passwordHash = await hashPassword(newPassword);
    await db.update(users).set({ passwordHash }).where(eq(users.id, id));
    return NextResponse.json({ ok: true });
  }

  return NextResponse.json({ error: 'Nothing to update' }, { status: 400 });
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id } = await params;

  // Refuse self-delete
  if (id === admin.id) {
    return NextResponse.json({ error: 'Cannot delete your own account' }, { status: 409 });
  }

  // Atomic delete with last-admin guardrail
  const targetUser = await db.select({ isAdmin: users.isAdmin }).from(users).where(eq(users.id, id)).limit(1);
  if (targetUser.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });

  if (targetUser[0].isAdmin) {
    const result = await db.execute(
      sql`DELETE FROM users WHERE id = ${id}
          AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
          RETURNING id`
    );
    if ((result.rowCount ?? 0) === 0) {
      return NextResponse.json({ error: 'Cannot delete the last admin' }, { status: 409 });
    }
  } else {
    await db.delete(users).where(eq(users.id, id));
  }

  return NextResponse.json({ ok: true });
}
