# Code Conventions

## Naming

**Files**
- Next.js App Router conventions: `page.tsx`, `layout.tsx`, `globals.css`
- Dynamic segments use bracket notation: `app/club/[id]/page.tsx`
- Library modules are lowercase with no separators: `lib/data.ts`, `lib/scoring.ts`
- Utility scripts use camelCase `.mjs`: `capture.mjs`, `recapture.mjs`, `recapture2.mjs`

**Components**
- PascalCase for React components: `FeatureMatrixPage`, `TableRows`, `FeatureDetail`, `ProductDetail`
- Sub-components defined in the same file as the page when tightly coupled
- Icon components use `Icon` suffix: `PadlockIcon`

**Functions**
- Event handlers are prefixed with `handle`: `handleShowFeatureDetail`, `handleClearFilters`, `handleCellMouseOver`, `handleLockedTabClick`
- Utility functions are camelCase: `getProductScores`, `getRankedProducts`, `bandColorVar`
- React hooks follow `use` prefix: `useMemo`, `useState`, `useRef`, `useCallback`

**Variables & Constants**
- Module-level constants are SCREAMING_SNAKE_CASE: `CATEGORIES`, `PRODUCTS`, `FEATURES`, `BAND_META`, `ALL_IDS`, `LOCKED_TABS`, `WEIGHT_LABELS`
- Local variables are camelCase: `visibleProds`, `visibleFeats`, `bandCounts`, `catCounts`
- Type aliases are PascalCase: `PresenceStatus`, `CategoryId`, `BandId`, `ProductType`, `SportType`
- Interfaces are PascalCase: `Category`, `Product`, `Feature`, `BandMeta`

**CSS Classes**
- BEM-adjacent kebab-case: `.matrix-shell`, `.detail-panel`, `.freq-bar-wrap`, `.cat-sep-inner`
- State modifiers as bare class additions: `.active`, `.highlighted`, `.collapsed`, `.visible`
- Band/status classes use the raw data ID as the class name: `.table_stakes`, `.expected`, `.competitive`, `.innovation`
- Weight classes use `w` prefix: `.w1` through `.w5`

## TypeScript

**Strictness**
- `"strict": true` in tsconfig — full strict mode enabled
- `noEmit: true` (compile checking only, Next.js handles bundling)
- `isolatedModules: true`
- `skipLibCheck: true`
- Target `ES2017`, moduleResolution `bundler`

**Patterns Used**
- Type aliases for union strings: `type PresenceStatus = 'full' | 'partial' | 'absent'`
- Interfaces for data shapes: `interface Feature { ... }`
- Optional properties with JSDoc `/** Computed by computeBands() */` to explain deferred fields
- `Record<string, PresenceStatus>` for dynamic key maps
- Inline type assertions with `!` non-null when data presence is guaranteed: `CATEGORIES.find(c => c.id === f.cat)!`
- `React.ReactNode[]` for dynamically built JSX arrays
- Async page components use `Promise<{ id: string }>` for Next.js 16 params

**Type Organization**
- All shared types and constants live in `lib/data.ts` — single source of truth
- Types are exported alongside the constants that use them
- Scoring utilities in `lib/scoring.ts` import types from `lib/data.ts`

## Component Patterns

**Structure**
- Page components are `export default` functions, named descriptively (not just `Page`)
- Sub-components that are only used by one page are co-located in the same file, defined after the default export
- Sub-components accept props via inline destructuring with an inline type literal, not a named interface:
  ```ts
  function TableRows({ feats, prods, ... }: { feats: Feature[]; prods: Product[]; ... })
  ```
- Component sections separated by large ASCII banner comments: `/* === FEATURE DETAIL === */`

**State Management**
- All state lives in the top-level page component; sub-components receive callbacks
- `useCallback` wraps every event handler passed as a prop
- `useMemo` used for all derived/filtered data
- `useRef` for DOM access (tooltip positioning, search input reset)

**Server vs Client**
- `app/page.tsx` is a Client Component (`'use client'` directive at top)
- `app/club/[id]/page.tsx` is a Server Component (no `'use client'`, uses `async/await`)
- `app/layout.tsx` is a Server Component with static metadata export

**Exports**
- Page components: default export only
- Library modules: named exports only (no default export in `lib/data.ts` or `lib/scoring.ts`)

## Import Style

**Path Aliases**
- `@/*` maps to the repo root (configured in tsconfig `paths`)
- Used as `@/lib/data`, `@/lib/scoring` — never relative paths for `lib/` imports

**Import Ordering** (observed pattern, no enforcer configured)
1. React hooks
2. `@/lib/*` module imports (data, scoring)
3. Next.js imports (`next/navigation`, `next/link`)
4. Type-only imports grouped with regular imports using `type` keyword inline: `import { ..., type Feature, type Product } from '@/lib/data'`

**No Barrel Files**
- No `index.ts` re-export files; modules are imported directly by path

## Styling

**Approach**
- Single global stylesheet: `app/globals.css`
- No CSS Modules, no Tailwind, no CSS-in-JS
- All styles are flat classes in the global file — no scoping mechanism
- Inline `style` props used for dynamic values (colors, widths, percentages)

**CSS Custom Properties**
- All colors, backgrounds, and borders defined as CSS variables on `:root`
- Semantic names: `--bg`, `--bg2`, `--bg3`, `--border`, `--text`, `--muted`, `--accent`
- Semantic color names: `--green`, `--yellow`, `--orange`, `--red`
- Alpha variants: `--green-bg`, `--red-bg`, etc. (rgba with 0.12 opacity)
- Category colors also stored as vars: `--cat-red`, `--cat-blue`, etc.

**Theming**
- Dark-only design — no light mode, no media query for `prefers-color-scheme`
- `prefers-reduced-motion` media query present and respected
- System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

**Class Naming Conventions**
- Page-specific prefixes used to avoid collision: `.bd-` (breakdown/detail page), `.matrix-shell` (main page)
- Layout wrappers: `-shell`, `-wrap`, `-inner`, `-row`, `-grid`
- Interactive states appended as modifier classes (not `--modifier` BEM): `.active`, `.highlighted`, `.visible`, `.collapsed`

## Linting & Formatting

**ESLint**
- `eslint` v9 + `eslint-config-next` v16.2.2
- No custom config file found (`.eslintrc`, `eslint.config.*`) — relies entirely on Next.js defaults
- `next lint` is run via `npm run lint` (calls `eslint` directly, Next.js config picked up automatically)

**Prettier**
- No Prettier config file found (`.prettierrc`, `prettier.config.*`)
- No Prettier dependency in `package.json`
- Not used in this project

**TypeScript**
- Type checking available via `tsc --noEmit`, but no dedicated `typecheck` script in `package.json`
- Next.js build (`npm run build`) performs type checking implicitly
