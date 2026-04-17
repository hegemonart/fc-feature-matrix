---
phase: infra-redesign-v2
plan: 01
subsystem: infra
tags: [design-tokens, css-variables, next-font, inter-tight, roboto-mono, playwright, visual-regression, vitest, font-readiness]

# Dependency graph
requires:
  - phase: bootstrap
    provides: Next.js app shell, app/globals.css, app/layout.tsx
provides:
  - neutral-dark + brand-orange design-token system in :root
  - --bg1 legacy alias preserving .login-input + .analytics-filters select
  - Inter Tight + Roboto Mono via next/font (CSS vars --font-body / --font-mono)
  - .mono-caption helper class for HeaderBar (10px / 13px / -1px tracking)
  - process.env.BUILD_DATE (ISO date slice) baked at build time
  - Playwright + chromium + playwright.config.ts with maxDiffPixelRatio 0.02
  - tests/visual/homepage.spec.ts scaffold (skipped until plan 04)
  - tests/setup-fonts.ts + tests/fonts.test.ts (jsdom-safe font assertion)
  - tests/components/ directory gate
affects: [infra-redesign-v2-02, infra-redesign-v2-03, infra-redesign-v2-04, infra-redesign-v2-05, redesign-rollout]

# Tech tracking
tech-stack:
  added: ["@playwright/test", "next/font/google (Inter Tight, Roboto Mono)"]
  patterns:
    - "Design tokens via CSS custom properties in :root with semantic + status palettes separated"
    - "Legacy aliases (--bg, --bg1, --bg2, --bg3) point at new tokens so downstream consumers migrate gracefully"
    - "Build-time env vars (BUILD_DATE) for hydration-safe values"
    - "next/font CSS vars exposed via html.className"
    - "Visual-regression scaffold with .skip until baseline-ready"

key-files:
  created:
    - playwright.config.ts
    - tests/visual/homepage.spec.ts
    - tests/setup-fonts.ts
    - tests/fonts.test.ts
    - tests/components/.gitkeep
    - .planning/phases/infra-redesign-v2/01-SUMMARY.md
  modified:
    - app/globals.css
    - app/layout.tsx
    - next.config.ts
    - vitest.config.ts
    - .gitignore
    - package.json
    - package-lock.json
    - README.md
    - CHANGELOG.md

key-decisions:
  - "Kept legacy --bg/--bg1/--bg2/--bg3 aliases pointing at new tokens (graceful downstream migration)"
  - "next/font/google Inter Tight as default; Suisse Int'l swap path documented in app/layout.tsx comment for owner-only opt-in"
  - "Playwright scaffold ships .skip; baseline PNG deferred to plan 04 once homepage refactor lands"
  - "Vitest config excludes tests/visual/** so Playwright specs don't get picked up by the wrong runner"

patterns-established:
  - "CSS-token rename strategy: introduce new semantic names + alias the old names so consumers can migrate plan-by-plan"
  - "Hydration-safe build metadata via process.env.BUILD_DATE in next.config.ts env block"
  - "jsdom-safe font assertion: gate document.fonts checks behind hasFontFaceSet() so vitest passes in jsdom + enforces in browser"

requirements-completed: [D-01, D-02, D-04, D-07, D-08, D-09, D-12, D-26, D-27]

# Metrics
duration: ~25min
completed: 2026-04-17
---

# Phase infra-redesign-v2 Plan 01: Foundation Summary

**Neutral-dark + brand-orange design-token system, Inter Tight + Roboto Mono via next/font, BUILD_DATE env, and Playwright visual-regression scaffold — Wave 0 gate for the visual redesign.**

## Performance

- **Duration:** ~25 min (resumed mid-plan; previous agent had completed token edit but not committed)
- **Started:** 2026-04-17T07:09:00Z (resume)
- **Completed:** 2026-04-17T07:18:00Z
- **Tasks:** 6/6
- **Files modified:** 11 (5 created, 6 modified)

## Accomplishments

