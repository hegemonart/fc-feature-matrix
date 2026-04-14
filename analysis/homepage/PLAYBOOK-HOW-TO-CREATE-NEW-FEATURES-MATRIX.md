# UX Feature Benchmark Playbook

**A step-by-step methodology for building weighted competitive feature benchmarks across homepages, transactional pages, and apps.**

**Version:** v1.0
**Date:** 13 April 2026

---

## What this methodology does

This playbook teaches you to build a structured comparison of digital product features across competitors. The output is a weighted score per competitor that answers three questions:

1. **What features does each competitor have and not have?**
2. **Which missing features are costing them the most?**
3. **Which features differentiate the best from the average?**

It replaces informal "their homepage looks better" design reviews with a defensible, repeatable, parser-friendly artefact. The same methodology works for homepages, ticketing flows, login pages, e-commerce surfaces, and mobile apps.

## When to use it

**Use when:**
- You are pitching or scoping a redesign and need evidence of a specific gap vs competitors
- You are planning a product roadmap and need to prioritise features by commercial impact
- You are onboarding into a new vertical and need to understand industry table stakes vs differentiators
- You want to track the same competitor set over time (quarterly audits)

**Do not use when:**
- You need qualitative UX insight (use usability testing or heuristic evaluation instead)
- You need to assess visual design quality (use a design review with rubrics instead)
- The feature landscape is too immature (fewer than 5 comparable competitors)
- The page type varies too much across competitors to compare (use archetype clustering first)

---

## The 7-step process

1. **Define scope**: which page, which competitors, what fold/viewport
2. **Capture source material**: screenshots with metadata
3. **Build feature taxonomy**: group features into 10-15 sections
4. **Define your atomic unit**: what qualifies as a "block" or equivalent
5. **Write criteria**: one strict rule per feature, testable from a screenshot
6. **Assign tiers and weights**: Fibonacci scale with asymmetric penalties
7. **Score and report**: Yes/No per feature, total per competitor, per-section subtotals

Each step is covered in detail below.

---

## Step 1. Define scope

Before opening any competitor site, make three decisions and write them down.

### 1.1 Which page?

Decide whether you are benchmarking:
- **Homepage** (landing, unauthenticated, desktop)
- **Transactional page** (ticket purchase, checkout, signup)
- **Content page** (match centre, article, player profile)
- **Mobile app screen** (home tab, match tab, commerce tab)
- **Authenticated state** (logged-in homepage, account page)

A single benchmark should cover exactly one page type. Mixing page types in one benchmark produces unusable output because features do not transfer. A "login form" feature does not belong in a homepage benchmark.

### 1.2 Viewport, fold, state

Fix these variables across all competitors or the benchmark becomes unfair:
- **Viewport width**: 1440px is standard for desktop benchmarks in 2026
- **Fold**: define a pixel cutoff (e.g. 900px) for any "above the fold" criteria
- **Device**: desktop-only, mobile-only, or both (scored separately)
- **Logged-in state**: always logged out for first pass
- **Localisation**: English default, or capture each market separately
- **Page state**: for sports sites, non-matchday default; matchday is a separate benchmark

Document these in the top of the file so future updates stay comparable.

---

## Step 2. Capture source material

Never benchmark from memory. Always from fresh captures.

### 2.1 Screenshots

For each competitor, capture:
- Full-page screenshot of the target page
- Optionally: viewport-only screenshot (to verify above-fold criteria)
- Optionally: component-level screenshots for ambiguous features

Store screenshots with filenames that encode `competitor-page-date-state`, e.g. `fc-barcelona-homepage-2026-04-13-loggedout.png`.

### 2.2 Metadata per capture

Record for each competitor:
- Date of capture
- URL
- Viewport
- Language / region
- Logged-in state
- Page state (matchday, international break, transfer window, etc.)

Metadata matters because homepages change weekly. A score that was true three months ago may be wrong today.

### 2.3 Static vs behavioural capture

