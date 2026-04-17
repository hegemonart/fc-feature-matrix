---
phase: infra-redesign-v2
plan: 05
subsystem: infra
tags: [system-rollout, club-page, admin, recharts, modals, lighthouse-a11y, visual-regression, playwright, design-system, phase-close]

# Dependency graph
requires:
  - phase: infra-redesign-v2
    plan: 01
    provides: design tokens (--bg-page/cell/hover/border/accent/text/muted/yellow/red/green), .mono-caption helper, Inter Tight + Roboto Mono via next/font, Playwright + visual-regression scaffold
  - phase: infra-redesign-v2
    plan: 02
    provides: 7 atomic matrix components used downstream by /club/[id]
  - phase: infra-redesign-v2
    plan: 03
    provides: HoverTooltipCard + hooks, CellScoring/TooltipData types
  - phase: infra-redesign-v2
    plan: 04
    provides: Server/Client split for app/page.tsx, MatrixIsland with three inline modals (LOCKED/LOGIN/COMING SOON), homepage visual-regression baseline pattern
provides:
  - app/club/[id]/page.tsx re-themed via token swap (D-22) — stat labels gain .mono-caption, "Back to matrix" is white-outlined (single orange CTA preserved)
  - app/admin/analytics/page.tsx Recharts dashboard re-colored per RESEARCH.md "Recharts Re-Theme — Diff Sketch" (D-23) — all 13 numbered substitutions, hard-coded #FF490C in <linearGradient><stop> per RESEARCH.md P2
  - app/admin/layout.tsx chrome re-themed (D-23) — admin-page-title becomes .mono-caption, admin-table gains var(--bg-cell) chrome with rounded corners + border, admin-btn-primary stays the single orange CTA
  - app/admin/users/_actions.tsx + app/admin/requests/_actions.tsx re-themed (D-23) — premium badge uses rgba(255,73,12,.12) + var(--accent), StatusBadge uses var(--yellow-bg)/var(--green) tokens, section headers gain mono-caption styling
  - tests/components/Modal.test.tsx — 9 specs asserting single-orange-CTA per modal (D-24) with three fixture components mirroring inline JSX in MatrixIsland
  - tests/visual/club-page.spec.ts + baseline PNG (1440x900, maxDiffPixelRatio 0.02 from playwright.config.ts) for /club/real_madrid
  - tests/visual/admin.spec.ts scaffold (test.skip with TODO(infra-redesign-v2.1) — admin auth fixture pending DATABASE_URL + seeded admin user)
  - tests/visual/lighthouse/{homepage-a11y.html,homepage-a11y.json,homepage-a11y.png,capture-score-png.mjs} — Lighthouse a11y report committed; score 91/100 >= 90 (D-29 gate)
  - CLAUDE.md "## Design system rules" section codifying single-orange-CTA-per-surface (D-25), design tokens, type stack, visual-regression pattern, score-invariant gate
  - CHANGELOG.md v9.0 entry — system-wide visual rollout closes infra-redesign-v2
  - README.md project-structure expanded to enumerate new specs and CLAUDE.md design rules pointer
affects: []  # phase close — no downstream plans in this phase

# Tech tracking
tech-stack:
  added:
    - "lighthouse@12 (one-shot via npx, devDep not added) — used to capture HTML+JSON a11y report committed to tests/visual/lighthouse/"
  patterns:
    - "Token-swap-only rule for downstream pages: replace hex literals + cool-blue tokens with var(--bg-page|bg-cell|bg-hover|border|text|muted|accent), keep status semantics on var(--green|yellow|orange|red), preserve markup and behavior"
    - "Single-orange-CTA-per-surface invariant — at most one element with background: var(--accent) per page/panel/modal; secondary actions are .locked-dismiss / white-outlined / text-only"
    - "Modal CTA test pattern: fixture components mirror inline JSX, querySelectorAll('.locked-btn').length === 1"
    - "Admin re-theme uses inline-style var(--token) replacements (no need to touch globals.css for component-local color overrides)"
    - "Lighthouse a11y gate as a one-shot commit-time artifact (HTML+JSON+PNG), not CI-integrated yet — score gate enforced by node -e check"

key-files:
  created:
    - tests/components/Modal.test.tsx
    - tests/visual/club-page.spec.ts
    - tests/visual/admin.spec.ts
    - tests/visual/club-page.spec.ts-snapshots/club-real-madrid-1440x900-win32.png
    - tests/visual/lighthouse/homepage-a11y.html
    - tests/visual/lighthouse/homepage-a11y.json
    - tests/visual/lighthouse/homepage-a11y.png
    - tests/visual/lighthouse/capture-score-png.mjs
    - .planning/phases/infra-redesign-v2/05-SUMMARY.md
  modified:
    - app/club/[id]/page.tsx
    - app/admin/analytics/page.tsx
    - app/admin/layout.tsx
    - app/admin/users/_actions.tsx
    - app/admin/requests/_actions.tsx
    - CLAUDE.md
    - CHANGELOG.md
    - README.md

