# Cross-Check Agent

Verify feature values across all websites using Chrome browser automation.

## How to use

In Claude Code terminal, prompt with the features and rubric source:

```
Cross-check "sponsor_lockup_in_header" across all websites
using rubric: fc-feature-matrix/analysis/homepage/HOME-PAGE.md
```

```
Cross-check all features in "Hero" category
using rubric: fc-feature-matrix/analysis/homepage/HOME-PAGE.md
```

```
Cross-check "social_native_content" and "homepage_video_block"
using rubric: fc-feature-matrix/analysis/homepage/HOME-PAGE.md
```

## What happens

1. Claude reads **this file** for the execution procedure
2. Claude reads the **rubric file** (e.g. `HOME-PAGE.md`) to get feature names, "Qualifies as Yes if" criteria, and descriptions
3. Claude visits every site in Chrome, one at a time, verifying all requested features per site
4. Claude presents a discrepancies table for user approval
5. After approval, Claude applies fixes and recalculates scores

---

## Feature resolution

Features and their YES/NO criteria come from the **rubric file**, not from this README.

For homepage features, the rubric is `analysis/HOME-PAGE.md`. It contains:
- Category headings (e.g. "## 3. Match & Fixtures")
- Feature tables with columns: **Feature**, **Qualifies as Yes if**, **Description**, **Tier**, **Weight if Yes**, **Weight if No**

When the user specifies a **category name** (e.g. "Hero"), read all features under that heading in the rubric. When they specify **feature keys directly**, match them to the rubric rows.

The rubric file is the single source of truth for what counts as YES.

**IMPORTANT**: Never use the original analysis screenshots from `analysis/homepage/screenshots/` during a cross-check. Always visit the actual live website in the browser. The whole point of the cross-check is to independently verify against the real site, not to re-read the same screenshots that produced the original (potentially wrong) values.

---

## Websites (33)

| # | ID | URL |
|---|-----|-----|
| 1 | real_madrid | realmadrid.com |
| 2 | fc_barcelona | fcbarcelona.com |
| 3 | bayern_munich | fcbayern.com |
| 4 | psg | psg.fr/en |
| 5 | liverpool | liverpoolfc.com |
| 6 | man_city | mancity.com |
| 7 | arsenal | arsenal.com |
| 8 | man_united | manutd.com |
| 9 | tottenham | tottenhamhotspur.com |
| 10 | chelsea | chelseafc.com |
| 11 | inter_milan | inter.it |
| 12 | bvb_dortmund | bvb.de |
| 13 | atletico_madrid | atleticodemadrid.com |
| 14 | aston_villa | avfc.co.uk |
| 15 | ac_milan | acmilan.com/en |
| 16 | juventus | juventus.com/en |
| 17 | newcastle | newcastleunited.com |
| 18 | vfb_stuttgart | vfb.de/en |
| 19 | sl_benfica | slbenfica.pt |
| 20 | west_ham | whufc.com |
| 21 | uefa | uefa.com |
| 22 | f1 | formula1.com |
| 23 | motogp | motogp.com |
| 24 | mls | mlssoccer.com |
| 25 | mlb | mlb.com |
| 26 | nba | nba.com |
| 27 | brentford | brentfordfc.com |
| 28 | atp_tour | atptour.com |
| 29 | club_brugge | clubbrugge.be |
| 30 | eintracht | eintracht.de |
| 31 | itf_tennis | itftennis.com |
| 32 | rb_leipzig | rbleipzig.com |
| 33 | valencia_cf | valenciacf.com |

---

## Execution procedure

### Step 1: Read current values and rubric

1. Read the **rubric file** to get the "Qualifies as Yes if" criteria for each feature being checked
2. Read current values from `analysis/homepage/results/*.json` for the features being checked
3. Build a reference table: club → feature → current value

### Step 2: Visit each site (one at a time)

Process **one website at a time**, checking **all features** for that site before moving to the next. This avoids revisiting sites and provides natural checkpoints — if context runs out, you know exactly which sites are done.

**Recommended batch size**: 8–10 sites per context window. After each batch, present findings so far and save progress.

For each website, follow this sequence:

#### 2a. Ensure desktop viewport width

