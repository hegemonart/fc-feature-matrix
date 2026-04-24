---
phase: 02-hospitality-pilot
plan: 05
subsystem: scanner/flow
tags:
  - scanner
  - flow-discovery
  - crawler
  - schema-additive

requires:
  - scanner.flow.schema.FlowMap (Phase 1, Plan 01-02)
  - scanner.flow.validate.validate_flow_map (Phase 1, Plan 01-03)
  - scanner.capture.cookies.dismiss_cookies (Phase 1, Plan 01-05)
  - playwright>=1.49 (scanner/pyproject.toml dep)

provides:
  - scanner.flow.schema.FlowMapMetadata (model)
  - scanner.flow.schema.FlowMap.metadata (field, default-factory)
  - scanner.flow.discover.discover_flow (replaces NotImplementedError stub)
  - scanner.flow.discover.BROKER_DOMAINS (allowlist)
  - scanner.flow.discover.HOSPITALITY_LINK_PATTERN
  - scanner.flow.discover.LOGIN_URL_PATTERN
  - scanner.flow.discover.CAPTCHA_SELECTORS
  - CLI: scanner flow discover --area --club --headless

affects:
  - scanner/cli.py (flow_discover_cmd docstring + new flags; Phase-2-stub text removed)

tech-stack:
  added: []
  patterns:
    - sync_playwright() context manager (matches scanner.capture.browser idiom)
    - default_factory for backward-compat additive fields (Pydantic v2)
    - detect/halt per-branch pattern (no recursion explosion on JS-heavy pages)

key-files:
  created: []
  modified:
    - scanner/flow/schema.py            (62 → 101 LOC)
    - scanner/flow/discover.py          (44 → 517 LOC — full crawler)
    - scanner/tests/test_flow_schema.py (138 → 213 LOC — +5 tests)
    - scanner/tests/test_flow_discover.py (27 → 394 LOC — deleted 2 stub tests, added 9)
    - scanner/cli.py                    (+43 LOC — --area/--club/--headless + summary echo)

decisions:
  - "Scoped broker allowlist to 5 vendors (seatunique, keithprowse, eventmasters, p1travel, pitchinternational). Non-broker cross-origin halts the branch, preserving D-16 (no form submits into unknown domains)."
  - "Extended HOSPITALITY_LINK_PATTERN with 'enquiry|enquire|enquiries' — many club hospitality CTAs are labeled 'Enquire Now' rather than 'VIP'."
  - "Broker-vendor capture uses first-encountered winner — nested broker hops (unlikely) don't overwrite."
  - "DUMMY_FORM_FIELDS are module-level FormField constants (D-10 values). Copied via list() into each fill step so mutation in one step can't bleed into another."
  - "_write_and_validate truncates at MAX_STEPS preserving steps[0] (landing) and steps[-1] (terminal screenshot) — middle steps dropped if truncation needed."

metrics:
  duration: 35 minutes
  completed: 2026-04-24
  tasks: 2/2
  commits: 5
  tests_before: 155
  tests_after: 167  # +12 net (5 schema + 9 discover − 2 deleted stubs)
---

# Phase 2 Plan 05: Flow-Discovery Crawler Implementation Summary

Replaced the `scanner.flow.discover.NotImplementedError` stub with a real sync-Playwright crawler that performs keyword-ranked depth-limited click-path discovery and emits schema-valid `FlowMap` JSON with a new `FlowMapMetadata` block recording login/CAPTCHA/broker/external/dead-end outcomes.

## What This Plan Delivers

The Phase 2 dry-run pipeline needs flow-maps for the 5 pilot clubs. Plan 02-05 delivers the engine that produces them; Plan 02-06 runs it live. Before this plan, `scanner flow discover` raised `NotImplementedError` with a Phase-1-era pointer to hand-authored flow-maps. After this plan, it opens a real Chromium session, dismisses cookies, enumerates hospitality-keyword-ranked links, descends greedily up to 3 levels deep (capped at 15 steps per D-15), and halts per-branch on any of six detection hooks: login gate, CAPTCHA, external redirect, dead-end, or pre-submit form (plus continue-through for allowlisted brokers).

The design is deliberately conservative: the crawler never clicks submit buttons (D-16 + regression test), never traverses login gates (D-15), never attempts CAPTCHA bypass (user decision 7), and halts on unknown cross-origin redirects. All halted branches are recorded in `FlowMap.metadata` so the downstream capture wave (back-half) can triage them deliberately — login-gated flows become credential-requiring runs, external redirects become tracker-audit evidence, and dead-ends become rubric signals.

## Architecture

### Schema change (additive)

