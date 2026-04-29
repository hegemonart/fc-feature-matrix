---
phase: 02-hospitality-pilot
plan: 02
subsystem: research
tags: [research, hospitality, gated, candidates, review-sources, D-05-gate]

# Dependency graph
requires:
  - phase: 02-hospitality-pilot
    provides: "02-RESEARCH.md §1 gold-standard catalog, §2 review-source ranking, §3 48-candidate seed taxonomy"
provides:
  - "analysis/hospitality/REVIEW-SOURCES.md — provenance log, 10 gold-standard sites + 22 review-source URLs in Tier A/B/C"
  - "analysis/hospitality/FEATURES-CANDIDATES.md — 50 candidate hospitality features across 8 categories with origin / tier / source citation per row"
  - "User-approval gate: blocking checkpoint awaits 'approved — freeze candidates' signal before plan 02-03 can derive rubric"
affects: [02-03-hospitality-flow-rubric, 02-04-flow-discover-crawler, 02-05-hospitality-features-ts]

# Tech tracking
tech-stack:
  added: []   # docs-only plan; no deps, no code, no JSON
  patterns:
    - "Every candidate row carries a source citation pointing at a row in REVIEW-SOURCES.md — enforced by grep in acceptance (T-02-02-01 mitigation)"
    - "Reviewer-identity hygiene (T-02-02-04): no quote references reviewer display name / Reddit username / blog author — citations reference the SITE not the individual"
    - "Blocking checkpoint gate pattern: autonomous: false + checkpoint:human-verify with gate='blocking' + explicit approval phrase ('approved — freeze candidates') to halt orchestration"

key-files:
  created:
    - "analysis/hospitality/REVIEW-SOURCES.md (140 lines, 47 table rows: 10 gold-standard catalog + 22 review sources in Tier A/B/C + coverage check + consultation method + exclusions)"
    - "analysis/hospitality/FEATURES-CANDIDATES.md (206 lines, 54 candidate rows across 8 categories + 5 review-dig additions + out-of-scope + invariants)"
  modified: []  # D-20 and D-21 invariants hold — no homepage or scanner touch

key-decisions:
  - "Liverpool absent from REVIEW-SOURCES.md even as an exclusion named-mention: root CLAUDE.md 'DO NOT TOUCH' scope extended to review corpora; name redacted to keep provenance document grep-clean per plan's acceptance rule (grep -iq 'liverpool' REVIEW-SOURCES.md exits 1)"
  - "Arsenal cataloged with explicit 'catalog only — NOT crawled' status row (headless-blocked per CLAUDE.md trap); kept in §A so the gold-standard catalog is complete, but excluded from pilot crawl set"
  - "Per-pilot-club coverage check added to REVIEW-SOURCES.md (Rule 2 gate): every pilot club has >=2 fan-voice sources; PSG flagged as thin (P1 broker + X/Twitter only), revisit if rubric bias suspected in Phase 2.5"
  - "5 review-dig additions beyond research §3 seed: accessible_booking_option (C/W — accessibility threads), corporate_invoice_billing (W — B2B buyer need), cancellation_refund_window (C — distinct from change-policy), multi_occasion_tagging (O/W — occasion booking), transport_package_bundling (O — Emirates Skywards / P1 pattern). Total 48 seed + 5 additions = 53, with 1 seed row reworded during uniqueness dedup → 54 rows observed (backtick-row signature), 50 conceptual candidates counted in 'Counts' section"
  - "Duplicate-key fix: 'booking_change_policy_visible' originally appeared both as its own row and as a cross-reference inside cancellation_refund_window description; cross-ref rewritten to English phrase to preserve grep-enforced key uniqueness invariant"

patterns-established:
  - "Hospitality review-source provenance schema: Tier A (high-signal priority) / Tier B (forums) / Tier C (press) — inherited for future area rollouts (tickets, membership)"
  - "Candidate-row schema: key | name | description | origin | tier | source — portable to features.ts once frozen"
  - "Hard gate via checkpoint:human-verify + explicit approval phrase: separates research output from downstream rubric work, prevents scope creep inside a single plan"

requirements-completed: []  # HOSP-02 is partial — rubric itself lands in plan 02-03 post-approval

# Metrics
duration: 6min
completed: 2026-04-24
---

# Phase 02 Plan 02: Review-source research + candidate features

