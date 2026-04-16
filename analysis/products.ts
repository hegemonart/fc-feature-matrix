/* ================================================================
   analysis/products.ts  --  25 clubs, leagues & governing bodies
   (Only products with homepage analysis results)
   ================================================================ */

import type { Product } from './types';

const L = '/img/logos';

export const PRODUCTS: Product[] = [
  { id: 'real_madrid',     name: 'Real Madrid',     type: 'club',      sport: 'football',    logo: `${L}/real_madrid.svg` },
  { id: 'fc_barcelona',    name: 'FC Barcelona',    type: 'club',      sport: 'football',    logo: `${L}/fc_barcelona.svg` },
  { id: 'bayern_munich',   name: 'Bayern Munich',   type: 'club',      sport: 'football',    logo: `${L}/bayern_munich.svg` },
  { id: 'psg',             name: 'PSG',             type: 'club',      sport: 'football',    logo: `${L}/psg.svg` },
  { id: 'liverpool',       name: 'Liverpool',       type: 'club',      sport: 'football',    logo: `${L}/liverpool.svg` },
  { id: 'man_city',        name: 'Man City',        type: 'club',      sport: 'football',    logo: `${L}/man_city.svg` },
  { id: 'arsenal',         name: 'Arsenal',         type: 'club',      sport: 'football',    logo: `${L}/arsenal.svg` },
  { id: 'man_united',      name: 'Man United',      type: 'club',      sport: 'football',    logo: `${L}/man_united.svg` },
  { id: 'tottenham',       name: 'Tottenham',       type: 'club',      sport: 'football',    logo: `${L}/tottenham.svg` },
  { id: 'chelsea',         name: 'Chelsea',         type: 'club',      sport: 'football',    logo: `${L}/chelsea.svg` },
  { id: 'inter_milan',     name: 'Inter Milan',     type: 'club',      sport: 'football',    logo: `${L}/inter_milan.svg` },
  { id: 'bvb_dortmund',    name: 'BVB Dortmund',    type: 'club',      sport: 'football',    logo: `${L}/bvb_dortmund.svg` },
  { id: 'atletico_madrid', name: 'Atletico Madrid', type: 'club',      sport: 'football',    logo: `${L}/atletico_madrid.svg` },
  { id: 'aston_villa',     name: 'Aston Villa',     type: 'club',      sport: 'football',    logo: `${L}/aston_villa.svg` },
  { id: 'ac_milan',        name: 'AC Milan',        type: 'club',      sport: 'football',    logo: `${L}/ac_milan.svg` },
  { id: 'juventus',        name: 'Juventus',        type: 'club',      sport: 'football',    logo: `${L}/juventus.svg`, darkLogo: true },
  { id: 'newcastle',       name: 'Newcastle',       type: 'club',      sport: 'football',    logo: `${L}/newcastle.svg` },
  { id: 'vfb_stuttgart',   name: 'VfB Stuttgart',   type: 'club',      sport: 'football',    logo: `${L}/vfb_stuttgart.svg` },
  { id: 'sl_benfica',      name: 'SL Benfica',      type: 'club',      sport: 'football',    logo: `${L}/sl_benfica.svg` },
  { id: 'west_ham',        name: 'West Ham',        type: 'club',      sport: 'football',    logo: `${L}/west_ham.svg` },
  { id: 'uefa',            name: 'UEFA',            type: 'governing', sport: 'football',    logo: `${L}/uefa.svg` },
  { id: 'f1',              name: 'Formula 1',       type: 'league',    sport: 'motorsport',  logo: `${L}/f1.svg` },
  { id: 'motogp',          name: 'MotoGP',          type: 'league',    sport: 'motorsport',  logo: `${L}/motogp.svg`, darkLogo: true },
  { id: 'mls',             name: 'MLS',             type: 'league',    sport: 'football',    logo: `${L}/mls.svg` },
  { id: 'mlb',             name: 'MLB',             type: 'league',    sport: 'baseball',    logo: `${L}/mlb.svg` },
  { id: 'nba',             name: 'NBA',             type: 'league',    sport: 'basketball',  logo: `${L}/nba.svg` },
  { id: 'brentford',       name: 'Brentford',       type: 'club',      sport: 'football',    logo: `${L}/brentford.svg` },
  { id: 'atp_tour',        name: 'ATP Tour',        type: 'league',    sport: 'tennis',      logo: `${L}/atp_tour.svg` },
  { id: 'club_brugge',     name: 'Club Brugge',     type: 'club',      sport: 'football',    logo: `${L}/club_brugge.svg` },
  { id: 'eintracht',       name: 'Eintracht Frankfurt', type: 'club',  sport: 'football',    logo: `${L}/eintracht.svg` },
  { id: 'itf_tennis',      name: 'ITF Tennis',      type: 'governing', sport: 'tennis',      logo: `${L}/itf_tennis.svg` },
  { id: 'rb_leipzig',      name: 'RB Leipzig',      type: 'club',      sport: 'football',    logo: `${L}/rb_leipzig.svg` },
  { id: 'valencia_cf',     name: 'Valencia CF',     type: 'club',      sport: 'football',    logo: `${L}/valencia_cf.svg` },
];

export const ALL_IDS: string[] = PRODUCTS.map(p => p.id);
