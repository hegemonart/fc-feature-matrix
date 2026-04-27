/* ================================================================
   app/hospitality/page.tsx — Plan 02-13 (D-19, HOSP-03)

   Server Component shell for the Hospitality Packages back-half pilot.
   Mirrors app/page.tsx (homepage RSC pattern):
     1. Loads HOSPITALITY_FEATURES + filters PRODUCTS down to the 5
        pilot clubs (Man City, Tottenham, Real Madrid, PSG, Chelsea).
     2. Pre-computes per-pilot-product weighted scores INLINE — does
        NOT call lib/scoring.getProductScores (that's hardcoded to
        homepage FEATURES; D-20 score-data invariant forbids touching it).
     3. Resolves BUILD_DATE from process.env (set in next.config.ts).
     4. Hands serializable props to <HospitalityIsland> (Client island).

   The "Pilot: 5 clubs" label lives inside <HospitalityIsland> to keep
   it co-located with the matrix it describes.
   ================================================================ */

import { PRODUCTS, HOSPITALITY_FEATURES } from '@/lib/data';
import HospitalityIsland from './HospitalityIsland';

const PILOT_IDS = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];

export default function HospitalityPage() {
  const pilotProducts = PRODUCTS.filter(p => PILOT_IDS.includes(p.id));

  // Pre-compute weighted scores inline (D-20: do not modify lib/scoring.ts).
  // Mirrors getProductScores math — sum of weightYes for 'full' presence
  // + weightNo otherwise — but iterates HOSPITALITY_FEATURES instead of
  // homepage FEATURES.
  const scores: Record<string, number> = {};
  pilotProducts.forEach(p => {
    let total = 0;
    HOSPITALITY_FEATURES.forEach(f => {
      total += f.presence[p.id] === 'full' ? f.weightYes : f.weightNo;
    });
    scores[p.id] = total;
  });

  const buildDate = process.env.BUILD_DATE ?? '';

  return (
    <HospitalityIsland
      pilotProducts={pilotProducts}
      hospitalityFeatures={HOSPITALITY_FEATURES}
      scores={scores}
      buildDate={buildDate}
    />
  );
}
