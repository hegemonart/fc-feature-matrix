import { type NextRequest, NextResponse } from 'next/server';
import { env } from '@/lib/env';
import { pool } from '@/lib/db';

// Must run on Node.js runtime (edge doesn't support Neon WebSocket pool)
export const runtime = 'nodejs';

const BATCH_LIMIT = 10_000;
const WALL_BUDGET_MS = 15_000; // 15 seconds max

export async function GET(req: NextRequest) {
  // Bearer token auth
  const auth = req.headers.get('authorization');
  const expected = `Bearer ${env.CRON_SECRET}`;
  if (auth !== expected) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const client = await pool.connect();
  const start = Date.now();
  let totalDeleted = 0;

  try {
    // Delete events older than 90 days in batches until none left or budget exhausted.
    // Uses a CTE to delete with a LIMIT (Postgres doesn't support DELETE ... LIMIT directly).
    const batchSql = `
      WITH batch AS (
        SELECT id FROM events
        WHERE created_at < now() - interval '90 days'
        LIMIT $1
      )
      DELETE FROM events
      WHERE id IN (SELECT id FROM batch)
    `;

    while (true) {
      if (Date.now() - start > WALL_BUDGET_MS) break;

      const result = await client.query(batchSql, [BATCH_LIMIT]);
      const deleted = result.rowCount ?? 0;
      totalDeleted += deleted;

      // Stop when fewer rows deleted than batch size — nothing left to clean
      if (deleted < BATCH_LIMIT) break;
    }
  } finally {
    client.release();
  }

  const durationMs = Date.now() - start;
  console.log(`[retention] Deleted ${totalDeleted} events in ${durationMs}ms`);

  return NextResponse.json({ ok: true, deleted_count: totalDeleted, duration_ms: durationMs });
}
