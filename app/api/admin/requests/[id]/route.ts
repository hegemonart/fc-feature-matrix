import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSessionFromCookie, getUserByEmail, hashPassword } from '@/lib/auth';
import { logEvent } from '@/lib/analytics';
import { db } from '@/lib/db';
import { users, accessRequests } from '@/lib/db/schema';
import { eq, sql } from 'drizzle-orm';

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

const bodySchema = z.discriminatedUnion('action', [
  z.object({ action: z.literal('grant'), password: z.string().min(12) }),
  z.object({ action: z.literal('dismiss') }),
]);

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id } = await params;

  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }

  const parsed = bodySchema.safeParse(body);
  if (!parsed.success) return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });

  // Fetch the request row
  const [reqRow] = await db.select().from(accessRequests).where(eq(accessRequests.id, id)).limit(1);
  if (!reqRow) return NextResponse.json({ error: 'Request not found' }, { status: 404 });
  if (reqRow.status !== 'pending') {
    return NextResponse.json({ error: `Request already ${reqRow.status}` }, { status: 409 });
  }

  if (parsed.data.action === 'dismiss') {
    await db
      .update(accessRequests)
      .set({ status: 'dismissed', resolvedAt: sql`now()` })
      .where(eq(accessRequests.id, id));

    logEvent('admin_request_dismissed', admin.email, { request_id: id, email: reqRow.email }).catch(() => {});
    return NextResponse.json({ ok: true });
  }

  // Grant: create user inside a transaction, update access_request row
  const passwordHash = await hashPassword(parsed.data.password);

  const newUser = await db.transaction(async (tx) => {
    // Create user (idempotent — if email already exists, skip creating)
    const existing = await tx.select({ id: users.id }).from(users)
      .where(eq(users.email, reqRow.email.toLowerCase())).limit(1);

    let userId: string;
    if (existing.length > 0) {
      userId = existing[0].id;
    } else {
      const [created] = await tx
        .insert(users)
        .values({
          email: reqRow.email.toLowerCase(),
          passwordHash,
          isAdmin: false,
        })
        .returning({ id: users.id });
      userId = created.id;
    }

    await tx
      .update(accessRequests)
      .set({ status: 'granted', grantedUserId: userId, resolvedAt: sql`now()` })
      .where(eq(accessRequests.id, id));

    return { id: userId };
  });

  logEvent('admin_request_granted', admin.email, {
    request_id: id,
    email: reqRow.email,
    new_user_id: newUser.id,
  }).catch(() => {});

  return NextResponse.json({ ok: true });
}
