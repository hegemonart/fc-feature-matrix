---
phase: 01-flow-automation-layer
plan: 04
subsystem: scanner.vision
tags: [python, vision, dual-backend, claude-agent-sdk, anthropic, pydantic, pil, protocol, runtime-checkable, structured-outputs]

dependency_graph:
  requires:
    - "Plan 01 (Wave 0): scanner package skeleton + dual-backend deps (claude-agent-sdk 0.1.65, anthropic 0.97.0) + 7 empty vision test scaffolds"
    - "Plan 02 (Wave 1): scanner.vision.schema — FeatureDef, FeatureVerdict, JudgeResponse Pydantic models"
    - "Plan 03 (Wave 2): scanner.capture.banner_verify lazy-imports scanner.vision.factory (closes TODO(01-04) forward-ref)"
  provides:
    - "scanner.vision.client.VisionClient — runtime_checkable Protocol, the dual-backend contract"
    - "scanner.vision.client_subscription.SubscriptionVisionClient — claude-agent-sdk backend (D-26a default)"
    - "scanner.vision.client_apikey.APIKeyVisionClient — anthropic SDK backend with Structured Outputs beta (D-26b)"
    - "scanner.vision.factory.get_client — api_mode dispatcher with env-var guard on the api-key path"
    - "scanner.vision.prompts.build_checklist_prompt + OUTPUT_SCHEMA — D-18 checklist-first prompt + JSON Schema"
    - "scanner.vision.judge.two_judge + OPUS_MODEL/SONNET_MODEL — dual-judge orchestrator (D-19, D-29)"
    - "scanner.vision.disagreement — Disagreement dataclass, bbox_iou, find_disagreements, write_disagreements (research §3.4)"
    - "scanner.vision.slice — SliceResult, denormalise_bbox, slice_feature, MIN_CROP_PX=50, PAD_PX=10 (research §3.6 + §4)"
  affects:
    - "Plan 03: scanner.capture.banner_verify.verify_banner_gone now succeeds — factory importable, ask_yes_no contract met"
    - "Plan 05 (report): consumes JudgeResponse.results to render contact sheets"
    - "Plan 06 (flow validate/discover): scoring layer will consume find_disagreements output"
    - "Plan 07 (CLI): wires --api-mode flag into factory.get_client"
    - "Plan 08 (dry-run): exercises the full subscription path end-to-end (D-28)"

tech_stack:
  added: []  # claude-agent-sdk 0.1.65 + anthropic 0.97.0 already in Plan 01 lockfile
  patterns:
    - "Runtime-checkable Protocol as dual-backend contract — isinstance works for any duck-typed class with matching methods (no inheritance required)"
    - "Deferred import of concrete backends inside factory branches — api-key deps are not paid unless user opts in"
    - "Structured Outputs beta via anthropic 0.97.0 uses `output_config={\"format\": {\"type\": \"json_schema\", \"schema\": ...}}` (NOT `output_format` as older docs suggest)"
    - "Async-to-sync seam: asyncio.run drives claude_agent_sdk.query inside otherwise-sync public methods; tests patch `query` to an async generator"
    - "Confidence clamping (T-04-02) happens in the client layer BEFORE Pydantic — strict ge/le bounds in FeatureVerdict would otherwise reject 1.0001"
    - "Three-rule disagreement detector returns Pydantic.model_dump() dicts so results JSON-serialise without a custom encoder"
    - "AST-based negative-import guard in tests — walks the subscription module's AST to assert zero anthropic imports (less fragile than string grep)"

