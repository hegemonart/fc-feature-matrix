import { z } from 'zod';

const isProd = process.env.NODE_ENV === 'production';

// During `next build`, Next.js sets NEXT_PHASE=phase-production-build.
// Env vars are available at runtime on Vercel, not necessarily at build time
// locally. We skip strict validation during the build phase so `npm run build`
// works in CI (where DATABASE_URL etc. are not set).
const isBuildPhase = process.env.NEXT_PHASE === 'phase-production-build';

const envSchema = z.object({
  // Always required at runtime; relaxed during build
  DATABASE_URL: isBuildPhase
    ? z.string().default('')
    : z.string().min(1, 'DATABASE_URL is required'),

  // Required for migrations; may not be set in Vercel runtime (that's fine)
  DATABASE_URL_UNPOOLED: z.string().optional(),

  // Required in production at runtime; relaxed during build
  AUTH_SECRET: isBuildPhase
    ? z.string().default('build-phase-placeholder')
    : isProd
      ? z.string().min(32, 'AUTH_SECRET must be at least 32 characters in production')
      : z.string().default('fc-benchmark-dev-secret-do-not-use-in-prod-xxxxxxxxxxxxxxxx'),

  // Optional — Resend integration
  RESEND_API_KEY: z.string().optional(),

  // Required in production at runtime; relaxed during build
  CRON_SECRET: isBuildPhase
    ? z.string().default('build-phase-placeholder')
    : isProd
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
