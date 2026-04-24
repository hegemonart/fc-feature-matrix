# Hospitality Review Sources — ranked consultation list

**Phase:** 2 (hospitality pilot — front half)
**Generated:** 2026-04-24
**Status:** Final (provenance log for `FEATURES-CANDIDATES.md`)

Per D-04 / D-05 / D-07. Two corpora anchor the hospitality rubric:
(a) observed-on-site features from gold-standard sites, (b) complained-about
/ wished-for signals from user-review platforms. This document lists every
source consulted, ranked by expected signal density. The output of this
consultation is `FEATURES-CANDIDATES.md`.

This is a **provenance log**, not a scrape target — every source below was
read as human-written narrative. URLs are preserved verbatim so the user
can re-audit any row.

---

## A. Gold-Standard Sites Cataloged (observed-on-site signal)

Ten sites consulted. Arsenal is read-only (catalog) — **NOT crawled** per
user decision 5 / CLAUDE.md headless-block trap. Pilot clubs (MCFC, TOT,
RMA, PSG, CHE) will later be crawled by plan 02-04/02-05; the other five
sites (F1, FIFA 2026, Arsenal, MSG/MetLife, SuiteHop-broker) are catalog-only
in Phase 2 and contribute feature observations only.

| # | Site | URL | Why included | Expected feature count | Status |
|---|------|-----|--------------|------------------------|--------|
| 1 | Manchester City (pilot) | https://www.mancity.com/hospitality | Phase 1 dry-run target. Tunnel Club Premier, Tunnel Club Ground, Commonwealth Bar, 1894 Bar, Backstage, Managers Corner, Matchday Experience — each tier with its own landing page. Mature premium-only sub-architecture. | 15–20 | catalog + crawl |
| 2 | Tottenham Hotspur (pilot) | https://www.tottenhamhotspur.com/tickets/premium-experiences/ | Premium Seats (£299), Broadcast Booth (£449), Stratus (£449), H Club, The Loge, The Cockerel, Tunnel Club, NFL suite. **Transparent pricing is rare in the category** — Tottenham is the EPL reference for price-visible hospitality. | 18–22 | catalog + crawl |
| 3 | Formula 1 Paddock Club | https://tickets.formula1.com/en/pc-paddock-club | Top-of-market luxury reference. Legends Club, Champions Club, House 44, Team Paddock Club (Ferrari/Red Bull/Mercedes), guaranteed-driver-appearances selector, per-circuit pricing ($4,728–$15,000). **Multi-tier comparison UX is the gold standard** the football clubs will be measured against. | 15–18 | catalog only |
| 4 | FIFA World Cup 2026 Hospitality | https://fifaworldcup26.hospitality.fifa.com | Host-country selector + multi-city + multi-match aggregation. Single matches AND private suites ($43,200 entry, $100,000+ boxes). **Unusually strong match-selector UX** because they must disambiguate 104 matches × 16 cities. | 12–15 | catalog only |
| 5 | Arsenal Diamond Club | https://hospitality.arsenal.com/packages | Diamond Club, Avenell (grazing menu on Box Level), Foundry, Legends Bar, Emirates Lounge. Arsenal is **headless-blocked per CLAUDE.md** — catalog via source inspection only. | 12–15 | catalog only — NOT crawled |
| 6 | Chelsea Club Chelsea (pilot) | https://hospitality.chelseafc.com/match-by-match-hospitality-packages | Centenary Club, Platinum, Home Dugout Club (pitchside, metres above dugout), Museum suite, Tambling Suite. Uses a separate hospitality subdomain (`hospitality.chelseafc.com`) — unusual architecture worth surfacing. | 15–18 | catalog + crawl |
| 7 | Real Madrid VIP Area (pilot) | https://www.realmadrid.com/en-US/vip-area/ | Bilingual toggle (ES/EN baked into URL path), Matchday Premium vs Palcos VIP (seasonal boxes), gourmet catering / hostess / cloakroom. Clean seasonal-vs-match-by-match split; reference for i18n hospitality. | 12–15 | catalog + crawl |
| 8 | PSG VIP offers (pilot) | https://billetterie.psg.fr/en/home-vip | All Executive Club, Europe Premium Space (season tickets). French-primary with `/en/` branch. **Separate ticketing subdomain pattern** (`billetterie.*`) that several Ligue 1 clubs share. | 10–13 | catalog + crawl |
| 9 | MSG / MetLife Stadium Suites | https://suites.allegiantstadium.com | US cross-sport contrast — multi-event suite booking (football + concerts + other), long-season vs single-event pricing axis, guided concierge form vs self-serve distinction. | 10–12 | catalog only |
| 10 | Etihad Stadium Suites via SuiteHop | https://suitehop.com/venues/etihad-stadium-suites | Third-party marketplace view of the same inventory as #1 Manchester City. **Own-domain vs broker-domain UX contrast** per D-16 scoring dimension. | 8–10 | catalog only |

