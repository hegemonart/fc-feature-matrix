/* ================================================================
   app/hospitality/page.tsx — Plan 02-13 → unified by Plan 02-21

   Server Component shell for the Hospitality Packages back-half pilot.
   Mirrors app/page.tsx (homepage RSC pattern):
     1. Loads HOSPITALITY_FEATURES + HOSPITALITY_CATEGORIES, filters
        PRODUCTS down to the 5 pilot clubs (Man City, Tottenham, Real
        Madrid, PSG, Chelsea).
     2. Pre-computes per-pilot-product weighted scores INLINE — does
        NOT call lib/scoring.getProductScores (that's hardcoded to
        homepage FEATURES; D-20 score-data invariant forbids touching it).
     3. Resolves BUILD_DATE from process.env (set in next.config.ts).
     4. Hands serializable props to <MatrixIsland area="hospitality">
        — the SAME client island that powers /, just configured for
        hospitality data + active "Hospitality Packages" tab pill.

   Plan 02-21 unified the hospitality view with the homepage matrix
   shell: same HeaderBar, TopNav, sidebar (CategoryFilter+TypeFilter),
   matrix grid, detail panel, hover tooltips. The earlier minimal
   <HospitalityIsland> standalone view is removed.
   ================================================================ */

import {
  PRODUCTS,
  HOSPITALITY_FEATURES,
  HOSPITALITY_CATEGORIES,
} from '@/lib/data';
import MatrixIsland from '../MatrixIsland';

const PILOT_IDS = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];

export const metadata = {
  title: 'FC Benchmark — Hospitality Packages (Pilot: 5 clubs)',
  description:
    '55-feature hospitality matrix across 5 pilot clubs (Man City, Tottenham, Real Madrid, PSG, Chelsea).',
};

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
    <MatrixIsland
      area="hospitality"
      products={pilotProducts}
      features={HOSPITALITY_FEATURES}
      categories={HOSPITALITY_CATEGORIES}
      scores={scores}
      buildDate={buildDate}
    />
  );
}
