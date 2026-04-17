---
phase: infra-redesign-v2
plan_id: 01
wave: 0
depends_on: []
files_modified:
  - package.json
  - package-lock.json
  - playwright.config.ts
  - next.config.ts
  - app/layout.tsx
  - app/globals.css
  - tests/setup-fonts.ts
  - tests/fonts.test.ts
  - tests/visual/homepage.spec.ts
  - tests/components/.gitkeep
  - CHANGELOG.md
  - README.md
autonomous: true
decisions_addressed: [D-01, D-02, D-04, D-07, D-08, D-09, D-27]
must_haves:
  - '`app/globals.css` `:root` block replaced: `--bg-page #0F0F0F`, `--bg-cell #1A1A1A`, `--bg-hover #383838`, `--border #262626`, `--accent #FF490C`, `--column-tint rgb(51,24,15)`, `--text #FFFFFF`, `--muted #ABABAB`.'
  - 'Legacy `--bg1` alias added (`--bg1: var(--bg-cell);`) so `.login-input` keeps working (RESEARCH.md P1).'
  - 'Hard-coded blue tint `rgba(79,110,247,.12)` on `.locked-card .lock-big` replaced with `rgba(255,73,12,.12)`.'
  - 'Inter Tight + Roboto Mono wired through `next/font/google` in `app/layout.tsx`; CSS vars `--font-body` / `--font-mono` exposed via `html.className`.'
  - '`body { letter-spacing: -0.32px; }` (Inter Tight compensation per RESEARCH.md).'
  - '`process.env.BUILD_DATE` exported from `next.config.ts` (ISO date slice).'
  - '`@playwright/test` installed as devDependency; `playwright.config.ts` targets `tests/visual/` with `maxDiffPixelRatio: 0.02` and `colorScheme: "dark"`.'
  - '`tests/setup-fonts.ts` awaits `document.fonts.ready`; `tests/fonts.test.ts` asserts Inter Tight + Roboto Mono are loaded.'
  - '`tests/visual/homepage.spec.ts` scaffold exists (baseline PNG captured after homepage refactor in plan 04 — scaffold ships disabled via `.skip` for this plan).'
  - '`tests/components/` directory present (empty gate for plans 02–03 to drop specs into).'
  - '`npx next build` passes. `npm test` passes. No regression in `lib/scoring.test.ts`.'
  - 'CHANGELOG.md v6.0 entry at top (major — new design-token system + test infra).'
---

<objective>
Lay the foundation for the full visual redesign. Wave 0 gate — every downstream plan depends on this one. Replace the cool-blue `:root` design tokens in `app/globals.css` with the neutral-dark + brand-orange palette from Figma (D-01, D-02, D-04). Wire Inter Tight + Roboto Mono through `next/font` as the default type stack (D-07, D-08, D-09 — default path per RESEARCH.md; Sergey may opt in to paid Suisse Int'l before plan 01 merges, in which case one-file swap in `app/layout.tsx` per RESEARCH.md §"Alternate snippet"). Install Playwright for visual regression (D-26 tooling only — spec scaffold is `.skip`'d until plan 04 lands the homepage). Verify `npx next build` + `npm test` green (D-27). Ship legacy `--bg1: var(--bg-cell);` alias so the modal CSS in `app/globals.css:309` does not break. Set `process.env.BUILD_DATE` now so `<HeaderBar>` in plan 02 has it available (RESEARCH.md P4).
</objective>

<tasks>

