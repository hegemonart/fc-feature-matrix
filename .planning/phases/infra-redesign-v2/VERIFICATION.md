---
phase: infra-redesign-v2
verified: 2026-04-17T08:36:00Z
status: passed
score: 14/14 must-haves verified
---

# Phase infra-redesign-v2: Visual Redesign v2 Verification Report

**Phase Goal:** Replace the visual layer of FC Benchmark with the new Figma redesign and propagate the resulting design system across `/club/[id]`, `/admin/*`, and the modals. Closes with single-orange-CTA-per-surface rule codified.

**Verified:** 2026-04-17T08:36:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### D-Decision Verification (29 D-decisions across 5 plans)

| #   | Check                                                     | Status     | Evidence                                                                                              |
| --- | --------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| 1   | D-01–D-04: 6 new tokens in globals.css                    | VERIFIED   | `app/globals.css:3-8` defines `--bg-page #0F0F0F`, `--bg-cell #1A1A1A`, `--bg-hover #383838`, `--border #262626`, `--accent #FF490C`, `--column-tint rgb(51,24,15)` |
| 2   | D-07–D-09: Inter Tight + Roboto Mono via next/font        | VERIFIED   | `app/layout.tsx:4` imports `Inter_Tight, Roboto_Mono` from `next/font/google`; exposed as `--font-body` and `--font-mono` CSS variables on `<html>` |
| 3   | D-10–D-15: 7 atomic components + colocated CSS + tests    | VERIFIED   | All 7 `.tsx` + `.module.css` pairs exist under `app/components/matrix/`; 7 corresponding Vitest specs exist under `tests/components/` (each passing 5–12 tests) |
| 4   | D-15: PRODUCTS.type drives TypeFilter (not JSON results)  | VERIFIED   | `analysis/products.ts:11+` shows every entry has `type: 'club' \| 'governing' \| 'league'`; `TypeFilter.tsx` documents PRODUCTS-as-source and receives data from parent (no JSON import) |
| 5   | D-16, D-03: HoverTooltipCard portals to body, 100ms grace | VERIFIED   | `HoverTooltipCard.tsx:90` calls `createPortal(node, document.body)`; `useHoverTooltip.ts:31` exports `TOOLTIP_CLOSE_GRACE_MS = 100` |
| 6   | D-17: app/page.tsx is Server Component, MatrixIsland is Client | VERIFIED | `app/page.tsx` has no `'use client'` directive (grep returned 0 matches); `app/MatrixIsland.tsx:1` has `'use client'` and imports all 7 atomic components |
| 7   | D-22: /club/[id] re-themed with new tokens                | VERIFIED   | Page uses semantic class names (`.club-detail-shell`, `.bd-score-card`, `.page-header`); `globals.css:365,454` shows those classes use `var(--bg-cell)`, `var(--border)`, `var(--bg-hover)`, etc. (87 var() references in globals.css) |
| 8   | D-23: Recharts re-color (no leftover blue literals)       | VERIFIED   | `grep -c "#4f6ef7" app/admin/analytics/page.tsx` returns 0; charts use `#FF490C` accent + `var(--border)` grayscale grid |
| 9   | D-24: Modal CTA audit test exists and passes              | VERIFIED   | `tests/components/Modal.test.tsx` exists with fixtures for LOCKED/LOGIN/COMING SOON; vitest reports 9/9 passing |
| 10  | D-25: CLAUDE.md codifies single-orange-CTA rule           | VERIFIED   | `CLAUDE.md:79` documents rule with grep-alias `single orange CTA`; references Modal.test.tsx for enforcement |
| 11  | D-26: Visual baseline unskipped, maxDiffPixelRatio: 0.02  | VERIFIED   | `tests/visual/homepage.spec.ts:23` uses `test(...)` (not `.skip`); `playwright.config.ts` sets `maxDiffPixelRatio: 0.02`; baseline `homepage-1440x900-win32.png` committed in snapshots dir |
| 12  | D-28: Score-data invariant (recalc → no JSON drift)       | VERIFIED   | `node analysis/homepage/crosscheck/recalculate-scores.js` ran cleanly; `git diff` shows ONLY `generated_at` date field changed in both `_scores.json` and `_aggregate.json` — zero score data drift |
| 13  | D-29: Lighthouse a11y ≥ 90                                | VERIFIED   | `tests/visual/lighthouse/homepage-a11y.{html,json,png}` all exist; extracted accessibility category score = **0.91** (91 / 100) |
| 14  | D-27: Build + tests pass                                  | VERIFIED   | `npx next build` → "Compiled successfully in 3.2s"; `npm test` → 16 test files / 99 tests passed; Playwright admin spec is `.skip`'d per acknowledged variance (auth fixture deferred to v2.1) |

**Score:** 14/14 must-haves verified

### Required Artifacts

