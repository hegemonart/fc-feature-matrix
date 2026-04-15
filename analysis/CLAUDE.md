# analysis/ folder

This folder is the **data layer** for the FC Benchmark app. The app itself lives in `app/` and `lib/` — everything here feeds into it.

Each page type (homepage, player page, etc.) gets its own subfolder with a rubric, features, results, and crosscheck tooling. Shared infrastructure (products, types) lives at the root.

## Architecture

```
analysis/
├── products.ts              ← 33 products (clubs/leagues/governing bodies) — shared
├── types.ts                 ← Shared TypeScript types
├── index.ts                 ← Barrel export + band computation
├── CLAUDE.md                ← This file
│
└── homepage/                ← Homepage analysis (one folder per page type)
    ├── HOME-PAGE.md         ← Feature rubric (source of truth for scoring)
    ├── PLAYBOOK-...md       ← Methodology documentation
    ├── features.ts          ← 60 features — imports presence from results/*.json
    ├── categories.ts        ← 12 feature categories with display colors
    ├── results/             ← One JSON per club + aggregate files
    │   ├── real_madrid.json
    │   ├── ...              (33 club files)
    │   ├── _scores.json     ← Ranked scores
    │   └── _aggregate.json  ← Full feature×club matrix
    ├── screenshots/         ← Homepage PNGs used for visual audit
    │   ├── 01-real-madrid.png
    │   └── ...
    └── crosscheck/          ← Browser verification tooling
        ├── CLAUDE.md        ← Cross-check agent instructions
        ├── recalculate-scores.js  ← Score recalculation script
        ├── capture_elements.py    ← Main Playwright capture script
        ├── redo_bad_weak.py       ← Re-capture failed screenshots
        ├── recapture_deleted.py   ← Batch re-capture with cookie strategies
        ├── recapture_round5.py    ← Full-page screenshot + PIL crop approach
        └── img/             ← 536 element-level screenshot evidence files
```

To add a new page type (e.g. player page), copy the `homepage/` folder and adapt the rubric, features, and crosscheck instructions.

## How it connects to the app

`lib/data.ts` re-exports everything from this folder:

```ts
export { CATEGORIES, PRODUCTS, FEATURES, ... } from '@/analysis';
```

`analysis/index.ts` is the barrel that wires homepage data to the app:
- `CATEGORIES` and `FEATURES` come from `homepage/categories.ts` and `homepage/features.ts`
- `PRODUCTS` comes from the shared `products.ts`

`homepage/features.ts` imports all `homepage/results/*.json` files and builds presence maps automatically. When you add a new JSON result, the app picks it up after you add the import in `homepage/features.ts`.

## Scoring system

Each feature has a **tier** (A–F) with asymmetric weights:

| Tier | Name | Yes weight | No weight |
|------|------|-----------|-----------|
| A | Must-have | +1 | −3 |
| B | Commercial table stakes | +2 | −2 |
| C | ROI driver | +5 | −2 |
| D | Differentiator | +8 | −1 |
| E | Content depth | +3 | −1 |
| F | Experimental | +8 | 0 |

A club's total score = sum of all feature weights (Yes or No). Scores can be negative.

---

## Common tasks

### Re-run analysis for an existing club

1. Take a fresh full-page screenshot of their homepage
2. Replace the old PNG in `homepage/screenshots/` (keep the same filename)
3. Ask Claude: "Re-analyze `homepage/screenshots/XX-club-name.png` against the `homepage/HOME-PAGE.md` rubric and update `homepage/results/club_name.json`"
4. Recalculate scores: `node homepage/crosscheck/recalculate-scores.js`

### Add a new club

1. **Take a screenshot** — full-page PNG of the homepage, save to `homepage/screenshots/` as `NN-club-name.png`

2. **Add the product** to `products.ts`:
   ```ts
   { id: 'club_name', name: 'Club Name', type: 'club', sport: 'football',
     logo: 'https://upload.wikimedia.org/wikipedia/...' },
   ```

3. **Run the analysis** — ask Claude:
   > "Analyze the screenshot at `homepage/screenshots/NN-club-name.png` against all features in `homepage/HOME-PAGE.md`. Write the result to `homepage/results/club_name.json` using the same JSON format as the other result files."

4. **Add the import** in `homepage/features.ts`:
   ```ts
   import club_name from './results/club_name.json';
   ```
   And add to the `RESULTS` object:
   ```ts
   club_name: club_name.features,
   ```

5. **Recalculate scores and regenerate aggregates**:
   ```bash
   node homepage/crosscheck/recalculate-scores.js
   ```

6. **Verify** — run `npx next build` to confirm no errors.

### Remove a club

1. Delete its JSON from `homepage/results/`
2. Delete its screenshot from `homepage/screenshots/`
3. Remove its entry from `products.ts`
4. Remove its import and `RESULTS` entry from `homepage/features.ts`
5. Recalculate: `node homepage/crosscheck/recalculate-scores.js`

### Cross-check features in browser

See `homepage/crosscheck/CLAUDE.md` for the full procedure. Quick start:

```
Cross-check all features in "Hero" category
using rubric: analysis/homepage/HOME-PAGE.md
```

### Batch analysis (multiple clubs in parallel)

For analyzing many clubs at once, split them across 4–5 parallel agents balanced by screenshot file size (large PNGs take more context). Each agent gets:
- The full `homepage/HOME-PAGE.md` rubric
- A batch of screenshot paths
- Instructions to read one PNG at a time, evaluate all features, and write the JSON

### Change the rubric

If you modify `homepage/HOME-PAGE.md` (add/remove/change features):
1. Update the feature definitions in `homepage/features.ts` (add/remove `feat()` calls)
2. Re-run analysis for all clubs — the old JSONs won't have the new feature keys
3. Recalculate: `node homepage/crosscheck/recalculate-scores.js`

### Change scoring weights

Edit the per-feature weights in `homepage/features.ts` — each feature's `weightYes` and `weightNo` are set in the `feat()` call. The rubric in `homepage/HOME-PAGE.md` is the reference.
