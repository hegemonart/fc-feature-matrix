# Cross-Check Agent

Verify any feature(s) across all 33 websites using Chrome browser automation.

## How to use

In Claude Code terminal, prompt with the features you want to check:

```
Cross-check "sponsor_lockup_in_header" across all websites
```

```
Cross-check all features in "Header & Navigation" category
```

```
Cross-check "social_native_content" and "homepage_video_block"
```

Claude will read this file, resolve which feature keys to check, visit every site in Chrome, and present a discrepancies table.

---

## Feature resolution

When the user specifies a **category name**, map it to feature keys using the table below. When they specify **feature keys directly**, use those as-is.

### Categories → Feature keys

**Header & Navigation** (`header_nav`)
`language_switcher_in_header`, `login_account`, `search_input_in_header`, `shop_shortcut_in_header`, `tickets_shortcut_in_header`, `sponsor_lockup_in_header`

**Hero** (`hero`)
`hero_carousel`, `secondary_editorial_strip_below_hero`, `brand_sponsor_highlighted_in_hero`

**Match & Fixtures** (`match_fixtures`)
`next_match_block`, `next_match_feature_rich`, `results_block`, `standings_block`, `birthday_squad_calendar`, `live_match_indicator`, `push_notification_opt_in`

**Content & Editorial** (`content`)
`dedicated_news_section`, `news_rich_structure`, `homepage_video_block`, `episodic_docu_series`, `video_thumbnails_inline`, `documentary_promo`, `social_native_content`, `podcast_audio`, `photo_gallery_block`, `press_conference_block`, `transfer_news`, `interactive_fan_poll`

**Tickets & Hospitality** (`tickets_hospitality`)
`tickets_block`, `hospitality_block`, `stadium_tours_block`, `multi_sport_tickets`

**Commerce & Store** (`commerce`)
`store_block`, `store_individual_products`, `member_only_commerce`

**Community & Membership** (`community`)
`newsletter_signup`, `fan_club_signup`, `paid_membership`, `draws_contests`, `fan_clubs_directory`

**Heritage & Identity** (`heritage`)
`trophies_honours`, `heritage_past_content`, `stadium_content_block`, `museum_block`, `anniversary_milestone`, `tribute_memorial`

**Players & Teams** (`players_teams`)
`player_roster_preview`, `individual_player_cards`, `player_social_links`, `womens_team_featured`, `womens_team_tickets`, `academy_youth_block`, `esports_gaming_block`, `charity_csr_block`

**Partners, Sponsors & App** (`partners_sponsors`)
`footer_sponsor_wall`, `in_content_sponsor`, `app_store_badges`, `club_tv_app_promo`, `b2b_partnerships`

**Personalization & Engagement** (`personalization`)
`ai_chat_assistant`, `w3c_a11y_features`, `loyalty_rewards`, `predictor_fantasy`, `quiz_trivia`, `wallpapers_downloads`

**Footer** (`footer_nav`)
`social_links_in_footer`, `language_selector_in_footer`

---

## Websites (33)

| # | ID | URL |
|---|-----|-----|
| 1 | real_madrid | realmadrid.com/en |
| 2 | fc_barcelona | fcbarcelona.com/en |
| 3 | bayern_munich | fcbayern.com/en |
| 4 | psg | psg.fr/en |
| 5 | liverpool | liverpoolfc.com |
| 6 | man_city | mancity.com |
| 7 | arsenal | arsenal.com |
| 8 | man_united | manutd.com |
| 9 | tottenham | tottenhamhotspur.com |
| 10 | chelsea | chelseafc.com |
| 11 | inter_milan | inter.it/en |
| 12 | bvb_dortmund | bvb.de/eng |
| 13 | atletico_madrid | atleticodemadrid.com/en |
| 14 | aston_villa | avfc.co.uk |
| 15 | ac_milan | acmilan.com/en |
| 16 | juventus | juventus.com/en |
| 17 | newcastle | newcastleunited.com |
| 18 | vfb_stuttgart | vfb.de/en |
| 19 | sl_benfica | slbenfica.pt/en-us |
| 20 | west_ham | whufc.com |
| 21 | uefa | uefa.com |
| 22 | f1 | formula1.com |
| 23 | motogp | motogp.com |
| 24 | mls | mlssoccer.com |
| 25 | mlb | mlb.com |
| 26 | nba | nba.com |
| 27 | brentford | brentfordfc.com |
| 28 | atp_tour | atptour.com |
| 29 | club_brugge | clubbrugge.be/en |
| 30 | eintracht | eintracht.de |
| 31 | itf_tennis | itftennis.com |
| 32 | rb_leipzig | rbleipzig.com/en |
| 33 | valencia_cf | valenciacf.com/en |

---

## Execution procedure

### Step 1: Read current values

