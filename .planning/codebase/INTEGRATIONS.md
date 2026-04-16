# External Integrations

**Analysis Date:** 2026-04-16

## APIs & External Services

**Email Delivery:**
- Resend - Transactional email service
  - SDK/Client: `resend` package (v6.12.0)
  - Auth: `RESEND_API_KEY` environment variable
  - Implementation: `app/api/email/route.ts` - POST endpoint for sending access request emails
  - Usage: Sends notification emails to `hi@humbleteam.com` with reply-to set to requester email if provided

**Analytics:**
- Vercel Analytics - Web analytics and performance monitoring
  - SDK/Client: `@vercel/analytics/next` package (v2.0.1)
  - Implementation: `app/layout.tsx` - `<Analytics />` component in root layout
  - Automatically captures page views, Core Web Vitals, and user interactions
  - No explicit configuration required (uses Vercel defaults)

## Data Storage

**Databases:**
- None (no traditional database required)

**File Storage:**
- Local filesystem (JSON-based user store)
  - Location: `data/users.json`
  - Format: JSON array of user objects with `email`, `passwordHash`, and optional `name`
  - Access: Loaded in-memory via `lib/auth.ts` functions `loadUsers()` and `getUsersFilePath()`
  - Committed: Yes, checked into version control with sample/seeded data

**Caching:**
- Upstash Redis (KV store)
  - Provider: Upstash (serverless Redis)
  - Connection: `KV_REST_API_URL` and `KV_REST_API_TOKEN` environment variables
  - Client: `@upstash/redis` package (v1.37.0) - `Redis` class with REST API
  - Usage: Analytics event storage
    - Implementation: `lib/analytics.ts`
    - Stores events in list at key `analytics:events`
    - Max capacity: 10,000 events (FIFO with `ltrim`)
    - Fallback: Logs to console if Redis credentials unavailable (dev mode)

## Authentication & Identity

**Auth Provider:**
- Custom (no external OAuth provider)

**Implementation:**
- Password-based authentication with sessions
  - Password hashing: `bcryptjs` package (v3.0.3)
    - Hash function: `hashPassword()` in `lib/auth.ts` (10 salt rounds)
    - Verification: `verifyPassword()` uses bcrypt comparison
  - Session tokens: HMAC-SHA256 signed tokens
    - Token format: `{email}:{timestamp}:{signature}`
    - Signing key: `AUTH_SECRET` environment variable (falls back to dev default)
    - Session duration: 7 days (MAX_AGE = 604800 seconds)
  - Cookie-based sessions:
    - Cookie name: `fc_session`
    - Flags: HttpOnly, SameSite=Lax
    - Helpers: `sessionCookieHeader()`, `clearSessionCookieHeader()`, `getSessionFromCookie()`
  - User store: `data/users.json` - JSON file with plaintext user records (must be protected in production)
  - Session validation: `parseSessionToken()` verifies signature before accepting session

## Monitoring & Observability

**Error Tracking:**
- None (no dedicated error tracking service)

**Logs:**
- Console logging only
  - Analytics: Falls back to `console.log()` when Redis unavailable
  - Errors: `console.error()` for analytics and email failures
  - No persistent logging system

## CI/CD & Deployment

**Hosting:**
- Vercel - Serverless platform for Next.js applications
  - Configuration: `vercel.json` specifies `"framework": "nextjs"`
  - Automatic deployments on push to `master` branch

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
  - Triggers: On push to `master` and pull requests to `master`
  - Node version: 20
  - Steps:
    1. Checkout code (`actions/checkout@v4`)
    2. Setup Node.js with npm cache (`actions/setup-node@v4`)
    3. Install dependencies (`npm ci`)
    4. Lint code (`npm run lint`)
    5. Type check (`npm run typecheck`)
    6. Run tests (`npm test`)
    7. Build application (`npm run build`)
  - All steps must pass before deployment
  - Environment: ubuntu-latest

## Environment Configuration

**Required env vars (critical):**
- `KV_REST_API_URL` - Upstash Redis REST endpoint
- `KV_REST_API_TOKEN` - Upstash Redis authentication token
- `RESEND_API_KEY` - Resend email API key
- `AUTH_SECRET` - HMAC secret for session tokens (optional, has dev default)

**Secrets location:**
- Vercel project settings (recommended for production)
- `.env.local` file (for local development, not committed)
- Environment variables must be manually set in Vercel dashboard or via CLI

**Local development fallbacks:**
- Upstash Redis: Gracefully degrades to console logging if credentials missing
- Resend: Will fail if `RESEND_API_KEY` not provided (no fallback)
- Auth: Uses hardcoded dev secret if `AUTH_SECRET` not set

## Webhooks & Callbacks

**Incoming:**
- None (API is request-response only)

**Outgoing:**
- Email notifications (triggered by `POST /api/email`)
  - Sends to: `hi@humbleteam.com`
  - Triggered by: User access requests
  - Includes optional reply-to if requester email provided
  - Rate limiting: 5 requests per IP per minute (in-memory tracking in `app/api/email/route.ts`)

---

*Integration audit: 2026-04-16*
