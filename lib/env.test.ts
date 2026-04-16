import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Test the env schema logic directly, isolated from the module-level parseEnv() call
// (which already ran at import time with whatever env the test process has).

// Re-create the schema logic here to test it in isolation
function buildSchema(nodeEnv: 'development' | 'production' | 'test') {
  const isProd = nodeEnv === 'production';
  return z.object({
    DATABASE_URL: z.string().min(1),
    DATABASE_URL_UNPOOLED: z.string().optional(),
    AUTH_SECRET: isProd
      ? z.string().min(32)
      : z.string().default('fc-benchmark-dev-secret-do-not-use-in-prod-xxxxxxxxxxxxxxxx'),
    RESEND_API_KEY: z.string().optional(),
    CRON_SECRET: isProd
      ? z.string().min(16)
      : z.string().default('dev-cron-secret'),
    NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  });
}

describe('env schema', () => {
  describe('development / test mode', () => {
    const schema = buildSchema('development');

    it('passes with only DATABASE_URL set', () => {
      const result = schema.safeParse({ DATABASE_URL: 'postgresql://localhost/dev', NODE_ENV: 'development' });
      expect(result.success).toBe(true);
    });

    it('uses default AUTH_SECRET when not provided', () => {
      const result = schema.safeParse({ DATABASE_URL: 'postgresql://localhost/dev', NODE_ENV: 'development' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.AUTH_SECRET).toContain('dev-secret');
      }
    });

    it('fails when DATABASE_URL is missing', () => {
      const result = schema.safeParse({ NODE_ENV: 'development' });
      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.issues.map((i) => i.path[0]);
        expect(paths).toContain('DATABASE_URL');
      }
    });
  });

  describe('production mode', () => {
    const schema = buildSchema('production');

    it('fails when AUTH_SECRET is missing in production', () => {
      const result = schema.safeParse({
        DATABASE_URL: 'postgresql://prod/db',
        NODE_ENV: 'production',
        CRON_SECRET: 'a-valid-cron-secret',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.issues.map((i) => i.path[0]);
        expect(paths).toContain('AUTH_SECRET');
      }
    });

    it('fails when AUTH_SECRET is too short in production', () => {
      const result = schema.safeParse({
        DATABASE_URL: 'postgresql://prod/db',
        NODE_ENV: 'production',
        AUTH_SECRET: 'short',
        CRON_SECRET: 'a-valid-cron-secret',
      });
      expect(result.success).toBe(false);
    });

    it('passes with all required production fields set', () => {
      const result = schema.safeParse({
        DATABASE_URL: 'postgresql://prod/db',
        NODE_ENV: 'production',
        AUTH_SECRET: 'a-valid-secret-that-is-at-least-32-chars-long!',
        CRON_SECRET: 'a-valid-cron-secret',
      });
      expect(result.success).toBe(true);
    });

    it('fails when CRON_SECRET is missing in production', () => {
      const result = schema.safeParse({
        DATABASE_URL: 'postgresql://prod/db',
        NODE_ENV: 'production',
        AUTH_SECRET: 'a-valid-secret-that-is-at-least-32-chars-long!',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.issues.map((i) => i.path[0]);
        expect(paths).toContain('CRON_SECRET');
      }
    });
  });
});