`scanner/flow/schema.py` gains one new model and one new field. The field is `default_factory`-initialized, so every pre-existing Phase-1 flow-map JSON (no `metadata` key) still validates unchanged.

```python
class FlowMapMetadata(BaseModel):
    broker_vendor: str | None = None
    login_gated_steps: list[str] = Field(default_factory=list)
    external_redirects: list[str] = Field(default_factory=list)
    dead_ends: list[str] = Field(default_factory=list)
    cookie_dismiss_failed: bool = False
    fixture_id: str | None = None
    captcha_encountered: bool = False

class FlowMap(BaseModel):
    # ... existing fields ...
    metadata: FlowMapMetadata = Field(default_factory=FlowMapMetadata)
```

### Crawler core

`discover_flow(entry_url, out_path, *, area, club, headless)` orchestrates:

1. `sync_playwright()` launch → Chromium `new_context(viewport=1440×900, dpr=2)` → `new_page()`.
2. `page.goto(entry_url, wait_until="networkidle")` and record `(navigate, wait, screenshot)` triple.
3. `dismiss_cookies(page, club=...)`; on failure flip `meta.cookie_dismiss_failed` but continue.
4. Landing-level dead-end shortcut — if response status ≥ 400 or h1 matches `404|not found`, record and short-circuit.
5. Call `_descend(depth=1)` — greedy per-level: rank all `<a href>` against `HOSPITALITY_LINK_PATTERN`, click the highest-scoring unvisited link, emit the `(click, wait, screenshot)` triple, apply detection hooks on the new page, recurse one level deeper.
6. After descent completes, `_write_and_validate` writes the FlowMap JSON (truncating to MAX_STEPS preserving first + last) and round-trips through `validate_flow_map`.

### Detection hook ordering

The order matters because origin/login detection must happen before click emission to avoid wasting steps:

```text
for each page visited:
  1. CAPTCHA          → captcha_encountered=True;  halt branch
  2. origin check     → broker (record vendor, continue) | external (record URL, halt)
  3. login gate       → login_gated_steps append;  halt branch
  4. form pre-submit  → emit fill + shot;          halt branch (never submit)
  5. rank + click     → emit click/wait/shot triple and recurse
```

### Broker allowlist

Top-level `BROKER_DOMAINS` constant in `discover.py`:

| Domain                   | Vendor label            |
| ------------------------ | ----------------------- |
| seatunique.com           | seat_unique             |
| keithprowse.co.uk        | keith_prowse            |
| eventmasters.co.uk       | eventmasters            |
| p1travel.com             | p1_travel               |
| pitchinternational.com   | pitch_international     |

Matched by `netloc == domain` or `netloc.endswith('.' + domain)` so subdomains count. Only the first broker encountered wins (prevents nested-hop overwrites).

## Tests

`test_flow_schema.py` — 5 new tests on top of the existing 10:

| Test | Asserts |
| ---- | ------- |
| test_flow_map_defaults_metadata_to_empty | FlowMap without `metadata` key gets default-factory instance (backward compat) |
| test_flow_map_metadata_roundtrips | Fully populated metadata survives JSON roundtrip |
| test_flow_map_metadata_login_gated_steps_is_list_of_str | Non-string items raise ValidationError |
| test_flow_map_metadata_rejects_obviously_wrong_types | Wrong-type scalars raise ValidationError |
| test_flow_map_metadata_mutable_defaults_are_isolated | Mutable-default trap: sibling instances' lists are distinct |

`test_flow_discover.py` — 2 stub tests deleted, 9 behavior tests added:

| Test | Scenario | Assertion |
| ---- | -------- | --------- |
| test_discover_emits_valid_flow_map_against_stub_page | Landing + one hospitality link → dead-end | FlowMap valid, metadata.dead_ends populated |
| test_discover_detects_login_gate | Link leads to `/account/login` with password input | login_gated_steps populated; no click past login |
| test_discover_detects_broker_redirect | Link targets `seatunique.com` | broker_vendor == "seat_unique"; crawl continues |
| test_discover_detects_external_unknown_redirect | Same-origin link resolves to `randomtracker.example` | external_redirects populated; broker_vendor None |
| test_discover_detects_dead_end | Click leads to HTTP 404 + "404 Not Found" h1 | dead_ends populated; JSON still valid on disk |
| test_discover_detects_captcha | New page has recaptcha iframe | captcha_encountered == True |
| test_discover_never_emits_submit_action | Form scenario | No FlowStep.action == "submit" anywhere (regression guard on D-16) |
| test_discover_output_passes_validate_flow_map | Happy path | validate_flow_map(out) returns without raising |
| test_discover_detects_form_and_fills_with_dummy_data | Page has ≥3 text/email/tel inputs | fill step emits D-10 dummy values |