- Replaced cool-blue palette (`--accent #4f6ef7`, `--bg #0d0d14`, …) with neutral-dark + brand-orange (`--accent #FF490C`, `--bg-page #0F0F0F`, `--bg-cell #1A1A1A`, `--bg-hover #383838`, `--border #262626`, `--column-tint rgb(51,24,15)`, `--text #FFFFFF`, `--muted #ABABAB`)
- Added legacy `--bg`/`--bg1`/`--bg2`/`--bg3` aliases so `.login-input`, `.analytics-filters select`, `.locked-card`, etc. keep working until plans 02–04 migrate them
- Wired Inter Tight (body) + Roboto Mono (caption) through `next/font/google`; CSS vars exposed via `html.className`; body `letter-spacing: -0.32px` per RESEARCH.md
- Added `.mono-caption` helper (10px / 13px / -1px tracking) ready for plan 02-04 HeaderBar
- Exported `process.env.BUILD_DATE` from `next.config.ts` (ISO slice) for hydration-safe `<HeaderBar>` build-date span (D-12)
- Installed Playwright + chromium; `playwright.config.ts` with `colorScheme: 'dark'`, `maxDiffPixelRatio: 0.02`; `tests/visual/homepage.spec.ts` scaffold (skipped until plan 04)
- Added `tests/setup-fonts.ts` + `tests/fonts.test.ts` (jsdom-safe FontFaceSet assertion); `tests/components/.gitkeep` directory gate
- Final D-27 gate green: `npx next build` passes, `npm test` 18/18 pass

## Task Commits

1. **Task 01-01: Token swap + lock-icon tint + --bg1 alias** — `462b7d6` (refactor)
2. **Task 01-02: Inter Tight + Roboto Mono via next/font** — `730f2ea` (feat)
3. **Task 01-03: BUILD_DATE env in next.config.ts** — `b395a7a` (feat)
4. **Task 01-04: Playwright + visual-regression scaffold** — `cab2480` (test)
5. **Task 01-05: Font-readiness harness + components dir gate** — `b5ecb69` (test)
6. **Task 01-06: CHANGELOG v7.0 + README test-dir structure** — `995e86e` (docs)

**Plan metadata:** (created after this SUMMARY)

## Files Created/Modified

### Created
- `playwright.config.ts` — Playwright runner config (testDir tests/visual, dark color scheme, 2% max diff ratio)
- `tests/visual/homepage.spec.ts` — Visual-regression scaffold (skipped until plan 04 baseline)
- `tests/setup-fonts.ts` — `hasFontFaceSet()` + `waitForFontsReady()` helpers (jsdom-safe)
- `tests/fonts.test.ts` — Vitest spec asserting Inter Tight + Roboto Mono load after readiness
- `tests/components/.gitkeep` — Empty dir gate for plans 02–03 component specs
- `.planning/phases/infra-redesign-v2/01-SUMMARY.md` — This file

### Modified
- `app/globals.css` — `:root` token swap, body font/letter-spacing, `.mono-caption`, lock-icon tint
- `app/layout.tsx` — `next/font` Inter Tight + Roboto Mono import, html.className font vars
- `next.config.ts` — `env: { BUILD_DATE }` block
- `vitest.config.ts` — Exclude `tests/visual/**` so Playwright specs are not picked up
- `.gitignore` — Playwright report + test-results paths
- `package.json` / `package-lock.json` — `@playwright/test` devDep
- `README.md` — Project-structure block lists `tests/visual/`, `tests/components/`, `tests/fonts.test.ts`, `tests/setup-fonts.ts`, `playwright.config.ts`
- `CHANGELOG.md` — v7.0 entry at top (foundation system + test infra)

## Decisions Made

- **Kept legacy CSS-var aliases** (`--bg`, `--bg1`, `--bg2`, `--bg3`) pointing at new semantic tokens. Lets plans 02–04 migrate consumers class-by-class instead of needing a single big-bang refactor in this plan.
- **Inter Tight as the green-light default.** Sergey's Suisse Int'l decision is pending; the swap path is one-file via `next/font/local` per RESEARCH.md §"Alternate snippet" and is documented inline in `app/layout.tsx`.
- **`tests/visual/homepage.spec.ts` ships `.skip`'d.** Capturing a baseline now would be invalidated by plans 02–04. The scaffold compiles and `npx playwright test --list` recognizes it; plan 04 unskips after the homepage refactor lands.
- **CHANGELOG bumped to v7.0** (not 6.1) because this is a major foundation introducing a new design-token system, typography stack, and test infrastructure — the project's "minor vs major" rule in CLAUDE.md classifies new tooling and rubric/system changes as major.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing node_modules in worktree**
- **Found during:** Task 01-01 verification (`npx next build`)
- **Issue:** Worktree had no `node_modules/` directory, so the Turbopack build failed with `Module not found: Can't resolve '@neondatabase/serverless'` (and 14 similar errors for `drizzle-orm`, `zod`, etc.). This was a worktree-bootstrap gap, not a code issue caused by the token swap.
- **Fix:** Ran `npm install` in the worktree root (455 packages added).
- **Files modified:** None (created `node_modules/`, gitignored).
- **Verification:** `npx next build` then succeeded.
- **Committed in:** N/A (no source change; lockfile unchanged at this step).

