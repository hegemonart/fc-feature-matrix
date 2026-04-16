/**
 * One-shot migration: seeds Neon Postgres `users` table from data/users.json.
 *
 * Usage:
 *   npm run db:migrate-users
 *
 * Idempotent — uses ON CONFLICT DO NOTHING on the email unique constraint.
 * Safe to re-run; already-existing users are skipped and logged.
 *
 * Admins: any user whose email ends with @humbleteam.com gets is_admin=true.
 * Run this BEFORE deleting data/users.json from the repo.
 */
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from 'ws';
import { readFileSync } from 'fs';
import { join } from 'path';
import { users } from '../lib/db/schema';

neonConfig.webSocketConstructor = ws;

const url = process.env.DATABASE_URL ?? process.env.DATABASE_URL_UNPOOLED;
if (!url) {
  console.error('Error: DATABASE_URL or DATABASE_URL_UNPOOLED must be set.');
  process.exit(1);
}

const pool = new Pool({ connectionString: url });
const db = drizzle(pool);

interface StoredUser {
  email: string;
  passwordHash: string;
  name?: string;
}

async function main() {
  const usersPath = join(process.cwd(), 'data', 'users.json');
  let stored: StoredUser[];
  try {
    stored = JSON.parse(readFileSync(usersPath, 'utf-8')) as StoredUser[];
  } catch (err) {
    console.error(`Could not read data/users.json: ${(err as Error).message}`);
    process.exit(1);
  }

  console.log(`Seeding ${stored.length} users from data/users.json…`);

  let inserted = 0;
  let skipped = 0;

  for (const u of stored) {
    const email = u.email.toLowerCase();
    const isAdmin = email.endsWith('@humbleteam.com');
    const result = await db
      .insert(users)
      .values({
        email,
        passwordHash: u.passwordHash,
        name: u.name ?? null,
        isAdmin,
      })
      .onConflictDoNothing({ target: users.email });

    const count = result.rowCount ?? 0;
    if (count > 0) {
      console.log(`  ✓ Inserted: ${email}${isAdmin ? ' (admin)' : ''}`);
      inserted++;
    } else {
      console.log(`  – Skipped (already exists): ${email}`);
      skipped++;
    }
  }

  console.log(`\nDone. Inserted: ${inserted}, Skipped: ${skipped}`);
  await pool.end();
}

main().catch((err) => {
  console.error('Unexpected error:', err);
  pool.end().finally(() => process.exit(1));
});
