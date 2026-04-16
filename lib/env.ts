import { z } from 'zod';

const isProd = process.env.NODE_ENV === 'production';

const envSchema = z.object({
  // Always required — runtime queries
  DATABASE_URL: z.string().min(1, 'DATABASE_URL is required'),

  // Required for migrations; may not be set in Vercel runtime (that's fine)
  DATABASE_URL_UNPOOLED: z.string().optional(),

  // Required in production; dev can use a local default
  AUTH_SECRET: isProd
    ? z.string().min(32, 'AUTH_SECRET must be at least 32 characters in production')
    : z.string().default('fc-benchmark-dev-secret-do-not-use-in-prod-xxxxxxxxxxxxxxxx'),

  // Optional — Resend integration; app degrades gracefully without it
  RESEND_API_KEY: z.string().optional(),

  // Required in production for the cron endpoint
  CRON_SECRET: isProd
    ? z.string().min(16, 'CRON_SECRET is required in production')
    : z.string().default('dev-cron-secret'),

  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

function parseEnv() {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    const formatted = result.error.issues
      .map((i) => `  - ${i.path.join('.')}: ${i.message}`)
      .join('\n');
    throw new Error(`Environment validation failed:\n${formatted}`);
  }
  return result.data;
}

export const env = parseEnv();
