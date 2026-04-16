# Coding Conventions

**Analysis Date:** 2026-04-16

## Naming Patterns

**Files:**
- Route handlers: `route.ts` in folder structure (e.g., `app/api/auth/login/route.ts`)
- Components (React): PascalCase with `.tsx` extension (e.g., `CategoryFilter.tsx`, `ScrollRestore.tsx`)
- Utilities/modules: camelCase with `.ts` extension (e.g., `auth.ts`, `analytics.ts`, `scoring.ts`)
- Configuration: kebab-case (e.g., `next.config.ts`, `tsconfig.json`)
- JSON data files: snake_case (e.g., `real_madrid.json`, `fc_barcelona.json`)

**Functions:**
- camelCase for all function names
- Async functions explicitly labeled with `async` keyword
- Helper functions may use descriptive prefixes: `get*`, `load*`, `log*`, `create*`, `parse*`, `verify*`, `build*`, `compute*`, `generate*`

**Variables:**
- camelCase for local variables and constants
- SCREAMING_SNAKE_CASE for configuration constants that should not change (e.g., `COOKIE_NAME`, `MAX_AGE`, `EVENTS_KEY`, `MAX_EVENTS`)
- Implicit constant inference: `const` keyword is used, capitalization follows value type

**Types:**
- PascalCase for all interface and type names (e.g., `Feature`, `Product`, `Category`, `StoredUser`, `AnalyticsEvent`)
- Type suffixes optional but meaningful when used (e.g., `*Id`, `*Status`, `*Meta`)
- Type discriminant literals commonly used (e.g., `'full' | 'absent'` for `PresenceStatus`)

## Code Style

**Formatting:**
- No explicit formatter configured (Prettier not installed)
- ESLint v9 installed but no `.eslintrc` config file
- Uses Next.js ESLint config via `eslint-config-next` dependency
- Manual style adherence to TypeScript strict mode

**Linting:**
- ESLint v9 with Next.js configuration
- Command: `npm run lint` (runs `eslint` with default config)
- TypeScript strict mode enabled in `tsconfig.json`

**Indentation:**
- 2 spaces (inferred from source files)

## Import Organization

**Order:**
1. External libraries and Next.js built-ins (`import { NextRequest, NextResponse } from 'next/server'`)
2. Type imports (prefixed with `type`, e.g., `import type { Feature, CategoryId } from '@/lib/data'`)
3. Local modules with `@/` alias (e.g., `import { CATEGORIES, FEATURES } from '@/lib/data'`)
4. Component imports (e.g., `import CategoryFilter from './CategoryFilter'`)
5. Comments separating logical groups when multiple imports per group

**Path Aliases:**
- Single alias configured: `@/*` maps to root directory
- All imports use absolute `@/` paths (e.g., `@/lib/auth`, `@/analysis`, `@/lib/data`)
- Never use relative imports like `../../../`

**Type imports:**
- Use `import type { }` for type-only imports to improve build performance
- Example: `import type { Metadata } from 'next'`

## Error Handling

**Patterns:**
- Try-catch blocks wrap all async operations that may fail
- Catch blocks swallow errors with empty catch body `catch { }` when error is not critical
- Fire-and-forget patterns used for non-critical operations: `somePromise().catch(() => {})`
- Returns `null` for validation failures and not-found states (e.g., `parseSessionToken()` returns `null` on invalid token)
- Returns empty arrays or empty objects as defaults (e.g., `loadUsers()` returns `[]` on file read failure)
- HTTP handlers return appropriate status codes (400, 401, 404, 500)
- Generic error messages returned to client to avoid leaking implementation details (e.g., "Invalid email or password" instead of distinguishing user vs password failure)
- Console logging used for server-side errors as fallback (e.g., `console.error('[analytics] Failed to log event:', err)`)

## Logging

**Framework:** console (built-in Node.js `console` object)

**Patterns:**
- Server-side analytics logged via `logEvent()` helper in `lib/analytics.ts`
- Client-side tracking via `trackEvent()` helper in `lib/track.ts` (POST to `/api/analytics`)
- Log entries prefixed with scope in brackets: `console.log('[analytics]', ...)`, `console.error('[analytics] Failed...')`
- Analytics events are structured objects with `type`, `email`, `timestamp` fields
- Local dev fallback: if Redis/Upstash not available, events logged to console via `console.log('[analytics]', JSON.stringify(event))`
- Silent failures preferred for analytics (errors caught but not thrown)

## Comments

**When to Comment:**
- File headers document purpose and structure (e.g., `/* ================================================================ analysis/features.ts ... */`)
- Section dividers use ASCII art: `// ── Section Name ──`
- Inline comments rare; code should be self-documenting
- Comments explain "why" not "what" (the code shows what)
- Complex logic commented with context (e.g., tier floor logic in `computeBands()`)

**JSDoc/TSDoc:**
- Not consistently used
- Some functions have descriptive comments but no @param/@return decorators
- Example: multi-line comment above `logEvent()` in `analytics.ts` explains behavior without formal JSDoc
- Component prop types documented via interface definitions rather than JSDoc

## Function Design

**Size:**
- Small, focused functions preferred
- Utility functions typically 5-20 lines (e.g., `getRedis()`, `sign()`, `createSessionToken()`)
- Complex business logic like `generateClubSummary()` may be longer (100+ lines) but remains logically cohesive

**Parameters:**
- Named parameters via destructuring when objects passed (e.g., `{ email, password }` in route handlers)
- Options objects for functions with multiple optional params (e.g., `getEvents(opts: { limit?, type?, email? })`)
- Type annotations always present for parameters
- Default values used for optional parameters

**Return Values:**
- Explicit return types annotated on function declarations
- Promise return type for async functions
- Nullable types used where `null` is valid return (e.g., `{ email: string } | null`)
- Void return for side-effect-only functions (e.g., `trackEvent()`)

## Module Design

**Exports:**
- Named exports preferred for utilities and types (e.g., `export async function hashPassword()`, `export interface Feature`)
- Default exports used only for React components (e.g., `export default function RootLayout()`)
- Barrel files used to group related exports (e.g., `analysis/index.ts` re-exports from subdirectories)

**Barrel Files:**
- `lib/data.ts` re-exports from `@/analysis` for backward compatibility
- `analysis/index.ts` re-exports types, categories, products, features, and helper functions
- Simplifies consuming code: `import { FEATURES, PRODUCTS } from '@/lib/data'` instead of multiple imports

**File Organization:**
- Shared types in `analysis/types.ts`
- Per-page-type data in `analysis/{pageType}/` (currently only `homepage/`)
- Library utilities in `lib/` (auth, analytics, data, scoring, tracking, summary)
- App routes in `app/` with Next.js App Router structure
- API routes in `app/api/` following REST conventions

## Client/Server Boundaries

**Client Components:**
- Marked with `'use client'` directive (e.g., `CategoryFilter.tsx`, `PageTracker.tsx`)
- Used for interactive state and event handlers

**Server Components:**
- Default behavior in Next.js App Router
- Async components with `await params` pattern (e.g., `params: Promise<{ id: string }>`)
- Static generation with `generateStaticParams()` for dynamic routes
- Metadata generation with `generateMetadata()` for SEO

## Async/Await Patterns

- All async operations use async/await, not `.then()` chains
- Promise-based fire-and-forget operations use `.catch(() => {})` for error suppression
- No promise chaining; each async call awaited explicitly

---

*Convention analysis: 2026-04-16*
