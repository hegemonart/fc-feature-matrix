# Technology Stack

**Analysis Date:** 2026-04-16

## Languages

**Primary:**
- TypeScript 5 - Source code, configuration, and all production/test code
- JavaScript (JSX/TSX) - React component files

**Secondary:**
- YAML - CI/CD workflow definitions

## Runtime

**Environment:**
- Node.js 20 (specified in CI workflow, no `.nvmrc` in repo)

**Package Manager:**
- npm (inferred from `npm ci` in CI and package.json structure)
- Lockfile: `package-lock.json` (standard for npm)

## Frameworks

**Core:**
- Next.js 16.2.2 - Full-stack React framework with App Router, API routes, server components
- React 19.2.4 - UI component library
- React DOM 19.2.4 - Browser rendering

**Testing:**
- Vitest 2.1.8 - Unit and component test runner (configured in `vitest.config.ts`)

**Build/Dev:**
- ESLint 9 - Code linting (flat config via `eslint.config.mjs`)
- eslint-config-next 16.2.2 - Next.js linting rules
- TypeScript 5 - Type checking and compilation

## Key Dependencies

**Critical:**
- bcryptjs 3.0.3 - Password hashing and verification
- @types/bcryptjs 2.4.6 - TypeScript types for bcryptjs

**Infrastructure & External Services:**
- @upstash/redis 1.37.0 - Redis client for Upstash KV storage (analytics event persistence)
- resend 6.12.0 - Email service SDK for transactional emails
- @vercel/analytics 2.0.1 - Vercel Analytics tracking and reporting

**Development Dependencies:**
- @types/node 20 - Node.js type definitions
- @types/react 19 - React type definitions
- @types/react-dom 19 - React DOM type definitions

## Configuration

**Environment:**
- Environment variables required (loaded from `.env` or hosting platform):
  - `KV_REST_API_URL` - Upstash Redis endpoint
  - `KV_REST_API_TOKEN` - Upstash Redis authentication token
  - `RESEND_API_KEY` - Resend email service API key
  - `AUTH_SECRET` - HMAC secret for session signing (falls back to dev default in `lib/auth.ts`)
- `.env*` files not tracked in repository (standard practice)

**TypeScript:**
- Target: ES2017
- Strict mode: enabled (`strict: true` in `tsconfig.json`)
- Module resolution: bundler (Next.js optimized)
- JSX: react-jsx
- Path alias: `@/*` maps to project root
- Incremental compilation: enabled

**Build:**
- `next.config.ts` - Minimal Next.js configuration (template, no customizations)
- `vercel.json` - Vercel deployment metadata (specifies Next.js framework)

**Linting:**
- `eslint.config.mjs` - Flat config with Next.js preset, excludes non-core directories

**Testing:**
- `vitest.config.ts` - Test runner configuration with path alias matching, includes `**/*.{test,spec}.{ts,tsx}`

## Platform Requirements

**Development:**
- Node.js 20+
- npm (or compatible package manager)
- TypeScript knowledge required for development

**Production:**
- Vercel hosting platform (inferred from `vercel.json` and Analytics integration)
- Environment variables must be set in Vercel project settings

## Scripts

Available npm scripts (from `package.json`):
- `npm run dev` - Start Next.js development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript type checking (`tsc --noEmit`)
- `npm run test` - Run Vitest in single-run mode
- `npm run test:watch` - Run Vitest in watch mode
- `npm run concept` - Run concept subdirectory dev server

---

*Stack analysis: 2026-04-16*
