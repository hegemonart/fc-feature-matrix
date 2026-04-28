# Scanner v2 — Changelog

Architecture changes layered on top of the Phase 1 / Phase 2 front-half scanner. Strictly additive — every Phase 1 entrypoint (`capture_page`, `capture_flow`, `two_judge`) keeps its old signature and the dual-backend vision contract is unchanged.

---

## v2.0 — 2026-04-28 — Plan 02-15 Scanner V2 architecture upgrade

### Why

Plan 02-11's pilot vision wave produced an aggregate **88% absence rate** (225 of 275 cells reported absent across the 5 pilot clubs). Two operational gaps caused most of that:

1. **Bot blocks** — Cloudflare Turnstile + headless detection fired on MCFC, PSG, and Real Madrid landing pages, leaving 30 of 32 capture steps deferred to manual Chrome MCP work.
2. **Vision-only detection** — every feature, even programmatically obvious ones (count form inputs, find a `tel:` link, scan headings for "menu"), went through Opus + Sonnet. Vision is excellent at brand judgment but expensive at 16 PNGs × $0.30–0.50 ≈ $5.50–6.50 retail-equivalent for one wave, and noisier than necessary on rule-friendly features.

v2 attacks both: stealth fingerprint masks reduce the bot-block surface; DOM intel + a hybrid routing layer answers the cheap features without a vision call.

### D-21 deviation note (Phase 2 modifying Phase 1 territory)

`scanner/capture/` and `scanner/vision/` are Phase 1 territory. Phase 2 normally only adds flow-maps and rubric data. This plan modifies both subsystems because the operational gap above cannot be closed by data alone — it needs anti-bot + DOM extraction in the capture layer and routing in the vision layer. Approved by reading "Risks carried into back-half" in `.planning/phases/02-hospitality-pilot/02-BACK-HALF-HANDOFF.md` and accepted as the delta-21 escape hatch (same pattern as Plan 02-10 added `capture_flow`, Plan 02-08 added bbox calibration).

### What shipped

Five waves, atomic per-task commits.

| Wave | Subsystem | Commit | Highlights |
|------|-----------|--------|-----------|
| A | `scanner/capture/browser.py` | `57c8798` | `playwright-stealth>=1.1` dep, `create_browser(stealth=True)` default. Lazy import + try/except so missing dep degrades to a logged warning. |
| B | `scanner/capture/{capture,dom_intel}.py`, `scanner/config/schema.py` | `64ed70d` | `EXTRACT_DOM_INTEL_JS` + `DomIntel` pydantic schema. `capture_page`/`capture_flow` write `{output_dir}/html/{club}_{step}.html` and `{output_dir}/dom/{club}_{step}_intel.json` alongside the PNG. `AreaEntry.html_dir` + `dom_intel_dir` (optional, default None). |
| C | `scanner/vision/dom_detect.py` | `d37036a` | 22-rule registry (`RULES`) covering pricing, F&B, amenities, enquiry, post-booking, match-selector. `detect_feature` + `detect_features` wrappers return `FeatureVerdict` at confidence 0.95 with `step="dom-detect"`. |
| D | `analysis/hospitality/{HOSPITALITY-FLOW.md,features.ts}`, `analysis/types.ts`, `scanner/vision/schema.py` | `b42ebb7` | Detection column added to all 8 hospitality category tables. 33 `dom`, 3 `visual`, 19 `hybrid` of 55 features. `FeatureDef.detection: DetectionMode` pydantic field (default `"visual"` for back-compat). |
| E | `scanner/vision/judge.py` | `d3fd73c` | `two_judge(image_path, rubric, *, dom_intel_path=None)` — DOM-tagged features answered by rule, hybrid features short-circuited when DOM rule fires at confidence ≥ 0.85, visual features always routed to Opus + Sonnet. Pre-15 behavior preserved when `dom_intel_path` is omitted (rubric forwarded by identity, `get_client` unconditionally invoked). |

### Cost projection

| Mode | 16 PNGs (Plan 02-11 re-run estimate) | Saving |
|------|----:|----:|
| v1 vision-only retail equivalent (Plan 02-11) | $5.50–6.50 | — |
| v2 hybrid (33 dom rules + 19 hybrid + 3 visual) | $1.50–2.50 | ~60% |