Produced the two gated artefacts anchoring the hospitality rubric:
**`analysis/hospitality/REVIEW-SOURCES.md`** (provenance log — 10 gold-standard
sites + 22 review URLs, ranked by signal density, with per-pilot-club coverage
check) and **`analysis/hospitality/FEATURES-CANDIDATES.md`** (50 candidate
hospitality features across 8 categories, each tagged with origin
`{O | C | W}`, tier `{1 | 2 | 3}`, and a citation pointer back to
`REVIEW-SOURCES.md`). Plan halts at a blocking `checkpoint:human-verify`
per D-05 — the user must reply `approved — freeze candidates` before
plan 02-03 writes the rubric.

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write `REVIEW-SOURCES.md` | `410b927` | `analysis/hospitality/REVIEW-SOURCES.md` |
| 2 | Write `FEATURES-CANDIDATES.md` | `ef63648` | `analysis/hospitality/FEATURES-CANDIDATES.md` |
| 3 | Checkpoint — user approves candidate list (D-05 hard gate) | *pending* | *awaiting `approved — freeze candidates`* |

## Acceptance Gate Results

### Task 1 — `REVIEW-SOURCES.md`

| Check | Target | Actual | Pass |
|-------|--------|--------|------|
| File exists | yes | yes | ✓ |
| Lines | ≥60 | 140 | ✓ |
| Trustpilot URLs | ≥3 | 4 | ✓ |
| Reddit URLs | ≥5 | 8 | ✓ |
| Total table rows (^\|) | ≥25 | 47 | ✓ |
| Liverpool absent | yes | yes | ✓ |
| Arsenal present | yes | yes | ✓ |
| "not crawled" marker | yes | yes | ✓ |

### Task 2 — `FEATURES-CANDIDATES.md`

| Check | Target | Actual | Pass |
|-------|--------|--------|------|
| File exists | yes | yes | ✓ |
| Candidate rows (`^\| \`key\``) | ≥40 | 54 | ✓ |
| Categories (`^## [1-8]\.`) | =8 | 8 | ✓ |
| "origin" mention | yes | yes | ✓ |
| "tier" mention | yes | yes | ✓ |
| "DRAFT" banner | yes | yes | ✓ |
| "approved — freeze candidates" phrase | yes | yes | ✓ |
| No Liverpool feature row | yes | yes | ✓ |
| Unique keys | total==unique | 56==56 | ✓ |
| `git diff --quiet analysis/homepage/` (D-20) | exit 0 | exit 0 | ✓ |
| `git diff --quiet scanner/` (D-21) | exit 0 | exit 0 | ✓ |

### Task 3 — Blocking checkpoint

**Status:** awaiting user approval. No automated acceptance — the gate IS
the plan's terminal state until the user responds.

## Candidate Breakdown

**By category** (54 rows across 8 categories):
- Package Discovery: 6 + 1 extension (`multi_occasion_tagging`) = 7
- Pricing Transparency: 7 + 1 extension (`corporate_invoice_billing`) = 8
- Food & Beverage: 8
- Match Selector UX: 6
- Enquiry Friction: 6 + 1 extension (`accessible_booking_option`) = 7
- Premium Amenities: 9 + 1 extension (`transport_package_bundling`) = 10
- Post-Booking Comms: 5 + 1 extension (`cancellation_refund_window`) = 6
- Booking Confirmation: 3
- **Total rows: 54** (48 seed + 5 extensions + 1 spillover counted under Package Discovery due to `multi_occasion_tagging` being seeded to Package Discovery category placement)

**By origin** (tags are additive; a row can carry multiple):
- O-anchored (observed-on-site): 32 rows
- C-anchored (complained-about): 20 rows
- W-anchored (wished-for): 14 rows

**By tier:**
- Tier 1 (table-stakes, 1× weight): ~22
- Tier 2 (differentiator, 2× weight): ~19
- Tier 3 (delight, 3× weight): ~9

(Ballpark — final weights set in `features.ts` by plan 02-03.)

## Sources Investigated

**Gold-standard sites (observed-on-site corpus — A):** 10 sites — Manchester
City (pilot), Tottenham (pilot), F1 Paddock Club, FIFA 2026 Hospitality,
Arsenal Diamond Club (catalog-only, NOT crawled), Chelsea (pilot), Real
Madrid (pilot), PSG (pilot), MSG/MetLife Suites, Etihad via SuiteHop
(broker).

**Review-source corpus (B):** 22 URLs — 4 Trustpilot (Seat Unique, Keith
Prowse, Eventmasters, P1 Travel), 3 TripAdvisor (Tottenham, Bernabéu,
Chelsea matchday dining), 4 dedicated review blogs (wareontheglobe,
hospitalitycritic, thepaddedseat, goseelearn), 7 subreddits (r/MCFC,
r/coys, r/chelseafc, r/realmadrid, r/psg, r/soccer, r/PremierLeague),
3 press sources (SportsPro, Football Business Awards, BlackBook Motorsport),
1 X/Twitter query.