Screenshots miss: hover states, scroll animations, sticky behaviours, autoplay video, lazy-loaded content, push notification prompts.

If any of your features depend on behaviour, capture video or annotate manually. For first-pass benchmarks, stick to features visible in static screenshots.

---

## Step 3. Build the feature taxonomy

The taxonomy is the backbone of the benchmark. Build it before you write any criteria.

### 3.1 Start with sections

A section is a group of related features. Target 10-15 sections. More than 15 and the benchmark becomes unwieldy. Fewer than 10 and related features get lost.

For any page type, most sections fall into these archetypes:
- **Navigation and orientation** (nav, search, language)
- **Primary content area** (hero, feed, product grid)
- **Commercial surfaces** (tickets, shop, subscriptions)
- **Community and engagement** (membership, newsletter, social)
- **Identity and trust** (credentials, heritage, certifications)
- **Technical and accessibility** (a11y, AI, personalisation)
- **Peripheral** (footer, partners)

### 3.2 Generate candidate features per section

For each section, list every feature you have seen across the competitor set. Work from screenshots, not memory. Cast a wide net at first, then prune.

Target 3-10 features per section. Fewer than 3 and the section is not worth its own heading. More than 10 and you are probably splitting hairs.

### 3.3 Deduplicate aggressively

Look for overlap in 3 patterns:
- **Nested features**: "Store block" and "Product cards in store block" - the second is a subset of the first. Keep both only if a competitor might have one without the other.
- **Synonym features**: "Video block" and "Video section" - pick one name.
- **Layout vs content duplicates**: "News section" and "News cards" - the cards are part of the section.

Rule of thumb: if two features correlate >80% across the competitor set, merge them.

### 3.4 Drop features with near-universal presence unless strategically important

A feature that scores Yes for 19 of 20 competitors adds noise, not signal. Drop it unless it is a must-have and the one missing it deserves to be flagged (e.g. no login link at all).

---

## Step 4. Define your atomic unit

Every feature criterion will reference an atomic unit: "a block", "a card", "a module", "a section". You must define this unit explicitly at the top of the benchmark or annotators will disagree.

### 4.1 The "block" definition (recommended default)

A **block** is a homepage region that occupies its own visual container AND contains at least one of:

- Descriptive text beyond a one-word label (headline, subheading, or body copy)
- A call-to-action (button or link with actionable text, e.g. "Shop now", "View plans")
- Interactivity (form, poll, vote, swiper, calculator, player, filter)

The following do NOT qualify:
- A banner with only an image or logo
- A standalone button without surrounding descriptive content
- A single link or nav entry
- A one-word label or badge

### 4.2 Alternative atomic units for other page types

For different page types, you may need different atomic units:

| Page type | Atomic unit | Definition |
|---|---|---|
| Homepage | Block | See above |
| Ticket purchase | Step | A discrete user action with its own UI view (seat select, payment, confirm) |
| Login / signup | Field or method | A specific input or authentication path |
| E-shop product page | Module | Product image gallery, description, reviews, related items - each is a module |
| E-shop cart | Row or summary block | Line item or checkout summary element |
| Mobile app screen | Tab or card | Bottom-nav tab or primary scroll card |

Pick one definition and apply it consistently. The definition goes at the top of the file with examples of what does and does not qualify.

### 4.3 Why this matters

Without a block definition, your parser (or human annotators) will disagree on edge cases. A nav link to the museum is not a museum block. A button that says "Learn more" is not a block. Without a rule, half your annotators will score these as Yes and half as No. The rule is the difference between a usable benchmark and noise.

---

## Step 5. Write criteria

Each feature has one criterion: the "Qualifies as Yes if..." rule. This is the authoritative test. If an annotator can read the criterion and the screenshot and answer Yes/No without ambiguity, the criterion is good.

### 5.1 Criterion grammar

Standardise to one grammatical pattern. Recommended: "A [thing] that [property]" or "A [thing] with [property]".

