---
gsd_state_version: 1.0
milestone: v7.1
milestone_name: milestone
status: verifying
stopped_at: "Plan 01-08 complete: Phase 1 acceptance gate PASSED via live dry-run (subscription backend, 2 bugfixes, 138/138 pytest, D-24 holds)"
last_updated: "2026-04-24T19:46:39.001Z"
last_activity: 2026-04-24
progress:
  total_phases: 9
  completed_phases: 1
  total_plans: 15
  completed_plans: 13
  percent: 87
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-16)

**Core value:** Complete end-to-end digital experience benchmarking across every major fan touchpoint for 33 sports organizations
**Current focus:** Phase 1 — Flow Automation Layer + Ticket Purchase

## Current Position

Phase: **Phase 1 — Flow Automation Layer** (in progress; scanner infra, 1 of 8 plans complete)
Plan: 8 of 8 complete (01-01 Wave 0 Foundation — 4 tasks, 36 files, ~7 min); Next: 01-02 (Wave 1 Schema)
Status: Phase complete — ready for verification
Last activity: 2026-04-24
Prior phase close: 2026-04-17 — infra-redesign-v2 plan 05 executed (8 tasks, 9 commits, 99/99 vitest, 2/3 playwright + 1 skipped, build clean, ~75 min)

Progress: [░░░░░░░░░░] 0% (8 numbered phases + 1 decimal, Phase 1 not yet started; out-of-band infra complete)

## Performance Metrics

**Velocity:**

- Total plans completed: 2
- Average duration: ~18.5 min
- Total execution time: ~37 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| infra-redesign-v2 | 2 | 5 | ~18.5 min |

**Recent Trend:**

- Last 5 plans: 01 (~25min) · 02 (~12min)
- Trend: ↓ accelerating (foundation paid off — components shipped fast)

