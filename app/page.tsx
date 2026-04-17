/* ================================================================
   app/page.tsx — Server Component shell (D-17)

   Loads the homepage matrix data on the server (PRODUCTS, FEATURES
   already shipped with computed bands + adoption from
   analysis/homepage/features.ts via lib/data.ts; per-product totals
   from lib/scoring.ts) and passes everything as serializable props
   into <MatrixIsland>, the Client Component island that owns ALL
   interactive state.

   See:
     - .planning/phases/infra-redesign-v2/04-PLAN.md
     - app/MatrixIsland.tsx (the island)
   ================================================================ */

import { PRODUCTS, FEATURES } from '@/lib/data';
import { getProductScores } from '@/lib/scoring';
import MatrixIsland from './MatrixIsland';

export default function FeatureMatrixPage() {
  // Pre-compute per-product totals on the server so the Client island
  // doesn't need to re-derive them from PRODUCTS x FEATURES on first
  // paint. Object is fully serializable for the RSC → Client boundary.
  const scores: Record<string, number> = {};
  PRODUCTS.forEach(p => {
    scores[p.id] = getProductScores(p.id).weightedScore;
  });

  // BUILD_DATE is set in next.config.ts at build time (D-12). Resolve it
  // to a string here so the Client component never reaches into
  // process.env (avoids a client-side env access + hydration mismatch).
  const buildDate = process.env.BUILD_DATE ?? '';

  return (
    <MatrixIsland
      products={PRODUCTS}
      features={FEATURES}
      scores={scores}
      buildDate={buildDate}
    />
  );
}