```bash
cd analysis/results
for f in *.json; do
  [[ "$f" == _* ]] && continue
  python3 -c "
import json, sys
d = json.load(open('$f'))
vals = {k: v for k, v in d['features'].items() if k in FEATURE_KEYS}
if vals:
    print(f\"=== {d['product_id']} ===\")
    for k, v in vals.items():
        print(f'  {k}: {v}')
"
done
```

(Replace `FEATURE_KEYS` with the actual list of keys being checked.)

### Step 2: Visit each site in Chrome

For each website:

1. **Navigate** to the URL
2. **Wait 4s** for JS to render
3. **Dismiss cookie banner** via JS:
   ```js
   const btns = document.querySelectorAll('button, a, [role="button"]');
   for (const b of btns) {
     const txt = (b.textContent || '').toLowerCase().trim();
     if (txt.includes('reject') || txt.includes('decline') || txt.includes('necessary only')
         || txt.includes('refuse') || txt.includes('deny all')) {
       b.click(); break;
     }
   }
   ```
4. **Scroll to bottom** to trigger lazy-load: `window.scrollTo(0, document.body.scrollHeight)`
5. **Wait 2s**, then **scroll back to top**: `window.scrollTo(0, 0)`
6. **Screenshot** the relevant page area
7. **DOM inspection** — run JS queries relevant to the features being checked
8. **Compare** screenshot + DOM findings against current JSON values
9. **Record** any discrepancies

### Step 3: Present results

**Discrepancies Found** table:

```
| # | Club | Feature | Current | Should be | Evidence |
|---|------|---------|---------|-----------|----------|
| 1 | Club Name | feature_key | FALSE | TRUE | What you observed |
```

Also include:
- **Inaccessible Sites** — any sites that couldn't be loaded
- **Uncertain / Manual Review** — ambiguous cases where the user should verify

### Step 4: Apply fixes (after user approval)

```bash
cd analysis/results && python3 -c "
import json
changes = [
    ('club_id', 'feature_key', True),  # or False
    # ... all approved changes
]
for club, feature, value in changes:
    path = f'{club}.json'
    with open(path) as f:
        d = json.load(f)
    d['features'][feature] = value
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
        f.write('\n')
    print(f'{club}: {feature} -> {value}')
"
```

### Step 5: Regenerate aggregates

```bash
cd analysis/results && node -e "
const fs = require('fs');
const files = fs.readdirSync('.').filter(f => f.endsWith('.json') && !f.startsWith('_'));
const clubs = files.map(f => JSON.parse(fs.readFileSync(f, 'utf8')));
clubs.sort((a, b) => b.total_score - a.total_score);

const scores = {
  generated_at: new Date().toISOString().split('T')[0],
  total_clubs: clubs.length,
  rankings: clubs.map((c, i) => ({
    rank: i + 1, product_id: c.product_id, screenshot: c.screenshot,
    total_score: c.total_score,
    yes_count: Object.values(c.features).filter(v => v === true).length,
    no_count: Object.values(c.features).filter(v => v === false).length,
    feature_count: Object.keys(c.features).length
  }))
};
fs.writeFileSync('_scores.json', JSON.stringify(scores, null, 2));

const allFeatureKeys = Object.keys(clubs[0].features).sort();
const aggregate = {
  generated_at: scores.generated_at,
  total_clubs: clubs.length,
  total_features: allFeatureKeys.length,
  features: {}
};
allFeatureKeys.forEach(key => {
  const adoption = clubs.filter(c => c.features[key] === true).length;
  aggregate.features[key] = {
    adoption_count: adoption,
    adoption_pct: Math.round(adoption / clubs.length * 100),
    clubs_yes: clubs.filter(c => c.features[key] === true).map(c => c.product_id),
    clubs_no: clubs.filter(c => c.features[key] !== true).map(c => c.product_id)
  };
});
fs.writeFileSync('_aggregate.json', JSON.stringify(aggregate, null, 2));
console.log('Done:', clubs.length, 'clubs');
"
```

---

## Tips

- **Hamburger menus**: Items inside a collapsed hamburger that are part of the header navigation count as YES. Check `el.offsetParent !== null` to distinguish visible vs hidden-in-menu.
- **Sponsor lockup**: Look for sponsor logos IN the header bar itself, not just on jerseys in hero images. Partner bars above or integrated into the header count.
- **Cookie banners**: Some sites (F1, Bundesliga clubs) have persistent banners. Try both JS click and manual click.
- **404 pages**: If the /en path 404s, try the base URL — the header is usually still visible.
- **JS-heavy sites**: WebFetch misses JS-rendered content (e.g., Storyteller widgets). Always use real browser.
- **Social native content**: Look for Storyteller/stories widgets (circular thumbnails at top), Instagram/TikTok embeds, or native social feed blocks.
- **Video blocks**: Distinguish between a dedicated video section and video thumbnails inline within news cards.
- **Store block vs shop shortcut**: `store_block` = a merchandise section on the homepage body. `shop_shortcut_in_header` = a link in the header nav.
