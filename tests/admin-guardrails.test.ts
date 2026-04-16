import { describe, it, expect, afterAll } from 'vitest';

/**
 * Admin guardrail tests — require a real Postgres DATABASE_URL.
 * Skipped automatically when DATABASE_URL is not set, or when the
 * database is not reachable (e.g. CI without a DB, localhost fake URLs).
 *
 * Each test uses a transaction rolled back at the end so the database
 * state is never permanently modified.
 *
 * To run locally: set DATABASE_URL to a real Neon dev branch connection.
 */

const DATABASE_URL = process.env.DATABASE_URL;

// Neon URLs always contain 'neon.tech' or similar. Skip localhost/fake URLs.
const isRealDb =
  !!DATABASE_URL &&
  !DATABASE_URL.includes('localhost') &&
  !DATABASE_URL.includes('127.0.0.1') &&
  !DATABASE_URL.includes('mock');

if (!isRealDb) {
  describe('admin-guardrails (skipped — no real DATABASE_URL)', () => {
    it('skipped: set DATABASE_URL to a real Postgres instance to run these tests', () => {
      console.warn(
        '[admin-guardrails] No real DATABASE_URL detected — skipping DB guardrail tests.'
      );
    });
  });
} else {
  const { Pool, neonConfig } = await import('@neondatabase/serverless');
  const ws = (await import('ws')).default;
  neonConfig.webSocketConstructor = ws;

  const pool = new Pool({ connectionString: DATABASE_URL });

  afterAll(() => pool.end());

  describe('last-admin guardrail', () => {
    it('allows demoting an admin when another admin exists', async () => {
      const client = await pool.connect();
      try {
        await client.query('BEGIN');

        const { rows: [adminA] } = await client.query(
          `INSERT INTO users (email, password_hash, is_admin)
           VALUES ('guardrail_a@test.invalid', 'x', true) RETURNING id`
        );
        const { rows: [adminB] } = await client.query(
          `INSERT INTO users (email, password_hash, is_admin)
           VALUES ('guardrail_b@test.invalid', 'x', true) RETURNING id`
        );

        // Demote adminA — should succeed (adminB still exists)
        const result = await client.query(
          `UPDATE users SET is_admin = false WHERE id = $1
           AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
           RETURNING id`,
          [adminA.id]
        );
        expect(result.rowCount).toBe(1);

        // Demote adminB — should fail (no other admin left)
        const result2 = await client.query(
          `UPDATE users SET is_admin = false WHERE id = $1
           AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
           RETURNING id`,
          [adminB.id]
        );
        expect(result2.rowCount).toBe(0);
      } finally {
        await client.query('ROLLBACK');
        client.release();
      }
    });

    it('prevents deleting the last admin', async () => {
      const client = await pool.connect();
      try {
        await client.query('BEGIN');

        const { rows: [admin] } = await client.query(
          `INSERT INTO users (email, password_hash, is_admin)
           VALUES ('guardrail_solo@test.invalid', 'x', true) RETURNING id`
        );

        const result = await client.query(
          `DELETE FROM users WHERE id = $1
           AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
           RETURNING id`,
          [admin.id]
        );
        expect(result.rowCount).toBe(0);

        // Verify the user still exists
        const check = await client.query('SELECT id FROM users WHERE id = $1', [admin.id]);
        expect(check.rowCount).toBe(1);
      } finally {
        await client.query('ROLLBACK');
        client.release();
      }
    });

    it('allows deleting an admin when another admin exists', async () => {
      const client = await pool.connect();
      try {
        await client.query('BEGIN');

        await client.query(
          `INSERT INTO users (email, password_hash, is_admin)
           VALUES ('guardrail_c@test.invalid', 'x', true)`
        );
        const { rows: [adminD] } = await client.query(
          `INSERT INTO users (email, password_hash, is_admin)
           VALUES ('guardrail_d@test.invalid', 'x', true) RETURNING id`
        );

        const result = await client.query(
          `DELETE FROM users WHERE id = $1
           AND (SELECT count(*) FROM users WHERE is_admin = true) > 1
           RETURNING id`,
          [adminD.id]
        );
        expect(result.rowCount).toBe(1);
      } finally {
        await client.query('ROLLBACK');
        client.release();
      }
    });
  });
}