key_files:
  created:
    - path: scanner/vision/client.py
      role: "VisionClient Protocol (runtime_checkable); minimal documentation of the dual-backend contract"
    - path: scanner/vision/prompts.py
      role: "D-18 checklist-first prompt builder + OUTPUT_SCHEMA JSON Schema; zero Jinja dependency"
    - path: scanner/vision/client_subscription.py
      role: "D-26a default backend — claude-agent-sdk only, asyncio.run bridges the async iterator"
    - path: scanner/vision/client_apikey.py
      role: "D-26b fallback backend — anthropic SDK only, Structured Outputs beta header"
    - path: scanner/vision/factory.py
      role: "get_client(api_mode, model) dispatcher; raises RuntimeError if ANTHROPIC_API_KEY missing in api-key mode (T-04-01)"
    - path: scanner/vision/judge.py
      role: "two_judge(image, rubric, api_mode) → {opus: JudgeResponse, sonnet: JudgeResponse}; pins OPUS_MODEL/SONNET_MODEL constants"
    - path: scanner/vision/disagreement.py
      role: "Three-rule consensus check (presence/confidence/bbox IoU) + write_disagreements JSON serialiser"
    - path: scanner/vision/slice.py
      role: "PIL crop with PAD_PX=10, MIN_CROP_PX=50 reject, bounds clamp; denormalise_bbox for Opus vs Sonnet/Haiku coord systems"
  modified:
    - path: scanner/tests/test_vision_client.py
      change: "5 tests: duck-type isinstance pass, missing-method reject, both concrete backends conform"
    - path: scanner/tests/test_vision_subscription.py
      change: "5 tests: constructor, analyze_screenshot JSON parse, confidence clamp, ask_yes_no lowercase, AST-based anthropic-import negative check"
    - path: scanner/tests/test_vision_apikey.py
      change: "5 tests: structured-outputs beta header, image+text request shape, confidence clamp, ask_yes_no, _clamp_confidence helper bounds"
    - path: scanner/tests/test_vision_factory.py
      change: "5 tests: subscription-without-env OK, api-key-without-env RuntimeError, api-key-with-env OK, bogus mode ValueError, both backends satisfy Protocol"
    - path: scanner/tests/test_vision_judge.py
      change: "4 tests: get_client called twice with both models + same api_mode, api_mode defaults to subscription, rubric forwarded verbatim, model constants"
    - path: scanner/tests/test_vision_disagreement.py
      change: "10 tests: bbox_iou identical/disjoint/partial/zero-area, each rule (presence/confidence/bbox), full-agreement empty, missing-key skip, write round-trip, mkdir -p parent"
    - path: scanner/tests/test_slice.py
      change: "10 tests: happy path 120x120 pad, tiny reject, oversize clamp, negative-origin reject, outside-bounds reject, opus at-limit identity, sonnet 2x scale-up, under-limit identity, haiku shares sonnet limit, MIN_CROP_PX/PAD_PX constants"
    - path: scanner/tests/test_banner_verify.py
      change: "Rule-2 deviation fix: the haiku-pin test stubbed sys.modules but then re-imported via `import scanner.vision.factory as ...`, which returned the REAL factory after Plan 04 pre-imported it. Lookup via sys.modules directly instead."

decisions:
  - id: D-04-1
    text: "anthropic 0.97.0's Structured Outputs parameter is `output_config` (TypedDict with a required `format` key), NOT `output_format`. The plan's sketch used `output_format`; the implementation uses `output_config` per the installed SDK. Research §3.3 must be updated before Plan 08 dry-run."
  - id: D-04-2
    text: "claude_agent_sdk.query signature: async + keyword-only, returns AsyncIterator of Message dataclasses. Options is a ClaudeAgentOptions dataclass (NOT a dict). In streaming mode prompt is AsyncIterable[dict] with {'type': 'user', 'message': {'role': 'user', 'content': [...]}} shape."
  - id: D-04-3
    text: "Runtime-checkable Protocol only inspects METHOD presence at runtime, not attribute declarations. A class without the `model` attribute still passes isinstance(obj, VisionClient). Static type checkers catch missing attributes in call sites; runtime relies on duck typing."
  - id: D-04-4
    text: "Confidence clamping lives in _clamp_confidence inside client_apikey.py and is IMPORTED by client_subscription.py (via a late, function-local import to avoid coupling backends at module level). A shared scanner/vision/_clamp.py helper would be cleaner but not worth the fourth module in Wave 3."