Examples:
- ✅ "A block listing trophies or honours, including a footer trophy strip"
- ✅ "A top-level nav item linking to the club store"
- ❌ "Has a trophies section somewhere" (vague)
- ❌ "Club shows their honours" (subjective)

### 5.2 Criterion must be testable from the source material

If the criterion requires inspecting code, clicking, scrolling, or waiting for animation, and your source is a static screenshot, the feature is not testable. Either:
- Drop the feature
- Upgrade the source material (video, live capture)
- Rewrite the criterion to be testable statically

### 5.3 Specify thresholds everywhere possible

Every "large", "small", "featured", "dense", "prominent" must resolve to a number or a concrete relationship.

Examples:
- ❌ "A large sponsor visual" → ✅ "A sponsor image occupying at least 25% of the viewport area in the top 900px fold"
- ❌ "A featured news card" → ✅ "One news card at least 1.5x larger in one dimension than other cards in the same block"
- ❌ "A sponsor wall" → ✅ "A block with 3+ third-party sponsor logos, excluding payment icons and app store badges"
- ❌ "Multiple fixtures" → ✅ "2 or more future fixtures"

### 5.4 Handle exclusions explicitly

If certain things superficially look like the feature but should score No, say so in the criterion.

Examples:
- "A block about the museum (a nav or footer link alone does not qualify)"
- "A block with 3+ sponsor logos (excluding payment method icons and app store badges)"
- "A block dedicated to photo galleries (a filter tab inside news does not qualify)"

### 5.5 Add a plain-language description

Alongside the strict criterion, include a short human-friendly description (max 90 characters). This helps future readers and annotators who are not parsers. Example:

- **Criterion**: "A block with at least a brief description of hospitality packages (a link alone does not qualify)"
- **Description**: "Promotes premium hospitality packages with some descriptive content"

---

## Step 6. Assign tiers and weights

Flat +1 / 0 scoring loses information. Use a tiered weighting system so differentiators and must-haves pull the total score differently.

### 6.1 The 6-tier Fibonacci system

| Tier | Name | Weight if Yes | Weight if No | Logic |
|---|---|---|---|---|
| A | Must-have | +1 | -8 | Missing it is a disaster. Having it is expected. |
| B | Commercial table stakes | +2 | -5 | Standard revenue plumbing. Absence hurts. |
| C | ROI driver | +5 | -3 | Direct revenue impact. Strong reward, real penalty. |
| D | Differentiator | +8 | -1 | Rare, strategically advanced. Big reward, tiny penalty. |
| E | Content depth | +3 | -1 | Quality signal, not essential. |
| F | Experimental | +8 | 0 | Only advanced competitors do this. No penalty, big upside. |

### 6.2 How to assign tiers

Ask these questions per feature:

1. **"If this feature is missing, does the user notice immediately?"**
   Yes → Tier A (Must-have)

2. **"Does this feature generate revenue directly?"**
   Yes, and it is standard across the industry → Tier B (Commercial table stakes)
   Yes, and execution quality matters a lot → Tier C (ROI driver)

3. **"Do fewer than 30% of competitors have this feature?"**
   Yes, and it signals strategic advancement → Tier D (Differentiator)

4. **"Does this feature add quality but not revenue or retention?"**
   Yes → Tier E (Content depth)

5. **"Is this bleeding-edge tech that might not pay off?"**
   Yes → Tier F (Experimental)

### 6.3 Calibration rules

- Must-haves (A) should be 10-15% of total features. If you have 40% must-haves, you are too strict.
- Differentiators (D) should be 30-40%. They are the features that actually separate winners from losers.
- Experimental (F) should be 5% or less. If you have 20% experimental features, you are too generous.

### 6.4 Document every tier assignment

For each feature, record the tier as its own column. This lets parsers filter and aggregate by tier, and lets you see at a glance whether your tiering is balanced.

---

## Step 7. Score and report

### 7.1 Score per feature

For each feature, evaluate every competitor against the criterion. The output is `Yes` or `No`. No partials, no maybes, no freeform notes.

