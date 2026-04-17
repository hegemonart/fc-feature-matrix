---
phase: infra-redesign-v2
slug: infra-redesign-v2
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase infra-redesign-v2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Sourced from `RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Unit framework** | Vitest 2.1.8 (already wired — see `lib/auth.test.ts`, `lib/scoring.test.ts`) |
| **Visual / E2E framework** | Playwright (`@playwright/test`) — installed in Wave 0 |
| **Score recompute** | `node analysis/homepage/crosscheck/recalculate-scores.js` |
| **Build gate** | `npx next build` |
| **Quick run command** | `npm test` |
| **Full suite command** | `npm test && npx playwright test && npx next build && node analysis/homepage/crosscheck/recalculate-scores.js` |
| **Lighthouse (manual phase gate)** | `npx lighthouse http://localhost:3000 --only-categories=accessibility --chrome-flags="--headless"` |
| **Estimated runtime (quick)** | ~2 seconds (Vitest) |
| **Estimated runtime (full)** | ~30–60 seconds + manual Lighthouse |

---

## Sampling Rate

- **After every task commit:** `npm test` (Vitest only — fast feedback).
- **After every plan wave:** `npm test && npx playwright test --grep @smoke && npx next build`.
- **Before `/gsd:verify-work` (phase gate):** Full suite must be green + score-data unchanged + Lighthouse a11y ≥ 90 + manual visual diff against Figma reference.
- **Max feedback latency:** 60 seconds (Vitest+smoke).

---

## Per-Decision Verification Map

> Maps every locked decision (D-01–D-29 in CONTEXT.md) to its verification artifact. Filled by planner with concrete plan/wave/task IDs once `/gsd:plan-phase` produces PLAN.md files.

| Decision | Behavior | Test type | Automated command | File / Wave 0 status |
|----------|----------|-----------|-------------------|-----------------------|
| D-01 | Bg / border tokens applied; no blue cast | visual | `npx playwright test tests/visual/homepage.spec.ts` | ❌ W0 — `tests/visual/homepage.spec.ts` |
| D-02 | Single brand accent `#FF490C` on chrome + CTAs | visual | same | ❌ W0 |
| D-03 | Selected-column tint applies on click | unit + visual | Vitest snapshot + Playwright click→shot | ❌ W0 — `tests/components/DataCell.test.tsx` |
| D-04 | Text white / `#ABABAB` | visual | Playwright color sample | ❌ W0 |
| D-05 | Cell metrics `40×38`, padding 12, 3-side border, `-0.3px` tracking | unit + visual | Vitest + Testing Library DOM measure | ❌ W0 |
| D-06 | Score-meter band colors preserved | unit | Vitest snapshot of `<MeterRow band="competitive">` | ❌ W0 — `tests/components/MeterRow.test.tsx` |
| D-07 / D-08 | Type stack loaded (Inter Tight + Roboto Mono) | unit | Vitest `document.fonts.check()` after `document.fonts.ready` | ❌ W0 — `tests/fonts.test.ts` + `tests/setup-fonts.ts` |
| D-09 | Font choice committed (default Inter Tight) | manual | inspect `app/layout.tsx` import | n/a (commit-level) |
| D-10 | `<DataCell>` 8 visual states render | unit | Vitest snapshot per state | ❌ W0 — `tests/components/DataCell.test.tsx` |
| D-11 | `<SortHeader>` 3 states + `onSort` fires | unit | Vitest with `fireEvent.click` | ❌ W0 — `tests/components/SortHeader.test.tsx` |
| D-12 | `<HeaderBar>` shows `process.env.BUILD_DATE` (no hydration mismatch) | smoke | Playwright `page.textContent('header')` | ❌ W0 — `BUILD_DATE` env in `next.config.ts` |
| D-13 | `<TopNav>` Unlock tab solid orange; locked tabs at 60% opacity → existing modal | unit + smoke | Vitest click → modal opens | ❌ W0 — `tests/components/TopNav.test.tsx` |
| D-14 | `<CategoryFilter>` counts match `features.ts` | unit | Vitest count equality | ❌ W0 |
| D-15 | `<TypeFilter>` filters `PRODUCTS[].type` (not JSON results — see RESEARCH.md correction) | unit | Vitest filter assertion | ❌ W0 |
| D-16 / D-21 | Tooltip portaled to `body`, escapes overflow, 100ms close grace | unit + smoke | Vitest `createPortal` target check; Playwright hover-and-leave | ❌ W0 — `tests/components/HoverTooltipCard.test.tsx` |
| D-17 | `app/page.tsx` Server shell + Client island; auth/modal logic preserved | smoke | `npx next build` + existing scoring tests stay green | n/a |
| D-18 | Selected-column toggles on click | smoke | Playwright | ❌ W0 |
| D-19 | Sort cycles `desc → asc → null` | unit | Vitest reducer-style on sort handler | ❌ W0 |
| D-20 | Sidebar filter state local; clear-btn resets all | unit | Vitest | ❌ W0 |
| D-22 | `/club/[id]` re-themed; single orange CTA | smoke + visual | Playwright snapshot of `/club/real_madrid` | ❌ W0 — `tests/visual/club-page.spec.ts` |
| D-23 | `/admin/analytics` Recharts re-colored | smoke + visual | Playwright snapshot (auth-stubbed) | ❌ W0 — `tests/visual/admin.spec.ts` |
| D-24 | Modals — single orange CTA, white-outlined cancel | unit + smoke | Vitest snapshot of three modals | ❌ W0 |
| D-25 | `CLAUDE.md` documents single-orange-CTA-per-surface rule | manual | `grep -q "single orange CTA" CLAUDE.md` | append-only edit in Plan 5 |
| D-26 | Screenshot diff ≤ 2% vs Figma reference baseline | visual | `npx playwright test` with `maxDiffPixelRatio: 0.02` | ❌ W0 — baseline PNG committed |
| D-27 | `npx next build` + `npm test` green | gate | both commands | always |
| D-28 | Score JSON unchanged pre/post | gate | `recalculate-scores.js` then `git diff --quiet analysis/homepage/results/_scores.json _aggregate.json` | already exists |
| D-29 | Lighthouse a11y ≥ 90 | manual | Lighthouse CLI | manual at phase gate; report PNG committed |

