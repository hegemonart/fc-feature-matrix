/* ================================================================
   analysis/categories.ts  --  Feature categories & band metadata
   ================================================================ */

import type { Category, BandMeta } from './types';

export const CATEGORIES: Category[] = [
  { id: 'revenue', name: 'Revenue & Commerce',   color: '#ef4444' },
  { id: 'content', name: 'Content & Engagement', color: '#3b82f6' },
  { id: 'brand',   name: 'Brand & Identity',     color: '#8b5cf6' },
  { id: 'ux',      name: 'UX & Utility',         color: '#06b6d4' },
  { id: 'diff',    name: 'Differentiators',       color: '#f59e0b' },
];

export const BAND_META: BandMeta[] = [
  { id: 'table_stakes', name: 'Table Stakes', cls: 'table_stakes' },
  { id: 'expected',     name: 'Expected',     cls: 'expected' },
  { id: 'competitive',  name: 'Competitive',  cls: 'competitive' },
  { id: 'innovation',   name: 'Innovation',   cls: 'innovation' },
];