decisions:
  - id: D-22
    summary: "/club/[id] re-themed via token swap; back-button is white-outlined (single orange CTA per surface). Charts unchanged."
  - id: D-23
    summary: "/admin/* (layout chrome + analytics Recharts dashboard + users + requests) re-colored to new tokens. Recharts <linearGradient><stop> hard-coded #FF490C per RESEARCH.md P2 (var() inside SVG attribute is unreliable)."
  - id: D-24
    summary: "Three modals (LOCKED, LOGIN, COMING SOON) audited and each has exactly ONE .locked-btn (orange) and zero-or-one .locked-dismiss (text-only). Modal.test.tsx encodes the invariant with 9 assertions."
  - id: D-25
    summary: "CLAUDE.md gains '## Design system rules' section with five invariants. The literal phrase 'single orange CTA' is grep-able for future audits."
  - id: D-26
    summary: "Visual-regression baseline captured for /club/real_madrid at 1440x900. Admin spec scaffolded but test.skip()'d with TODO(infra-redesign-v2.1) — admin auth fixture requires DATABASE_URL + seeded admin user, neither available in this worktree."
  - id: D-28
    summary: "Score-data invariant verified at phase gate — recalculate-scores.js produced byte-identical content (only generated_at timestamp drifted; reverted to keep git diff --quiet exit 0)."
  - id: D-29
    summary: "Lighthouse a11y score 91/100 on the redesigned homepage (gate >= 90 PASS). Report committed to tests/visual/lighthouse/."

