# FC Benchmark

UX benchmarking tool for top sports club and league websites. Analyzes 58 homepage features across 33 organizations, scores them with asymmetric tier-based weighting, and presents an interactive comparison matrix.

## Stack

- **Next.js** with Turbopack
- **TypeScript**
- Deployed on **Vercel**

## Getting started

```bash
npm install
npx next dev --turbopack
```

Open [localhost:3000](http://localhost:3000)

## Project structure

```
app/                        Next.js pages and styles
lib/data.ts                 Re-exports analysis data to the app
analysis/
  CLAUDE.md                 Root analysis instructions
  products.ts               33 products (clubs, leagues, governing bodies)
  types.ts                  Shared TypeScript types
  index.ts                  Barrel export + band computation
  homepage/
    HOME-PAGE.md            58-feature scoring rubric (source of truth)
    features.ts             Feature definitions with tier weights
    categories.ts           12 feature categories with display colors
    results/                One JSON per organization + aggregates
      chelsea.json          Per-club feature values + confidence
      fc_barcelona.json
      arsenal.json
      ... (33 club files)
      _scores.json          Ranked scores
      _aggregate.json       Full feature x club matrix
    screenshots/            Full-page homepage PNGs for original analysis
    crosscheck/
      CLAUDE.md             Cross-check agent instructions
      recalculate-scores.js Score recalculation script
      img/                  536 element-level screenshot evidence files
      capture_elements.py   Main Playwright capture script
      redo_bad_weak.py      Re-capture failed screenshots
      recapture_deleted.py  Batch re-capture with cookie strategies
      recapture_round5.py   Full-page screenshot + PIL crop approach
public/                     Static assets
CHANGELOG.md                Version history
```

## Coverage

33 organizations across sports:

- **20 football clubs**: Real Madrid, FC Barcelona, Bayern Munich, PSG, Liverpool, Man City, Arsenal, Man United, Tottenham, Chelsea, Inter Milan, BVB Dortmund, Atletico Madrid, Aston Villa, AC Milan, Juventus, Newcastle, VfB Stuttgart, SL Benfica, West Ham
- **5 other clubs**: Brentford, Club Brugge, Eintracht Frankfurt, RB Leipzig, Valencia CF
- **5 leagues/tours**: UEFA, F1, MotoGP, MLS, MLB, NBA, ATP Tour
- **1 federation**: ITF Tennis

## Scoring system

Each feature has a tier (A-F) with asymmetric weights. Missing a must-have hurts more than missing a differentiator.

| Tier | Name | Yes weight | No weight |
|------|------|-----------|-----------|
| A | Must-have | +1 | -3 |
| B | Commercial table stakes | +2 | -2 |
| C | ROI driver | +5 | -2 |
| D | Differentiator | +8 | -1 |
| E | Content depth | +3 | -1 |
| F | Experimental | +8 | 0 |

A club's total score = sum of all feature weights (Yes or No). Scores can be negative.

## Analysis workflow

### 1. Original analysis (screenshot-based)

Each organization's homepage is captured as a full-page PNG screenshot (saved in `homepage/screenshots/`). An LLM analyzes every screenshot against the 58-feature rubric in `HOME-PAGE.md` and produces a JSON result file with `true`/`false` for each feature.

### 2. Browser cross-check

Every JSON result is independently verified by visiting the live website in Chrome. The cross-check agent follows instructions in `analysis/homepage/crosscheck/CLAUDE.md`:

1. Navigate to the live site at 1400x900 viewport
2. Dismiss all popups, overlays, and cookie banners
3. Scroll to trigger lazy-loading
4. Run JS data extraction for feature signals
5. Compare live observations against current JSON values
6. Flip any incorrect TRUE/FALSE values with evidence
7. Update confidence fields to `"browser-verified"`

All 33 organizations have been browser cross-checked. Discrepancies are logged in commit messages (e.g. `cross-check: Arsenal — 9 fixes, score 49 -> 46`).

### 3. Element-level screenshot evidence (crosscheck/img)

For proof-of-concept validation, element-level screenshots are captured for each TRUE feature on a club's homepage. Each screenshot crops the specific page region showing the feature, saved as `{club_id}_{feature_key}.png` in `analysis/homepage/crosscheck/img/`.

**Current coverage**: 444 element screenshots across all 33 clubs. Some TRUE features have `needs-live-check` confidence pending recapture.

**Capture tooling**: Playwright Python sync API, 1400x900 viewport. 5 sites block headless Chromium (Arsenal, Bayern, Liverpool, NBA, West Ham) — use Chrome MCP for live verification. Scripts:

| Script | Purpose |
|--------|---------|
| `capture_elements.py` | Main capture with JS feature locators, cookie dismissal, lazy-load scrolling |
| `redo_bad_weak.py` | Re-capture for screenshots that failed quality audit |
| `recapture_deleted.py` | Batch re-capture with per-club cookie strategies |
| `recapture_round5.py` | Full-page screenshot + PIL crop approach (most reliable) |

**Quality rules** (documented in `crosscheck/CLAUDE.md`):

- Always dismiss ALL popups/overlays/cookies before any capture
- Each screenshot must show the specific feature, not adjacent content
- Carousel screenshots must show navigation controls (arrows/dots)
- Video block screenshots must show a large player (>33% page width)
- News "rich structure" must show visually different card layouts, not uniform grids
- Header features require tight cropping around the specific element
- Stadium content must show the venue itself, not a ticket purchase section
- Press conference block is TRUE when press conf videos are accessible from homepage
- Academy/youth block is TRUE when youth team content is prominently placed

### 4. Score recalculation

After any JSON change, run:

```bash
node analysis/homepage/crosscheck/recalculate-scores.js
```

This parses weights from `features.ts`, recalculates all `total_score` values, and regenerates `_scores.json` (rankings) and `_aggregate.json` (adoption stats).

## Common tasks

### Re-analyze a club

1. Take a fresh full-page screenshot, save to `homepage/screenshots/`
2. Analyze against `HOME-PAGE.md` rubric, update `homepage/results/{club}.json`
3. Recalculate: `node analysis/homepage/crosscheck/recalculate-scores.js`

### Add a new club

1. Add to `products.ts`
2. Take screenshot, run analysis, create result JSON
3. Add import in `features.ts`
4. Recalculate scores
5. Verify: `npx next build`

### Cross-check features in browser

```
Cross-check "sponsor_lockup_in_header" across all websites
using rubric: analysis/homepage/HOME-PAGE.md
```

See `analysis/homepage/crosscheck/CLAUDE.md` for the full procedure.

### Capture element screenshots

```bash
cd analysis/homepage/crosscheck
python3 capture_elements.py       # Main capture
python3 redo_bad_weak.py          # Re-capture failed screenshots
python3 recapture_deleted.py      # Batch re-capture with cookie strategies
python3 recapture_round5.py       # Full-page + PIL crop (most reliable)
```

## Current rankings (top 10)

| Rank | Organization | Score |
|------|-------------|-------|
| 1 | FC Barcelona | 69 |
| 2 | Valencia CF | 42 |
| 3 | MotoGP | 30 |
| 4 | Juventus | 22 |
| 5 | Arsenal | 21 |
| 6 | Chelsea | 19 |
| 7 | Eintracht Frankfurt | 4 |
| 8 | Real Madrid | 4 |
| 9 | Liverpool | -1 |
| 10 | PSG | -1 |