**Coverage math:** 10 sites × avg 13 features = ~130 observations → deduped
to ~40–60 candidates in `FEATURES-CANDIDATES.md`. Enough breadth to surface
tier-specific features (F1 exposes pit-lane access, guaranteed appearances,
per-circuit pricing); enough football density to ground in the pilot stack.

---

## B. User-Review Sources (complained-about / wished-for signal)

### Tier A — high-signal, specific review pages (priority reads)

| # | URL | What it yields | Research action |
|---|-----|----------------|-----------------|
|  1 | https://www.trustpilot.com/review/seatunique.com | Broker UX pain: "seat numbers not told until 4–5 days before", "food voucher couldn't be exchanged", "date change refund refused", "different amenities than described". 229+ review pages. | Lowest-rated 2–3 pages; extract features implied by complaints. |
|  2 | https://www.trustpilot.com/review/keithprowse.co.uk | 4.0/5, 1,485 reviews (~69 pages). Allergy handling complaints, long lunch waits, arrival-info gaps, vegetarian dining shortfalls. | Focus on ≤3-star reviews. |
|  3 | https://www.trustpilot.com/review/eventmasters.co.uk | 5★ overall, 290 reviews. Fixture-change notification failures, table-allocation errors, communication-speed issues. | Workflow gaps. |
|  4 | https://www.trustpilot.com/review/p1travel.com | Travel + package bundling UX, international-traveler concerns. | ≤3-star scan. |
|  5 | https://www.tripadvisor.com/Attraction_Review-g186338-d10769361-Reviews-Tottenham_Hotspur_Stadium-London_England.html | "NFL suite was disappointing / most expensive", "restaurant ran out of fish", "spirits had to be purchased at a separate bar". Concrete amenity-gap complaints. | Pull all reviews mentioning "premium" / "lounge" / "hospitality". |
|  6 | https://www.tripadvisor.com/Attraction_Review-g187514-d796251-Reviews-Santiago_Bernabeu_Stadium-Madrid.html | "Emirates Skywards VIP trip" — international-airline-partner package (surprising feature). Good service flagged at Tribuna Fondo Norte. | Pull VIP/premium mentions. |
|  7 | https://www.tripadvisor.com/Attraction_Review-g186338-d1879880-Reviews-Matchday_Dining_Packages_at_Chelsea_FC-London_England.html | Dedicated TripAdvisor entity for Chelsea matchday dining — high signal, many recent reviews. | Pull recent 3-star reviews. |
|  8 | https://wareontheglobe.com/2026/02/17/tottenham-hotspur-premium-travel-club-review-is-the-hospitality-package-worth-it/ | Detailed blog review of Tottenham premium travel package. | Single deep read. |
|  9 | https://hospitalitycritic.co.uk/tottenham-hotspur-stadium/tottenham-hotspur-fc-hospitality/premium-seats-package-review/ | Dedicated hospitality review site. | Single deep read + scan for MCFC / CHE reviews. |
| 10 | https://thepaddedseat.co.uk/review/the-tunnel-club-review-man-city/ | Tunnel Club detailed review (Man City). | Single deep read. |
| 11 | https://goseelearn.com/manchester-city-tunnel-club-premier/ | Family-with-kids hospitality review — surfaces the "is this kid-friendly?" feature axis. | Single deep read. |

### Tier B — forums / subreddits (reddit native search, not Google `site:`)

Google `site:reddit.com` is unreliable (research §2 verified). Use
`old.reddit.com/r/<sub>/search/?q=hospitality` URL pattern directly.

| # | Subreddit | Search query | Signal |
|---|-----------|--------------|--------|
| 12 | https://old.reddit.com/r/MCFC/search/?q=hospitality&restrict_sr=on | hospitality / tunnel club / matchday | Fan-voiced value judgement; "worth it / not worth it" framing. |
| 13 | https://old.reddit.com/r/coys/search/?q=hospitality&restrict_sr=on | premium / hospitality / Club H | Tottenham-specific tier-name vocabulary (fan shorthand differs from marketing copy). |
| 14 | https://old.reddit.com/r/chelseafc/search/?q=hospitality&restrict_sr=on | Centenary / Millennium Suite / hospitality | Chelsea-specific. |
| 15 | https://old.reddit.com/r/realmadrid/search/?q=hospitality+OR+palco&restrict_sr=on | Area VIP / palco / hospitality | ES/EN mix — surfaces language-switching pain point. |
| 16 | https://old.reddit.com/r/psg/search/?q=hospitality+OR+VIP&restrict_sr=on | VIP / loge / Europe space | PSG-specific. |
| 17 | https://old.reddit.com/r/soccer/search/?q=hospitality&restrict_sr=on&sort=top | Cross-club hospitality comparisons | "Which club has best hospitality" threads. |
| 18 | https://old.reddit.com/r/PremierLeague/search/?q=hospitality&restrict_sr=on | Premier-league-wide comparisons | Same, league-scoped. |

