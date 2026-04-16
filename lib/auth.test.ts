import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock lib/db so auth.ts can be imported without a real DB connection
vi.mock('@/lib/db', () => ({
  db: { select: vi.fn(), update: vi.fn() },
  pool: {},
}));
vi.mock('@/lib/db/schema', () => ({
  users: {},
}));

// Set required env vars before importing the module under test
process.env.DATABASE_URL = 'postgresql://mock:mock@localhost/mock';
process.env.AUTH_SECRET = 'test-secret-that-is-at-least-32-chars-long-xxxx';
// NODE_ENV is read-only in TypeScript strict mode; cast to avoid the TS error
(process.env as Record<string, string>).NODE_ENV = 'test';

const { createSessionToken, parseSessionToken } = await import('./auth');

const MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days

describe('parseSessionToken', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-01T00:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('accepts a fresh token', () => {
    const token = createSessionToken('user@example.com');
    const result = parseSessionToken(token);
    expect(result).not.toBeNull();
    expect(result?.email).toBe('user@example.com');
  });

  it('rejects a token older than MAX_AGE', () => {
    const token = createSessionToken('user@example.com');
    // Advance time by 8 days (past the 7-day max age)
    vi.advanceTimersByTime((MAX_AGE_SECONDS + 24 * 60 * 60) * 1000);
    expect(parseSessionToken(token)).toBeNull();
  });

  it('accepts a token just within MAX_AGE', () => {
    const token = createSessionToken('user@example.com');
    // Advance by 6 days 23 hours — still valid
    vi.advanceTimersByTime((MAX_AGE_SECONDS - 3600) * 1000);
    expect(parseSessionToken(token)).not.toBeNull();
  });

  it('rejects a tampered HMAC', () => {
    const token = createSessionToken('user@example.com');
    // Flip the last character of the HMAC
    const parts = token.split(':');
    const last = parts[parts.length - 1];
    parts[parts.length - 1] = last.slice(0, -1) + (last.endsWith('a') ? 'b' : 'a');
    expect(parseSessionToken(parts.join(':'))).toBeNull();
  });

  it('rejects a malformed token (too few segments)', () => {
    expect(parseSessionToken('notavalidtoken')).toBeNull();
    expect(parseSessionToken('')).toBeNull();
  });

  it('rejects a token with a tampered email', () => {
    const token = createSessionToken('user@example.com');
    // Replace email but keep rest — HMAC will fail
    const parts = token.split(':');
    parts[0] = 'evil@example.com';
    expect(parseSessionToken(parts.join(':'))).toBeNull();
  });
});