**2. [Rule 3 - Blocking] Excluded `tests/visual/**` from vitest discovery**
- **Found during:** Task 01-04 (Playwright scaffold)
- **Issue:** `vitest.config.ts` had `include: ['**/*.{test,spec}.{ts,tsx}']`. Without an exclude, vitest would try to run `tests/visual/homepage.spec.ts` and fail because that file imports `@playwright/test` (incompatible with vitest globals).
- **Fix:** Added `'tests/visual/**'` to the `exclude` array in `vitest.config.ts`.
- **Files modified:** `vitest.config.ts`
- **Verification:** `npm test` (full suite) shows 5 test files / 18 tests passing; `tests/visual/homepage.spec.ts` is correctly skipped by vitest. `npx playwright test --list tests/visual/homepage.spec.ts` correctly lists 1 test.
- **Committed in:** `cab2480` (folded into the task 01-04 commit).

**3. [Rule 2 - Missing Critical] Added Playwright artifact paths to `.gitignore`**
- **Found during:** Task 01-04 (Playwright scaffold)
- **Issue:** Plan didn't call out gitignore. Without it, future `playwright test` runs would dirty the worktree with `playwright-report/`, `test-results/`, `blob-report/`, and `playwright/.cache/` paths — would break the `git diff --quiet analysis/homepage/results/` D-28 invariant noise check and pollute commits.
- **Fix:** Added the four standard Playwright paths under a `# Playwright (D-26)` heading in `.gitignore`.
- **Files modified:** `.gitignore`
- **Verification:** `git status` after `npx playwright test --list` shows no untracked Playwright artifacts.
- **Committed in:** `cab2480` (folded into the task 01-04 commit).

---

**Total deviations:** 3 auto-fixed (1 missing critical, 2 blocking)
**Impact on plan:** All three were necessary to keep the verification gates green and to avoid future-plan pollution. No scope creep, no architectural change.

## Issues Encountered

- **Workspace-root warning:** `npx next build` emits a warning about multiple lockfiles (parent repo `package-lock.json` + worktree `package-lock.json`) and inferred root. Build still passes. Cleanest long-term fix is to set `turbopack.root` in `next.config.ts` once the worktree merges back to master — left for later (out of scope for this plan).
- **CRLF/LF warnings on commit:** Git autocrlf normalized line endings on the new TS files. Cosmetic only; no behavioral impact.

## User Setup Required

None. All deps installable via standard `npm install`; no external service config; Sergey's Suisse Int'l font opt-in is documented in `app/layout.tsx` and remains optional.

## Next Phase Readiness

- **Wave 0 gate cleared.** All downstream plans (02 components, 03 cell-tooltip, 04 homepage refactor, 05 club-detail rollout) have what they need:
  - Design tokens: `--accent`, `--bg-page`, `--bg-cell`, `--bg-hover`, `--border`, `--column-tint`, `--text`, `--muted` all available
  - Typography: `var(--font-body)`, `var(--font-mono)`, `.mono-caption` helper
  - HeaderBar build-date: `process.env.BUILD_DATE` ready
  - Visual-regression: `tests/visual/` directory + Playwright config; plan 04 unskips and captures baseline
  - Component tests: `tests/components/` directory ready for plans 02–03 to drop specs into
- **Decision still pending (non-blocking):** Suisse Int'l vs Inter Tight (owner-only). Default green-light path shipped; one-file swap if Sergey opts in before phase merge.

## Self-Check: PASSED

- All 6 claimed created files exist on disk.
- All 6 task commits (462b7d6, 730f2ea, b395a7a, cab2480, b5ecb69, 995e86e) exist in `git log`.
- D-28 invariant verified: `git diff --quiet HEAD analysis/homepage/results/` returns clean.
- `npx next build`: passes.
- `npm test`: 18/18 pass.

---
*Phase: infra-redesign-v2*
*Completed: 2026-04-17*