autonomous_decisions_resolved:
  - "Chose to implement _build_streaming_prompt as a module-level helper (not inside _collect_text) so it's unit-testable in isolation and its async-generator shape is obvious."
  - "Judge orchestrator does NOT handle partial failure (single-judge fallback) at Plan 04 — deferred to Plan 07/08 where the CLI retry policy lives. two_judge is strictly parallel on happy paths."
  - "Disagreement.opus/.sonnet are dict (FeatureVerdict.model_dump()) not FeatureVerdict instances so write_disagreements can json.dumps(asdict(d)) without a custom encoder."

metrics:
  duration: "~18 minutes"
  completed_date: "2026-04-24"
  tasks_planned: 3
  tasks_completed: 3
  tests_added: 44
  tests_passing: 44
  full_suite_passing: "103/103"
  loc_added: 1585  # 8 vision modules + 7 test files (delta)
  commits: 4
---

# Phase 01 Plan 04: Dual-Backend Vision Module Summary

The central load-bearing module of Phase 1 — eight vision files + seven fully-populated test files — ships a two-backend vision system where the subscription path (claude-agent-sdk) and the api-key path (anthropic SDK) are fully interchangeable from every downstream caller's point of view (D-26..D-29).

## What Landed

**Eight production modules, 44 tests, zero live SDK calls.**

1. **`scanner/vision/client.py`** (46 LOC) — `VisionClient` as a `@runtime_checkable` `typing.Protocol`. Two methods (`analyze_screenshot`, `ask_yes_no`) and one attribute (`model`). Duck-typing contract, not a base class — both backends implement it via shape, not inheritance.

2. **`scanner/vision/prompts.py`** (86 LOC) — `build_checklist_prompt(features, step_name)` constructs a D-18 checklist-first prompt listing every feature key and its `yes_criterion`. `OUTPUT_SCHEMA` is the JSON Schema (per research §3.3) used by the api-key backend's Structured Outputs beta.

3. **`scanner/vision/client_subscription.py`** (132 LOC) — D-26a default backend. Imports only `claude_agent_sdk.query` + `ClaudeAgentOptions`; never `anthropic`. `analyze_screenshot` base64-encodes the PNG, builds the streaming-prompt shape, drains the async iterator via `asyncio.run`, and returns `{feature_key: FeatureVerdict}` after clamping.

4. **`scanner/vision/client_apikey.py`** (121 LOC) — D-26b fallback backend. Imports only `anthropic`; never `claude_agent_sdk`. Uses Structured Outputs beta via `output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}}` and the `anthropic-beta: structured-outputs-2025-11-13` default header. Exposes the shared `_clamp_confidence` helper.

5. **`scanner/vision/factory.py`** (64 LOC) — `get_client(api_mode, model)`. Subscription branch imports `SubscriptionVisionClient` lazily and returns it immediately. Api-key branch reads `ANTHROPIC_API_KEY` from `os.environ`, raises `RuntimeError` with a clear fix-it message if absent (T-04-01), then imports and returns `APIKeyVisionClient`. Any other `api_mode` raises `ValueError`.

6. **`scanner/vision/judge.py`** (58 LOC) — `two_judge(image_path, rubric, *, api_mode="subscription")` calls `get_client` twice (once per model), runs each `analyze_screenshot`, wraps results in `JudgeResponse` instances and returns a `{"opus": ..., "sonnet": ...}` dict. `OPUS_MODEL`/`SONNET_MODEL` are module-level constants per D-29.