metrics:
  duration: ~75 minutes (resumed from prior agent's mid-task state)
  tasks_completed: 8
  files_created: 9
  files_modified: 8
  completed_date: 2026-04-17
---

# Phase infra-redesign-v2 Plan 05: System-Wide Rollout + Phase Close Summary

System-wide visual redesign rollout closes the infra-redesign-v2 phase: `/club/[id]` and all `/admin/*` surfaces (layout chrome, analytics Recharts dashboard, users, requests) re-themed via pure token swap; three modals audited with `Modal.test.tsx` enforcing the single-orange-CTA invariant; `CLAUDE.md` "Design system rules" section codifies the rule for future contributors; club-page visual-regression baseline committed; Lighthouse a11y score 91/100 (gate ≥ 90); D-28 score-invariant verified.

## Per-Task Outcomes

| Task   | Description                                                                  | Commit    | Notes                                                                         |
| ------ | ---------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------- |
| 05-01  | `/club/[id]` token-swap re-theme (D-22)                                      | `4aea414` | Completed by previous agent.                                                  |
| 05-02  | Recharts dashboard re-color (D-23)                                           | `b26d71e` | Completed by previous agent.                                                  |
| 05-02b | Admin layout chrome token swap (D-23) — completed in-flight by prior agent   | `0e9d2e9` | Resumed from staged-but-uncommitted diff; reviewed and committed cleanly.     |
| 05-03  | Re-theme admin users + requests pages (D-23)                                 | `3a4c9b6` | Hard-coded blue/grey hex literals replaced with var(--token); StatusBadge cleaned up. |
| 05-04  | Modal CTA audit + Modal.test.tsx (D-24)                                      | `14090a2` | 9 tests pass. Audit found ZERO violations — modals already comply.            |
| 05-05  | Visual baseline /club/real_madrid + admin spec scaffold (D-26)               | `09606f5` | Admin spec test.skip()'d with TODO; fixture requires DATABASE_URL.            |
| 05-06  | CLAUDE.md design-system rules (D-25)                                         | `11fba2e` | `grep -q "single orange CTA"` PASS.                                           |
| 05-07  | Lighthouse a11y report (D-29)                                                | `03ebdcf` | Score 91/100 ≥ 90; HTML + JSON + PNG committed.                               |
| 05-08  | CHANGELOG v9.0 + README final pass — phase close                             | `be2897d` | Full suite green; D-28 strict gate clean.                                     |

## Phase Gate Results

- `npm test`: 99 passed across 16 files (added 9 tests in Modal.test.tsx)
- `npx playwright test`: 2 passed, 1 skipped (admin baseline pending auth fixture)
- `npx next build`: PASS
- `node analysis/homepage/crosscheck/recalculate-scores.js && git diff --quiet HEAD analysis/homepage/results/`: PASS (only `generated_at` timestamp drifted; reverted to keep gate strict per D-28)
- `grep -q "single orange CTA" CLAUDE.md`: PASS
- Lighthouse a11y: 91/100 (gate ≥ 90 PASS)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Admin auth fixture cannot be wired in this worktree**
- **Found during:** Task 05-05.
- **Issue:** `tests/visual/admin.spec.ts` requires authenticated `/admin/analytics` access. The auth gate at `app/admin/layout.tsx:18` calls `getSessionFromCookie` → `getUserByEmail` → DB lookup, which fails with `Environment validation failed: DATABASE_URL Required` because the worktree has no `.env` (only `.env.example`). Wiring a real DB user is out of scope for the visual-regression task.
- **Fix:** `test.skip(true, ...)` with explicit `TODO(infra-redesign-v2.1)` block in the spec file enumerating the steps to wire it later. Plan explicitly authorized this fall-back ("If `storageState` setup proves blocked by missing seed data, fall back to `test.skip(true, ...)`").
- **Files modified:** `tests/visual/admin.spec.ts` (created skipped scaffold).
- **Commit:** `09606f5`.

**2. [Rule 1 - Bug] D-28 strict gate failed due to `generated_at` timestamp drift**
- **Found during:** Task 05-08.
- **Issue:** `recalculate-scores.js` writes a `generated_at: today` timestamp into `_scores.json` and `_aggregate.json`. The previous run on `2026-04-16` and today's run on `2026-04-17` produced identical CONTENT but a different timestamp, breaking `git diff --quiet`.
- **Fix:** Reverted the timestamp-only diffs with `git checkout HEAD -- analysis/homepage/results/`. Verified via `git diff --ignore-all-space` that the only delta was `generated_at`. The D-28 invariant intent (no scoring drift) is satisfied; the strict CLI exit-0 also passes after revert.
- **Files modified:** none (revert).
- **Commit:** none (clean working tree before final commit).

### Filename Adjustments

- Plan referenced `app/admin/access-requests/page.tsx`; actual codebase path is `app/admin/requests/page.tsx`. Used the actual path. Same applies to `_actions.tsx`.
- Lighthouse output filenames: `lighthouse@12` writes `homepage-a11y.report.{html,json}` rather than `homepage-a11y.{html,json}`. Renamed post-generation to match plan's intent.
- Playwright sanitizes screenshot filenames; `club-real_madrid-1440x900.png` was written as `club-real-madrid-1440x900-win32.png`. Acceptable (the path is referenced only by the spec itself).

### CHANGELOG Version Bump

- Plan called for `v7.0` major bump but the head of CHANGELOG.md already had `v8.0` from plan 04. Bumped to `v9.0` to maintain monotonic version history (v8 → v9). Plan intent ("major bump for system-wide rollout") preserved.

## Authentication Gates

None encountered — no human auth was required at any task boundary. The admin spec is a deferred fixture, not a runtime auth gate.

## Phase Close Notes

This is the final plan of `infra-redesign-v2`. All 5 plans landed:

| Plan | Title                                            | Status |
| ---- | ------------------------------------------------ | ------ |
| 01   | Tokens + Fonts + Visual-Regression Scaffold      | DONE   |
| 02   | Atomic Matrix Components (7)                     | DONE   |
| 03   | Hover Tooltip + Column Selection                 | DONE   |
| 04   | Homepage Server/Client Split + MatrixIsland      | DONE   |
| 05   | System-Wide Rollout + Phase Close                | DONE   |

**Manual sign-off pending:** Sergey eyeballs `/` against Figma node `43:36` at 1440×900 (CONTEXT.md D-26 manual gate). Codified gates (build, tests, a11y, score-invariant, single-orange-CTA grep) are all green.

## Self-Check: PASSED

Verified the following exist:
- `app/admin/layout.tsx` (modified, committed `0e9d2e9`)
- `app/admin/users/_actions.tsx` (modified, committed `3a4c9b6`)
- `app/admin/requests/_actions.tsx` (modified, committed `3a4c9b6`)
- `tests/components/Modal.test.tsx` (created, committed `14090a2`)
- `tests/visual/club-page.spec.ts` (created, committed `09606f5`)
- `tests/visual/admin.spec.ts` (created, committed `09606f5`)
- `tests/visual/club-page.spec.ts-snapshots/club-real-madrid-1440x900-win32.png` (created, committed `09606f5`)
- `tests/visual/lighthouse/homepage-a11y.html` (created, committed `03ebdcf`)
- `tests/visual/lighthouse/homepage-a11y.json` (created, committed `03ebdcf`)
- `tests/visual/lighthouse/homepage-a11y.png` (created, committed `03ebdcf`)
- `CLAUDE.md` (modified, committed `11fba2e`, contains "single orange CTA")
- `CHANGELOG.md` (modified, committed `be2897d`, v9.0 entry at top)
- `README.md` (modified, committed `be2897d`, project-structure updated)

All 8 commits present in `git log`.
