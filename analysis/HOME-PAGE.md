# Football Club Homepage Feature Comparison

**Version:** v2.0
**Date:** 13 April 2026

## Scoring system

Every feature is classified into one of six tiers. Yes/No values have different weights per tier (Fibonacci scale). Asymmetric penalties reflect the reality that missing a must-have hurts more than missing a differentiator.

| Tier | Name |
|---|---|
| A | Must-have |
| B | Commercial table stakes |
| C | ROI driver |
| D | Differentiator |
| E | Content depth |
| F | Experimental |

### Scoring rules
- Each feature has exactly one value per club column: **Yes** or **No**
- Score per row = `Weight if Yes` when cell is `Yes`, `Weight if No` when cell is `No`
- A club's total score = sum of all row scores
- Scores can be negative if a club misses many must-have or commercial table-stakes features

## Definition of "block"

A **block** is a homepage region that occupies its own visual container AND contains at least one of:

- Descriptive text beyond a one-word label (a headline, subheading, or body copy)
- A call-to-action (a button or link with an actionable label, e.g. "Shop now", "View plans", "Read more")
- Interactivity (form, poll, vote, swiper, calculator, player, filter)

The following do **not** qualify as a block:

- A banner with only an image or logo (e.g. "FC Bayern Online Store" banner)
- A standalone button with no surrounding descriptive content
- A single link or nav entry
- A one-word label or badge

**Examples:**

- ✅ A "Goal of the Month" card with category label, hero image, headline, description, and a video/vote CTA → qualifies as a block (interactive + text)
- ✅ A Champions League match-preview card with kickoff time, teams, and ticket CTA → qualifies
- ❌ A full-bleed banner showing the club crest and the words "FC Bayern Online Store" → does not qualify (image/logo only, no descriptive text)

---

## 1. Header & Navigation

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Language switcher in header | A visible control to change language rendered in the header | Lets users switch site language from the header | A | +1 | −3 |
| Login / account | A login link, login button, or account icon rendered in the header | Entry point for user account, sign-in, or profile | A | +1 | −3 |
| Search input in header | A search input field or search icon rendered in the header | Search bar or icon visible in the top nav | E | +3 | −1 |
| Shop shortcut in header | A top-level nav item linking to the club store | Top-nav link sending users straight to the club store | B | +2 | −2 |
| Tickets shortcut in header | A top-level nav item linking to tickets | Top-nav link sending users straight to tickets | B | +2 | −2 |
| Sponsor lockup in header | A sponsor logo locked directly into the header bar alongside or in place of standard header elements | Sponsor logo integrated alongside the club crest in the header | D | +8 | −1 |
| Persistent bar above header | A horizontal bar rendered above the main header, containing any content (offer, sponsor attribution, or utility links) | Thin bar above the main header with offers, sponsor credits, or utility links | E | +3 | −1 |

---

## 2. Hero

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Hero carousel | A hero that rotates between 2+ slides, indicated by any of: auto-advance, left/right arrows, pagination dots, or a strip of thumbnail tabs below/beside the hero that switch the hero content. Check the area immediately around and below the main hero, not only the hero image itself - thumbnail strips are a common carousel indicator that can be missed when looking at the hero in isolation. | Hero rotates through multiple slides to show more content at the top | E | +3 | −1 |
| Secondary editorial strip below hero | A row of 2+ editorial cards rendered within 200px below the hero area | Row of editorial cards just under the hero for quick content access | A | +1 | −3 |
| Brand sponsor highlighted in hero block | A sponsor image or illustration rendered in the top 900px fold occupying at least 25% of the viewport area (not the header lockup, not a small logo) | Large sponsor visual taking significant space in the first view | D | +8 | −1 |

---

## 3. Match & Fixtures

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Next-match block | A block showing the next scheduled fixture with at least one of: date, time, or opponent | Shows the upcoming match so fans know when the team plays next | A | +1 | −3 |
| Next-match block is feature-rich | The next-match block contains 3+ of the following: live countdown, 2+ upcoming fixtures, opponent crest, competition logo, ticket CTA, broadcaster info, add-to-calendar button | Next-match block adds extras like countdown, tickets, or broadcaster info | C | +5 | −2 |
| Results block | A block showing at least one recent match result with score | Shows recent match scores for quick catch-up | E | +3 | −1 |
| Standings block or prominent link | A block showing the league table, or a prominent homepage link to it (footer-only does not qualify) | League table access directly from the homepage | E | +3 | −1 |
| Live match indicator | A badge, card, or banner indicating a currently-live match | Visible signal when a match is happening right now | C | +5 | −2 |
| Matchday experience info block | A block with matchday logistics (transport, food, fan zone, or gates) | Practical info about attending a match: transport, food, gates, fan zone | C | +5 | −2 |