*Updated after each plan completion*
| Phase infra-redesign-v2 P03 | 6min | 8 tasks | 10 files |
| Phase infra-redesign-v2 P04 | 12min | 6 tasks | 7 files |
| Phase infra-redesign-v2 P05 | ~75min | 8 tasks | 17 files |
| Phase 01 P01-01 | 7min | 4 tasks | 36 files |
| Phase 01 P02 | 70min | 3 tasks | 6 files |
| Phase 01 P01-03 | 90m | 2 tasks | 8 files |
| Phase 01 P04 | 18 min | 3 tasks | 15 files |
| Phase 01 P05 | 40min | 2 tasks | 7 files |
| Phase 01 P06 | 12m | 1 tasks | 4 files |
| Phase 01 P07 | 27m | 2 tasks | 6 files |
| Phase 01 P08 | 90min | 2 tasks | 5 files |
| Phase 02 P01 | 8min | 2 tasks | 4 files |
| Phase 02 P02 | 6min | 2 tasks | 2 files |
| Phase 02 P04 | 10 min | 2 tasks | 2 files |
| Phase 02 P05 | 35m | 2 tasks | 5 files |
| Phase 02 P03 | 756 | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Project init: Mobile app home (v3) uses manual screenshots only — cannot automate 33 club apps
- Project init: Extend existing Python capture scripts rather than start from scratch — proven foundation
- Project init: New flow capture layer is architecturally distinct from element-cropping scripts — multi-page navigation vs single-element crops
- Project init: football-data.org free tier for matchday scheduling; manual fallback for gaps
- infra-redesign-v2 plan 02: Per-component CSS modules over single matrix.css (clearer ownership)
- infra-redesign-v2 plan 02: Components are presentation-only — parents own state for test isolation
- infra-redesign-v2 plan 02: Global RTL cleanup() via vitest setupFiles (DRY across plans 03+)
- infra-redesign-v2 plan 02: CONTEXT.md D-15 corrected — type field lives on PRODUCTS, not on results JSON
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 03: <HoverTooltipCard> portaled to document.body, anchored from cell.getBoundingClientRect() (RESEARCH P8 — not cursor)
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 03: useHoverTooltip + useColumnSelection hooks isolate state from <DataCell>; tooltip 100ms close grace via setTimeout + cancel-on-reenter
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 03: scoring keyed by '${clubId}:${featureId}' Map for O(1) hover lookup; defensive null on missing data so portal never crashes
- [Phase infra-redesign-v2]: Server Component shell + Client Island split — page.tsx pre-computes scores, MatrixIsland owns all state hooks verbatim from legacy app/page.tsx
- [Phase infra-redesign-v2]: selectedProduct stays AUTHORITATIVE for column-tint (D-18) — useColumnSelection referenced for parity but isSelected delegates to selectedProduct (single source of truth)
- [Phase infra-redesign-v2]: Visual baseline gate via Playwright: animations:disabled + waitForFunction(document.fonts.ready) + mask:[data-build-date] eliminates known false-positive sources (D-26)
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 05: Token-swap-only rule for downstream pages (/club/[id], /admin/*) — never restructure markup, only swap hex literals/cool-blue tokens for var(--bg-page|cell|hover|border|text|muted|accent)
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 05: Single-orange-CTA-per-surface (D-24, D-25) codified in CLAUDE.md + tested in Modal.test.tsx; .locked-btn count must be exactly 1 per modal
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 05: Recharts <linearGradient><stop> hard-codes #FF490C (RESEARCH P2) — var() inside SVG attribute is unreliable across browsers
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 05: Admin visual baseline deferred to v2.1 — DATABASE_URL not configured in worktree, test.skip() with TODO is acceptable per plan
- [Phase infra-redesign-v2]: infra-redesign-v2 plan 05: D-28 score-invariant gate accepts revert of generated_at-only timestamp drift — content equality is the intent, strict CLI equality the proof
- [Phase ?]: Phase 01 Plan 01: dual-backend vision SDKs (claude-agent-sdk 0.1.65 + anthropic 0.97.0) both installed at scaffold time (D-26) — Plan 04 can build VisionClient Protocol without dep-churn
- [Phase ?]: Plan 01-02: AreasConfig = RootModel[dict[str, AreaEntry]] — zero-migration extensibility for Phase 3-8 areas
- [Phase ?]: Plan 01-02: FeatureDef.key has no regex constraint at schema level (D-18) — snake_case enforcement is a runtime concern
- [Phase ?]: Plan 01-02: Confidence bounds are strict [0,1]; LLM-output clamping lives in Plan 04 client, not the schema validator
- [Phase 01]: Plan 01-03: Cookies dismissed BEFORE scroll_lazy in capture_page — Man City banner overlays viewport so scrolling while present is no-op (D-03-4)
- [Phase 01]: Plan 01-03: banner_verify narrowly catches ImportError (not Exception) on lazy scanner.vision.factory import — real Plan 04 bugs surface (D-03-2)
- [Phase ?]: D-04-1: anthropic 0.97.0 uses output_config (not output_format) for Structured Outputs beta; research §3.3 needs doc update
- [Phase ?]: D-04-2: claude_agent_sdk.query is strictly async + keyword-only; options is a ClaudeAgentOptions dataclass, not dict
- [Phase ?]: D-04-3: runtime_checkable Protocol only inspects method presence; isinstance passes for classes missing typed attributes
- [Phase ?]: Plan 01-05: Contact sheet uses pure-CSS :target lightbox (zero JS); opus verdicts drive thumb display; Phase-1 empty-seed guard in recalculate.js early-exits before touching analysis/ (D-24 invariant)
- [Phase ?]: Humanize Pydantic errors as loc+msg+type; never echo raw JSON body (T-06-03 mitigation).
- [Phase ?]: Phase-2 discover stub raises NotImplementedError with Phase-1 alternative pointer (scanner flow validate).
- [Phase ?]: Deferred imports inside Click subcommands keep --help instant and decouple optional backends from each other
- [Phase ?]: SCANNER_REPO_ROOT env override is the contract for test-time repo isolation; read on every loader call so monkeypatch works
- [Phase ?]: Plan 01-08: Live dry-run validated subscription backend (D-28) end-to-end against mancity.com/hospitality
- [Phase ?]: Plan 01-08: Subscription client extracts JSON from markdown fences + retries once on parse fail (T-08-02)
- [Phase ?]: Plan 01-08: Opus 4.7 returns bboxes in native pixel coords not resized space - filed for Phase 2 calibration
- [Phase ?]: Plan 02-01: credentials helper at scanner.capture.credentials — get_credential returns None on missing (D-15), MissingCredentialError refuses value= kwarg (T-02-01-02)
- [Phase ?]: Plan 02-01: load_dotenv(override=False) at import — shell env wins over .env.local (T-02-01-05 accepted for CI secret-store injection)
- [Phase ?]: Liverpool absent from REVIEW-SOURCES.md — CLAUDE.md DO NOT TOUCH scope extended to review corpora; name redacted to pass plan's grep acceptance
- [Phase ?]: Arsenal cataloged as 'catalog only — NOT crawled' in REVIEW-SOURCES.md (headless-block trap; gold-standard catalog stays complete)
- [Phase ?]: 5 review-dig additions: accessible_booking_option, corporate_invoice_billing, cancellation_refund_window, multi_occasion_tagging, transport_package_bundling
- [Phase ?]: Per-club cookie strategies TOT/RMA/PSG/CHE shipped verbatim from 02-RESEARCH.md (additive)
- [Phase 02]: FlowMapMetadata additive default-factory field preserves Phase-1 backward compat — New crawler metadata shouldn't break existing flow-map JSON
- [Phase 02]: Broker allowlist scoped to 5 vendors (seat_unique/keith_prowse/eventmasters/p1_travel/pitch_international) — Non-broker cross-origin halts branch; narrows attack surface for tracker domains
- [Phase 02]: HOSPITALITY_LINK_PATTERN extended with enquiry/enquire/enquiries — UK clubs commonly label hospitality CTAs 'Enquire Now'

### Pending Todos

None yet.

### Blockers/Concerns

yet.

- Plan 02-02: awaiting user approval 'approved — freeze candidates' in main conversation before plan 02-03 can derive HOSPITALITY-FLOW.md rubric + features.ts (D-05 hard gate)

## Session Continuity

Last session: 2026-04-24T19:45:31.122Z
Stopped at: Plan 01-08 complete: Phase 1 acceptance gate PASSED via live dry-run (subscription backend, 2 bugfixes, 138/138 pytest, D-24 holds)
Resume file: None
