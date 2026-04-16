# Coding Conventions

**Analysis Date:** 2026-04-16

## Naming Patterns

**Files:**
- React components: PascalCase (e.g., `CategoryFilter.tsx`, `PageTracker.tsx`)
- Utilities/libraries: camelCase (e.g., `scoring.ts`, `track.ts`, `auth.ts`)
- Test files: `[name].test.ts` suffix (e.g., `scoring.test.ts`)
- API routes: lowercase with hyphens in directory structure (`app/api/auth/login/route.ts`)

**Functions:**
- Exported functions: camelCase (e.g., `getProductScores()`, `trackEvent()`, `createSessionToken()`)
- Arrow functions in components: camelCase (e.g., `handleLogin()`, `handleCellMouseOver()`)
- Helper functions: camelCase (e.g., `bandColorVar()`, `bandLabel()`)

**Variables:**
- State variables: camelCase (e.g., `filterTypes`, `activeCat`, `selectedFeature`)
- Constants (module-level): camelCase or SCREAMING_SNAKE_CASE for config (e.g., `LOCKED_TABS`, `totalProducts`, `COOKIE_NAME`, `MAX_AGE`)
- Boolean state: prefixed with active/visible/is (e.g., `authed`, `loginModalVisible`, `featureAlphaSort`)

**Types:**
- Interfaces: PascalCase with `I` prefix avoided (e.g., `interface CatScore`, `interface FeatureData`, `StoredUser`)
- Type aliases: PascalCase (e.g., `type PresenceStatus`, `type CategoryId`, `type BandId`)
- Enums: Avoided in favor of literal unions and type aliases

## Code Style

**Formatting:**
- No Prettier configured; code follows Next.js/ESLint defaults
- Semicolons: Always present
- Quotes: Single quotes for strings
- Indentation: 2 spaces
- Max line length: No strict limit, but lines are typically kept under 100 characters

**Linting:**
- ESLint v9 with Next.js config (`eslint-config-next`)
- Config: `eslint.config.mjs` (flat config format)
- Run with: `npm run lint`
- Ignores: `concept/`, `references/`, `.claude/`, `sergey playground/`, `analysis/`

## Import Organization

**Order:**
1. External libraries (React, Next.js, third-party packages)
2. Type imports (marked with `type` keyword)
3. Local absolute imports (using `@/` alias)
4. Comments (ASCII art dividers like `/* ── ... ── */`)

**Path Aliases:**
- `@/` maps to project root (configured in `tsconfig.json`)
- Used for all local imports (e.g., `@/lib/data`, `@/lib/track`, `@/app/layout.tsx`)

**Example:**
```typescript
import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import {
  CATEGORIES,
  PRODUCTS,
  FEATURES,
  type PresenceStatus,
  type CategoryId,
} from '@/lib/data';
import { trackEvent } from '@/lib/track';
```

## Error Handling

**API Routes:**
- Wrapped in try-catch blocks catching all errors generically
- Return NextResponse.json with `{ error: string }` on failure
- Status codes: 400 (validation), 401 (auth), 500 (server error)
- Pattern: See `app/api/auth/login/route.ts`

**Client Code:**
- Fetch calls use `.catch(() => {})` for silent failures in analytics
- UI errors use `alert()` for user notification or state-based error displays
- Comments explain intent when silently failing (e.g., `// Silently fail — analytics should never break the app`)

**Example:**
```typescript
try {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: loginEmail, password: loginPassword }),
  });
  const data = await res.json();
  if (res.ok && data.ok) {
    setAuthed(true);
  } else {
    setLoginError(data.error || 'Login failed');
  }
} catch {
  setLoginError('Network error');
} finally {
  setLoginLoading(false);
}
```

## CSS Conventions

