# Changelog

## v7.2 — 2026-04-17
Cross-cell interactivity layer (infra-redesign-v2 plan 03): <HoverTooltipCard> portaled to document.body — anchored from cell.getBoundingClientRect() (not cursor) per RESEARCH P8. useHoverTooltip hook with 100ms close grace + cancel-on-reenter. useColumnSelection hook for D-18 toggle-deselect. 15 new specs (90 total).

## v7.1 — 2026-04-17
Atomic matrix components (infra-redesign-v2 plan 02): DataCell (8 states), SortHeader (3 states), MeterRow (4 bands), HeaderBar (BUILD_DATE), TopNav + UnlockTab (locked-tab opacity), CategoryFilter, TypeFilter — all under app/components/matrix/ with colocated CSS modules + Vitest specs. CONTEXT.md D-15 corrected to PRODUCTS[].type.

## v7.0 — 2026-04-17
Visual redesign foundation (infra-redesign-v2 plan 01): neutral-dark + brand-orange design tokens replace cool-blue palette in app/globals.css. Inter Tight + Roboto Mono wired via next/font. BUILD_DATE env exposed for HeaderBar. Playwright visual-regression scaffold (.skip until plan 04). Font-readiness test harness.

## v6.0 — 2026-04-17
Users migrated from data/users.json → Neon Postgres (Drizzle ORM). /admin panel: Users tab (CRUD, admin toggle, last-admin guardrail), Analytics tab, Requests tab (access-request triage). Analytics events migrated from Upstash Redis → Postgres with 90-day cron retention. Three auth security fixes: no default secret, token-age validation, anon POST blocked.

## v5.0 — 2026-04-16
CI/CD pipeline: GitHub Actions runs lint, typecheck, test, build on every push/PR to master. Vitest added with smoke tests for scoring. ESLint 9 flat config wraps eslint-config-next (was missing). Vercel deploy unchanged. Pre-existing JSX lint error in header fixed.

## v4.3 — 2026-04-16
Eintracht Frankfurt full re-check: 21 features flipped FALSE→TRUE after sequential browser verification. Score -64→57 (3rd overall). 26 screenshot evidence files. New TRUE: search, next match, results, standings, news rich, video, podcast, store, products, membership, heritage, stadium, museum, players, women, academy, esports, sponsors, social.

## v4.2 — 2026-04-16
Local logos: download all 33 SVGs from Wikimedia to public/img/logos/, no more external CDN dependency. Score row moved below logos in thead. "Coming Soon" modal updated: "contact admin to unlock" + "Send request" CTA. Real Madrid search_input_in_header flipped FALSE (score 32→28).

## v4.1 — 2026-04-16
Feature tooltip now shows element-level screenshot evidence on hover for TRUE cells. API route serves PNGs from crosscheck/img/. Added `key` field to Feature type so screenshot filenames resolve correctly.

## v4.0 — 2026-04-15
Screenshot-truth enforcement: flip 106 TRUE features to FALSE across 17 clubs where no screenshot evidence exists (Liverpool excluded). 536 screenshots now match 1:1 with TRUE values. Cleanup: delete 21 obsolete capture scripts, unused result files (_live_crawl, _meta_analysis). Update all CLAUDE.md instructions with headless-blocked site notes, capture script inventory, full-page+PIL crop technique.

## v3.0 — 2026-04-15
Batch 1 element screenshots: Real Madrid, Bayern Munich, PSG, Man City, Man United, Tottenham, Liverpool. 224 total screenshots across 10 clubs. Flipped 8 features to FALSE (Bayern: store_block, fan_club_signup, heritage, in_content_sponsor, club_tv; Man City: episodic_docu; Man United: app_store_badges; Tottenham: next_match_feature_rich; PSG: app_store_badges). Liverpool partial (Hillsborough memorial). New capture scripts with anti-bot stealth.

## v2.1 — 2026-04-14
Cleanup: remove 4 one-off fix scripts (fix_screenshots v1/v2/v3, fix_press_conf), archive v1 screenshots folder, and outdated PLAYBOOK-HOW-TO-CREATE-NEW-FEATURES-MATRIX.md. Update README to match.

## v2.0 — 2026-04-14
Element-level screenshot cross-check system for Chelsea, FC Barcelona, Arsenal. Playwright capture scripts with popup/cookie dismissal, lazy-load scrolling, JS element detection. 80 screenshots across 3 clubs. Quality audit with BAD/WEAK re-capture. CLAUDE.md updated with 14 feature-specific screenshot rules.

## v1.9 — 2026-04-14
Arsenal: flip heritage_past_content and charity_csr_block to FALSE after screenshot evidence review. Classics merchandise is store_block not heritage; trending video with community clip is not a charity block. Score 42 -> 29.

## v1.8 — 2026-04-13
Cross-check: RB Leipzig browser-verified, 9 fixes, score -24 -> 12. ITF Tennis 2 fixes, score 1 -> 5. Eintracht 7 fixes, score 32 -> 23. Club Brugge 4 fixes, score 14 -> 10.

## v1.7 — 2026-04-13
Cross-check: Valencia CF (7 fixes, 63 -> 61), ATP Tour (2 fixes), Brentford (2 fixes, -8 -> -12), NBA (5 fixes, -3 -> -12), MLB (4 fixes), MLS (4 fixes, 15 -> -1).

## v1.6 — 2026-04-13
Cross-check: MotoGP (7 fixes, 92 -> 49), F1 (4 fixes, 12 -> 16), UEFA (6 fixes, 1 -> -2), West Ham (1 fix), SL Benfica (3 fixes), VfB Stuttgart (5 fixes, -12 -> -34), Newcastle (1 fix).

## v1.5 — 2026-04-13
Cross-check: Juventus (33 -> 42), PSG + Bayern episodic fix, stricter episodic_docu_series rules. AC Milan (36 -> 45). Aston Villa (4 fixes, -5 -> 12). Atletico Madrid (2 fixes, 10 -> 26).

## v1.4 — 2026-04-13
Cross-check: BVB Dortmund (4 fixes, 3 -> -8), Arsenal episodic fix (51 -> 42). Inter Milan (2 fixes, 26 -> 31), West Ham hero_carousel fix (30 -> 34). Chelsea (3 fixes, 44 -> 27).

## v1.3 — 2026-04-12
Cross-check: Tottenham (5 fixes, -19 -> -7), Man United (6 fixes, 11 -> 26), Arsenal (9 fixes, 49 -> 46), Man City (5 fixes, 9 -> 20). Remove w3c_a11y_features from rubric.

## v1.2 — 2026-04-12
Cross-check: Real Madrid (8 fixes, 41 -> 44), Liverpool (5 fixes, 61 -> 62), PSG (7 fixes, 35 -> 49), Bayern Munich (6 fixes, 62 -> 62). Brand sponsor fix revert for 5 clubs.

## v1.1 — 2026-04-12
Cross-check agent system created. CLAUDE.md with 33-site execution procedure, JS data extraction, cookie/popup strategies, site-specific notes. Recalculate-scores.js script.

## v1.0 — 2026-04-11
Initial analysis: 58-feature rubric (HOME-PAGE.md), 33 organizations scored from full-page screenshots. Next.js app with interactive comparison matrix, 12 feature categories, asymmetric tier-based scoring.
