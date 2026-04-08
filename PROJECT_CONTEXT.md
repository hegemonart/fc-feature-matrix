# FC Feature Matrix — Project Context

> **For agents picking up this project:** Read this file first. It tells you exactly what's been built, what the data looks like, what decisions were made, and what comes next.

---

## What This Project Is

A UX benchmarking tool that compares the homepages of 26 top sports websites — 20 football clubs + UEFA, F1, MotoGP, NBA, MLS, MLB — across 29 granular features. The output is a single-file interactive HTML prototype (`FEATURE_MATRIX_INTERACTIVE.html`) that lets stakeholders filter, explore, and compare feature presence across all sites.

**Client:** Humbleteam (internal UX research)
**Purpose:** Inform what features PSG and other top clubs should prioritize on their digital platforms.

---

## What's Been Built (v1 — Done)

### Deliverable
`FEATURE_MATRIX_INTERACTIVE.html` — single-file interactive prototype, no dependencies, dark theme.

**Features of the UI:**
- Sticky header row + sticky feature column for scrolling large matrix
- Sidebar filters: Category (5) and Band (4)
- Toolbar filters: Type (Club / League / Org), Sport (Football / Other), text search
- Three-state presence: **Full ✓** (bright), **Partial ✓** (faded, 35% opacity), **Absent ·**
- Color-coded **weight badges** (W1–W5) on every feature row
- **Feature detail panel** (right): adoption %, who has it, band + weight label
- **Product detail panel** (right): feature coverage %, Raw Score (+1 present / −1 absent), Weighted Score (±weight per feature), full feature list with W-badges
- Band legend at bottom

### Data Scope
- **26 products** across football clubs, leagues, and governing bodies
- **29 features** across 5 categories
- Presence verified against full-page screenshots for all 26 sites

### Screenshot Capture
Screenshots were taken with Playwright (headless, cookie banners auto-rejected). 4 sites blocked headless browsers (Bayern, Arsenal, NBA, MLB) — those were captured manually.

Scripts: `capture.mjs`, `recapture.mjs`, `recapture2.mjs`, `recapture-f1.mjs`
Screenshots: `.claude/worktrees/nostalgic-hopper/screenshots/` (excluded from git — 404MB)

---

## Data Architecture

### Products (26)

Football clubs (20): Real Madrid, FC Barcelona, Bayern Munich, PSG, Liverpool, Man City, Arsenal, Man United, Tottenham, Chelsea, Inter Milan, BVB Dortmund, Atletico Madrid, Aston Villa, AC Milan, Juventus, Newcastle, VfB Stuttgart, SL Benfica, West Ham

Other sports (6): UEFA, Formula 1, MotoGP, NBA, MLS, MLB

Each product has: `id`, `name`, `type` (club / league / governing), `sport` (football / motorsport / basketball / baseball)

### Features (29)

Organized into 5 categories with weights:

**Revenue & Commerce (W5 — Revenue Critical)**
- F01: E-Commerce / Shop (83%)
- F02: Ticketing (79%)
- F03: Membership Program (69%)
- F04: Streaming / OTT Platform (58%)

**Content & Engagement (W4 — Engagement Core, except Photo Gallery W3)**
- F05: News Feed (100%) ← Table Stakes
- F06: Fixtures & Results (81%) ← Expected
- F06b: Standings / League Table (33%) ← Innovation
- F07: Video Player / Section (90%) ← Table Stakes
- F07b: Match Highlights (62%) ← Competitive
- F07c: Photo Gallery (50%) ← Competitive [W3]
- F08: Hero / Banner (100%) ← Table Stakes
- F09: Navigation Depth (100%) ← Table Stakes

**Brand & Identity (W3 — Brand & Identity)**
- F10: Women's Team Visibility (52%) ← Competitive
- F11: Academy / Youth (54%) ← Competitive
- F12: Social Media Links (96%) ← Table Stakes
- F13: Sponsor Showcase (92%) ← Table Stakes
- F14: App Download Promotion (60%) ← Competitive

**UX & Utility (W2 — UX & Utility)**
- F15: Search (92%) ← Table Stakes
- F16: Multi-Language (12%) ← Innovation
- F17: Login / Registration (83%) ← Expected
- F18: Newsletter Signup (23%) ← Innovation
- F19: Footer Navigation (100%) ← Table Stakes

**Differentiators (W1 — Differentiators)**
- F20: Stadium / Museum / Tours (31%)
- F21: Foundation / Charity (35%)
- F22: Esports / Gaming (21%)
- F23: Heritage / History (31%)
- F24: Other Sports (12%)
- F25: Transfer Tracker (8%)
- F26: Fan Feedback / Surveys (4%)