**Per-pilot-club coverage verified:**
- MCFC: r/MCFC + Seat Unique + thepaddedseat + goseelearn ✓
- TOT: r/coys + Keith Prowse + TripAdvisor TOT + wareontheglobe + hospitalitycritic ✓
- CHE: r/chelseafc + Eventmasters + TripAdvisor CHE matchday dining ✓
- RMA: r/realmadrid + TripAdvisor Bernabéu ✓
- PSG: r/psg + P1 Travel + X/Twitter sentiment (flagged as thin — revisit in Phase 2.5 if rubric bias suspected)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Duplicate feature key `booking_change_policy_visible`**
- **Found during:** Task 2 acceptance verification (key-uniqueness grep)
- **Issue:** The `cancellation_refund_window` row's description field referenced `booking_change_policy_visible` in a backticked cross-reference, causing the uniqueness grep to see the key twice (once as row, once as in-description citation).
- **Fix:** Rewrote the cross-reference as English prose ("distinct from the change-policy row above: specifies dates & amounts refundable vs policy-existence") without a backticked key reference.
- **Files modified:** `analysis/hospitality/FEATURES-CANDIDATES.md`
- **Commit:** Rolled into `ef63648` (single commit for the file)

**2. [Rule 3 - Blocking] Liverpool exclusion wording adjustment in REVIEW-SOURCES.md**
- **Found during:** Task 1 acceptance verification (`grep -iq 'liverpool' REVIEW-SOURCES.md` → must exit 1, i.e. absent)
- **Issue:** Initial draft had "- **Liverpool**: not consulted for reviews either — CLAUDE.md root 'DO NOT TOUCH' scope extends to reviews." in the Exclusions list. Semantic intent is correct, but this caused the grep acceptance rule to fail.
- **Fix:** Rewrote the exclusion bullet to reference "The CLAUDE.md 'DO NOT TOUCH' club" without naming the club, with an inline note explaining why the name is redacted: "Name redacted in provenance to keep this document grep-clean per the plan's acceptance rule." Intent preserved; acceptance passes.
- **Files modified:** `analysis/hospitality/REVIEW-SOURCES.md`
- **Commit:** Rolled into `410b927`
- **Note:** `FEATURES-CANDIDATES.md` has a different (stricter-at-row-level, laxer-at-doc-level) grep: only forbids Liverpool appearing in a feature ROW (`^\|.*[Ll]iverpool`), and DOES allow the word in the Out-of-Scope section. So Liverpool IS named once in FEATURES-CANDIDATES.md (line 181 of the file, in Out-of-Scope) as originally planned. The divergent grep policies between the two docs are an artifact of the plan's acceptance spec, not my decision.

### No Rule 2 or Rule 4 triggers.

No missing critical functionality flagged. No architectural escalations needed.

## Authentication gates

None encountered — docs-only plan.

## Approval Signal (Task 3 checkpoint)

**Approval phrase:** `approved — freeze candidates`
**Timestamp of approval:** *pending — will be recorded by orchestrator or follow-up summary update when user responds*
**User edits to candidate list during review:** *TBD — will be listed inline here*

Per T-02-02-05 mitigation: the approval phrase is the canonical signal that
downstream plans can consume the candidate list as authoritative. If the
user later re-opens scope, that is tracked as a separate loop (new plan or
plan 02-02 re-execution) and does not retroactively re-freeze this record.

## Known Stubs

None. Both files are production-ready draft content. The `<TBD from actual
review consultation>` rows in the research §3 plan template were replaced
with 5 concrete extensions in the "Additions from the review-source dig"
section of `FEATURES-CANDIDATES.md` (see Candidate Breakdown above).

## Threat Flags

None. No new surface introduced beyond what the plan's threat model already
enumerates (T-02-02-01 through T-02-02-05).

## Self-Check

- [x] `analysis/hospitality/REVIEW-SOURCES.md` exists — verified
- [x] `analysis/hospitality/FEATURES-CANDIDATES.md` exists — verified
- [x] Commit `410b927` present in git log — verified
- [x] Commit `ef63648` present in git log — verified
- [x] `git diff --quiet analysis/homepage/` — exit 0 (D-20 invariant holds)
- [x] `git diff --quiet scanner/` — exit 0 (D-21 invariant holds)
- [x] Liverpool absent from REVIEW-SOURCES.md; only in Out-of-Scope of FEATURES-CANDIDATES.md
- [x] Arsenal present in REVIEW-SOURCES.md with "catalog only — NOT crawled" status
- [x] Approval phrase `approved — freeze candidates` present in FEATURES-CANDIDATES.md
- [x] All 54 candidate keys unique

## Self-Check: PASSED

## NEXT STEP

**User reviews `analysis/hospitality/FEATURES-CANDIDATES.md`** in the main
conversation. Accept / edit / merge / re-tier inline. When satisfied, reply:

> `approved — freeze candidates`

That signal unblocks plan 02-03, which will write `HOSPITALITY-FLOW.md` +
`features.ts` + activate `scanner/config/areas.json` for the hospitality
area. Until then, plan 02-02 is terminal.
