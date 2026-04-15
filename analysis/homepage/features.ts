/* ================================================================
   analysis/features.ts  --  61 homepage features with presence
   built from individual club analysis JSON results.

   Feature metadata comes from HOME-PAGE.md rubric.
   Presence data comes from analysis/results/*.json files.
   ================================================================ */

import type { Feature, CategoryId, TierId, PresenceStatus } from '../types';
import { ALL_IDS } from '../products';

// ── Import all analysis results ──
import real_madrid from './results/real_madrid.json';
import fc_barcelona from './results/fc_barcelona.json';
import bayern_munich from './results/bayern_munich.json';
import psg from './results/psg.json';
import liverpool from './results/liverpool.json';
import man_city from './results/man_city.json';
import arsenal from './results/arsenal.json';
import man_united from './results/man_united.json';
import tottenham from './results/tottenham.json';
import chelsea from './results/chelsea.json';
import inter_milan from './results/inter_milan.json';
import bvb_dortmund from './results/bvb_dortmund.json';
import atletico_madrid from './results/atletico_madrid.json';
import aston_villa from './results/aston_villa.json';
import ac_milan from './results/ac_milan.json';
import juventus from './results/juventus.json';
import newcastle from './results/newcastle.json';
import vfb_stuttgart from './results/vfb_stuttgart.json';
import sl_benfica from './results/sl_benfica.json';
import west_ham from './results/west_ham.json';
import uefa from './results/uefa.json';
import f1 from './results/f1.json';
import motogp from './results/motogp.json';
import mls from './results/mls.json';
import mlb from './results/mlb.json';
import nba from './results/nba.json';
import brentford from './results/brentford.json';
import atp_tour from './results/atp_tour.json';
import club_brugge from './results/club_brugge.json';
import eintracht from './results/eintracht.json';
import itf_tennis from './results/itf_tennis.json';
import rb_leipzig from './results/rb_leipzig.json';
import valencia_cf from './results/valencia_cf.json';

// ── All results indexed by product_id ──
const RESULTS: Record<string, Record<string, boolean>> = {
  real_madrid: real_madrid.features,
  fc_barcelona: fc_barcelona.features,
  bayern_munich: bayern_munich.features,
  psg: psg.features,
  liverpool: liverpool.features,
  man_city: man_city.features,
  arsenal: arsenal.features,
  man_united: man_united.features,
  tottenham: tottenham.features,
  chelsea: chelsea.features,
  inter_milan: inter_milan.features,
  bvb_dortmund: bvb_dortmund.features,
  atletico_madrid: atletico_madrid.features,
  aston_villa: aston_villa.features,
  ac_milan: ac_milan.features,
  juventus: juventus.features,
  newcastle: newcastle.features,
  vfb_stuttgart: vfb_stuttgart.features,
  sl_benfica: sl_benfica.features,
  west_ham: west_ham.features,
  uefa: uefa.features,
  f1: f1.features,
  motogp: motogp.features,
  mls: mls.features,
  mlb: mlb.features,
  nba: nba.features,
  brentford: brentford.features,
  atp_tour: atp_tour.features,
  club_brugge: club_brugge.features,
  eintracht: eintracht.features,
  itf_tennis: itf_tennis.features,
  rb_leipzig: rb_leipzig.features,
  valencia_cf: valencia_cf.features,
};

/** Build a presence map for a given feature key from JSON results */
function buildPresence(featureKey: string): Record<string, PresenceStatus> {
  const m: Record<string, PresenceStatus> = {};
  ALL_IDS.forEach(id => {
    const result = RESULTS[id];
    m[id] = result && result[featureKey] ? 'full' : 'absent';
  });
  return m;
}

/** Helper to define a feature concisely */
function feat(
  id: string,
  key: string,
  name: string,
  desc: string,
  cat: CategoryId,
  tier: TierId,
  weightYes: number,
  weightNo: number,
): Feature {
  return {
    id,
    key,
    name,
    desc,
    cat,
    tier,
    weightYes,
    weightNo,
    weight: weightYes,   // backward compat
    presence: buildPresence(key),
  };
}

// ================================================================
//  69 FEATURES — organized by HOME-PAGE.md sections
// ================================================================