**Framework:** Plain CSS only, no Tailwind, no CSS-in-JS libraries
- All CSS in `app/globals.css` (single file)
- CSS custom properties for theming (e.g., `var(--bg)`, `var(--accent)`, `var(--green)`)
- BEM-like class naming (e.g., `.bd-feature-item`, `.col-header`)

**Colors:** Defined as CSS variables in `:root`:
```css
--bg: #0d0d14;
--accent: #4f6ef7;
--green: #22c55e;
--yellow: #eab308;
--orange: #f97316;
--red: #ef4444;
```

**Inline Styles:** Used sparingly for dynamic values (e.g., `style={{ color: bandColorVar(band) }}`)

## Logging

**Framework:** `console.log()` used directly, no logger library
- No explicit log level configuration observed
- Fire-and-forget pattern for analytics: `trackEvent()` function in `lib/track.ts`
- Analytics: POST to `/api/analytics` with event type and data
- Silent failures: `.catch(() => {})` used to prevent failures from breaking app

**Pattern:**
```typescript
export function trackEvent(type: string, data: Record<string, unknown> = {}): void {
  try {
    fetch('/api/analytics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, data }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // Silently fail — analytics should never break the app
  }
}
```

## Comments

**When to Comment:**
- Section dividers using ASCII art: `/* ── Section Name ── */`
- Explaining non-obvious logic (e.g., asymmetric scoring, cookie parsing)
- Warning about consequences (e.g., `// Silently fail — analytics should never break the app`)
- Rarely used for obvious code; let code be self-documenting

**JSDoc/TSDoc:**
- Used sparingly, mainly for utility functions
- Simple format: `/** [description] */`
- Example: `/** Client-side analytics helper. Fire-and-forget POST to /api/analytics. */`

**ASCII Dividers:**
Used to separate logical sections in large components and files:
```typescript
/* ── Padlock SVG (reused in flow nav) ── */
/* ── State ── */
/* ── Auth ── */
/* ── Derived data ── */
/* ── Handlers ── */
/* ── TABLE ROWS — separated to keep main component readable ── */
```

## TypeScript

**Strict Mode:** Enabled (`"strict": true` in `tsconfig.json`)
- All types must be explicit
- No implicit `any`
- Null/undefined must be handled explicitly

**Type Patterns:**
- Inline interfaces for component props (e.g., `interface CatScore { ... }`)
- Exported types from data modules (e.g., `type PresenceStatus`, `type CategoryId`)
- Re-export pattern in `lib/data.ts` for centralized type management

**Example:**
```typescript
export interface CatScore {
  id: CategoryId;
  name: string;
  color: string;
  got: number;
  total: number;
  pctCat: number;
  verdict: 'ok' | 'warning' | 'danger';
}
```

## Component Structure

**File Organization:**
- Inline components when simple and used once (e.g., `PadlockIcon()` in `app/page.tsx`)
- Separate `.tsx` files for reusable or moderately complex components (e.g., `CategoryFilter.tsx`, `PageTracker.tsx`)
- Props interface defined inline above component function
- Large components split with helper functions (see `app/page.tsx` with `TableRows()`, `FeatureDetail()`, `ProductDetail()`)

**Naming:**
- Export default for page components
- Named exports for helper functions within page components
- PascalCase function names for all components

**Pattern in `app/page.tsx`:**
```typescript
export default function FeatureMatrixPage() {
  // ... main component
}

function TableRows({ ... }) { ... }  // Helper, not exported
function FeatureDetail({ ... }) { ... }  // Helper, not exported
function ProductDetail({ ... }) { ... }  // Helper, not exported
```

## JSX Text Escaping

**Special Characters:**
- Unicode escapes used for special characters: `'\u2713'` (check), `'\u00B7'` (middle dot), `'\u00D7'` (times)
- Comment in code notes the JSX text literal fix: `//'` sequence escaped to prevent issues
- Example: `<div className="header-center">FC Benchmark <span>{'//'}</span> April 2026</div>`

---

*Convention analysis: 2026-04-16*