**CRITICAL**: Before visiting any site, ensure the browser window is **at least 1200px wide** (recommended: 1400×900). Many club sites use responsive layouts that collapse the header, hide sponsor logos, and remove navigation elements at narrower widths. Use `resize_window` to set the size before starting the batch — do NOT rely on the browser's default size.

If you skip this step, you will get false negatives for features like `sponsor_lockup_in_header`, `brand_sponsor_highlighted_in_hero`, `shop_shortcut_in_header`, and other header/hero elements that are hidden on mobile/tablet breakpoints.

#### 2b. Navigate and take initial screenshot

1. **Navigate** to the URL
2. **Wait 4s** for JS to render
3. **Screenshot** the page immediately — this is your primary verification tool

#### 2c. Dismiss popups and overlays

Some sites show promotional popups or campaign overlays on page load (e.g. Valencia CF shows a summer camp promo, Aston Villa shows ticket promos). These block the page and must be closed before any analysis.

1. **Look at the screenshot** — is there a popup/modal/overlay covering the page?
2. If yes, find the **close button** — look for an "X" button, "Close" text, or a dismiss icon, typically in the top-right corner of the overlay
3. **Click the close button** using coordinates from the screenshot, or use `read_page` with `filter=interactive` to find the close button by ref
4. If clicking coordinates doesn't work, try JS:
   ```js
   // Find and click close buttons
   var btn = document.querySelector('[class*="close"], [aria-label="Close"], [aria-label="close"], .modal-close');
   if (btn) btn.click();
   // Or remove the overlay entirely
   document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"]').forEach(e => e.remove());
   ```
5. **Screenshot again** to confirm the popup is gone

Only proceed to cookie dismissal and page analysis after all popups are cleared.

#### 2d. Dismiss cookie banners

Cookie banners must also be dismissed. Try each strategy in order until one works:

**Strategy 1: Visual click** — Look at the screenshot for the cookie banner and click the most appropriate button ("Accept all", "Reject all", "Confirm", etc.)

**Strategy 2: JS button click** — Find and click the button programmatically:
```js
const btns = document.querySelectorAll('button, a, [role="button"]');
for (const b of btns) {
  const txt = (b.textContent || '').toLowerCase().trim();
  if (txt.includes('accept all') || txt.includes('reject all') || txt.includes('agree')
      || txt.includes('confirm') || txt.includes('necessary only')
      || txt.includes('decline') || txt.includes('deny all')) {
    b.click(); break;
  }
}
```

**Strategy 3: Consent API** — For consentmanager-based banners (common on Bundesliga sites like BVB Dortmund, VfB Stuttgart):
```js
window.__cmp('setConsent', 0)
```

**Strategy 4: Interactive tree** — Use `read_page` with `filter=interactive` to find cookie-related buttons by ref and click via ref.

#### 2e. Scroll and trigger lazy-load

1. **Scroll to bottom** via JS: `window.scrollTo(0, document.body.scrollHeight)`
2. **Wait 2s** for lazy content to load
3. **Scroll back to top**: `window.scrollTo(0, 0)`
4. **Wait 1s**, then **screenshot** again

**Important: Lazy-loading workaround** — Many JS-heavy sites (React, Next.js) render blank white pages when scrolled to areas that haven't loaded. If the screenshot is blank after scrolling, do NOT rely on visual inspection of that area. Instead:
- Use the **JS data extraction snippet** (Step 2e) which reads the full DOM regardless of viewport
- Use `read_page` to get the accessibility tree, which includes off-screen content

#### 2f. Run JS data extraction

Run this reusable snippet on every site. It extracts signals for all common features in a single call:

```js
var r = {};
// Headings — reveals section structure
r.headings = Array.from(document.querySelectorAll('h1,h2,h3,h4'))
  .map(e => e.innerText.substring(0, 80).trim())
  .filter(t => t.length > 0).slice(0, 25);

// Score patterns — confirms results_block
r.scores = (document.body.innerText.match(/\b\d\s*[-–:]\s*\d\b/g) || []).slice(0, 10);

// Standings — search in main content only (exclude nav to avoid false positives)
var mainEl = document.querySelector('main, [role="main"], .content, #content') || document.body;
var mainText = mainEl.innerText || '';
r.hasStandings = /standings|classifica|league table|tabelle|tabela|clasificación|klassement|rangschikking/i.test(mainText);

// Carousel/slider elements
r.sliders = document.querySelectorAll('[class*="swiper"],[class*="carousel"],[class*="slider"],[data-swiper]').length;

// Match-related elements
var matchEls = document.querySelectorAll('[class*="fixture"],[class*="match"],[class*="next-match"],[class*="score"],[class*="result"]');
r.matchEls = Array.from(matchEls).slice(0, 5).map(e => ({
  cls: e.className.substring(0, 80),
  txt: e.innerText.substring(0, 200).replace(/\n/g, '|')
}));

// Next-match richness signals
var allText = document.body.innerText;
r.hasDate = /\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b/i.test(allText);
r.hasTime = /\d{1,2}:\d{2}/.test(allText);
r.hasVenue = /stadium|arena|park|ground|mestalla|bernab|camp nou|anfield|etihad|emirates/i.test(allText);
r.hasBroadcast = /DAZN|Sky|ESPN|TV|broadcast|live/i.test(allText);
r.hasTicketLink = /ticket|entrada|billet/i.test(allText);

JSON.stringify(r);
```

Adapt or extend this snippet based on the features being checked. For example, add sponsor detection queries when checking `brand_sponsor_highlighted_in_hero`, or video/podcast queries when checking Content features.

#### 2g. Compare, record, and update confidence

For each feature on this site:

1. **Compare** screenshot + JS findings against the current JSON value
2. The **screenshot is the primary source of truth** — JS data is supplementary confirmation
3. **Record** any discrepancies with clear evidence
4. **Update the confidence field** in the JSON:
   - `"browser-verified"` — feature confirmed or corrected via Chrome cross-check
   - `"screenshot"` — verified by screenshot only (no JS confirmation needed)
   - `"needs-live-check"` — couldn't verify (site down, content behind interaction, time-sensitive like live match)
   - `"exists-off-homepage"` — feature exists on the site but not on the homepage

**CRITICAL — Burden of proof for TRUE values:**

A feature value of TRUE means "this feature is visibly present on the homepage." During cross-check, **every TRUE must be positively confirmed** — you must be able to point to specific visual or DOM evidence that the feature exists. If you cannot find evidence, the value must flip to FALSE.

Do NOT preserve a TRUE just because you "couldn't disprove it." The absence of evidence IS evidence of absence for homepage features. Specifically:

- If the page loads shorter/differently than the original screenshot and you **cannot see or detect the feature** → flip to FALSE
- If JS detection finds zero signals and the screenshot shows no evidence → flip to FALSE
- If the only match is in navigation menus, cookie banners, or hidden hamburger menus → flip to FALSE (nav links ≠ homepage blocks)
- If the only match is a news headline mentioning the topic (e.g. "loyalty points update") rather than a dedicated feature block → flip to FALSE

When in doubt, add the site to the **Uncertain / Manual Review** table — but never silently keep a TRUE you couldn't verify.

**Page load validation:**

Before concluding a site, verify the page actually loaded fully:
1. Check `document.documentElement.scrollHeight` — if it's under 2000px for a club homepage, the page likely didn't render properly
2. Try dismissing cookie banners, scrolling to trigger lazy-load, and reloading if needed — some sites (especially German Bundesliga clubs using consentmanager) won't render content until cookies are handled
3. If a site fails to load or renders a stub page after multiple attempts, mark all features as `"needs-live-check"` rather than assuming the existing values are correct

After finishing all features for this site, move to the next. Log progress as you go so context loss doesn't waste work.

#### Live console reporting format

As you check each site, **print a one-line verdict to the console** so the user can follow along in real time. Use this exact format:

```
**Site N: Club Name** (url) — What you observed. **Verdict: TRUE/FALSE (correct)** or **Verdict: TRUE (currently FALSE → needs flip)**
```

Examples:
```
**Site 1: Real Madrid** (realmadrid.com) — Emirates + Adidas logos in header. **Verdict: TRUE (currently FALSE → needs flip)**
**Site 9: Tottenham** (tottenhamhotspur.com) — No sponsor logos in header or hero. Just "SPURS" text logo. **Verdict: FALSE (correct)**
```