> **Per-task table** (Task ID · Plan · Wave · Test command · Status) is appended after `/gsd:plan-phase` produces PLAN.md files. Planner is responsible for emitting one row per `<task>` block.

---

## Wave 0 Requirements

- [ ] `@playwright/test` dev dep + `playwright.config.ts` + `npx playwright install chromium`
- [ ] `tests/visual/` directory + baseline PNG (homepage @ 1440×900) + `tests/visual/homepage.spec.ts`
- [ ] `tests/components/` directory + per-atomic Vitest specs:
      `DataCell` · `SortHeader` · `MeterRow` · `HeaderBar` · `TopNav` · `CategoryFilter` · `TypeFilter` · `HoverTooltipCard` · `Modal`
- [ ] `BUILD_DATE` env var added in `next.config.ts` (D-12 prerequisite)
- [ ] `tests/visual/club-page.spec.ts` and `tests/visual/admin.spec.ts` (admin needs auth stub or storageState fixture — flagged as planner choice)
- [ ] `tests/setup-fonts.ts` — awaits `document.fonts.ready` before font assertions
- [ ] `--bg1: var(--bg-cell);` token alias added in `app/globals.css` (legacy `.login-input` compatibility)

---

## Manual-Only Verifications

| Behavior | Decision | Why Manual | Test Instructions |
|----------|----------|------------|-------------------|
| Final visual diff against Figma | D-26 | Pixelmatch can't catch "feels right" — Sergey eyeballs at phase gate | Open `/`, compare side-by-side with Figma node `43:36` at 1440×900 |
| Lighthouse a11y ≥ 90 | D-29 | Lighthouse not yet wired into CI | Run command above against `localhost:3000`, commit report PNG to `tests/visual/lighthouse/` |
| Suisse Int'l licensing decision (D-09) | D-09 | Owner-only commercial decision | Sergey confirms before Plan 1 merges; default fallback is Inter Tight |

---

## Validation Sign-Off

- [ ] All decisions D-01 through D-29 mapped to a verification artifact
- [ ] All Wave 0 items checked complete
- [ ] Sampling continuity: no 3 consecutive task commits without an automated verify
- [ ] No watch-mode flags in CI commands
- [ ] Feedback latency < 60s for per-task quick run
- [ ] Score JSON `git diff --quiet` confirmed at phase gate
- [ ] Lighthouse a11y ≥ 90 PNG committed
- [ ] `nyquist_compliant: true` set in frontmatter once all the above tick

**Approval:** pending

---

## Per-Task Verification Map

> Appended by `/gsd:plan-phase` (planner). One row per `<task>` block across plans 01–05.