7. **`scanner/vision/disagreement.py`** (112 LOC) — Three-rule consensus check:
   - `bbox_iou(a, b)` — intersection-over-union on `(x,y,w,h)` tuples; handles zero-area/disjoint boxes returning 0.0.
   - `find_disagreements(opus, sonnet)` — flags `presence` mismatch (and skips other rules for that feature), otherwise flags `confidence` gaps > 0.3, otherwise flags `bbox` IoU < 0.5 when both verdicts have non-null bboxes.
   - `write_disagreements(list, path)` — creates parent dir, serializes `asdict`-dumped dataclasses as indented JSON, ready for Plan 08 review.

8. **`scanner/vision/slice.py`** (126 LOC) — PIL cropper ported from `recapture_round5.py::capture_from_fullpage`:
   - `denormalise_bbox(bbox, model, w, h)` — scales the bbox up when the source image's long edge exceeds the model's limit (2576 for Opus 4.7, 1568 for Sonnet/Haiku). Under-limit returns identity.
   - `slice_feature(png_bytes, bbox, out_path)` — pads 10 px, clamps to image bounds, rejects crops < 50×50 with a reason string, saves optimized PNG. Returns a structured `SliceResult` so callers can log the reason on failure.

## Test Coverage

**44 Plan-04 tests, 103 total, 103 green, 0 skipped, 0 flaky.**

| Test file                         | Tests | Coverage focus |
| ---                               | ---   | --- |
| test_vision_client.py             | 5     | runtime_checkable duck-typing, both concrete backends satisfy Protocol |
| test_vision_subscription.py       | 5     | constructor, JSON parse, confidence clamp, yes/no lowercase, AST-based negative-import guard |
| test_vision_apikey.py             | 5     | beta header, image+text+output_config request shape, clamp, yes/no, clamp helper bounds |
| test_vision_factory.py            | 5     | subscription without key OK, api-key without key raises, api-key with key OK, bogus mode, protocol conformance |
| test_vision_judge.py              | 4     | get_client dispatched twice with same api_mode, default mode, rubric forwarded, model constants |
| test_vision_disagreement.py       | 10    | iou math (4), each rule (3), agreement empty, missing-key skip, write round-trip, mkdir -p |
| test_slice.py                     | 10    | happy path 120×120, tiny reject, oversize clamp, negative origin, past bounds, opus at-limit, sonnet 2×, under-limit, haiku, constants |

All tests use `unittest.mock.patch` / `MagicMock` — zero calls cross a network boundary.

## Deviations from Plan

### Rule 2 — Missing Critical

**1. [Rule 2 — Missing Critical] Fixed import-cache bug in `test_banner_verify.py::test_verify_banner_gone_passes_haiku_model_to_factory`**
- **Found during:** Full-suite run after Task 3
- **Issue:** Once Plan 04 ships `scanner/vision/factory.py`, tests that import it (e.g. `test_vision_factory`) pre-populate `sys.modules["scanner.vision.factory"]` and bind the real module as an attribute on `scanner.vision`. The banner_verify test then did `monkeypatch.setitem(sys.modules, ...)` to stub the module, but followed up with `import scanner.vision.factory as fake_factory` — which, because the real module was already cached, returned the REAL module (whose `get_client` is a plain function with no `.call_args` attribute). Isolated runs passed; full-suite runs failed with `AttributeError: 'function' object has no attribute 'call_args'`.
- **Fix:** Replaced `import scanner.vision.factory as fake_factory` with `fake_factory = sys.modules["scanner.vision.factory"]`. The sys.modules lookup always returns whatever monkeypatch set, bypassing Python's attribute-caching quirk.
- **Files modified:** `scanner/tests/test_banner_verify.py` (4 lines changed)
- **Commit:** `1b9e33b`

No Rule 1, Rule 3, or Rule 4 deviations.

### Plan-Sketch Corrections