Always include the URL so the user can easily double-check in their browser.

### Step 3: Present results

After checking all sites, present a summary **Discrepancies Found** table:

```
| # | Club | URL | Feature | Current | Should be | Evidence |
|---|------|-----|---------|---------|-----------|----------|
| 1 | Club Name | club-url.com | feature_key | FALSE | TRUE | What you observed |
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
    old = d['features'][feature]
    d['features'][feature] = value
    # Update confidence to browser-verified
    if 'confidence' in d:
        d['confidence'][feature] = 'browser-verified'
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
        f.write('\n')
    print(f'{club}: {feature} {old} -> {value}')
"
```

### Step 5: Recalculate scores and regenerate aggregates

Run the recalculation script — it parses weights directly from `features.ts`, recalculates all `total_score` values, and regenerates `_scores.json` and `_aggregate.json`:

```bash
node analysis/crosscheck/recalculate-scores.js
```

This script:
- Reads all `feat()` calls from `analysis/homepage/features.ts` to extract `weightYes` and `weightNo` per feature
- Only features defined in `features.ts` count toward the score
- Features that exist in the JSON but not in `features.ts` are excluded from scoring
- Regenerates `_scores.json` (rankings) and `_aggregate.json` (adoption stats)

### Step 6: Verify build

```bash
npx next build
```

---

## Cookie and popup strategies by site

| Site(s) | Banner type | Best strategy |
|---------|-------------|---------------|
| BVB Dortmund, VfB Stuttgart | consentmanager | `__cmp('setConsent', 0)` |
| Atletico Madrid | OneTrust | `read_page` interactive → find "Allow All" button by ref |
| Valencia CF | Promotional popup | Find X/close button visually or via `read_page` interactive |
| Aston Villa | Ticket promo popup | `read_page` interactive → find "close" button by ref |
| F1, Bundesliga clubs | Persistent banners | Try JS click first, then visual click, then API |
| Most Premier League clubs | Simple consent banner | Visual click on "Accept" or JS button click |

---

## Site-specific notes

- **Atletico Madrid**: Always use base URL `atleticodemadrid.com` — the `/en` path intermittently shows a maintenance page
- **Valencia CF**: Frequently shows promotional popup overlays on load — must find and click X/close button before analysis
- **Aston Villa**: Frequently shows ticket promo overlays — close before analysis
- **Bundesliga sites** (BVB, Stuttgart, Eintracht, RB Leipzig): Use consentmanager for cookies — the `__cmp` API is the most reliable dismissal method
- **Juventus**: Small cookie banner in bottom-right corner — easy to miss, may need precise click coordinates
- **404 fallback**: If the `/en` path returns a 404, try the base URL — the header/footer are usually still visible and analyzable

---

## Tips