### Adoption Bands
- **Table Stakes** ≥90%: News Feed, Hero/Banner, Nav Depth, Video Player, Social Links, Sponsor Showcase, Search, Footer Nav (8 features)
- **Expected** 70–89%: Fixtures & Results, Login/Registration (4 features incl. revenue)
- **Competitive** 40–69%: Match Highlights, Photo Gallery, Women's Team, Academy, App Download, Membership, Ticketing, Streaming (7 features)
- **Innovation** <40%: Everything else — Standings, Multi-Language, Newsletter, all Differentiators (10 features)

### Scoring
- **Raw Score** per product: +1 for each full/partial feature, −1 for each absent
- **Weighted Score** per product: +weight for full, +⌊weight/2⌋ for partial, −weight for absent
- **Adoption %** per feature: (full + partial×0.5) / 26 products

---

## Key Decisions Made

1. **Social Feed Embed dropped** — 0% adoption across all 26 sites; no club embeds live social timelines
2. **"Match Center" split** into Fixtures & Results (81%) vs Standings (33%) — very different adoption rates
3. **"Video & Highlights" split** into Video Player (90%) vs Match Highlights (62%) vs Photo Gallery (50%)
4. **"Social Media Integration" renamed** to Social Media Links (icons/links only — feeds are absent everywhere)
5. **Partial icon redesigned** from ◐ half-circle to faded ✓ checkmark (35% opacity, same color as full)
6. **Weight badges** (W1–W5) added to every row in the matrix and in both detail panels
7. **No revenue data** shown anywhere in the prototype (client requirement)

---

## File Structure

```
/
├── FEATURE_MATRIX_INTERACTIVE.html   ← Main deliverable (single-file, ~700 lines)
├── FEATURE_MATRIX_INTERACTIVE.html   ← Open in browser or via http-server (port 8090)
├── feature-matrix.md                 ← Full markdown analysis with all 26 sites
├── brainstorm.md                     ← Initial feature ideation
├── analysis/
│   ├── analysis-batch1.md            ← Sites 1–8 detailed feature notes
│   ├── analysis-batch2.md            ← Sites 9–16
│   └── analysis-batch3.md            ← Sites 17–26 (incl. UEFA, F1, MotoGP, NBA, MLS, MLB)
├── capture.mjs                       ← Playwright screenshot capture (all 26 sites)
├── recapture.mjs / recapture2.mjs    ← Re-capture scripts for specific sites
├── recapture-f1.mjs                  ← F1-specific capture (anti-bot workaround)
├── package.json                      ← playwright, http-server deps
├── .claude/launch.json               ← Dev server config: npx http-server . -p 8090 -c-1
└── .gitignore                        ← Excludes screenshots/ (404MB) and node_modules/
```

### Running Locally
```bash
npm install
npx http-server . -p 8090 -c-1
# Open http://localhost:8090/FEATURE_MATRIX_INTERACTIVE.html
```

---

## What's Next (Planned, Not Built)

### 1. Club Detail Pages (immediate next task)
A separate view/page per club showing:
- **Overall score** (weighted score, raw score, coverage %)
- **Must-have breakdown**: which Table Stakes / Expected features are present vs missing
- **Differentiators**: which Innovation/Competitive features they uniquely have
- **Already have**: full list of present features with weights

This was explicitly requested by the user at the end of the last session.

### 2. Roadmap (from README / brainstorm.md)
- **v2** — Analyze ticket purchase flows (5–15 pages per club)
- **v3** — Analyze mobile app home screens (first 3000px scroll)
- **Future** — Filtered views by user journey (tickets, merch, subscriptions, matchday)
- **Future** — Merch shop analysis, hospitality, subscription flows

---

## HTML File Internal Structure

The single HTML file is structured as:
1. **CSS** (~200 lines) — dark theme variables, table layout, cell styles, detail panel, weight badge colors
2. **HTML** (~60 lines) — header, toolbar, sidebar, table container, detail panel, legend
3. **JavaScript** (~440 lines):
   - `CATEGORIES[]` — 5 categories with color
   - `PRODUCTS[]` — 26 products with id/name/type/sport
   - `FEATURES[]` — 29 features with id/name/desc/cat/weight/presence map
   - `makePresence(full[], partial[])` — helper builds presence object for all 26 IDs
   - `COMPUTE BANDS` — calculates adoption% and band for each feature
   - `render()` → calls renderHeader, renderSidebar, renderTable, renderLegend
   - `renderTable(feats, prods)` — builds the full matrix HTML
   - `showFeatureDetail(fid)` — right panel for clicking a feature/cell
   - `showProductDetail(pid)` — right panel for clicking a column header
   - `closeDetail()` — closes right panel
   - Event delegation on `document` for all clicks (no per-cell listeners — fixes lag)

### Performance Note
The app uses **event delegation** (single click listener on `document`). Earlier version had recursive render loop where `showFeatureDetail` → `render` → `showFeatureDetail` causing multi-second lag. This is fixed — clicks respond in ~5ms.