Subscription mode: $0 marginal cost in both cases. The retail-equivalent figure is the projection for the eventual API-key wave or for the 33-club rollout once subscription quota tightens.

### Backward compatibility

- Plan 02-11 result JSONs (visioned 16 PNGs, no DOM intel captured at the time) remain loadable. The vision pipeline still works without `dom_intel_path`; missing intel files log a warning and route every feature to vision.
- The 288 existing pytest tests still pass. 59 net-new tests across the five waves (288 → 347).
- `analysis/homepage/` rubric and results JSONs untouched (D-20 invariant: `git diff --quiet analysis/homepage/` → exit 0).
- `analysis/hospitality/results/*.json` from Plan 02-12 untouched (the user-facing data is the responsibility of Plan 02-17 — this plan only delivers the engine).

### Migration notes

Areas that want DOM intel + hybrid routing:

1. Add `html_dir` and `dom_intel_dir` to the area entry in `scanner/config/areas.json` (optional — defaults pull from `evidence_dir/{html,dom}`).
2. Tag each feature in the rubric (`HOSPITALITY-FLOW.md`-equivalent) and the TS port with a `detection` mode. Default of `"visual"` preserves the old behavior.
3. Pass `dom_intel_path=...` to `two_judge` in the area's vision wave script.

If `playwright-stealth` is unavailable on a target environment, set `stealth=False` on `create_browser()` and the scanner reverts to v1 fingerprinting. The lazy import in `_apply_stealth_sync` swallows missing-dep ImportErrors with a logged warning, so an uninstall never breaks captures.

### Test count delta

| Suite | v1 | v2 | Δ |
|-------|---:|---:|--:|
| `test_browser.py` | 12 | 18 | +6 (stealth + dom capture) |
| `test_dom_detect.py` | 0 | 40 | +40 (new) |
| `test_vision_schema.py` | 12 | 15 | +3 (detection mode) |
| `test_vision_judge.py` | 4 | 12 | +8 (hybrid routing) |
| `test_areas_schema.py` | 7 | 9 | +2 (html_dir / dom_intel_dir) |
| **Other suites** | 253 | 253 | 0 |
| **Total** | **288** | **347** | **+59** |

### Open issues / TBD

- The 22 rules in `RULES` cover the highest-volume hospitality features but are not exhaustive. Plan 02-17 (re-run capture + vision) is expected to surface 5–10 additional rules.
- `live_chat_availability` is tagged `hybrid` but the DOM rule is not yet registered (the capture layer hides the widget per D-11 before extraction, so DOM cannot see it). This is the right v2 behavior — it falls back to vision at 100% — but a follow-up could capture intel BEFORE selector-hiding for chat-detection only.
- Stealth efficacy on Cloudflare Turnstile is empirical; the capture re-run in Plan 02-17 will measure how many of MCFC / PSG / RMA's 30 deferred steps complete unattended after v2.
- `dom_intel_path` is currently passed per call. A follow-up could let `two_judge` infer the path from `image_path` + a convention.

### File map

Created:

- `scanner/capture/dom_intel.py` (180 LOC)
- `scanner/vision/dom_detect.py` (220 LOC)
- `scanner/tests/test_dom_detect.py` (300 LOC, 40 tests)
- `scanner/CHANGELOG-V2.md` (this file)

Modified (additive only):

- `scanner/pyproject.toml` — `playwright-stealth>=1.1`
- `scanner/capture/browser.py` — stealth integration
- `scanner/capture/capture.py` — DOM intel capture in `capture_page` + `capture_flow.screenshot`
- `scanner/config/schema.py` — `html_dir` + `dom_intel_dir` on `AreaEntry`
- `scanner/vision/schema.py` — `DetectionMode` literal + `FeatureDef.detection`
- `scanner/vision/judge.py` — `two_judge(dom_intel_path=...)` hybrid routing
- `scanner/tests/test_browser.py` — stealth + DOM capture tests
- `scanner/tests/test_vision_schema.py` — detection mode tests
- `scanner/tests/test_vision_judge.py` — hybrid routing tests
- `scanner/tests/test_areas_schema.py` — html_dir / dom_intel_dir tests
- `analysis/hospitality/HOSPITALITY-FLOW.md` — Detection column on 8 tables
- `analysis/hospitality/features.ts` — `detection` argument on all 55 `feat()` calls
- `analysis/types.ts` — `DetectionMode` type + optional `Feature.detection`