- **Hamburger menus**: Items inside a collapsed hamburger that are part of the header navigation count as YES. Check `el.offsetParent !== null` to distinguish visible vs hidden-in-menu.
- **Sponsor lockup**: Look for sponsor logos IN the header bar itself, not just on jerseys in hero images. Partner bars above or integrated into the header count.
- **JS-heavy sites**: WebFetch misses JS-rendered content (e.g., Storyteller widgets). Always use real browser.
- **Social native content**: Look for Storyteller/stories widgets (circular thumbnails at top), Instagram/TikTok embeds, or native social feed blocks.
- **Video blocks**: Distinguish between a dedicated video section and video thumbnails inline within news cards.
- **Store block vs shop shortcut**: `store_block` = a merchandise section on the homepage body. `shop_shortcut_in_header` = a link in the header nav.
- **False positives from nav text**: When checking `standings_block` or similar, always exclude nav/menu/footer elements from your DOM search. A "Standings" link in the nav is NOT a standings block.
- **Screenshot-first approach**: Always take a fresh browser screenshot BEFORE running JS. This live screenshot is the primary source of truth. JS data is supplementary confirmation, not the other way around. Never refer to the original analysis screenshots in `analysis/homepage/screenshots/` — those are what you're checking against, not a source of truth.
- **Browser width matters**: At viewport widths below ~1200px, most club sites switch to mobile/tablet layouts — headers collapse into hamburger menus, sponsor logos disappear, hero sections resize. Always verify the browser is at least 1200px wide (1400px recommended) before starting any cross-check. This was discovered when Real Madrid's Emirates + Adidas hero sponsors were invisible at 948px width.
- **Never trust unverified TRUEs**: The cross-check exists to catch errors in the original analysis. A TRUE that can't be confirmed in the browser is a FALSE — don't carry forward original values on faith. If you can't see it and JS can't find it, flip it. This applies especially when pages render differently (shorter, different language, different content) than the original screenshot.
- **Short pages = red flag**: If a homepage loads under ~2000px tall, something is wrong (cookie wall blocking content, geo-redirect, JS failure). Compare against the original screenshot. If the live page is dramatically shorter, flag every TRUE that relies on content you can't see.
- **brand_sponsor_highlighted_in_hero = header bar sponsors count**: Sponsor logos in the header navigation bar (e.g. Emirates, Adidas, Puma, Nike) count as TRUE for this feature because the header is part of the first viewport the user sees. Do NOT flip to FALSE just because the logo is in the header rather than overlaid on the hero image. If the sponsor logo is prominent anywhere in the top viewport area (header bar, hero image, or hero overlay), it qualifies as TRUE.
- **footer_sponsor_wall = partner/sponsor logos**: This feature is TRUE when the footer area contains a wall of sponsor or partner logos (e.g. "Official Partners", "Global Partners"). These may include both third-party sponsors AND club-branded entities. Do NOT flip to FALSE just because some logos appear to be club-related — if there is a dedicated partner/sponsor logo section in the footer, it counts as TRUE.
- **Mega-menu pollution**: Many clubs (Arsenal, Tottenham, Chelsea) have extensive mega-menus/dropdowns in their navigation. Content inside these menus does NOT count as homepage blocks. When running JS extraction, always filter out elements inside `<nav>`, `<header>`, `[role="navigation"]`, or elements with classes containing "menu", "nav", "dropdown". Only content in `<main>` or the page body (excluding header/nav/footer) counts for features like `standings_block`, `tickets_block`, `store_block`, etc.
- **Avoid innerHTML in JS extraction**: Using `innerHTML` in JS snippets can trigger `[BLOCKED: Cookie/query string data]` if the DOM contains URLs with tracking cookies. Always use `innerText`, `className`, `getAttribute()`, or computed values instead.
- **paid_membership vs free membership**: `paid_membership` = TRUE only if the homepage promotes a subscription with a visible price or "paid"/"premium" language. Free membership programs (e.g. Liverpool's "All Red Essential" at £0) do NOT count. Look for actual price tags or "subscribe"/"join for £X" language.
- **press_conference_block**: A dedicated press conference section on the homepage, not just a news article about a press conference. Look for a labelled "Press Conference" or "Manager's Press Conference" block with video/audio content.
- **club_tv_app_promo**: Look for explicit promotion of the club's streaming/TV app (MUTV, CITY+, SPURSPLAY, Barça One, etc.). A generic "Watch" link in the nav is not enough — there should be a visible block, banner, or CTA specifically promoting the club's media platform.
- **episodic_docu_series**: This feature requires a CLEARLY BRANDED multi-episode series promoted on the homepage — e.g. "All or Nothing", "Inside Matchday Ep.3", "Matchday: Inside FC Barcelona". Look for: (1) a named series with consistent branding, (2) episode numbering or "Episode X" language, (3) a dedicated carousel or block collecting multiple episodes. A single video article, a generic "Watch" section, or a club TV block does NOT qualify. Even a video section with multiple videos is NOT episodic unless they are explicitly presented as episodes of a named series. When in doubt, mark FALSE — this is a differentiator feature (D-tier) that very few clubs actually have.
- **store_block vs shop nav link**: `store_block` = TRUE only when there is a merchandise/store SECTION in the homepage body with visible products. A "Shop" or "Fanshop" link in the header navigation does NOT count. The homepage must show actual product cards, images, or a store promo block in the page body.
- **in_content_sponsor**: Sponsor/partner content must appear in the page BODY (between header and footer). Sponsor logos that appear only in the footer sponsor wall do NOT count as in-content sponsor. Look for sponsor banners, "powered by X" labels, or sponsor blocks woven into the page content sections.
