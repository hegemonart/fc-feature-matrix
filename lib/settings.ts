/* ================================================================
   lib/settings.ts

   Runtime-editable site settings backed by the site_settings table.
   Each helper returns the DB value when present, otherwise an env
   default — so the app keeps working before the migration runs and
   if the DB read fails for any reason.

   Currently exposed:
   - DISPLAY_DATE — ISO YYYY-MM-DD string rendered in <HeaderBar>.
     Editable from /admin/settings; defaults to process.env.BUILD_DATE
     (which itself falls back to '' if unset, see next.config.ts).
   ================================================================ */

import { db } from './db';
import { siteSettings, type SiteSetting } from './db/schema';
import { eq } from 'drizzle-orm';

export const SETTING_KEYS = {
  DISPLAY_DATE: 'display_date',
} as const;

export type SettingKey = typeof SETTING_KEYS[keyof typeof SETTING_KEYS];

/**
 * Read a setting from the DB. Returns null if the row doesn't exist
 * OR if the DB read fails (e.g. migration not run, network blip).
 * Caller should fall back to an env default in either case.
 */
export async function getSetting(key: SettingKey): Promise<string | null> {
  try {
    const rows = await db.select().from(siteSettings).where(eq(siteSettings.key, key)).limit(1);
    return rows[0]?.value ?? null;
  } catch {
    return null;
  }
}

/** Convenience wrapper — display date with env fallback. */
export async function getDisplayDate(): Promise<string> {
  return (await getSetting(SETTING_KEYS.DISPLAY_DATE)) ?? process.env.BUILD_DATE ?? '';
}

/**
 * Upsert a setting. `updatedBy` is the admin user's UUID for audit.
 * Throws if the DB write fails — callers should surface to the UI.
 */
export async function setSetting(
  key: SettingKey,
  value: string,
  updatedBy: string | null,
): Promise<SiteSetting> {
  const now = new Date();
  const [row] = await db
    .insert(siteSettings)
    .values({ key, value, updatedAt: now, updatedBy })
    .onConflictDoUpdate({
      target: siteSettings.key,
      set: { value, updatedAt: now, updatedBy },
    })
    .returning();
  return row;
}
