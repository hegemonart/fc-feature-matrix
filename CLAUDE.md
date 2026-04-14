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

Element-level screenshots for TRUE features. Naming: `{club_id}_{feature_key}.png`. Current coverage: Chelsea, FC Barcelona, Arsenal.

Capture scripts are in `analysis/homepage/crosscheck/`:
- `capture_elements.py` — Main capture
- `redo_bad_weak.py` — Re-capture failed screenshots
- `redo_barcelona.py` — Barcelona-specific (Didomi consent)

Key rules:
- Always dismiss popups/cookies FIRST
- Carousel must show navigation controls
- Video block must be large (>33% width)
- News rich structure must show different layouts
- See `crosscheck/CLAUDE.md` for full rules
