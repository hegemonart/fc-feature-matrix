/* ================================================================
   analysis/products.ts  --  25 clubs, leagues & governing bodies
   (Only products with homepage analysis results)
   ================================================================ */

import type { Product } from './types';

const W = 'https://upload.wikimedia.org/wikipedia';

export const PRODUCTS: Product[] = [
  { id: 'real_madrid',     name: 'Real Madrid',     type: 'club',      sport: 'football',    logo: `${W}/en/thumb/5/56/Real_Madrid_CF.svg/200px-Real_Madrid_CF.svg.png` },
  { id: 'fc_barcelona',    name: 'FC Barcelona',    type: 'club',      sport: 'football',    logo: `${W}/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/200px-FC_Barcelona_%28crest%29.svg.png` },
  { id: 'bayern_munich',   name: 'Bayern Munich',   type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/8/8d/FC_Bayern_M%C3%BCnchen_logo_%282024%29.svg/200px-FC_Bayern_M%C3%BCnchen_logo_%282024%29.svg.png` },
  { id: 'psg',             name: 'PSG',             type: 'club',      sport: 'football',    logo: `${W}/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/200px-Paris_Saint-Germain_F.C..svg.png` },
  { id: 'liverpool',       name: 'Liverpool',       type: 'club',      sport: 'football',    logo: `${W}/en/thumb/0/0c/Liverpool_FC.svg/200px-Liverpool_FC.svg.png` },
  { id: 'man_city',        name: 'Man City',        type: 'club',      sport: 'football',    logo: `${W}/en/thumb/e/eb/Manchester_City_FC_badge.svg/200px-Manchester_City_FC_badge.svg.png` },
  { id: 'arsenal',         name: 'Arsenal',         type: 'club',      sport: 'football',    logo: `${W}/en/thumb/5/53/Arsenal_FC.svg/200px-Arsenal_FC.svg.png` },
  { id: 'man_united',      name: 'Man United',      type: 'club',      sport: 'football',    logo: `${W}/en/thumb/7/7a/Manchester_United_FC_crest.svg/200px-Manchester_United_FC_crest.svg.png` },
  { id: 'tottenham',       name: 'Tottenham',       type: 'club',      sport: 'football',    logo: `${W}/en/thumb/0/05/Spurs_2017_badge.svg/200px-Spurs_2017_badge.svg.png` },
  { id: 'chelsea',         name: 'Chelsea',         type: 'club',      sport: 'football',    logo: `${W}/en/thumb/c/cc/Chelsea_FC.svg/200px-Chelsea_FC.svg.png` },
  { id: 'inter_milan',     name: 'Inter Milan',     type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/200px-FC_Internazionale_Milano_2021.svg.png` },
  { id: 'bvb_dortmund',    name: 'BVB Dortmund',    type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/6/67/Borussia_Dortmund_logo.svg/200px-Borussia_Dortmund_logo.svg.png` },
  { id: 'atletico_madrid', name: 'Atletico Madrid', type: 'club',      sport: 'football',    logo: `${W}/en/thumb/f/f9/Atletico_Madrid_Logo_2024.svg/200px-Atletico_Madrid_Logo_2024.svg.png` },
  { id: 'aston_villa',     name: 'Aston Villa',     type: 'club',      sport: 'football',    logo: `${W}/en/thumb/9/9a/Aston_Villa_FC_new_crest.svg/200px-Aston_Villa_FC_new_crest.svg.png` },
  { id: 'ac_milan',        name: 'AC Milan',        type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/d/d0/Logo_of_AC_Milan.svg/200px-Logo_of_AC_Milan.svg.png` },
  { id: 'juventus',        name: 'Juventus',        type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/e/ed/Juventus_FC_-_logo_black_%28Italy%2C_2020%29.svg/200px-Juventus_FC_-_logo_black_%28Italy%2C_2020%29.svg.png`, darkLogo: true },
  { id: 'newcastle',       name: 'Newcastle',       type: 'club',      sport: 'football',    logo: `${W}/en/thumb/5/56/Newcastle_United_Logo.svg/200px-Newcastle_United_Logo.svg.png` },
  { id: 'vfb_stuttgart',   name: 'VfB Stuttgart',   type: 'club',      sport: 'football',    logo: `${W}/commons/thumb/e/eb/VfB_Stuttgart_1893_Logo.svg/200px-VfB_Stuttgart_1893_Logo.svg.png` },
  { id: 'sl_benfica',      name: 'SL Benfica',      type: 'club',      sport: 'football',    logo: `${W}/en/thumb/a/a2/SL_Benfica_logo.svg/200px-SL_Benfica_logo.svg.png` },
  { id: 'west_ham',        name: 'West Ham',        type: 'club',      sport: 'football',    logo: `${W}/en/thumb/c/c2/West_Ham_United_FC_logo.svg/200px-West_Ham_United_FC_logo.svg.png` },
  { id: 'uefa',            name: 'UEFA',            type: 'governing', sport: 'football',    logo: `${W}/en/thumb/9/9d/UEFA_full_logo.svg/200px-UEFA_full_logo.svg.png` },
  { id: 'f1',              name: 'Formula 1',       type: 'league',    sport: 'motorsport',  logo: `${W}/commons/thumb/2/2d/Formula_One_logo.svg/200px-Formula_One_logo.svg.png` },
  { id: 'motogp',          name: 'MotoGP',          type: 'league',    sport: 'motorsport',  logo: `${W}/commons/thumb/f/f9/MotoGP_logo_%282024%29.svg/200px-MotoGP_logo_%282024%29.svg.png`, darkLogo: true },
  { id: 'mls',             name: 'MLS',             type: 'league',    sport: 'football',    logo: `${W}/commons/thumb/c/c7/Major_League_Soccer_logo.svg/200px-Major_League_Soccer_logo.svg.png` },
  { id: 'mlb',             name: 'MLB',             type: 'league',    sport: 'baseball',    logo: `${W}/commons/thumb/a/a6/Major_League_Baseball_logo.svg/200px-Major_League_Baseball_logo.svg.png` },
];

export const ALL_IDS: string[] = PRODUCTS.map(p => p.id);