If a criterion is genuinely ambiguous for a given competitor, the criterion is broken. Rewrite the criterion before continuing.

### 7.2 Score per competitor

Total score = sum of row scores. Each row contributes `Weight if Yes` or `Weight if No` depending on the cell value.

A competitor can have a negative total if they miss many must-haves or commercial table stakes. This is a feature of the system, not a bug. It tells you they are below industry baseline.

### 7.3 Report per-section subtotals

A single total is misleading. A competitor scoring +50 on Commerce and -20 on Content tells a very different story than one scoring +15 on both. Always produce per-section subtotals.

### 7.4 Totals table format

```markdown
| Competitor | Total Score | Yes count |
|---|---|---|
| A | +79 | 33 / 69 |
| B | +19 | 28 / 69 |
| C | +6  | 25 / 69 |
```

Include both the weighted total (strategic signal) and the Yes count (feature count signal). They tell different stories.

### 7.5 Write a "Quick read" narrative

At the bottom of the benchmark, write 3-5 sentences explaining what the scores actually reveal. This is the "so what" layer. Example:

> **A** dominates through commercial depth (Tickets/Hospitality, Commerce, Players) - +79 total reflects a homepage engineered for conversion.
>
> **B** leads on Content and Hero but loses heavily on Commerce (no store block) and Tickets. Editorial-strong, commerce-weak.
>
> **C** is near break-even (+6). Wins on Heritage but loses hard on Match & Fixtures (no next-match block triggers double must-have penalty).

---

## Managing versions and iteration

### Versioning

Stamp every benchmark with a semantic version and a date:

```markdown
**Version:** v1.3
**Date:** 13 April 2026
```

Bump:
- **Patch** (v1.3 → v1.4): criteria tightening, individual score corrections
- **Minor** (v1.3 → v2.0): tier reassignment, section merge, weighting change, feature addition or removal

A v1.x benchmark is comparable across competitors at a point in time. A v2.x is not comparable to v1.x; do not plot them on the same chart.

### Parser-friendliness

If the output will be consumed by a parser (TypeScript, Python, LLM), enforce:
- Strict cell values: exactly `Yes` or `No`, no variants
- Stable unique keys per row (section number + feature name)
- No em-dashes (use hyphens)
- No pipe characters (`|`) in cell content
- Escape commas in CSV export

### When to reassess the whole benchmark

Full reassessment is needed when:
- Industry shifts (new product category enters the market)
- A major competitor launches a redesign that adds 5+ new features
- Your scoring reveals that most competitors cluster around the same total (the benchmark is no longer discriminating)

Plan for a major rev every 12-18 months for fast-moving industries, 2-3 years for slow ones.

---

## Common pitfalls

**1. Benchmarking too many page types in one document.**
Keep homepage, ticketing, and e-shop benchmarks in separate files. Each has its own atomic unit and tier logic.

**2. Criteria that require interpretation.**
"Feels premium", "looks modern", "is well organised" are not criteria. Rewrite with measurable thresholds or drop.

**3. Forgetting to define the atomic unit.**
Without a block definition, annotators disagree. Without annotators agreeing, the benchmark is noise.

**4. Equal weights across all features.**
Flat +1/0 scoring means a podcast block counts as much as a login field. Use tiers.

**5. Scoring from memory instead of screenshots.**
Homepages change. Score from fresh captures, store captures alongside the benchmark.

**6. Letting the feature list grow unchecked.**
Every benchmark I have seen grows from 50 to 120 features over time. Past 80 features, annotator consistency drops. Prune aggressively.

**7. Not separating structured features from qualitative judgment.**
If you want to say "Barça's heritage presentation feels more premium than Real Madrid's", that belongs in a separate observations section, not in a Yes/No cell.

**8. No per-section subtotals.**
A single total score hides the story. Always show subtotals so readers can see where each competitor wins and loses.

---

## Templates for common page types

Each template below gives you a starter feature taxonomy for that page type. Use them as a starting point; add or remove features based on your specific benchmark scope.

