/* ================================================================
   lib/data.ts  --  Single source of truth for FC Feature Matrix
   ================================================================ */

// ── Types ──

export type PresenceStatus = 'full' | 'partial' | 'absent';

export type CategoryId = 'revenue' | 'content' | 'brand' | 'ux' | 'diff';

export type BandId = 'table_stakes' | 'expected' | 'competitive' | 'innovation';

export type ProductType = 'club' | 'league' | 'governing';

export type SportType = 'football' | 'motorsport' | 'basketball' | 'baseball';

export interface Category {
  id: CategoryId;
  name: string;
  color: string;
}

export interface Product {
  id: string;
  name: string;
  type: ProductType;
  sport: SportType;
}

export interface Feature {
  id: string;
  name: string;
  desc: string;
  cat: CategoryId;
  weight: number;
  presence: Record<string, PresenceStatus>;
  /** Computed by computeBands() */
  adoption?: number;
  /** Computed by computeBands() */
  adoptionPct?: number;
  /** Computed by computeBands() */
  band?: BandId;
}

export interface BandMeta {
  id: BandId;
  name: string;
  cls: string;
}

// ── Constants ──

export const CATEGORIES: Category[] = [
  { id: 'revenue', name: 'Revenue & Commerce',   color: '#ef4444' },
  { id: 'content', name: 'Content & Engagement', color: '#3b82f6' },
  { id: 'brand',   name: 'Brand & Identity',     color: '#8b5cf6' },
  { id: 'ux',      name: 'UX & Utility',         color: '#06b6d4' },
  { id: 'diff',    name: 'Differentiators',       color: '#f59e0b' },
];

export const PRODUCTS: Product[] = [
  { id: 'real_madrid',     name: 'Real Madrid',     type: 'club',      sport: 'football' },
  { id: 'fc_barcelona',    name: 'FC Barcelona',    type: 'club',      sport: 'football' },
  { id: 'bayern_munich',   name: 'Bayern Munich',   type: 'club',      sport: 'football' },
  { id: 'psg',             name: 'PSG',             type: 'club',      sport: 'football' },
  { id: 'liverpool',       name: 'Liverpool',       type: 'club',      sport: 'football' },
  { id: 'man_city',        name: 'Man City',        type: 'club',      sport: 'football' },
  { id: 'arsenal',         name: 'Arsenal',         type: 'club',      sport: 'football' },
  { id: 'man_united',      name: 'Man United',      type: 'club',      sport: 'football' },
  { id: 'tottenham',       name: 'Tottenham',       type: 'club',      sport: 'football' },
  { id: 'chelsea',         name: 'Chelsea',         type: 'club',      sport: 'football' },
  { id: 'inter_milan',     name: 'Inter Milan',     type: 'club',      sport: 'football' },
  { id: 'bvb_dortmund',    name: 'BVB Dortmund',    type: 'club',      sport: 'football' },
  { id: 'atletico_madrid', name: 'Atletico Madrid', type: 'club',      sport: 'football' },
  { id: 'aston_villa',     name: 'Aston Villa',     type: 'club',      sport: 'football' },
  { id: 'ac_milan',        name: 'AC Milan',        type: 'club',      sport: 'football' },
  { id: 'juventus',        name: 'Juventus',        type: 'club',      sport: 'football' },
  { id: 'newcastle',       name: 'Newcastle',       type: 'club',      sport: 'football' },
  { id: 'vfb_stuttgart',   name: 'VfB Stuttgart',   type: 'club',      sport: 'football' },
  { id: 'sl_benfica',      name: 'SL Benfica',      type: 'club',      sport: 'football' },
  { id: 'west_ham',        name: 'West Ham',        type: 'club',      sport: 'football' },
  { id: 'uefa',            name: 'UEFA',            type: 'governing', sport: 'football' },
  { id: 'f1',              name: 'Formula 1',       type: 'league',    sport: 'motorsport' },
  { id: 'motogp',          name: 'MotoGP',          type: 'league',    sport: 'motorsport' },
  { id: 'nba',             name: 'NBA',             type: 'league',    sport: 'basketball' },
  { id: 'mls',             name: 'MLS',             type: 'league',    sport: 'football' },
  { id: 'mlb',             name: 'MLB',             type: 'league',    sport: 'baseball' },
];

export const ALL_IDS: string[] = PRODUCTS.map(p => p.id);

// ── Helpers ──

export function makePresence(
  full: string[],
  partial: string[],
): Record<string, PresenceStatus> {
  const m: Record<string, PresenceStatus> = {};
  ALL_IDS.forEach(id => (m[id] = 'absent'));
  full.forEach(id => (m[id] = 'full'));
  partial.forEach(id => (m[id] = 'partial'));
  return m;
}

// ── Features (29 total: F01-F26 including F06b, F07b, F07c) ──