---

## 4. Content (News, Video, Editorial)

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Dedicated news section | A homepage section labelled News or equivalent containing 2+ news items | A section of the homepage clearly devoted to news stories | A | +1 | −3 |
| News section has rich structure | The news section contains 2+ of the following: tabs or category filters, card grid layout, mixed photo and video thumbnails, one featured/hero news card at least 1.5x larger than others | News section uses multiple UX features like tabs, mixed media, or hero card | E | +3 | −1 |
| Homepage video block | A block dedicated to video content, rendered outside the news section | A dedicated area for video content, separate from news | B | +2 | −2 |
| Episodic / docu-series block | A block promoting a multi-episode series or campaign (docu-series or marketing campaign both count) | Promotes a series of episodes or a campaign with multiple chapters | D | +8 | −1 |
| Video thumbnails inline with news | Video items appear mixed into the news grid | Video items shown mixed into the news grid | E | +3 | −1 |
| Documentary promo block | A block, modal, or upsell specifically promoting a documentary | Specific promo for a documentary film, often with a paywall CTA | C | +5 | −2 |
| Social-native content block | A block in Stories row format (3+ tappable tiles) or platform-native UI showcasing social content (IG/TikTok/X style) | Stories-style tiles or a block that mimics Instagram/TikTok UI | D | +8 | −1 |
| Podcast / audio content block | A block dedicated to podcast or audio content | Area dedicated to the club's podcasts or audio shows | D | +8 | −1 |
| Photo gallery as dedicated block | A block dedicated to photo galleries (a filter tab inside news does not qualify) | A standalone photo gallery block, not just a filter in news | E | +3 | −1 |
| Press conference / manager interview block | A block or card featuring a press conference or manager interview | Card or block featuring a manager talking to press or being interviewed | E | +3 | −1 |
| Transfer news / rumors block | A block dedicated to transfer news | A dedicated area for transfer market news | D | +8 | −1 |
| Interactive fan voting / poll block | An interactive voting or poll block rendered on the homepage | A poll or vote that fans can actually interact with on the page | D | +8 | −1 |

---

## 5. Tickets & Hospitality

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Tickets block on homepage | A block promoting ticket sales (not just a header nav link) | A real block selling or promoting tickets, not just a nav link | C | +5 | −2 |
| Hospitality block | A block with at least a brief description of hospitality packages (a link alone does not qualify) | Promotes premium hospitality packages with some descriptive content | C | +5 | −2 |
| Stadium tours block | A block promoting stadium tours (a nav entry alone does not qualify) | Promotes tours of the stadium with content, not just a nav link | C | +5 | −2 |

---

## 6. Commerce & Store

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Store block on homepage | A block dedicated to the club store (any size, must meet the block definition) | Any block dedicated to the official club store | B | +2 | −2 |
| Store block shows individual products with CTAs | The store block contains individual product cards or featured collections, each with its own buy/shop CTA | Store block features specific product cards, each with its own buy button | C | +5 | −2 |
| Member-only commerce block | A block promoting products or discounts exclusive to members | Products or discounts available only to signed-up members | C | +5 | −2 |

---

## 7. Community & Membership

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Newsletter signup block | A block containing an email input, or a block dedicated to newsletter subscription with a CTA | An email capture block for joining the club's newsletter | B | +2 | −2 |
| Fan-club / free membership sign-up block | A block promoting sign-up to the club's official fan community or membership programme (a standalone CTA button does not qualify) | Promotes joining the club's free official fan community or membership | C | +5 | −2 |
| Paid membership / subscription plans block | A block with a CTA leading to paid sign-up or a plans list (e.g. "View plans", "See plans", "Become Premium", "Subscribe") | Promotes paid tiers like premium access, streaming, or subscription plans | C | +5 | −2 |
| Draws / contests block | A block promoting member draws, contests, or giveaways | Promotes giveaways or competitions available to members or fans | D | +8 | −1 |
| Fan clubs directory block | A block listing or linking to official supporter/fan clubs | Lists or links to the club's official supporter clubs around the world | E | +3 | −1 |