---

### Template: Homepage

**Atomic unit:** Block (see Step 4)

**Sections (12):**

1. Header & Navigation
2. Hero
3. Primary content feed (news, matches, products, depending on vertical)
4. Secondary content (video, audio, social)
5. Commercial surfaces (tickets, commerce, subscriptions)
6. Community & Membership
7. Identity & Heritage
8. People / Team / Players
9. Partners, Sponsors & Ecosystem
10. Personalization & Tech
11. Engagement & Loyalty
12. Footer

**Sample features per tier:**

| Tier | Examples |
|---|---|
| A | Language switcher in header, Login / account, Dedicated news section, Social links in footer |
| B | Shop shortcut in header, Tickets shortcut in header, Newsletter signup, App store badges |
| C | Next-match block feature-rich, Tickets block, Hospitality block, Paid membership plans |
| D | Social-native content block, Documentary promo, Player roster preview, Anniversary block |
| E | Search input, Hero carousel, News rich structure, Trophies block |
| F | AI chat widget, On-page a11y controls, Push notification opt-in |

Target: 60-80 features.

---

### Template: Ticket purchase page / flow

**Atomic unit:** Step or module. A step is a discrete user action with its own UI view.

**Sections (8):**

1. Entry & Orientation (page header, event info, breadcrumbs)
2. Seat selection (map, zones, prices, filters)
3. Price & fees transparency (breakdown, service fees, tax)
4. Account & guest checkout (login, signup, guest path)
5. Payment (methods, wallets, international support)
6. Confirmation & delivery (email, wallet, mobile ticket)
7. Accessibility & assistance (a11y seating, help, chat)
8. Trust & reassurance (refund policy, ticket authenticity, support)

**Sample features with suggested tiers:**

| Feature | Tier | Criterion |
|---|---|---|
| Event info summary at top (opponent, date, venue) | A | A block at page top with at least opponent name and date |
| Interactive seat map | A | An interactive seat map allowing zone or seat selection |
| Price breakdown before payment | A | A breakdown of ticket price, fees, and taxes before payment step |
| Guest checkout path | B | A visible option to check out without creating an account |
| Apple Pay / Google Pay | B | Apple Pay or Google Pay button in the payment step |
| Mobile wallet ticket delivery | C | Explicit option to deliver ticket to Apple Wallet or Google Pay |
| Accessible seating filter | C | A filter or section specifically for accessible seating |
| Price-per-view / category comparison | D | A view comparing categories side-by-side with clear differences |
| 3D stadium view per seat | D | 3D preview of the view from a selected seat |
| Group booking tool | D | A dedicated flow for booking 10+ tickets together |
| Dynamic pricing indicator | D | A clear indicator that prices are dynamic with last-updated info |
| Resale / exchange option | D | An explicit option to resell or exchange the ticket post-purchase |
| Hospitality upsell in flow | C | An upsell to hospitality packages within the purchase flow |
| Multi-language checkout | B | Language selector available throughout the flow |
| Refund policy visible pre-purchase | A | Refund terms shown before payment submission |

Target: 30-50 features.

---

### Template: Login / signup page

**Atomic unit:** Field or method. A method is a distinct authentication path (email, Apple, Google, passkey).

**Sections (6):**

1. Form layout & clarity
2. Authentication methods
3. Password handling & recovery
4. Error handling & validation
5. Trust & privacy signals
6. Post-login onboarding

**Sample features with suggested tiers:**