<task>
  <id>01-01</id>
  <description>Replace `:root` token block + fix blue lock-icon tint + add `--bg1` alias in `app/globals.css`. Swap `--accent #4f6ef7` (blue) for `#FF490C` (orange). Replace `--bg #0d0d14`/`--bg2 #13131e`/`--bg3 #1a1a28` with `--bg-page #0F0F0F`/`--bg-cell #1A1A1A`/`--bg-hover #383838`. Replace `--border #252535` with `--border #262626`. Add `--column-tint: rgb(51, 24, 15)` (D-03 token definition — consumed in plan 03). Replace `--text #e8e8f0` with `--text #FFFFFF`; `--muted #6b6b8a` with `--muted #ABABAB`. Add `--bg1: var(--bg-cell);` for legacy `.login-input` compat. Rebind hard-coded `rgba(79,110,247,.12)` on `.locked-card .lock-big` (line ~293) to `rgba(255,73,12,.12)`. Do NOT delete `.locked-zone` animation rules yet — plan 04 removes them when `<TopNav>` replaces the markup (RESEARCH.md P9). Do NOT touch `.cell-tooltip` classes — plan 03 replaces them.</description>
  <files>app/globals.css</files>
  <commit>refactor(infra-redesign-v2-01): replace design tokens with neutral-dark + orange palette (D-01, D-02, D-04)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>01-02</id>
  <description>Wire Inter Tight + Roboto Mono through `next/font/google` in `app/layout.tsx`. Default path per RESEARCH.md — if Sergey confirms Suisse Int'l license before this task starts, swap to the `next/font/local` snippet from RESEARCH.md §"Alternate snippet" and drop the `-0.32px` letter-spacing override. Expose `--font-body` and `--font-mono` CSS variables via `html.className`. In `app/globals.css`, set `body { font-family: var(--font-body); letter-spacing: -0.32px; }` and add `.mono-caption { font-family: var(--font-mono); font-weight: 500; font-size: 10px; line-height: 13px; letter-spacing: -1px; }` per Figma variable defs (D-07, D-08). Keep existing imports (`Analytics`, metadata) intact.</description>
  <files>app/layout.tsx, app/globals.css</files>
  <commit>feat(infra-redesign-v2-01): load Inter Tight + Roboto Mono via next/font (D-07, D-08, D-09)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>01-03</id>
  <description>Add `BUILD_DATE` env var in `next.config.ts`. Append `env: { BUILD_DATE: new Date().toISOString().slice(0, 10) }` into the existing `NextConfig` object without disturbing `redirects()` or other existing config (RESEARCH.md P4). This is the prerequisite for `<HeaderBar>` in plan 02-04 to render the build-date span without triggering hydration mismatch (D-12).</description>
  <files>next.config.ts</files>
  <commit>feat(infra-redesign-v2-01): export process.env.BUILD_DATE for HeaderBar (D-12 prereq)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>01-04</id>
  <description>Install Playwright + chromium as dev dep. Run `npm install -D @playwright/test` then `npx playwright install chromium`. Write `playwright.config.ts` with `testDir: './tests/visual'`, `use: { baseURL: 'http://localhost:3000', colorScheme: 'dark' }` (RESEARCH.md P3), `expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.02 } }` (D-26). Create `tests/visual/homepage.spec.ts` scaffold that imports `@playwright/test`, wraps the homepage screenshot test body, but uses `test.skip(true, 'baseline captured in plan 04 once homepage refactor lands')` so the skeleton compiles and can be unskipped later. Do NOT start the dev server or capture a baseline PNG yet — that happens in plan 04 once `<HeaderBar>` / `<TopNav>` / matrix refactor ships.</description>
  <files>package.json, package-lock.json, playwright.config.ts, tests/visual/homepage.spec.ts</files>
  <commit>test(infra-redesign-v2-01): add Playwright + visual-regression scaffold (D-26)</commit>
  <automated>npx playwright test --list tests/visual/homepage.spec.ts</automated>
</task>

<task>
  <id>01-05</id>
  <description>Add font-readiness test infra. Create `tests/setup-fonts.ts` exporting a helper that awaits `document.fonts.ready` (guarded for jsdom which lacks `document.fonts`). Create `tests/fonts.test.ts` (Vitest) that imports the helper and asserts `document.fonts.check('16px "Inter Tight"')` + `document.fonts.check('10px "Roboto Mono"')` resolve true after readiness. In jsdom this will be a conditional skip; in a browser env it enforces D-07/D-08. Add empty `tests/components/.gitkeep` so plans 02–03 have the directory ready.</description>
  <files>tests/setup-fonts.ts, tests/fonts.test.ts, tests/components/.gitkeep</files>
  <commit>test(infra-redesign-v2-01): add font-readiness harness + components dir gate (D-07, D-08)</commit>
  <automated>npm test -- --run tests/fonts.test.ts</automated>
</task>

<task>
  <id>01-06</id>
  <description>Update `README.md` if structure sections now list test dirs (project-structure diagram gets `tests/visual/` and `tests/components/` entries). Add CHANGELOG.md v6.0 entry at top — major: "New design-token system (neutral-dark + brand-orange), Inter Tight + Roboto Mono via next/font, Playwright visual-regression scaffold, BUILD_DATE env var. Foundation for visual redesign (infra-redesign-v2)." Keep under 300 chars. Finish with `npx next build` + `npm test` to satisfy D-27.</description>
  <files>README.md, CHANGELOG.md</files>
  <commit>docs(infra-redesign-v2-01): changelog v6.0 + README test-dir structure update</commit>
  <automated>npx next build &amp;&amp; npm test</automated>
</task>

</tasks>

<verification>
- Wave merge: `npm test &amp;&amp; npx next build` green.
- Phase gate prerequisite: `tests/visual/homepage.spec.ts` exists (skipped); `tests/components/` exists.
- Decision-verification rows appended to `VALIDATION.md` for each task in this plan.
- No file in `analysis/homepage/results/*.json` changed (D-28 invariant — verify via `git diff --quiet analysis/homepage/results/`).
</verification>
