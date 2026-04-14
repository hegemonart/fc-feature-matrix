/* ================================================================
   analysis/index.ts  --  Barrel export + band computation
   ================================================================ */

export * from './types';
export { CATEGORIES, BAND_META } from './homepage/categories';
export { PRODUCTS, ALL_IDS } from './products';
export { FEATURES } from './homepage/features';

import { FEATURES } from './homepage/features';
import { PRODUCTS } from './products';

// ── Band computation (runs once on import) ──

/**
 * Compute adoption bands for each feature.
 * Bands are based on adoption rate BUT floored by tier:
 *   Tier A (must-have)        → minimum band: "expected"
 *   Tier B (commercial)       → minimum band: "competitive"
 *   Tier C–F                  → pure adoption-based
 * This prevents absurd labels like "Language Switcher = Innovation"
 * when the feature is a must-have that many sites simply miss.
 */
export function computeBands(): void {
  const totalProducts = PRODUCTS.length;

  // Minimum band floor per tier (higher index = higher floor)
  const BAND_RANK: Record<string, number> = {
    innovation: 0, competitive: 1, expected: 2, table_stakes: 3,
  };
  const RANK_BAND: Record<number, 'innovation' | 'competitive' | 'expected' | 'table_stakes'> = {
    0: 'innovation', 1: 'competitive', 2: 'expected', 3: 'table_stakes',
  };
  const TIER_FLOOR: Record<string, number> = {
    A: 2, // expected
    B: 1, // competitive
    C: 0, D: 0, E: 0, F: 0,
  };

  FEATURES.forEach(f => {
    let score = 0;
    PRODUCTS.forEach(p => {
      if (f.presence[p.id] === 'full') score += 1;
    });
    f.adoption = score / totalProducts;
    f.adoptionPct = Math.round(f.adoption * 100);

    // Adoption-based band
    let adoptionRank: number;
    if (f.adoption >= 0.9) adoptionRank = 3;
    else if (f.adoption >= 0.7) adoptionRank = 2;
    else if (f.adoption >= 0.4) adoptionRank = 1;
    else adoptionRank = 0;

    // Apply tier floor
    const floor = TIER_FLOOR[f.tier] ?? 0;
    f.band = RANK_BAND[Math.max(adoptionRank, floor)];
  });
}

computeBands();