export const FEATURES: Feature[] = [
  // ── 1. Header & Navigation ──
  feat('H01', 'language_switcher_in_header', 'Language Switcher in Header',
    'Lets users switch site language from the header', 'header_nav', 'A', 1, -3),
  feat('H02', 'login_account', 'Login / Account',
    'Entry point for user account, sign-in, or profile', 'header_nav', 'A', 1, -3),
  feat('H03', 'search_input_in_header', 'Search Input in Header',
    'Search bar or icon visible in the top nav', 'header_nav', 'E', 3, -1),
  feat('H04', 'shop_shortcut_in_header', 'Shop Shortcut in Header',
    'Top-nav link sending users straight to the club store', 'header_nav', 'B', 2, -2),
  feat('H05', 'tickets_shortcut_in_header', 'Tickets Shortcut in Header',
    'Top-nav link sending users straight to tickets', 'header_nav', 'B', 2, -2),
  feat('H06', 'sponsor_lockup_in_header', 'Sponsor Lockup in Header',
    'Sponsor logo integrated alongside the club crest in the header', 'header_nav', 'D', 8, -1),

  // ── 2. Hero ──
  feat('R01', 'hero_carousel', 'Hero Carousel',
    'Hero rotates through multiple slides to show more content at the top', 'hero', 'E', 3, -1),
  feat('R02', 'secondary_editorial_strip_below_hero', 'Secondary Editorial Strip Below Hero',
    'Row of editorial cards just under the hero for quick content access', 'hero', 'A', 1, -3),
  feat('R03', 'brand_sponsor_highlighted_in_hero', 'Brand Sponsor in Hero',
    'Large sponsor visual taking significant space in the first view', 'hero', 'D', 8, -1),

  // ── 3. Match & Fixtures ──
  feat('M01', 'next_match_block', 'Next-Match Block',
    'Shows the upcoming match so fans know when the team plays next', 'match_fixtures', 'A', 1, -3),
  feat('M02', 'next_match_feature_rich', 'Next-Match Feature-Rich',
    'Next-match block adds extras like countdown, tickets, or broadcaster info', 'match_fixtures', 'C', 5, -2),
  feat('M03', 'results_block', 'Results Block',
    'Shows recent match scores for quick catch-up', 'match_fixtures', 'E', 3, -1),
  feat('M04', 'standings_block', 'Standings Block',
    'League table access directly from the homepage', 'match_fixtures', 'E', 3, -1),

  // ── 4. Content (News, Video, Editorial) ──
  feat('C01', 'dedicated_news_section', 'Dedicated News Section',
    'A section of the homepage clearly devoted to news stories', 'content', 'A', 1, -3),
  feat('C02', 'news_rich_structure', 'News Rich Structure',
    'News section uses multiple UX features like tabs, mixed media, or hero card', 'content', 'E', 3, -1),
  feat('C03', 'homepage_video_block', 'Homepage Video Block',
    'A dedicated area for video content, separate from news', 'content', 'B', 2, -2),
  feat('C04', 'episodic_docu_series', 'Episodic / Docu-Series Block',
    'Promotes a series of episodes or a campaign with multiple chapters', 'content', 'D', 8, -1),
  feat('C05', 'video_thumbnails_inline', 'Video Thumbnails Inline with News',
    'Video items shown mixed into the news grid', 'content', 'E', 3, -1),
  feat('C06', 'documentary_promo', 'Documentary Promo Block',
    'Specific promo for a documentary film, often with a paywall CTA', 'content', 'C', 5, -2),
  feat('C07', 'social_native_content', 'Social-Native Content Block',
    'Stories-style tiles or a block that mimics Instagram/TikTok UI', 'content', 'D', 8, -1),
  feat('C08', 'podcast_audio', 'Podcast / Audio Content',
    'Area dedicated to the club\'s podcasts or audio shows', 'content', 'D', 8, -1),
  feat('C09', 'photo_gallery_block', 'Photo Gallery Block',
    'A standalone photo gallery block', 'content', 'E', 3, -1),
  feat('C10', 'press_conference_block', 'Press Conference / Interview Block',
    'Card or block featuring a manager talking to press or being interviewed', 'content', 'E', 3, -1),
  feat('C11', 'transfer_news', 'Transfer News Block',
    'A dedicated area for transfer market news', 'content', 'D', 8, -1),
  feat('C12', 'interactive_fan_poll', 'Interactive Fan Voting / Poll',
    'A poll or vote that fans can actually interact with on the page', 'content', 'D', 8, -1),

  // ── 5. Tickets & Hospitality ──
  feat('T01', 'tickets_block', 'Tickets Block',
    'A real block selling or promoting tickets, not just a nav link', 'tickets_hospitality', 'C', 5, -2),
  feat('T02', 'hospitality_block', 'Hospitality Block',
    'Promotes premium hospitality packages with some descriptive content', 'tickets_hospitality', 'C', 5, -2),
  feat('T03', 'stadium_tours_block', 'Stadium Tours Block',
    'Promotes tours of the stadium with content, not just a nav link', 'tickets_hospitality', 'C', 5, -2),

  // ── 6. Commerce & Store ──
  feat('S01', 'store_block', 'Store Block',
    'Any block dedicated to the official club store', 'commerce', 'B', 2, -2),
  feat('S02', 'store_individual_products', 'Store Shows Individual Products',
    'Store block features specific product cards, each with its own buy button', 'commerce', 'C', 5, -2),
  feat('S03', 'member_only_commerce', 'Member-Only Commerce',
    'Products or discounts available only to signed-up members', 'commerce', 'C', 5, -2),

  // ── 7. Community & Membership ──
  feat('N01', 'newsletter_signup', 'Newsletter Signup Block',
    'An email capture block for joining the club\'s newsletter', 'community', 'B', 2, -2),
  feat('N02', 'fan_club_signup', 'Fan-Club / Free Membership',
    'Promotes joining the club\'s free official fan community or membership', 'community', 'C', 5, -2),
  feat('N03', 'paid_membership', 'Paid Membership / Subscriptions',
    'Promotes paid tiers like premium access, streaming, or subscription plans', 'community', 'C', 5, -2),
  feat('N04', 'draws_contests', 'Draws / Contests Block',
    'Promotes giveaways or competitions available to members or fans', 'community', 'D', 8, -1),

  // ── 8. Heritage & Identity ──
  feat('I01', 'trophies_honours', 'Trophies / Honours Block',
    'Showcases the club\'s trophies, titles, or honours', 'heritage', 'E', 3, -1),
  feat('I02', 'heritage_past_content', 'Heritage / Past Content',
    'Content about club history, past seasons, legends, or hall of fame', 'heritage', 'E', 3, -1),
  feat('I03', 'stadium_content_block', 'Stadium Content Block',
    'A block with the stadium as its main subject, not just a background photo', 'heritage', 'E', 3, -1),
  feat('I04', 'museum_block', 'Museum Block',
    'A dedicated block promoting the club\'s museum', 'heritage', 'C', 5, -2),

  // ── 9. Players & Teams ──
  feat('P01', 'player_roster_preview', 'Player Roster Preview',
    'A block showcasing the squad or selected players', 'players_teams', 'D', 8, -1),
  feat('P02', 'individual_player_cards', 'Individual Player Cards',
    'Named players shown as individual cards on the homepage', 'players_teams', 'D', 8, -1),
  feat('P03', 'player_social_links', 'Player Social Links',
    'Direct links to players\' social media from the homepage', 'players_teams', 'D', 8, -1),
  feat('P04', 'womens_team_featured', "Women's Team Featured",
    'Any women\'s team content visible on the homepage', 'players_teams', 'B', 2, -2),
  feat('P05', 'womens_team_tickets', "Women's Team Tickets",
    'A ticketing entry specifically for women\'s matches', 'players_teams', 'D', 8, -1),
  feat('P06', 'academy_youth_block', 'Academy / Youth Team',
    'Content about the youth academy or reserve teams', 'players_teams', 'D', 8, -1),
  feat('P07', 'esports_gaming_block', 'eSports / Gaming Block',
    'Content about the club\'s eSports or gaming division', 'players_teams', 'D', 8, -1),
  feat('P08', 'charity_csr_block', 'Charity / CSR Block',
    'Content about the club\'s charity, foundation, or social impact work', 'players_teams', 'D', 8, -1),

  // ── 10. Partners, Sponsors & App Ecosystem ──
  feat('A01', 'footer_sponsor_wall', 'Footer Sponsor Wall',
    'Block of sponsor logos in the footer area', 'partners_sponsors', 'E', 3, -1),
  feat('A02', 'in_content_sponsor', 'In-Content Sponsor Placement',
    'Sponsor shown inside homepage content, not just header or footer', 'partners_sponsors', 'C', 5, -2),
  feat('A03', 'app_store_badges', 'App Store Badges',
    'App Store, Google Play, or AppGallery download badges on the homepage', 'partners_sponsors', 'B', 2, -2),
  feat('A04', 'club_tv_app_promo', 'Club TV App Promotion',
    'Promotes the club\'s streaming app with a subscribe or download CTA', 'partners_sponsors', 'C', 5, -2),
  feat('A05', 'b2b_partnerships', 'B2B Partnerships / Become a Sponsor',
    'Block inviting businesses to partner with or sponsor the club', 'partners_sponsors', 'D', 8, -1),

  // ── 11. Personalization, Tech & Engagement ──
  feat('E01', 'ai_chat_assistant', 'AI Chat / Fan Assistant',
    'An AI-powered chatbot or helper widget on the homepage', 'personalization', 'F', 8, 0),
  feat('E03', 'loyalty_rewards', 'Loyalty Points / Rewards',
    'A points or rewards system promoted on the homepage', 'personalization', 'C', 5, -2),
  feat('E04', 'predictor_fantasy', 'Predictor / Fantasy League',
    'Promotes a prediction game or fantasy football league', 'personalization', 'D', 8, -1),
  feat('E05', 'quiz_trivia', 'Quiz / Trivia Block',
    'A quiz or trivia game featured on the homepage', 'personalization', 'D', 8, -1),
  feat('E06', 'wallpapers_downloads', 'Wallpapers / Digital Downloads',
    'Offers downloadable wallpapers or digital goods to fans', 'personalization', 'D', 8, -1),

  // ── 12. Footer ──
  feat('F01', 'social_links_in_footer', 'Social Links in Footer',
    'Social media icons or links in the footer area', 'footer_nav', 'A', 1, -3),
];
