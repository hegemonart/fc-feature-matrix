/* ================================================================
   analysis/index.ts  --  Barrel export + band computation
   ================================================================ */

export * from './types';
export { CATEGORIES, BAND_META } from './categories';
export { PRODUCTS, ALL_IDS } from './products';
export { makePresence } from './presence';
export { FEATURES } from './features';

import { FEATURES } from './features';
import { PRODUCTS } from './products';

// ── Band computation (runs once on import) ──

export function computeBands(): void {
  const totalProducts = PRODUCTS.length;
  FEATURES.forEach(f => {
    let score = 0;
    PRODUCTS.forEach(p => {
      if (f.presence[p.id] === 'full') score += 1;
    });
    f.adoption = score / totalProducts;
    f.adoptionPct = Math.round(f.adoption * 100);
    if (f.adoption >= 0.9) f.band = 'table_stakes';
    else if (f.adoption >= 0.7) f.band = 'expected';
    else if (f.adoption >= 0.4) f.band = 'competitive';
    else f.band = 'innovation';
  });
}

computeBands();
