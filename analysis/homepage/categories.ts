/* ================================================================
   analysis/categories.ts  --  12 feature sections & band metadata
   ================================================================ */

import type { Category, BandMeta } from '../types';

export const CATEGORIES: Category[] = [
  { id: 'header_nav',          name: 'Header & Navigation',              color: '#06b6d4' },
  { id: 'hero',                name: 'Hero',                             color: '#8b5cf6' },
  { id: 'match_fixtures',      name: 'Match & Fixtures',                 color: '#22c55e' },
  { id: 'content',             name: 'Content & Editorial',              color: '#3b82f6' },
  { id: 'tickets_hospitality', name: 'Tickets & Hospitality',            color: '#ef4444' },
  { id: 'commerce',            name: 'Commerce & Store',                 color: '#f97316' },
  { id: 'community',           name: 'Community & Membership',           color: '#ec4899' },
  { id: 'heritage',            name: 'Heritage & Identity',              color: '#a855f7' },
  { id: 'players_teams',       name: 'Players & Teams',                  color: '#14b8a6' },
  { id: 'partners_sponsors',   name: 'Partners, Sponsors & App',         color: '#f59e0b' },
  { id: 'personalization',     name: 'Personalization & Engagement',     color: '#6366f1' },
  { id: 'footer_nav',          name: 'Footer',                           color: '#64748b' },
];

export const BAND_META: BandMeta[] = [
  { id: 'table_stakes', name: 'Table Stakes', cls: 'table_stakes' },
  { id: 'expected',     name: 'Expected',     cls: 'expected' },
  { id: 'competitive',  name: 'Competitive',  cls: 'competitive' },
  { id: 'innovation',   name: 'Innovation',   cls: 'innovation' },
];