| Artifact                                                  | Expected                            | Status     | Details                                             |
| --------------------------------------------------------- | ----------------------------------- | ---------- | --------------------------------------------------- |
| `app/globals.css`                                         | 6 new tokens                        | VERIFIED   | Lines 3–8                                           |
| `app/layout.tsx`                                          | Font CSS variables                  | VERIFIED   | Inter Tight + Roboto Mono wired to `<html>`         |
| `app/components/matrix/{7 components}.tsx`                | 7 atomic components                 | VERIFIED   | All present                                         |
| `app/components/matrix/{7 components}.module.css`         | 7 colocated CSS Module files        | VERIFIED   | All present                                         |
| `tests/components/{7 components}.test.tsx`                | 7 Vitest specs                      | VERIFIED   | All passing                                         |
| `app/components/matrix/HoverTooltipCard.tsx`              | Portal to body                      | VERIFIED   | createPortal at line 90                             |
| `app/components/matrix/useHoverTooltip.ts`                | 100ms close grace                   | VERIFIED   | Line 31                                             |
| `app/components/matrix/useColumnSelection.ts`             | Column selection hook               | VERIFIED   | Present + 5 passing tests                           |
| `app/page.tsx`                                            | Server Component                    | VERIFIED   | No `'use client'` directive                         |
| `app/MatrixIsland.tsx`                                    | Client island                       | VERIFIED   | `'use client'` + imports all 7 atoms                |
| `app/club/[id]/page.tsx`                                  | Re-themed (via globals.css classes) | VERIFIED   | Semantic class names backed by token-based CSS rules |
| `app/admin/analytics/page.tsx`                            | No `#4f6ef7` literals               | VERIFIED   | 0 occurrences                                       |
| `tests/components/Modal.test.tsx`                         | Modal CTA audit                     | VERIFIED   | 9/9 tests pass                                      |
| `CLAUDE.md`                                               | Single-orange-CTA rule              | VERIFIED   | Line 79                                             |
| `tests/visual/homepage.spec.ts`                           | Unskipped, baseline-enforced        | VERIFIED   | maxDiffPixelRatio 0.02 from playwright.config.ts    |
| `tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png` | Baseline PNG            | VERIFIED   | File present                                        |
| `tests/visual/lighthouse/homepage-a11y.{html,json,png}`   | A11y report ≥ 90                    | VERIFIED   | Score 0.91                                          |

### Key Link Verification

| From                            | To                                       | Via                                       | Status |
| ------------------------------- | ---------------------------------------- | ----------------------------------------- | ------ |
| `MatrixIsland.tsx`              | 7 atomic components                      | named imports from `./components/matrix/` | WIRED  |
| `app/page.tsx` (Server)         | `MatrixIsland` (Client)                  | data load + island render                 | WIRED  |
| `TypeFilter`                    | `PRODUCTS.type`                          | parent passes derived list (not JSON)     | WIRED  |
| Club detail JSX                 | New tokens                               | `.bd-*` / `.page-header` classes in globals.css using `var(--*)` | WIRED  |
| Recharts                        | `--accent` + grayscale                   | `#FF490C` + `var(--border)` only          | WIRED  |
| Modal markup                    | `single orange CTA` rule                 | `.locked-btn` + `.locked-dismiss` validated by Modal.test.tsx | WIRED  |
| Lighthouse report               | a11y baseline                            | `homepage-a11y.json` score field          | WIRED  |

### Anti-Patterns Found

None.

- No TODO/FIXME/PLACEHOLDER comments introduced in scoped files.
- No stub returns (no `return null` / empty handler) in atomic components — all have substantive markup.
- No leftover blue literal `#4f6ef7` in analytics.
- No `'use client'` leak into Server Component shell.

### Acknowledged Scope Variances (NOT gaps)

- `tests/visual/admin.spec.ts` is `.skip`'d — explicitly authorized fall-back per plan 05 (auth fixture deferred to v2.1).
- Suisse Int'l licensing not adopted — Inter Tight is the green-light fallback per CONTEXT.md D-09.

### Human Verification Required

None — all 14 automated checks landed.

### Gaps Summary

No gaps. The phase goal is achieved end-to-end:
- Tokens, fonts, atomic components, hooks, and tooltip portal are in place (plans 01–03).
- Homepage refactored to Server/Client split with visual baseline locked (plan 04).
- System-wide rollout covers club detail, admin analytics, and modals; single-orange-CTA rule is codified in CLAUDE.md and enforced by Modal.test.tsx (plan 05).
- Score data is provably untouched (only `generated_at` timestamp changes on recalc).
- Build + 99 vitest tests pass clean; Lighthouse a11y = 0.91 ≥ 0.90.

---

_Verified: 2026-04-17T08:36:00Z_
_Verifier: Claude (gsd-verifier)_