### Tier C — press / blogs (single-visit reads)

| # | URL | Signal |
|---|-----|--------|
| 19 | https://www.sportspro.com/?s=hospitality | Industry-side commentary; partnership deals (e.g. OKX × Tottenham). |
| 20 | https://footballbusinessawards.com — past hospitality shortlists / winners | Industry-judged benchmarks; tells us what "good" looks like to judges. |
| 21 | https://www.blackbookmotorsport.com/news/nascar-hospitality-experience-f1-paddock-club-february-2026/ | Cross-sport competitive analysis (NASCAR vs F1 Paddock). |
| 22 | X/Twitter search: `"hospitality disappointing" OR "hospitality worth it" <club name>` (past-year) | Recent-season sentiment; lower signal than Reddit/Trustpilot but captures latest-season pain. |

---

## Consultation method

- **Gold-standard sites (A)** were read manually; feature observations captured in `FEATURES-CANDIDATES.md` with origin `O` (observed-on-site).
- **Trustpilot / TripAdvisor (B Tier A)**: focus on ≤3-star reviews and direct complaints. Origin `C` (complained-about).
- **Blog reviews (B Tier A #8–11)**: full reads; extract wishes and complaints. Origin `C` or `W`.
- **Reddit (B Tier B)**: read top + most-recent relevant threads per club sub. Origin `C` or `W`.
- **Press (B Tier C)**: signal calibration — what the industry considers "good".

**Reviewer-identity hygiene (T-02-02-04):** No quote in
`FEATURES-CANDIDATES.md` includes a reviewer display name, Reddit username,
or identifying language. Citations reference the SITE (Trustpilot,
TripAdvisor, subreddit, blog), not the individual. Reviewer names on those
platforms are already public — but we still don't include them because
feature candidates don't require attribution at that level.

---

## Coverage for the 5 pilot clubs

Rule 2 (Missing Critical) gate: every pilot club must have ≥2 user-review
sources (at least one Reddit + one Trustpilot/TripAdvisor/blog).

| Pilot club | Reddit | Trustpilot / TripAdvisor / Blog | Gap? |
|------------|--------|----------------------------------|------|
| Manchester City (MCFC) | #12 r/MCFC | #1 Seat Unique (MCFC inventory), #10 thepaddedseat (Tunnel Club), #11 goseelearn (family angle) | none |
| Tottenham Hotspur (TOT) | #13 r/coys | #2 Keith Prowse (major TOT vendor), #5 TripAdvisor stadium, #8 wareontheglobe, #9 hospitalitycritic | none |
| Chelsea (CHE) | #14 r/chelseafc | #3 Eventmasters, #7 TripAdvisor Chelsea matchday dining | none |
| Real Madrid (RMA) | #15 r/realmadrid | #6 TripAdvisor Bernabéu | none |
| PSG | #16 r/psg | #4 P1 Travel (international bundler w/ PSG inventory), #22 X/Twitter sentiment | thin — P1 is broker-only; revisit in Phase 2.5 if rubric bias suspected |

---

## Exclusions

- **The CLAUDE.md "DO NOT TOUCH" club**: not consulted for reviews either — the root trap list extends to review corpora. Name redacted in provenance to keep this document grep-clean per the plan's acceptance rule. Rule 4 trigger: escalate if tempted.
- **FC Barcelona**: Socios overlay; deferred to Phase 2.5. Not consulted.
- **Bayern, NBA, West Ham**: headless-blocked per CLAUDE.md; deferred to Phase 2.5.
- **Newcastle / Aston Villa**: 6th stress-test club — post-pilot decision (D-18).

---

## Provenance notes

- All URLs verified resolvable at **2026-04-24** during research-agent session.
- If a URL 404s during later consultation, the row is preserved as provenance — the point is to record *what was consulted*, not to guarantee perpetual link liveness. Substitutes, if needed, are appended inline to the row.
- `REVIEW-SOURCES.md` is stable once frozen with `FEATURES-CANDIDATES.md`. Plan 02-03 does not consume this file directly; it references it only for audit-trail purposes.

---

*Written by Plan 02-02, Phase 02-hospitality-pilot. Source data: 02-RESEARCH.md §1 (gold-standard sites), §2 (review sources).*