---

## 8. Heritage & Identity

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Trophies / honours block | A block listing trophies or honours, including a footer trophy strip | Showcases the club's trophies, titles, or honours | E | +3 | −1 |
| Heritage / past content block | A block mentioning any of: past seasons, past players, club history, legends, or hall of fame (a nav or footer link alone does not qualify) | Content about club history, past seasons, legends, or hall of fame | E | +3 | −1 |
| Stadium content block | A block that explicitly features the stadium as its primary subject (a passing stadium photo inside a generic block does not qualify) | A block with the stadium as its main subject, not just a background photo | E | +3 | −1 |
| Museum block | A block about the museum (a nav or footer link alone does not qualify) | A dedicated block promoting the club's museum | C | +5 | −2 |

---

## 9. Players & Teams

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Player roster preview block | A block previewing the squad or selected players | A block showcasing the squad or selected players | D | +8 | −1 |
| Individual player cards | Named individual players shown as cards on the homepage | Named players shown as individual cards on the homepage | D | +8 | −1 |
| Player social links | Links to individual player social media accounts rendered on the homepage | Direct links to players' social media from the homepage | D | +8 | −1 |
| Women's team featured on homepage | Women's team content (news, tickets, or a block) appears anywhere on the homepage | Any women's team content visible on the homepage | B | +2 | −2 |
| Women's team has its own tickets entry | A dedicated ticket entry for women's matches on the homepage | A ticketing entry specifically for women's matches | D | +8 | −1 |
| Academy / youth team block | A block about the academy or youth team (a single passing mention in news does not qualify) | Content about the youth academy or reserve teams | D | +8 | −1 |
| eSports / FIFA / gaming team block | A block about the club's eSports or gaming team | Content about the club's eSports or gaming division | D | +8 | −1 |
| Charity / CSR block | A block about charity, foundation, or CSR initiatives | Content about the club's charity, foundation, or social impact work | D | +8 | −1 |

---

## 10. Partners, Sponsors & App Ecosystem

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Footer sponsor wall | A block with 3+ third-party sponsor logos (excluding payment method icons and app store badges) | Block of sponsor logos in the footer area | E | +3 | −1 |
| In-content sponsor placement | A sponsor visibly placed within homepage content, outside the header and footer | Sponsor shown inside homepage content, not just header or footer | C | +5 | −2 |
| App store badges | Apple, Google, or AppGallery download badges rendered on the homepage | App Store, Google Play, or AppGallery download badges on the homepage | B | +2 | −2 |
| Club TV app promotion block | A block promoting the club's streaming/TV app with a subscribe or download CTA | Promotes the club's streaming app with a subscribe or download CTA | C | +5 | −2 |
| B2B partnerships / become a sponsor block | A block inviting B2B or sponsor enquiries (a footer link alone does not qualify) | Block inviting businesses to partner with or sponsor the club | D | +8 | −1 |

---

## 11. Personalization, Tech & Engagement

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| AI chat / fan assistant | An AI chatbot or assistant widget rendered on the homepage | An AI-powered chatbot or helper widget on the homepage | F | +8 | 0 |
| W3C / a11y features visible | An on-page accessibility widget, toolbar, or controls (a footer link alone does not qualify) | On-page accessibility tools like a widget or contrast controls | F | +8 | 0 |
| Loyalty points / rewards block | A block about a points or rewards programme (implied via generic membership does not qualify) | A points or rewards system promoted on the homepage | C | +5 | −2 |
| Predictor / fantasy league block | A block promoting a prediction game or fantasy league | Promotes a prediction game or fantasy football league | D | +8 | −1 |
| Quiz / trivia block | A block with a quiz or trivia game | A quiz or trivia game featured on the homepage | D | +8 | −1 |
| Wallpapers / digital downloads block | A block offering downloadable wallpapers or digital goods | Offers downloadable wallpapers or digital goods to fans | D | +8 | −1 |

---

## 12. Footer

| Feature | Qualifies as Yes if | Description | Tier | Weight if Yes | Weight if No |
|---|---|---|---|---|---|
| Social links in footer | Social media icons or links rendered in the footer | Social media icons or links in the footer area | A | +1 | −3 |
| Language / region selector in footer | A language or region switcher rendered in the footer | Language or region switcher placed in the footer | A | +1 | −3 |