All 24 flow tests pass; full scanner suite is 167/167 green (was 155, net +12: 5 schema + 9 discover − 2 deleted stubs).

## Mocking Notes

Building a `MagicMock`-based Playwright Page surface worked well once I factored out a `_FakeResponse` dataclass-shaped helper and a `_make_page(responses)` factory. Key trick: `type(page).url = property(lambda _: _current().url)` so `page.url` reads the *current* response dynamically — this is what lets `test_discover_detects_external_unknown_redirect` simulate a same-origin href that "redirects" to a tracker domain post-click.

Two edge cases surfaced during implementation:

1. **Initial test iteration failed** on `test_discover_detects_external_unknown_redirect` because I made the href itself cross-origin. `_rank_links` correctly filters non-broker cross-origin hrefs at ranking time (it's an attack-surface narrower), so the click never happened and no external-redirect was recorded. The fix was to make the test realistic: a same-origin hospitality href (`/hospitality/partner`) that resolves to a tracker domain *after* click — which is how real-world server-side 302 redirects work.
2. **Form-fill step ordering**: I initially put the `fill` step emission inside the click loop; had to move it into the detection-hook section so the form is recognized on the *landed* page, not the pre-click page. The fix was straightforward — check `_detect_form(page)` before ranking links on each iteration.

## Deviations from Plan

### Added beyond the plan spec (Rule 2 — Missing Critical)

- **CLI flags `--area`, `--club`, `--headless`** (scanner/cli.py). The underlying function now accepts these; the CLI previously had none. Without them, the CLI cannot dispatch cookie strategies by club slug (D-15 regression risk) and cannot be toggled headed for manual debugging. Plan Task 2 deviation rules explicitly permit this as "a CLI-layer addition, not a module-internals change, so D-21 still holds."
- **CLI help text update**: replaced `Phase 2 stub — raises NotImplementedError` with a substantive description of what the command actually does. The old text would have confused users who tried the CLI post-plan.
- **Extended `HOSPITALITY_LINK_PATTERN`** with `enquiry|enquire|enquiries`. Observed during research that many UK club hospitality CTAs are labeled "Enquire Now" rather than "VIP"; without this the keyword ranker would skip those links. Added as a same-tier inclusion in the existing regex.

### Fixed during implementation (Rule 1 — Bug)

- **Test 4 (`test_discover_detects_external_unknown_redirect`)** — initial mock setup had the `<a href>` itself cross-origin, which `_rank_links` correctly filters at ranking time. Rewritten to use a same-origin href that "redirects" to a tracker domain after click (realistic scenario).

### None of the following occurred

- No CAPTCHA bypass code was added (user decision 7).
- No credentials were threaded through (front-half scope; Plan 02-01's credentials helper is untouched here).
- No `submit` action emitted anywhere (D-16 held; verified by regression test).
- `scanner/capture/browser.py`, `scanner/capture/banner_verify.py`, `scanner/vision/`, `scanner/scoring/`, `scanner/report/` untouched (D-21).
- `analysis/` untouched (D-20).

## Authentication Gates

None. Plan executed purely against mocked Playwright objects; no live network calls required.

## Commits

```
f762eae test(02-05): add failing tests for FlowMapMetadata additive field
82059c1 feat(02-05): add FlowMapMetadata to FlowMap schema
c59ec3f test(02-05): replace NotImplementedError tests with 9 crawler behavior tests
cfa0975 feat(02-05): implement discover_flow crawler with login/broker/captcha/dead-end detection
e6b3607 feat(02-05): wire discover_flow CLI flags (--area, --club, --headless)
```

## Self-Check: PASSED

- scanner/flow/schema.py — 101 LOC, FlowMapMetadata class present, metadata field present, __all__ exports FlowMapMetadata.
- scanner/flow/discover.py — 517 LOC, `def discover_flow` present, `BROKER_DOMAINS` present, `sync_playwright` imported, no `raise NotImplementedError`, no emit of `"submit"` action.
- scanner/tests/test_flow_discover.py — 9 `test_discover_*` functions, 0 `test_discover_flow_raises_not_implemented`.
- scanner/tests/test_flow_schema.py — 15 tests (10 existing + 5 new).
- Full scanner suite: 167 passed.
- `git diff --quiet analysis/` → exit 0 (D-20 holds).
- `git diff --quiet scanner/capture/browser.py scanner/capture/banner_verify.py scanner/vision/ scanner/scoring/ scanner/report/` → exit 0 (D-21 holds).
- Commits present: f762eae, 82059c1, c59ec3f, cfa0975, e6b3607.