export const FEATURES: Feature[] = [
  // ── Revenue & Commerce ──
  {
    id: 'F01', name: 'E-Commerce / Shop',
    desc: 'Online store link, merchandise showcase, kit display, product cards on homepage',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','f1','motogp','nba'],
      ['arsenal'],
    ),
  },
  {
    id: 'F02', name: 'Ticketing',
    desc: 'Ticket purchase links, match-day info, hospitality',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','liverpool','man_city','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','vfb_stuttgart','west_ham','f1','nba'],
      ['bayern_munich','psg','arsenal','juventus','newcastle','sl_benfica','motogp','mls','mlb'],
    ),
  },
  {
    id: 'F03', name: 'Membership Program',
    desc: 'Named fan membership, loyalty programs, subscription tiers — direct recurring revenue and fan data capture',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','man_united','tottenham','inter_milan','atletico_madrid','juventus','sl_benfica','west_ham','motogp','nba','mls','mlb'],
      ['chelsea','bvb_dortmund','aston_villa','vfb_stuttgart'],
    ),
  },
  {
    id: 'F04', name: 'Streaming / OTT Platform',
    desc: 'Club-branded TV/streaming service — premium content monetization and global fan reach',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','tottenham','chelsea','inter_milan','ac_milan','sl_benfica','f1','motogp','nba','mls'],
      ['bvb_dortmund','uefa'],
    ),
  },

  // ── Content & Engagement ──
  {
    id: 'F05', name: 'News Feed',
    desc: 'Editorial news articles, grid/cards with thumbnails — primary traffic driver and SEO engine',
    cat: 'content', weight: 4,
    presence: makePresence(ALL_IDS, []),
  },
  {
    id: 'F06', name: 'Fixtures & Results',
    desc: 'Upcoming match schedule, past match scores/results widget visible on homepage — core matchday engagement',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','psg','liverpool','arsenal','tottenham','inter_milan','atletico_madrid','ac_milan','vfb_stuttgart','uefa','f1','motogp','nba','mls','mlb'],
      ['bayern_munich','man_city','man_united','chelsea','bvb_dortmund','aston_villa','juventus','newcastle','sl_benfica','west_ham'],
    ),
  },
  {
    id: 'F06b', name: 'Standings / League Table',
    desc: 'Current league table, standings widget, ranking display on homepage — competitive context for fans',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['inter_milan','atletico_madrid','vfb_stuttgart','uefa','f1','motogp','nba','mlb'],
      ['liverpool'],
    ),
  },
  {
    id: 'F07', name: 'Video Player / Section',
    desc: 'Dedicated video area, embedded video player, video content cards with play buttons on homepage',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','ac_milan','juventus','newcastle','sl_benfica','uefa','f1','motogp','nba','mls','mlb'],
      ['atletico_madrid','aston_villa','vfb_stuttgart'],
    ),
  },
  {
    id: 'F07b', name: 'Match Highlights',
    desc: 'Specific match highlight clips, replay content, goal clips — highest-demand video format',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','arsenal','tottenham','chelsea','ac_milan','sl_benfica','uefa','f1','motogp'],
      ['psg','man_united','inter_milan','bvb_dortmund','atletico_madrid','mls'],
    ),
  },
  {
    id: 'F07c', name: 'Photo Gallery',
    desc: 'Photo gallery section, image grid, behind-the-scenes photo collections on homepage',
    cat: 'content', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','arsenal','bvb_dortmund','ac_milan','juventus','newcastle','vfb_stuttgart','uefa','motogp'],
      ['liverpool','chelsea'],
    ),
  },
  {
    id: 'F08', name: 'Hero / Banner',
    desc: 'Hero carousel, featured story banner — first impression and editorial control point',
    cat: 'content', weight: 4,
    presence: makePresence(ALL_IDS, []),
  },
  {
    id: 'F09', name: 'Navigation Depth',
    desc: 'Rich top nav with 6+ items — information architecture and content discoverability',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },

  // ── Brand & Identity ──
  {
    id: 'F10', name: "Women's Team Visibility",
    desc: "Dedicated women's team content on homepage — brand inclusivity and growing market segment",
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['fc_barcelona','liverpool','man_city','man_united','arsenal','chelsea','atletico_madrid','ac_milan','west_ham','uefa'],
      ['psg','tottenham','inter_milan','bvb_dortmund','aston_villa','juventus','newcastle'],
    ),
  },
  {
    id: 'F11', name: 'Academy / Youth',
    desc: 'Youth development, academy section on homepage — brand storytelling and talent pipeline visibility',
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['fc_barcelona','man_city','man_united','arsenal','bvb_dortmund','ac_milan','juventus','vfb_stuttgart','west_ham','uefa'],
      ['real_madrid','bayern_munich','liverpool','tottenham','chelsea','inter_milan','atletico_madrid','aston_villa'],
    ),
  },
  {
    id: 'F12', name: 'Social Media Links',
    desc: 'Social platform icons/links in header or footer — cross-platform engagement and audience routing',
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','mls','nba','f1','motogp','mlb'],
      ['west_ham','uefa'],
    ),
  },
  {
    id: 'F13', name: 'Sponsor Showcase',
    desc: 'Dedicated partner/sponsor section, logo grid — commercial partner value demonstration',
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','sl_benfica','west_ham','f1','motogp','nba','mlb'],
      ['vfb_stuttgart','uefa'],
    ),
  },
  {
    id: 'F14', name: 'App Download Promotion',
    desc: 'Mobile app download badges/CTAs — mobile-first fan relationship and push notification channel',
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','liverpool','man_united','tottenham','chelsea','bvb_dortmund','aston_villa','juventus','sl_benfica','f1','motogp','nba','mlb'],
      ['inter_milan','ac_milan','mls'],
    ),
  },

  // ── UX & Utility ──
  {
    id: 'F15', name: 'Search',
    desc: 'Search icon/bar on homepage — content discoverability and user intent capture',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','bvb_dortmund','atletico_madrid','ac_milan','newcastle','sl_benfica','west_ham','uefa','f1','motogp','nba','mls','mlb'],
      ['inter_milan','aston_villa','juventus','vfb_stuttgart'],
    ),
  },
  {
    id: 'F16', name: 'Multi-Language',
    desc: 'Language selector visible — global accessibility for international fanbase',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona'],
      ['atletico_madrid','uefa'],
    ),
  },
  {
    id: 'F17', name: 'Login / Registration',
    desc: 'User account, sign-in button — first-party data capture and personalization gateway',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','man_united','tottenham','chelsea','atletico_madrid','ac_milan','sl_benfica','west_ham','uefa','f1','motogp','nba','mls','mlb'],
      ['arsenal','inter_milan','bvb_dortmund','juventus','newcastle'],
    ),
  },
  {
    id: 'F18', name: 'Newsletter Signup',
    desc: 'Email subscription form/CTA — owned audience channel for re-engagement',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['liverpool','west_ham','motogp','nba'],
      ['chelsea','bvb_dortmund','aston_villa','vfb_stuttgart'],
    ),
  },
  {
    id: 'F19', name: 'Footer Navigation',
    desc: 'Multi-column footer with organized links — secondary navigation and legal compliance',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },

  // ── Differentiators ──
  {
    id: 'F20', name: 'Stadium / Museum / Tours',
    desc: 'Stadium experience, museum, tour promotion — heritage monetization and matchday revenue',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','tottenham','aston_villa'],
      ['psg','chelsea','man_united','bvb_dortmund','juventus','sl_benfica'],
    ),
  },
  {
    id: 'F21', name: 'Foundation / Charity',
    desc: 'Club foundation, CSR, community section — brand purpose and community goodwill',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['real_madrid','fc_barcelona','liverpool','chelsea','newcastle','uefa'],
      ['psg','arsenal','ac_milan'],
    ),
  },
  {
    id: 'F22', name: 'Esports / Gaming',
    desc: 'Gaming section, esports, fantasy — youth audience acquisition and digital-native engagement',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['aston_villa','f1','motogp','nba'],
      ['mlb'],
    ),
  },
  {
    id: 'F23', name: 'Heritage / History',
    desc: 'Club history, "since XXXX", heritage messaging, trophy displays — emotional brand equity',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['bayern_munich','inter_milan','juventus','sl_benfica'],
      ['liverpool','man_united','bvb_dortmund','uefa'],
    ),
  },
  {
    id: 'F24', name: 'Other Sports',
    desc: 'Non-football sports coverage — cross-sport brand extension',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['real_madrid','bayern_munich','motogp'],
      [],
    ),
  },
  {
    id: 'F25', name: 'Transfer Tracker',
    desc: 'Transfer hub, tracker widget — high-traffic seasonal engagement driver',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['uefa','mls'],
      [],
    ),
  },
  {
    id: 'F26', name: 'Fan Feedback / Surveys',
    desc: 'User feedback, "help shape" sections — community co-creation and product insight',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['f1'],
      [],
    ),
  },
];

// ── Band metadata ──

export const BAND_META: BandMeta[] = [
  { id: 'table_stakes', name: 'Table Stakes', cls: 'table_stakes' },
  { id: 'expected',     name: 'Expected',     cls: 'expected' },
  { id: 'competitive',  name: 'Competitive',  cls: 'competitive' },
  { id: 'innovation',   name: 'Innovation',   cls: 'innovation' },
];

// ── Band computation ──

export function computeBands(): void {
  const totalProducts = PRODUCTS.length;
  FEATURES.forEach(f => {
    let score = 0;
    ALL_IDS.forEach(id => {
      if (f.presence[id] === 'full') score += 1;
      else if (f.presence[id] === 'partial') score += 0.5;
    });
    f.adoption = score / totalProducts;
    f.adoptionPct = Math.round(f.adoption * 100);
    if (f.adoption >= 0.9) f.band = 'table_stakes';
    else if (f.adoption >= 0.7) f.band = 'expected';
    else if (f.adoption >= 0.4) f.band = 'competitive';
    else f.band = 'innovation';
  });
}

// Auto-compute on import
computeBands();
