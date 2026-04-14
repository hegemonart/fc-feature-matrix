# Cross-Check Agent Instructions

Reusable procedure for verifying feature categories against live websites using Chrome browser automation.

## Prerequisites

- Chrome browser open with the Claude-in-Chrome MCP extension connected
- Access to `analysis/results/*.json` files
- A tab available in the MCP tab group

## Procedure per website

1. **Navigate** to the site URL in Chrome (`mcp__Claude_in_Chrome__navigate`)
2. **Wait 4s** for JS to render (`mcp__Claude_in_Chrome__computer` action: wait)
3. **Dismiss cookie banner** via JS:
   ```js
   const btns = document.querySelectorAll('button, a, [role="button"]');
   for (const b of btns) {
     const txt = (b.textContent || '').toLowerCase().trim();
     if (txt.includes('reject') || txt.includes('decline') || txt.includes('necessary only') || txt.includes('refuse') || txt.includes('deny all')) {
       b.click(); break;
     }
   }
   ```
4. **Scroll to bottom** to trigger lazy-load: `window.scrollTo(0, document.body.scrollHeight)`
5. **Wait 2s**, then **scroll back to top**: `window.scrollTo(0, 0)`
6. **Screenshot** the relevant page area
7. **DOM inspection** via JS — run queries specific to the feature category (see templates below)
8. **Compare** against current JSON values
9. **Record** any discrepancies

## Feature category templates

### Header & Navigation

Check these 6 features:

| Key | What to look for |
|-----|-----------------|
| `language_switcher_in_header` | Visible language dropdown, globe icon, or EN/ES/DE toggle in header |
| `login_account` | Login button, account icon, "Sign In" link in header |
| `search_input_in_header` | Search icon, magnifying glass, or search input in header |
| `shop_shortcut_in_header` | "Shop", "Store", cart icon, or merchandise link in header nav |
| `tickets_shortcut_in_header` | "Tickets" link or button in header nav |
| `sponsor_lockup_in_header` | Sponsor logo(s) integrated into the header bar (not just the club crest) |

DOM query template:
```js
const allEls = document.querySelectorAll('a, button, input');
const found = { search: [], lang: [], login: [], shop: [], tickets: [], sponsor: [] };
for (const el of allEls) {
  const txt = (el.textContent || '').toLowerCase().trim();
  const href = (el.getAttribute('href') || '').toLowerCase();
  const aria = (el.getAttribute('aria-label') || '').toLowerCase();
  const cls = (el.className || '').toString().toLowerCase();
  const rect = el.getBoundingClientRect();
  const inHeader = rect.top < 200;
  if (!inHeader) continue;
  if (txt.includes('search') || aria.includes('search') || cls.includes('search') || el.type === 'search')
    found.search.push(txt.substring(0, 30));
  if (txt.includes('language') || cls.includes('lang') || txt.match(/^(en|de|es|fr|it|pt)$/))
    found.lang.push(txt);
  if (txt.includes('login') || txt.includes('sign in') || txt.includes('account') || aria.includes('login'))
    found.login.push(txt.substring(0, 30));
  if (txt.includes('shop') || txt.includes('store') || href.includes('shop'))
    found.shop.push(txt.substring(0, 30));
  if (txt.includes('ticket') || href.includes('ticket'))
    found.tickets.push(txt.substring(0, 30));
}
// Check sponsor images
const imgs = document.querySelectorAll('header img, nav img, [class*="header"] img');
for (const img of imgs) {
  const alt = (img.alt || '').toLowerCase();
  const src = (img.src || '').toLowerCase();
  if (src.includes('sponsor') || src.includes('partner') || alt.includes('sponsor'))
    found.sponsor.push(alt);
}
JSON.stringify(found, null, 2);
```

### Content & Media

Check these features:
- `dedicated_news_section` — Look for a news section heading or news article cards
- `homepage_video_block` — Look for video embeds, video thumbnails, or a video section
- `social_native_content` — Look for Storyteller widgets, story circles, or social media embeds
- `photo_gallery_block` — Look for a standalone photo gallery section

### Commerce

- `store_block` — Prominent store/merchandise section on homepage
- `store_individual_products` — Individual product cards with prices shown on homepage
- `tickets_block` — Dedicated tickets section on homepage (not just header link)

## Websites list (33 products)

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

## Output format

Present results as a **Discrepancies Found** table:

```
| # | Club | Feature | Current | Should be | Evidence |
|---|------|---------|---------|-----------|----------|
| 1 | Club Name | feature_key | FALSE | TRUE | What you observed |
```

Also include:
- **Inaccessible Sites** table for any sites that couldn't be loaded
- **Uncertain / Manual Review** table for ambiguous cases

## Updating JSONs after approval

After the user approves changes, update each JSON file:
```bash
# Example: flip a boolean
python3 -c "
import json
with open('analysis/results/club_name.json', 'r') as f:
    d = json.load(f)
d['features']['feature_key'] = True  # or False
with open('analysis/results/club_name.json', 'w') as f:
    json.dump(d, f, indent=2)
"
```

Then regenerate aggregates:
```bash
cd analysis/results && node -e "
const fs = require('fs');
const files = fs.readdirSync('.').filter(f => f.endsWith('.json') && !f.startsWith('_'));
const clubs = files.map(f => JSON.parse(fs.readFileSync(f, 'utf8')));
clubs.sort((a, b) => b.total_score - a.total_score);
// ... (see analysis/CLAUDE.md for full script)
"
```

## Tips

- **Hamburger menus**: Items inside a collapsed hamburger that are part of the header navigation system count as YES. Check `el.offsetParent !== null` to distinguish visible vs hidden-in-menu.
- **Sponsor lockup**: Look for sponsor logos IN the header bar itself, not just on jerseys in hero images. Partner bars above or integrated into the header count.
- **Cookie banners**: Some sites (especially F1, Bundesliga clubs) have persistent cookie banners that block interaction. Try both JS click and manual click approaches.
- **404 pages**: If the /en path 404s, try the base URL — the header is usually still visible and functional.
- **JS-heavy sites**: WebFetch misses content rendered by JavaScript (e.g., Storyteller widgets). Always use real browser for verification.