| Feature | Tier | Criterion |
|---|---|---|
| Email + password form | A | Email input and password input both visible on the page |
| Password visibility toggle | A | A button or icon revealing/hiding password input |
| Forgot password link | A | A visible link to password recovery from the login form |
| Sign in with Apple | B | Apple sign-in button present |
| Sign in with Google | B | Google sign-in button present |
| Passkey support | D | An explicit passkey / WebAuthn sign-in option |
| Magic link email | C | An option to sign in via a magic link sent to email |
| Biometric sign-in (on supported devices) | D | Face ID or fingerprint sign-in offered on the page |
| Inline validation | B | Errors appear inline near the offending input, not only on submit |
| Rate limiting / lockout messaging | E | A clear message about lockout or retry delay on repeated failures |
| Social proof on signup | D | Testimonials, user count, or club statement visible on signup page |
| Terms link visible at signup | A | Links to terms and privacy visible before submission |
| Captcha (hidden or visible) | E | Some bot-protection mechanism is present |
| Email verification step | B | A verification email is sent before account is fully active |
| Onboarding tour after signup | C | A guided onboarding flow for new signups |
| Carry-over of intent (ticket in cart) | C | If user came from a protected flow, they return to it after login |

Target: 20-40 features.

---

### Template: E-shop main page / PLP (product listing page)

**Atomic unit:** Block (for marketing modules) or tile (for product cards).

**Sections (10):**

1. Navigation & filters
2. Hero / banner / campaign
3. Product grid structure
4. Product card anatomy
5. Sort & filter controls
6. Search & discovery
7. Commercial upsell (bundles, discounts, gift cards)
8. Community & reviews
9. Cart & account access
10. Trust, shipping & returns

**Sample features with suggested tiers:**

| Feature | Tier | Criterion |
|---|---|---|
| Category navigation (men/women/kids or equivalent) | A | A top-level nav with at least 3 category filters |
| Product grid with 3+ columns desktop | A | Desktop product grid rendering 3+ columns |
| Product card with image, name, price | A | Every product card contains image, name, and price |
| Filter panel (size, colour, team, price) | B | A persistent or collapsible filter panel with 3+ facet groups |
| Sort controls (price, popularity, newest) | B | A sort dropdown or control with 3+ options |
| Stock availability on card | B | Low-stock or out-of-stock indicator visible on product card |
| Product card hover or quick-view | C | A hover or quick-view shows alternate image or quick-add to cart |
| Customisation indicator (name / number) | C | Product cards indicate if customisation is available |
| Personalised recommendations | D | A block with personalised "For you" recommendations |
| Live shopping / streaming block | D | A block promoting live shopping events |
| Gift card entry in navigation | C | A top-level nav or block entry for gift cards |
| Kit launch countdown | D | A countdown timer to a kit launch or drop |
| Virtual try-on | F | Virtual try-on for kits or merch |
| Multi-language and multi-currency | A | Explicit controls to switch language and currency |
| Free shipping threshold banner | B | A banner showing free shipping threshold |
| Reviews / ratings on card | C | Star ratings visible on product cards |
| Wishlist / favourites | B | An icon on product cards to add to wishlist |
| Member-only pricing indicator | D | A badge or price differentiation for members |
| Sustainability / materials filter | D | A filter for sustainable materials or production |
| Cart icon with item count in header | A | Cart icon in header with visible item count |

Target: 50-70 features.

---

### Template: Mobile app home screen

**Atomic unit:** Tab, card, or widget. Bottom-nav tabs are a separate dimension from scroll content.

**Sections (9):**

1. Top app bar & brand identity
2. Bottom navigation structure
3. Hero / matchday banner
4. Personalised content feed
5. Commerce shortcuts (tickets, store)
6. Membership & loyalty integration
7. Live & notifications
8. Video & streaming access
9. Profile & settings access

**Sample features with suggested tiers:**

