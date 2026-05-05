import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { getDisplayDate, setSetting, SETTING_KEYS } from '@/lib/settings';

async function requireAdmin(req: NextRequest) {
  const session = getSessionFromCookie(req.headers.get('cookie'));
  if (!session) return null;
  const user = await getUserByEmail(session.email);
  return user?.isAdmin ? user : null;
}

const patchSchema = z.object({
  value: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .refine((v) => !Number.isNaN(Date.parse(v)), 'Date must be a real calendar date'),
});

/** GET — read current display date (admin-only; consumed by /admin/settings page). */
export async function GET(req: NextRequest) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const value = await getDisplayDate();
  return NextResponse.json({ value, fallback: process.env.BUILD_DATE ?? '' });
}

/** PATCH — upsert the display date (admin-only). */
export async function PATCH(req: NextRequest) {
  const admin = await requireAdmin(req);
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  try {
    const row = await setSetting(SETTING_KEYS.DISPLAY_DATE, parsed.data.value, admin.id);
    return NextResponse.json({
      value: row.value,
      updatedAt: row.updatedAt.toISOString(),
      updatedBy: row.updatedBy,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to save: ${msg}` }, { status: 500 });
  }
}
