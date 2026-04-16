# Technology Stack

**Analysis Date:** 2026-04-16

## Languages

**Primary:**
- TypeScript 5.x - Application code, type definitions, API routes
- JavaScript (ES2017+) - Build scripts, utilities

**Secondary:**
- CSS - Styling (globals.css in `app/`)
- JSON - Data configuration

## Runtime

**Environment:**
- Node.js (version not pinned - uses modern 20.x LTS compatible)
- Browser: React 19.2.4 client-side components

**Package Manager:**
- npm 9.x+ (inferred from lockfileVersion 3)
- Lockfile: `package-lock.json` (present)

## Frameworks

**Core:**
- Next.js 16.2.2 - Full-stack React framework for SSR, API routes, file-based routing
- React 19.2.4 - UI component framework
- React DOM 19.2.4 - DOM rendering

**Build/Dev:**
- TypeScript 5.x - Type checking and compilation
- ESLint 9.x - Code linting
- eslint-config-next 16.2.2 - Next.js linting rules

## Key Dependencies

**Critical:**
- @vercel/analytics 2.0.1 - Client-side analytics tracking via Vercel
- bcryptjs 3.0.3 - Password hashing for authentication (`lib/auth.ts`)
- @types/bcryptjs 2.4.6 - Type definitions for bcryptjs

**Infrastructure:**
- @upstash/redis 1.37.0 - Redis client for event analytics (`lib/analytics.ts`)
- resend 6.12.0 - Email service client for sending access requests (`app/api/email/route.ts`)

## Configuration

**Environment:**
- Next.js config: `next.config.ts` (minimal, no custom config)
- Deployment: Vercel (framework specified in `vercel.json`)
- TypeScript compiler: `tsconfig.json` with strict mode enabled

**Build:**
- Entry point: `app/layout.tsx` (root layout)
- Output: `.next/` directory (standard Next.js build output)
- Public assets: `public/` directory

**Required Environment Variables:**
- `RESEND_API_KEY` - API key for Resend email service
- `KV_REST_API_URL` - Upstash Redis REST API endpoint
- `KV_REST_API_TOKEN` - Upstash Redis authentication token
- `AUTH_SECRET` - Secret for session token signing (defaults to development value if not set)

## Platform Requirements

**Development:**
- Node.js 20.x LTS or later
- npm 9.x or later
- TypeScript 5.x support
- Next.js 16.2.2 compatible environment

**Production:**
- Deployment target: Vercel (specified in `vercel.json`)
- Requires: Node.js 18.x or later
- Environment variables must be configured in Vercel dashboard

## Build & Dev Commands

```bash
npm run dev      # Start development server (localhost:3000)
npm run build    # Production build
npm start        # Start production server
npm run lint     # Run ESLint
```

## TypeScript Configuration

**Compiler Options:**
- Target: ES2017
- Module: esnext (bundled by Next.js)
- Strict mode: enabled
- Module resolution: bundler
- Path aliases: `@/*` → project root

**Notable Settings:**
- `skipLibCheck: true` - Skip type checking for node_modules
- `resolveJsonModule: true` - Import JSON files directly
- `isolatedModules: true` - Ensure each file compiles independently

---

*Stack analysis: 2026-04-16*
