# FC Benchmark // April 2026

UX benchmarking tool for top sports club and league websites. Analyzes 59 homepage features across 33 organizations, scores them with asymmetric Fibonacci weighting, and presents an interactive comparison matrix.

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
app/            — Next.js pages and styles
lib/            — Data layer re-exports
analysis/
  HOME-PAGE.md  — 59-feature scoring rubric (source of truth)
  features.ts   — Feature definitions and tier weights
  products.ts   — 33 products (clubs, leagues, governing bodies)
  categories.ts — 12 feature categories
  results/      — One JSON per organization + aggregates
  crosscheck/   — Reusable browser cross-check instructions
  screenshots/  — Full-page homepage PNGs
public/         — Static assets
```

## Scoring

Each feature has a tier (A-F) with asymmetric weights:

| Tier | Yes | No |
|------|-----|-----|
| A Must-have | +1 | -8 |
| B Commercial | +2 | -5 |
| C ROI driver | +5 | -3 |
| D Differentiator | +8 | -1 |
| E Content depth | +3 | -1 |
| F Experimental | +8 | 0 |

## Coverage

33 organizations: 20 football clubs, 5 US leagues, 4 governing bodies, 4 other sports. See `analysis/products.ts` for the full list.
