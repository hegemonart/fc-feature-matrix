# FC Benchmark — Agent Instructions

## Project overview

UX benchmarking tool: 58 homepage features scored across 33 sports organizations. Next.js app with TypeScript data layer in `analysis/`.

## Key files

- `analysis/homepage/HOME-PAGE.md` — Feature rubric (source of truth for scoring)
- `analysis/homepage/features.ts` — Feature definitions with tier weights
- `analysis/homepage/results/*.json` — Per-club feature values
- `analysis/homepage/crosscheck/CLAUDE.md` — Cross-check agent instructions
- `analysis/homepage/crosscheck/img/` — Element-level screenshot evidence
- `CHANGELOG.md` — Version history with change descriptions
- `README.md` — Project documentation

## Commit and push rules

**Every commit and push MUST include these steps:**

1. **Update README.md** — If the change affects any of these, update the corresponding README section:
   - Rankings table (after score recalculations)
   - Coverage numbers (after adding/removing clubs)
   - Project structure (after adding new files/folders)
   - Feature count (after rubric changes)
   - Screenshot coverage numbers (after new captures)

2. **Update CHANGELOG.md** — Add a new entry at the top of the changelog:
   - **Minor changes (1.x)**: Bug fixes, score corrections, individual club cross-checks, screenshot fixes, documentation updates, single-feature adjustments
   - **Major changes (x.0)**: New clubs added, rubric changes (features added/removed/redefined), new tooling (capture scripts, cross-check procedures), batch cross-checks across multiple clubs, new page types added
   - Each version entry: max 300 characters description
   - Version numbering: increment minor (1.1 -> 1.2) for minor, increment major (1.x -> 2.0) for major
   - Format:
     ```
     ## vX.Y — YYYY-MM-DD
     Description (max 300 chars)
     ```

3. **Recalculate scores** if any JSON result files changed:
   ```bash
   node analysis/homepage/crosscheck/recalculate-scores.js
   ```

4. **Verify build** before pushing:
   ```bash
   npx next build
   ```

## Analysis workflow

See `analysis/CLAUDE.md` for the full analysis folder documentation, and `analysis/homepage/crosscheck/CLAUDE.md` for cross-check procedures.

## Screenshot evidence (crosscheck/img)

Element-level screenshots for TRUE features. Naming: `{club_id}_{feature_key}.png`. Current coverage: 536 screenshots across all 33 clubs.

**Always use Playwright** for screenshot captures. Playwright has direct filesystem access and can save element-level screenshots straight to `crosscheck/img/`. Use the Chrome MCP extension for live site verification and visual checks only — not for saving screenshots. 5 sites block headless Chromium (Arsenal, Bayern, Liverpool, NBA, West Ham) — use Chrome MCP for those.

Capture scripts in `analysis/homepage/crosscheck/`:
- `capture_elements.py` — Main capture script
- `redo_bad_weak.py` — Re-capture failed/weak screenshots
- `recapture_deleted.py` — Batch re-capture with per-club cookie strategies
- `recapture_round5.py` — Full-page screenshot + PIL crop approach (most reliable)
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
