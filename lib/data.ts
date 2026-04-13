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
