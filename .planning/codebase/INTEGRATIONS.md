# External Integrations

**Analysis Date:** 2026-04-16

## APIs & External Services

**Email Delivery:**
- Resend - Email service for access request notifications
  - SDK/Client: `resend` 6.12.0 npm package
  - Auth: `RESEND_API_KEY` environment variable
  - Usage: `app/api/email/route.ts` - sends access request emails to `hi@humbleteam.com`
  - Endpoint: POST `/api/email` - accepts feature name and source, rate-limited to 5 requests per IP per minute

**Analytics & Telemetry:**
- Vercel Analytics - Client-side web analytics
  - SDK/Client: `@vercel/analytics/next` 2.0.1
  - Integration: Embedded in `app/layout.tsx` as `<Analytics />` component
  - Purpose: Tracks page views, user interactions, performance metrics

## Data Storage

**Databases:**
- No database integration - data is file-based
  - User accounts: `data/users.json` - JSON file with bcrypt password hashes
  - Analytics events: Upstash Redis (optional, falls back to console logging)

**Redis/In-Memory Store:**
- Upstash Redis - Managed Redis for analytics events
  - Connection: REST API via `@upstash/redis` 1.37.0
  - Auth: `KV_REST_API_URL` and `KV_REST_API_TOKEN` environment variables
  - Usage: `lib/analytics.ts` - stores analytics events with lazy initialization
  - Key format: `analytics:events` (Redis list)
  - Fallback: Logs to console if Redis credentials not provided (local development)

**File Storage:**
- Local filesystem only - JSON files committed to repository
  - User data: `data/users.json`
  - Analysis results: `analysis/homepage/results/*.json` (per-club feature values)
  - Feature definitions: `analysis/homepage/features.ts` and `analysis/index.ts`

**Caching:**
- None - no explicit caching layer configured

## Authentication & Identity

**Auth Provider:**
- Custom - no external OAuth/SAML provider
  - Implementation: Session-based authentication in `lib/auth.ts`
  - Password hashing: bcryptjs (10 salt rounds)
  - Session tokens: HMAC-SHA256 signed tokens with email and timestamp
  - Storage: JSON file at `data/users.json` containing email, passwordHash, and name
  - Cookie-based: HttpOnly, SameSite=Lax, 7-day max age
  - API endpoints:
    - POST `/api/auth/login` - authenticate with email/password, returns session cookie
    - GET `/api/auth/me` - check current authentication status
    - POST `/api/auth/logout` - clear session cookie

**User Credentials:**
- Four hardcoded users in `data/users.json`:
  - sergey@humbleteam.com (Sergey)
  - admin@humbleteam.com (Admin)
  - atillyard@brentfordfc.com (A Tillyard)
  - thais.tsui@chelseafc.com (Thais Tsui)

## Monitoring & Observability

**Error Tracking:**
- None detected - no error tracking service integrated

**Logs:**
- Console logging fallback in `lib/analytics.ts` for development
- Email failures logged to console in `app/api/email/route.ts`
- Rate limit tracking: In-memory Map in `app/api/email/route.ts` (resets on server restart)

## CI/CD & Deployment

**Hosting:**
- Vercel - specified in `vercel.json` as Next.js framework
- Automatic deployments from git (standard Vercel workflow)

**CI Pipeline:**
- None detected - relying on Vercel's built-in build system

## Environment Configuration

**Required Environment Variables:**
- `RESEND_API_KEY` - Resend email service API key (production only)
- `KV_REST_API_URL` - Upstash Redis REST API endpoint (production analytics)
- `KV_REST_API_TOKEN` - Upstash Redis authentication token (production analytics)
- `AUTH_SECRET` - Session token signing secret (optional, defaults to development value if not set)

**Development Fallbacks:**
- `AUTH_SECRET` defaults to `'fc-benchmark-dev-secret-change-in-prod'` if not set
- Redis (KV_REST_API_*) is optional; events log to console if credentials missing
- Resend emails fail gracefully with error response if API key not configured

**Secrets Location:**
- Environment variables configured in Vercel dashboard for production
- Local development: Should be in `.env.local` (not committed)
- Never commit sensitive values; use Vercel dashboard or `.env.local`

## Webhooks & Callbacks

**Incoming:**
- POST `/api/email` - Accepts email requests from frontend (rate-limited)
  - Parameters: `feature` (requested feature name), `source` (origin/context)
  - Response: `{ ok: true }` or `{ error: string }`

**Outgoing:**
- Email callbacks: Resend sends emails to `hi@humbleteam.com` when access is requested
- No webhook callbacks to external services detected

## Data Flow

**Analytics Event Flow:**
1. Client action (login, page view, feature click) → `trackEvent()` in `lib/track.ts`
2. Event logged to `lib/analytics.ts` via `logEvent(type, email, data)`
3. If Redis configured: Push to `analytics:events` list via Upstash REST API
4. If Redis not configured: Log to console
5. Admin retrieves via `GET /api/analytics/view` (paginated, filterable by type/email)

**Email Request Flow:**
1. User clicks "Request Access" button on locked feature
2. Client calls `POST /api/email` with feature name
3. Rate limit check (5 per IP per minute)
4. Resend API sends email to `hi@humbleteam.com`
5. Response returned to client

---

*Integration audit: 2026-04-16*
