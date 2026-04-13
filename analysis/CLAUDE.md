# analysis/ folder

This folder is the **data layer** for the FC Benchmark app. The app itself lives in `app/` and `lib/` — everything here feeds into it.

## Architecture

```
analysis/
├── HOME-PAGE.md          ← 67-feature rubric (source of truth for scoring)
├── PLAYBOOK-...md        ← Methodology documentation
├── categories.ts         ← 12 feature categories with display colors
├── features.ts           ← 67 features — imports presence from results/*.json
├── products.ts           ← 25 products (clubs/leagues/governing bodies)
├── types.ts              ← Shared TypeScript types
├── index.ts              ← Barrel export + band computation
├── results/              ← One JSON per club + aggregate files
│   ├── real_madrid.json
│   ├── fc_barcelona.json
│   ├── ...               (25 club files)
│   ├── _scores.json      ← Ranked scores
│   └── _aggregate.json   ← Full feature×club matrix
└── screenshots/          ← Homepage PNGs used for visual audit
    ├── 01-real-madrid.png
    └── ...
```

## How it connects to the app

`lib/data.ts` re-exports everything from this folder:

```ts
export { CATEGORIES, PRODUCTS, FEATURES, ... } from '@/analysis';
```

`features.ts` imports all `results/*.json` files and builds presence maps automatically. When you add a new JSON result, the app picks it up after you add the import in `features.ts`.

## Scoring system

Each feature has a **tier** (A–F) with asymmetric weights:

| Tier | Name | Yes weight | No weight |
|------|------|-----------|-----------|
| A | Must-have | +1 | −8 |
| B | Commercial table stakes | +2 | −5 |
| C | ROI driver | +5 | −3 |
| D | Differentiator | +8 | −1 |
| E | Content depth | +3 | −1 |
| F | Experimental | +8 | 0 |

A club's total score = sum of all 67 feature weights (Yes or No). Scores can be negative.

---

## Common tasks

### Re-run analysis for an existing club

1. Take a fresh full-page screenshot of their homepage
2. Replace the old PNG in `screenshots/` (keep the same filename)
3. Ask Claude: "Re-analyze `screenshots/XX-club-name.png` against the HOME-PAGE.md rubric and update `results/club_name.json`"
4. Regenerate aggregates (see below)

### Add a new club

1. **Take a screenshot** — full-page PNG of the homepage, save to `screenshots/` as `NN-club-name.png`

2. **Add the product** to `products.ts`:
   ```ts
   { id: 'club_name', name: 'Club Name', type: 'club', sport: 'football',
     logo: 'https://upload.wikimedia.org/wikipedia/...' },
   ```

3. **Run the analysis** — ask Claude:
   > "Analyze the screenshot at `analysis/screenshots/NN-club-name.png` against all 67 features in `analysis/HOME-PAGE.md`. Write the result to `analysis/results/club_name.json` using the same JSON format as the other result files."

   The JSON format is:
   ```json
   {
     "product_id": "club_name",
     "screenshot": "NN-club-name.png",
     "analyzed_at": "2026-04-13",
     "total_score": 0,
     "features": {
       "language_switcher_in_header": true,
       "login_account": false,
       ... (all 67 feature keys)
     }
   }
   ```

4. **Add the import** in `features.ts`:
   ```ts
   import club_name from './results/club_name.json';
   ```
   And add to the `RESULTS` object:
   ```ts
   club_name: club_name.features,
   ```

5. **Regenerate aggregates** — run this in `analysis/results/`:
   ```bash
   node -e "
   const fs = require('fs');
   const files = fs.readdirSync('.').filter(f => f.endsWith('.json') && !f.startsWith('_'));
   const clubs = files.map(f => JSON.parse(fs.readFileSync(f, 'utf8')));
   clubs.sort((a, b) => b.total_score - a.total_score);

   const scores = {
     generated_at: new Date().toISOString().split('T')[0],
     total_clubs: clubs.length,
     rankings: clubs.map((c, i) => ({
       rank: i + 1,
       product_id: c.product_id,
       screenshot: c.screenshot,
       total_score: c.total_score,
       yes_count: Object.values(c.features).filter(v => v === true).length,
       no_count: Object.values(c.features).filter(v => v === false).length,
       feature_count: Object.keys(c.features).length
     }))
   };
   fs.writeFileSync('_scores.json', JSON.stringify(scores, null, 2));

   const allFeatureKeys = Object.keys(clubs[0].features).sort();
   const aggregate = {
     generated_at: scores.generated_at,
     total_clubs: clubs.length,
     total_features: allFeatureKeys.length,
     features: {}
   };
   allFeatureKeys.forEach(key => {
     const adoption = clubs.filter(c => c.features[key] === true).length;
     aggregate.features[key] = {
       adoption_count: adoption,
       adoption_pct: Math.round(adoption / clubs.length * 100),
       clubs_yes: clubs.filter(c => c.features[key] === true).map(c => c.product_id),
       clubs_no: clubs.filter(c => c.features[key] !== true).map(c => c.product_id)
     };
   });
   fs.writeFileSync('_aggregate.json', JSON.stringify(aggregate, null, 2));
   console.log('Done:', clubs.length, 'clubs');
   "
   ```

6. **Verify** — run `npx next build` to confirm no errors.

### Remove a club

1. Delete its JSON from `results/`
2. Delete its screenshot from `screenshots/`
3. Remove its entry from `products.ts`
4. Remove its import and `RESULTS` entry from `features.ts`
5. Regenerate aggregates (step 5 above)

### Batch analysis (multiple clubs in parallel)

For analyzing many clubs at once, split them across 4–5 parallel agents balanced by screenshot file size (large PNGs take more context). Each agent gets:
- The full HOME-PAGE.md rubric
- A batch of screenshot paths
- Instructions to read one PNG at a time, evaluate all 67 features, and write the JSON

Example batching for 25 clubs used 5 agents with ~5 screenshots each. Large files (30MB+) should be in a batch with fewer screenshots.

### Change the rubric

If you modify `HOME-PAGE.md` (add/remove/change features):
1. Update the feature definitions in `features.ts` (add/remove `feat()` calls)
2. Re-run analysis for all clubs — the old JSONs won't have the new feature keys
3. Regenerate aggregates

### Change scoring weights

Edit the tier weights in `features.ts` — each feature's `weightYes` and `weightNo` are set in the `feat()` call. The rubric in `HOME-PAGE.md` is the reference.
