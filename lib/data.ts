/* ================================================================
   lib/data.ts  --  Re-exports from analysis/

   All feature matrix data now lives in the analysis/ folder.
   This file exists for backward compatibility with existing imports.
   ================================================================ */

export {
  // Types
  type PresenceStatus,
  type CategoryId,
  type BandId,
  type TierId,
  type ProductType,
  type SportType,
  type Category,
  type Product,
  type Feature,
  type BandMeta,

  // Data
  CATEGORIES,
  BAND_META,
  PRODUCTS,
  ALL_IDS,
  FEATURES,

  // Helpers
  computeBands,
} from '@/analysis';

// ── Hospitality back-half (Plan 02-13) ──
// Re-export the 55 hospitality features for the /hospitality route.
// Homepage `FEATURES` export above stays untouched (D-20 score-data invariant).
export { FEATURES as HOSPITALITY_FEATURES } from '@/analysis/hospitality/features';
