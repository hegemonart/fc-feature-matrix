/**
 * Applies Drizzle SQL migrations to the Neon Postgres database.
 *
 * Usage:
 *   npm run db:migrate
 *
 * Requires DATABASE_URL_UNPOOLED (direct connection, no -pooler suffix).
 * Migrations MUST NOT run against a pooled connection — PgBouncer breaks
 * advisory locks and prepared statements that the migrator relies on.
 */
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import { migrate } from 'drizzle-orm/neon-serverless/migrator';
import ws from 'ws';

neonConfig.webSocketConstructor = ws;

const url = process.env.DATABASE_URL_UNPOOLED;

if (!url) {
  console.error('Error: DATABASE_URL_UNPOOLED is not set.');
  console.error('Set it to the direct (non-pooler) Neon connection string.');
  process.exit(1);
}

if (url.includes('-pooler')) {
  console.error('Error: DATABASE_URL_UNPOOLED must NOT contain "-pooler".');
  console.error(
    'Migrations require the direct connection string. The pooled (-pooler) URL\n' +
      'goes through PgBouncer which breaks advisory locks and the migration runner.'
  );
  process.exit(1);
}

const pool = new Pool({ connectionString: url });
const db = drizzle(pool);

async function main() {
  console.log('Running migrations…');
  try {
    await migrate(db, { migrationsFolder: './drizzle' });
    console.log('Migrations applied successfully.');
  } catch (err) {
    console.error('Migration failed:', err);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
