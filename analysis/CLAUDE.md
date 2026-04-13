# analysis/ folder

This folder contains all data and reference material for the UX benchmarking matrix. The app itself lives in `app/` and `lib/` — this folder is the **data layer**.

## Files

### `types.ts`
Shared TypeScript types used across all analysis files. Defines `PresenceStatus` ('full' | 'absent'), `CategoryId`, `BandId`, `Product`, `Feature`, etc. Change here if you need to add a new field to products or features.

### `categories.ts`
The 5 feature categories (Revenue & Commerce, Content & Engagement, Brand & Identity, UX & Utility, Differentiators) with their display colors. Also contains `BAND_META` — the 4 adoption bands (Table Stakes ≥90%, Expected ≥70%, Competitive ≥40%, Innovation <40%).

### `products.ts`
All 33 clubs, leagues, and governing bodies being benchmarked. Each has an id, name, type (club/league/governing), sport, and Wikipedia logo URL. `ALL_IDS` is derived from this list. To add a new club, add an entry here and then add its presence data in `features.ts`.

### `features.ts`
The core matrix — 35 features (F01–F32 including variants F06b, F07b, F07c) with:
- `name` and `desc` — what the feature is
- `cat` — which category it belongs to
- `weight` (1–5) — importance for scoring
- `presence` — which products have it, built via `makePresence()`

This is the file you edit most often when auditing a new club or updating feature coverage.

### `presence.ts`
The `makePresence()` helper function. Takes two arrays of product IDs — `full` (present) and `partial` (also treated as present, kept for backward compat) — and returns a presence map defaulting everything else to 'absent'.

### `index.ts`
Barrel export that re-exports everything from the other files. Also runs `computeBands()` on import, which calculates adoption percentages and assigns bands (table_stakes/expected/competitive/innovation) to each feature based on how many products have it.

### `screenshots/`
27 PNG screenshots of each club/league website homepage. These are the visual references used when manually auditing which features a site has. Not consumed by the app — purely reference material. Named `01-real-madrid.png` through `27-club_brugge.png`.

### `analysis-batch1.md`, `analysis-batch2.md`, `analysis-batch3.md`
Notes from the original audit passes. Context on methodology and decisions made during data collection.

## How it connects to the app

`lib/data.ts` is a thin re-export file:
```ts
export { CATEGORIES, PRODUCTS, FEATURES, ... } from '@/analysis';
```

All app code imports from `@/lib/data` as before. The analysis folder is the source of truth — `lib/data.ts` is just a passthrough.

## Common tasks

**Add a new club:**
1. Add entry to `products.ts`
2. Add the club's id to relevant feature presence arrays in `features.ts`
3. Optionally add a screenshot to `screenshots/`

**Add a new feature:**
1. Add entry to `features.ts` with id, name, desc, cat, weight, and presence
2. Bands recalculate automatically on import

**Change scoring thresholds:**
Edit `computeBands()` in `index.ts` — the `>=0.9`, `>=0.7`, `>=0.4` cutoffs.

**Change feature weights:**
Edit the `weight` field on the feature in `features.ts`. Weights range 1–5 and affect weighted scores in `lib/scoring.ts`.