| Task ID | Plan | Wave | Decision(s) | Test type | Command | Status |
|---------|------|------|-------------|-----------|---------|--------|
| 01-01 | 01 | 0 | D-01, D-02, D-04 | build | `npx next build` | ⬜ |
| 01-02 | 01 | 0 | D-07, D-08, D-09 | build | `npx next build` | ⬜ |
| 01-03 | 01 | 0 | D-12 (prereq) | build | `npx next build` | ⬜ |
| 01-04 | 01 | 0 | D-26 (tooling) | playwright list | `npx playwright test --list tests/visual/homepage.spec.ts` | ⬜ |
| 01-05 | 01 | 0 | D-07, D-08 | unit | `npm test -- --run tests/fonts.test.ts` | ⬜ |
| 01-06 | 01 | 0 | D-27 | gate | `npx next build && npm test` | ⬜ |
| 02-01 | 02 | 1 | D-10–D-15 (contracts) | typecheck | `npx tsc --noEmit` | ⬜ |
| 02-02 | 02 | 1 | D-05, D-10 | unit | `npm test -- --run tests/components/DataCell.test.tsx` | ⬜ |
| 02-03 | 02 | 1 | D-11 | unit | `npm test -- --run tests/components/SortHeader.test.tsx` | ⬜ |
| 02-04 | 02 | 1 | D-06 | unit | `npm test -- --run tests/components/MeterRow.test.tsx` | ⬜ |
| 02-05 | 02 | 1 | D-12 | unit | `npm test -- --run tests/components/HeaderBar.test.tsx` | ⬜ |
| 02-06 | 02 | 1 | D-13 | unit | `npm test -- --run tests/components/TopNav.test.tsx` | ⬜ |
| 02-07 | 02 | 1 | D-14 | unit | `npm test -- --run tests/components/CategoryFilter.test.tsx` | ⬜ |
| 02-08 | 02 | 1 | D-15 | unit | `npm test -- --run tests/components/TypeFilter.test.tsx` | ⬜ |
| 02-09 | 02 | 1 | D-27 | gate | `npm test && npx next build` | ⬜ |
| 03-01 | 03 | 1 | D-16 (contract) | typecheck | `npx tsc --noEmit` | ⬜ |
| 03-02 | 03 | 1 | D-16 | typecheck | `npx tsc --noEmit` | ⬜ |
| 03-03 | 03 | 1 | D-16 | typecheck | `npx tsc --noEmit` | ⬜ |
| 03-04 | 03 | 1 | D-03, D-18 (state) | typecheck | `npx tsc --noEmit` | ⬜ |
| 03-05 | 03 | 1 | D-16 | unit | `npm test -- --run tests/components/HoverTooltipCard.test.tsx` | ⬜ |
| 03-06 | 03 | 1 | D-16 | unit | `npm test -- --run tests/components/useHoverTooltip.test.tsx` | ⬜ |
| 03-07 | 03 | 1 | D-18 | unit | `npm test -- --run tests/components/useColumnSelection.test.tsx` | ⬜ |
| 03-08 | 03 | 1 | D-27 | gate | `npm test && npx next build` | ⬜ |
| 04-01 | 04 | 2 | D-17 | typecheck | `npx tsc --noEmit` | ⬜ |
| 04-02 | 04 | 2 | D-17, D-18, D-21 | build | `npx next build` | ⬜ |
| 04-03 | 04 | 2 | D-17 | build | `npx next build` | ⬜ |
| 04-04 | 04 | 2 | D-17 (cleanup) | build | `npx next build` | ⬜ |
| 04-05 | 04 | 2 | D-26 (baseline armed) | visual | `npx playwright test tests/visual/homepage.spec.ts` | ⬜ |
| 04-06 | 04 | 2 | D-19, D-20, D-29 (a11y deferred to 05-07) | gate | `npm test && npx playwright test && npx next build` | ⬜ |
| 05-01 | 05 | 3 | D-22 | build | `npx next build` | ⬜ |
| 05-02 | 05 | 3 | D-23 | build | `npx next build` | ⬜ |
| 05-03 | 05 | 3 | D-23 | build | `npx next build` | ⬜ |
| 05-04 | 05 | 3 | D-24 | unit | `npm test -- --run tests/components/Modal.test.tsx` | ⬜ |
| 05-05 | 05 | 3 | D-26 (full coverage) | visual | `npx playwright test tests/visual/club-page.spec.ts tests/visual/admin.spec.ts` | ⬜ |
| 05-06 | 05 | 3 | D-25 | grep | `grep -q "single orange CTA" CLAUDE.md` | ⬜ |
| 05-07 | 05 | 3 | D-29 | manual + node | Lighthouse JSON score ≥ 0.9 (node check) | ⬜ |
| 05-08 | 05 | 3 | D-27, D-28 (final gate) | gate | full suite + `git diff --quiet analysis/homepage/results/` | ⬜ |