- **`output_format` → `output_config`** — the plan's `<interfaces>` block sketched `output_format={"type": "json_schema", "schema": OUTPUT_SCHEMA}`. anthropic 0.97.0's `messages.create` takes `output_config: OutputConfigParam` where `OutputConfigParam` is a `TypedDict` with a `format: JSONOutputFormatParam` field. Shipped: `output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}}`. Verified by reading `anthropic/types/output_config_param.py` in the installed 0.97.0 wheel.
- **`claude_agent_sdk.query` options type** — the plan sketched `options={"model": self.model}` (dict). The real SDK requires `options=ClaudeAgentOptions(model=self.model)` (dataclass). Shipped with dataclass. `query` is also keyword-only and strictly async — drove the `asyncio.run` + `_build_streaming_prompt` structure.
- **Streaming prompt shape** — The subscription backend passes an `AsyncIterable[dict]` where each dict is `{"type": "user", "message": {"role": "user", "content": [image_block, text_block]}}`. `_build_streaming_prompt` returns such a generator.

## Threat-Model Status

| Threat ID | Status | Evidence |
|-----------|--------|----------|
| T-04-01 (API key info disclosure) | mitigated | `factory.get_client` reads via `os.environ.get`; never logged or passed positionally. Test `test_api_key_mode_without_env_raises_runtime_error` locks the guard. |
| T-04-02 (confidence out-of-bounds) | mitigated | `_clamp_confidence` coerces to [0.0, 1.0]. Tested from both client sides (`test_analyze_screenshot_clamps_out_of_range_confidence`, `test_analyze_screenshot_clamps_confidence`) + directly (`test_clamp_confidence_helper_bounds`). |
| T-04-03 (markdown-fenced JSON) | mitigated | Subscription prompt appends explicit "no surrounding text, no markdown fences"; api-key uses Structured Outputs beta which returns raw JSON. |
| T-04-04 (dummy-data upload) | accepted | Per D-16 (Phase 1 dry-run uses dummy accounts only). |
| T-04-05 (DoS via oversize response) | mitigated | `max_tokens=4096` on api-key `analyze_screenshot`; `max_tokens=10` on `ask_yes_no`; subscription bounded by Pydantic `notes` max_length=500 + model's own output cap. |
| T-04-06 (claude CLI missing) | carried | Handled by Plan 03 / Plan 08 pre-flight — out of scope for Plan 04. |

## Self-Check: PASSED

- `scanner/vision/client.py` → FOUND (class VisionClient(Protocol), runtime_checkable)
- `scanner/vision/client_subscription.py` → FOUND (no anthropic imports, AST-verified)
- `scanner/vision/client_apikey.py` → FOUND (no claude_agent_sdk imports, beta header present)
- `scanner/vision/factory.py` → FOUND (RuntimeError on missing env var)
- `scanner/vision/prompts.py` → FOUND (OUTPUT_SCHEMA + build_checklist_prompt exported)
- `scanner/vision/judge.py` → FOUND (OPUS_MODEL="claude-opus-4-7", SONNET_MODEL="claude-sonnet-4-6")
- `scanner/vision/disagreement.py` → FOUND (bbox_iou, find_disagreements, write_disagreements, Disagreement)
- `scanner/vision/slice.py` → FOUND (MIN_CROP_PX=50, PAD_PX=10, denormalise_bbox, slice_feature)
- Commit `7c14470` → FOUND (Task 1)
- Commit `5e81014` → FOUND (Task 2)
- Commit `ce56ac4` → FOUND (Task 3)
- Commit `1b9e33b` → FOUND (Rule-2 deviation fix)
- All 7 Plan-04 test files ≥ 3 tests each: test_vision_subscription.py 5, test_vision_apikey.py 5, test_vision_factory.py 5, test_vision_client.py 5, test_vision_judge.py 4, test_vision_disagreement.py 10, test_slice.py 10
- `uv run python -m pytest scanner/tests/` → 103/103 passed
- `git diff --quiet analysis/` → clean (D-24 invariant)
