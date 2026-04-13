/* ================================================================
   analysis/features.ts  --  35 features with weights & presence

   Features are organized by category:
   - Revenue & Commerce (5)
   - Content & Engagement (11)
   - Brand & Identity (6)
   - UX & Utility (5)
   - Differentiators (7)
   ================================================================ */

import type { Feature } from './types';
import { ALL_IDS } from './products';
import { makePresence } from './presence';

export const FEATURES: Feature[] = [
  // ── Revenue & Commerce ──
  {
    id: 'F01', name: 'E-Commerce / Shop',
    desc: 'Online store link, merchandise showcase, kit display, product cards on homepage',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','eintracht','rb_leipzig','valencia_cf','atp_tour','f1','motogp','nba','mlb'],
      ['club_brugge','mls'],
    ),
  },
  {
    id: 'F02', name: 'Ticketing',
    desc: 'Ticket purchase links, match-day info, hospitality',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','rb_leipzig','valencia_cf','atp_tour','uefa','f1','nba','mls','mlb'],
      ['juventus','eintracht','itf_tennis','motogp'],
    ),
  },
  {
    id: 'F03', name: 'Membership Program',
    desc: 'Named fan membership, loyalty programs, subscription tiers — direct recurring revenue and fan data capture',
    cat: 'revenue', weight: 5,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','man_united','tottenham','inter_milan','bvb_dortmund','atletico_madrid','ac_milan','juventus','vfb_stuttgart','sl_benfica','west_ham','brentford','motogp','nba','mls','mlb'],
      ['psg','arsenal','chelsea','aston_villa','eintracht','club_brugge','rb_leipzig','valencia_cf','f1'],
    ),
  },
  {
    id: 'F04', name: 'Streaming / OTT Platform',
    desc: 'Club-branded TV/streaming service — premium content monetization and global fan reach',
    cat: 'revenue', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_united','tottenham','chelsea','inter_milan','ac_milan','sl_benfica','valencia_cf','atp_tour','f1','motogp','nba','mls','mlb'],
      ['arsenal','man_city','bvb_dortmund','newcastle','west_ham','brentford','club_brugge','eintracht','rb_leipzig','uefa'],
    ),
  },
  {
    id: 'F29', name: 'Corporate / Hospitality',
    desc: 'Dedicated hospitality packages, VIP experiences, corporate event sections — premium revenue stream beyond standard ticketing',
    cat: 'revenue', weight: 3,
    presence: makePresence(
      [],
      ['fc_barcelona','bayern_munich','liverpool','atletico_madrid','chelsea','newcastle','west_ham','brentford','valencia_cf','motogp'],
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
    cat: 'content', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','rb_leipzig','valencia_cf','atp_tour','itf_tennis','uefa','f1','motogp','nba','mls','mlb'],
      ['juventus'],
    ),
  },
  {
    id: 'F06b', name: 'Standings / League Table',
    desc: 'Current league table, standings widget, ranking display on homepage — competitive context for fans',
    cat: 'content', weight: 2,
    presence: makePresence(
      ['inter_milan','atletico_madrid','vfb_stuttgart','eintracht','club_brugge','itf_tennis','atp_tour','uefa','f1','motogp','nba','mls','mlb'],
      ['fc_barcelona','liverpool','chelsea','rb_leipzig'],
    ),
  },
  {
    id: 'F07', name: 'Video Player / Section',
    desc: 'Dedicated video area, embedded video player, video content cards with play buttons on homepage',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','club_brugge','valencia_cf','atp_tour','itf_tennis','uefa','f1','motogp','nba','mls','mlb'],
      ['aston_villa','brentford','eintracht','rb_leipzig'],
    ),
  },
  {
    id: 'F07b', name: 'Match Highlights',
    desc: 'Specific match highlight clips, replay content, goal clips — highest-demand video format',
    cat: 'content', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','arsenal','tottenham','chelsea','ac_milan','sl_benfica','atp_tour','uefa','f1','motogp','mls','mlb'],
      ['psg','man_united','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','juventus','newcastle','vfb_stuttgart','club_brugge','itf_tennis','valencia_cf'],
    ),
  },
  {
    id: 'F07c', name: 'Photo Gallery',
    desc: 'Photo gallery section, image grid, behind-the-scenes photo collections on homepage',
    cat: 'content', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','arsenal','chelsea','ac_milan','newcastle','vfb_stuttgart','sl_benfica','brentford','club_brugge','valencia_cf','uefa','motogp'],
      ['liverpool','man_city','man_united','tottenham','inter_milan','bvb_dortmund','juventus','west_ham','atp_tour','itf_tennis','f1','nba','mlb'],
    ),
  },
  {
    id: 'F08', name: 'Hero / Banner',
    desc: 'Hero carousel, featured story banner — first impression and editorial control point',
    cat: 'content', weight: 3,
    presence: makePresence(ALL_IDS, []),
  },
  {
    id: 'F09', name: 'Navigation Depth',
    desc: 'Rich top nav with 6+ items — information architecture and content discoverability',
    cat: 'content', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','itf_tennis','rb_leipzig','valencia_cf','atp_tour','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },
  {
    id: 'F27', name: 'Live Scores Ticker',
    desc: 'Persistent scores/results bar at top of page showing live or recent scores across the league — real-time engagement hook',
    cat: 'content', weight: 2,
    presence: makePresence(
      ['atp_tour','uefa','nba','mls','mlb'],
      ['liverpool','arsenal','tottenham','west_ham','vfb_stuttgart','f1'],
    ),
  },
  {
    id: 'F28', name: 'Social Media Feed Embed',
    desc: 'Embedded social feed (Instagram grid, Twitter feed) on homepage — cross-platform content amplification beyond icon links',
    cat: 'content', weight: 1,
    presence: makePresence(
      ['brentford','uefa'],
      ['fc_barcelona','psg','vfb_stuttgart','valencia_cf'],
    ),
  },
  {
    id: 'F30', name: 'Player Profiles / Squad',
    desc: 'Player cards, squad roster, player spotlight sections on homepage — fan connection and content personalisation driver',
    cat: 'content', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','arsenal','liverpool','man_united','chelsea','inter_milan','atletico_madrid','ac_milan','eintracht','itf_tennis','atp_tour','uefa','f1','motogp'],
      ['bayern_munich','psg','man_city','tottenham','juventus','aston_villa','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','rb_leipzig','valencia_cf','nba','mlb'],
    ),
  },
  {
    id: 'F32', name: 'Podcast / Audio',
    desc: 'Podcast sections, audio content, "listen" CTAs — growing content format for commute-time fan engagement',
    cat: 'content', weight: 1,
    presence: makePresence(
      ['itf_tennis'],
      ['fc_barcelona','bayern_munich','man_united','bvb_dortmund','aston_villa','ac_milan','newcastle','motogp','nba','mlb'],
    ),
  },

  // ── Brand & Identity ──
  {
    id: 'F10', name: "Women's Team Visibility",
    desc: "Dedicated women's team content on homepage — brand inclusivity and growing market segment",
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','man_united','arsenal','chelsea','atletico_madrid','ac_milan','west_ham','brentford','itf_tennis','uefa'],
      ['psg','tottenham','bvb_dortmund','aston_villa','juventus','newcastle','vfb_stuttgart','valencia_cf'],
    ),
  },
  {
    id: 'F11', name: 'Academy / Youth',
    desc: 'Youth development, academy section on homepage — brand storytelling and talent pipeline visibility',
    cat: 'brand', weight: 2,
    presence: makePresence(
      ['fc_barcelona','bayern_munich','man_city','man_united','arsenal','chelsea','ac_milan','vfb_stuttgart','west_ham','valencia_cf','uefa'],
      ['real_madrid','liverpool','tottenham','inter_milan','newcastle','itf_tennis','f1'],
    ),
  },
  {
    id: 'F12', name: 'Social Media Links',
    desc: 'Social platform icons/links in header or footer — cross-platform engagement and audience routing',
    cat: 'brand', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','rb_leipzig','valencia_cf','atp_tour','itf_tennis','uefa','mls','nba','f1','motogp','mlb'],
      [],
    ),
  },
  {
    id: 'F13', name: 'Sponsor Showcase',
    desc: 'Dedicated partner/sponsor section, logo grid — commercial partner value demonstration',
    cat: 'brand', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','rb_leipzig','valencia_cf','atp_tour','itf_tennis','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },
  {
    id: 'F14', name: 'App Download Promotion',
    desc: 'Mobile app download badges/CTAs — mobile-first fan relationship and push notification channel',
    cat: 'brand', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','man_city','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','ac_milan','juventus','sl_benfica','west_ham','brentford','atp_tour','f1','motogp','nba','mls','mlb'],
      ['vfb_stuttgart'],
    ),
  },
  {
    id: 'F31', name: 'Trophy / Honours Showcase',
    desc: 'Visual trophy cabinet, honours list, trophy icons — emotional brand equity and competitive prestige display',
    cat: 'brand', weight: 2,
    presence: makePresence(
      ['bayern_munich','liverpool','inter_milan','valencia_cf'],
      ['real_madrid','fc_barcelona','man_city','juventus'],
    ),
  },

  // ── UX & Utility ──
  {
    id: 'F15', name: 'Search',
    desc: 'Search icon/bar on homepage — content discoverability and user intent capture',
    cat: 'ux', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','rb_leipzig','valencia_cf','atp_tour','itf_tennis','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },
  {
    id: 'F16', name: 'Multi-Language',
    desc: 'Language selector visible — global accessibility for international fanbase',
    cat: 'ux', weight: 3,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','inter_milan','bvb_dortmund','atletico_madrid','ac_milan','juventus','vfb_stuttgart','sl_benfica','eintracht','club_brugge','rb_leipzig','valencia_cf','atp_tour','itf_tennis','motogp','mls'],
      ['uefa'],
    ),
  },
  {
    id: 'F17', name: 'Login / Registration',
    desc: 'User account, sign-in button — first-party data capture and personalization gateway',
    cat: 'ux', weight: 4,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','rb_leipzig','valencia_cf','atp_tour','itf_tennis','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },
  {
    id: 'F18', name: 'Newsletter Signup',
    desc: 'Email subscription form/CTA — owned audience channel for re-engagement',
    cat: 'ux', weight: 3,
    presence: makePresence(
      ['bayern_munich','liverpool','west_ham','atp_tour'],
      ['real_madrid','fc_barcelona','chelsea','bvb_dortmund','aston_villa','sl_benfica','itf_tennis','motogp'],
    ),
  },
  {
    id: 'F19', name: 'Footer Navigation',
    desc: 'Multi-column footer with organized links — secondary navigation and legal compliance',
    cat: 'ux', weight: 1,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','psg','liverpool','man_city','arsenal','man_united','tottenham','chelsea','inter_milan','bvb_dortmund','atletico_madrid','aston_villa','ac_milan','juventus','newcastle','vfb_stuttgart','sl_benfica','west_ham','brentford','club_brugge','eintracht','itf_tennis','rb_leipzig','valencia_cf','atp_tour','uefa','f1','motogp','nba','mls','mlb'],
      [],
    ),
  },

  // ── Differentiators ──
  {
    id: 'F20', name: 'Stadium / Museum / Tours',
    desc: 'Stadium experience, museum, tour promotion — heritage monetization and matchday revenue',
    cat: 'diff', weight: 2,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich','liverpool','tottenham','aston_villa','sl_benfica','brentford','valencia_cf'],
      ['psg','chelsea','man_united','inter_milan','bvb_dortmund','juventus','newcastle','club_brugge','eintracht','mlb'],
    ),
  },
  {
    id: 'F21', name: 'Foundation / Charity',
    desc: 'Club foundation, CSR, community section — brand purpose and community goodwill',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['real_madrid','fc_barcelona','psg','liverpool','chelsea','newcastle','brentford','valencia_cf','uefa'],
      ['bayern_munich','man_city','man_united','arsenal','tottenham','atletico_madrid','ac_milan','eintracht'],
    ),
  },
  {
    id: 'F22', name: 'Esports / Gaming',
    desc: 'Gaming section, esports, fantasy — youth audience acquisition and digital-native engagement',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['f1','motogp','nba','mlb','uefa'],
      ['fc_barcelona','bvb_dortmund','atletico_madrid','mls'],
    ),
  },
  {
    id: 'F23', name: 'Heritage / History',
    desc: 'Club history, "since XXXX", heritage messaging, trophy displays — emotional brand equity',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['bayern_munich','liverpool','juventus','sl_benfica','motogp'],
      ['real_madrid','fc_barcelona','bvb_dortmund','valencia_cf'],
    ),
  },
  {
    id: 'F24', name: 'Other Sports',
    desc: 'Non-football sports coverage — cross-sport brand extension',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['real_madrid','fc_barcelona','bayern_munich'],
      ['sl_benfica','nba'],
    ),
  },
  {
    id: 'F25', name: 'Transfer Tracker',
    desc: 'Transfer hub, tracker widget — high-traffic seasonal engagement driver',
    cat: 'diff', weight: 1,
    presence: makePresence(
      ['uefa','mls'],
      ['eintracht'],
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