| Feature | Tier | Criterion |
|---|---|---|
| Bottom nav with 4-5 primary tabs | A | A bottom navigation bar with 4-5 destinations |
| Home tab is first / default | A | The home tab is the default active destination on app launch |
| Top app bar with club crest | A | The top app bar shows the club crest or logo |
| Profile / account icon in top bar | A | Account or profile icon in the top app bar |
| Matchday hero card | B | A hero card switching to matchday state on match day |
| Live match card with score | B | A live match card displays the current score during a match |
| Push-notification permission prompt | C | A prompt or onboarding step requesting push permission |
| Personalised feed based on favourite team / player | C | Feed content adapts to selected favourite player or team |
| Ticket wallet shortcut | C | A shortcut or card leading to the user's purchased tickets |
| Mobile ticket in Apple Wallet / Google Pay | C | Tickets can be added to the device wallet |
| Club TV streaming entry | C | A card or tab leading to club streaming content |
| Member benefits surfacing | D | A card or section surfacing member-only perks |
| Fantasy / predictor integration | D | An in-app fantasy league or predictor game |
| AR features (stadium view, player cards) | F | An AR feature integrated into the app |
| Biometric login (Face ID / Touch ID) | B | Biometric login option for returning users |
| Offline mode for content | D | Previously loaded content viewable offline |
| Deep links from notifications | B | Push notifications deep-link into the relevant in-app screen |
| Dark mode | B | Dark mode support, either automatic or manual toggle |
| Accessibility settings | C | In-app accessibility settings (text size, contrast) |
| Language switching in app | B | Language can be changed within the app without reinstall |
| Live chat / support | D | An in-app chat or support interface |

Target: 40-60 features.

---

### Template: Mobile app - match screen / live centre

**Atomic unit:** Card or widget.

**Sections (7):**

1. Match header (score, clock, teams)
2. Live commentary or timeline
3. Stats and visualisations
4. Lineups and formations
5. Fan engagement (polls, predictions)
6. Commerce during match (tickets for next match, merch)
7. Media (video highlights, photos)

**Sample features with suggested tiers:**

| Feature | Tier | Criterion |
|---|---|---|
| Live score at top persistent during scroll | A | The score bar stays visible while scrolling other content |
| Match clock with accurate time | A | A match clock that updates in real time |
| Team lineups | A | Both team lineups visible in a dedicated section |
| Text commentary / timeline | B | A text commentary updating in real time |
| Player heatmap | D | Interactive heatmap per player |
| Expected goals (xG) visualisation | D | xG shown as a graph or summary |
| In-match poll or vote | D | An interactive poll during the match |
| Goal video highlights (inline) | C | Goal videos playable inline within the match screen |
| Substitution notifications | B | Push or in-app notifications for substitutions |
| Share-to-social on goals | D | A share button appears when a goal is scored |
| Formation graphic | B | A graphical view of each team's formation |
| Player ratings (fan or algorithmic) | D | Per-player ratings visible during or after match |
| Match stats (possession, shots) | B | Key stats visible and updating in real time |
| Head-to-head comparison | C | Pre-match head-to-head widget |
| Pre-match venue info | E | Stadium info and kickoff details pre-match |

Target: 25-40 features.

---

## Final checklist before publishing a benchmark

- [ ] Scope defined at top of file (page type, viewport, state)
- [ ] Atomic unit (block or equivalent) defined with positive and negative examples
- [ ] 10-15 sections, each with 3-10 features
- [ ] Every feature has a strict testable criterion
- [ ] Every feature has a plain-language description (max 90 characters)
- [ ] Every feature has a tier assignment (A-F)
- [ ] Every feature has Weight if Yes and Weight if No columns
- [ ] Every cell is exactly `Yes` or `No`, no variants
- [ ] Tier distribution is balanced (A: 10-15%, D: 30-40%, F: 5% or less)
- [ ] Per-section subtotals included in totals section
- [ ] "Quick read" narrative at the bottom
- [ ] Version and date at the top
- [ ] Screenshots archived with metadata per competitor
- [ ] No em-dashes, no pipe characters inside cells

---

## What to do with the output

A finished benchmark should drive at least one of:

1. **A pitch deck slide** showing your client / prospect their gap vs leaders
2. **A product roadmap priority list** filtered by missing high-ROI features
3. **A design brief** scoped around the lowest-scoring sections
4. **A quarterly tracker** to show improvement over time
5. **A parser input** for dashboards showing the competitor set live

If the benchmark is not driving one of these, it is not doing its job. Either simplify it, delete it, or change the framing until it drives a decision.
