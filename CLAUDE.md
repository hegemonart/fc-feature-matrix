# FC Benchmark — CLAUDE.md

## Self-Improvement Protocol

After every task, ask: _did I hit something not in this file?_

- New trap or gotcha → add to Traps
- Architectural decision made or re-litigated → add to Decisions
- Pattern worth repeating → add inline where it fits

Update in the same commit as the code. One line per entry, terse. No filler.

---

## Traps

_Append gotchas as you discover them. Group by topic._

**Screenshots**
- 5 sites block headless Chromium (Arsenal, Bayern, Liverpool, NBA, West Ham) — use Chrome MCP for those
- Always dismiss popups/cookies FIRST before capturing
- Prefer full-page screenshot + PIL crop over Playwright clip — more reliable
- Carousel must show navigation controls in screenshot
- Video block must be large (>33% width) to count
- News rich structure must show different layouts
- Liverpool: DO NOT TOUCH

**Commits**
- Must update README.md if rankings, coverage, structure, feature count, or screenshot count changed
- Must update CHANGELOG.md — minor (1.x) for fixes/single-club, major (x.0) for new clubs/rubric changes/batch ops
- Must run `node analysis/homepage/crosscheck/recalculate-scores.js` if any JSON results changed
- Must run `npx next build` before pushing
- CHANGELOG entry: max 300 chars, format `## vX.Y — YYYY-MM-DD`

**State bloat**
- app/page.tsx had 130+ useState declarations — consolidated to 8 (Apr 2026). Watch for regression.

---

## Decisions

_Append when you make or re-examine an architectural choice. Format: DATE · decision (why)._

- 2026-04 · Playwright for screenshots, Chrome MCP only for blocked sites and visual verification (filesystem access)
- 2026-04 · Full-page screenshot + PIL crop as primary capture method (most reliable across sites)
- 2026-04 · Per-club cookie strategies in capture scripts (sites vary wildly in popup behavior)
- 2026-04 · Inline sign-in form swap in unlock modal instead of separate modal (cleaner UX)
- 2026-04 · 6-phase flow expansion roadmap: homepage → tickets → matchday → membership → content → commerce

---

## Project

UX benchmarking tool that scores 58 homepage features across 33 sports organizations. Built for fan experience auditors comparing digital presence. Next.js app with a TypeScript data layer in `analysis/`, element-level screenshot evidence, and a cross-check verification system.

Stack: Next.js 16, React 19, TypeScript, Playwright (Python), Vercel

Structure:
```
analysis/           — data layer: features, rubric, results, crosscheck scripts + evidence
  homepage/
    HOME-PAGE.md    — feature rubric (source of truth)
    features.ts     — feature definitions with tier weights
    results/*.json  — per-club scored feature values
    crosscheck/     — verification scripts, CLAUDE.md, img/ (536 screenshots)
app/                — Next.js pages and API routes (/me, /logout, /crosscheck-image)
lib/                — summary generator, shared utilities
data/               — users.json (4 accounts)
public/             — static assets
concept/            — design explorations (excluded from tsconfig)
references/         — reference materials (excluded from tsconfig)
```

---

## Key Files

- `analysis/homepage/HOME-PAGE.md` — Feature rubric (source of truth for scoring)
- `analysis/homepage/features.ts` — Feature definitions with tier weights
- `analysis/homepage/results/*.json` — Per-club feature values
- `analysis/homepage/crosscheck/CLAUDE.md` — Cross-check agent instructions (full capture rules)
- `analysis/CLAUDE.md` — Analysis folder documentation
- `CHANGELOG.md` — Version history
- `README.md` — Project documentation

---

## Screenshot Evidence

Naming: `{club_id}_{feature_key}.png` in `analysis/homepage/crosscheck/img/`

**Always use Playwright** for captures. Chrome MCP for live verification only.

Capture scripts in `analysis/homepage/crosscheck/`:
- `capture_elements.py` — Main capture script
- `redo_bad_weak.py` — Re-capture failed/weak screenshots
- `recapture_deleted.py` — Batch re-capture with per-club cookie strategies
- `recapture_round5.py` — Full-page + PIL crop (most reliable)
- `recalculate-scores.js` — Score recalculation after JSON changes

Key rules:
- Always dismiss popups/cookies FIRST
- Carousel must show navigation controls
- Video block must be large (>33% width)
- News rich structure must show different layouts
- Prefer full-page screenshot + PIL crop over Playwright clip
- Liverpool: DO NOT TOUCH
- See `crosscheck/CLAUDE.md` for full rules

## Design system rules

The visual layer was rebuilt in phase `infra-redesign-v2` (closes 2026-04-17). Future work must respect these invariants:

- **Single orange CTA per surface.** Every page, panel, or modal must contain at most one element styled with `background: var(--accent)` (`#FF490C`). Secondary actions are text-only or white-outlined. This keeps the brand accent semantically meaningful — orange means "this is the primary action." Tested by `tests/components/Modal.test.tsx` for modals; enforced by code review for pages. (Rule alias for grep: `single orange CTA`.)
- **Design tokens live in `app/globals.css :root`.** Use `var(--bg-page)`, `var(--bg-cell)`, `var(--bg-hover)`, `var(--border)`, `var(--text)`, `var(--muted)`, `var(--accent)`. Status semantics keep `var(--green)`, `var(--yellow)`, `var(--orange)`, `var(--red)` for score meters and deltas only — never for chrome or CTAs. Do not hand-code hex values for chrome.
- **Type stack: Inter Tight (body) + Roboto Mono (mono-caption).** Loaded via `next/font` in `app/layout.tsx` and exposed as `--font-body` / `--font-mono`. Section headers, score deltas, and `.mono-caption` (10/13/-1px) use the mono variable. Never hard-code `font-family` to a literal stack — reference the CSS variable.
- **Visual-regression baselines live in `tests/visual/`.** `homepage.spec.ts` and `club-page.spec.ts` enforce `maxDiffPixelRatio: 0.02` against committed PNGs. Update snapshots with `npx playwright test --update-snapshots` ONLY when the visual change is intentional, and call it out in the commit message.
- **Score data is invariant under visual changes.** A redesign commit must NEVER touch `analysis/homepage/results/*.json`, `lib/scoring.ts`, or `analysis/homepage/features.ts`. The phase gate is `node analysis/homepage/crosscheck/recalculate-scores.js && git diff --quiet analysis/homepage/results/`. If that diff is non-empty after a visual-only change, revert.
