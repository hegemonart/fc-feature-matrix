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
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { getDisplayDate } from '@/lib/settings';
import { cookies } from 'next/headers';
import MatrixIsland from '../MatrixIsland';

const PILOT_IDS = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];

export const metadata = {
  title: 'FC Benchmark — Hospitality Packages (Pilot: 5 clubs)',
  description:
    '55-feature hospitality matrix across 5 pilot clubs (Man City, Tottenham, Real Madrid, PSG, Chelsea).',
};

export default async function HospitalityPage() {
  // Resolve auth server-side — same pattern as app/page.tsx.
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.getAll().map(c => `${c.name}=${c.value}`).join('; ');
  const session = getSessionFromCookie(cookieHeader);
  const user = session ? await getUserByEmail(session.email) : null;
  const initialAuth = {
    authed: !!user,
    isAdmin: user?.isAdmin ?? false,
    isPremium: user?.isPremium ?? false,
  };
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

  // Compute adoptionPct + band for pilot clubs only (denominator = 5, not all 33).
  // HOSPITALITY_FEATURES are exported without computeBands(), so both fields
  // are undefined until we set them here server-side. Mirrors computeBands()
  // logic from analysis/index.ts but uses pilot product count as denominator.
  const RANK_BAND = ['innovation', 'competitive', 'expected', 'table_stakes'] as const;
  const TIER_FLOOR: Record<string, number> = { A: 2, B: 1, C: 0, D: 0, E: 0, F: 0 };
  const n = pilotProducts.length;

  const featuresWithAdoption = HOSPITALITY_FEATURES.map(f => {
    const presentCount = pilotProducts.filter(p => f.presence[p.id] === 'full').length;
    const adoption = presentCount / n;
    const adoptionPct = Math.round(adoption * 100);
    const adoptionRank = adoption >= 0.9 ? 3 : adoption >= 0.7 ? 2 : adoption >= 0.4 ? 1 : 0;
    const band = RANK_BAND[Math.max(adoptionRank, TIER_FLOOR[f.tier] ?? 0)];
    return { ...f, adoption, adoptionPct, band };
  });

  // site_settings → BUILD_DATE env fallback. See lib/settings.ts.
  const buildDate = await getDisplayDate();

  return (
    <MatrixIsland
      area="hospitality"
      products={pilotProducts}
      features={featuresWithAdoption}
      categories={HOSPITALITY_CATEGORIES}
      initialAuth={initialAuth}
      scores={scores}
      buildDate={buildDate}
    />
  );
}
