"""Two-judge orchestrator — runs Opus + Sonnet over the same screenshot.

Per D-19 and user-decision-4 both judges run through the *same* ``api_mode``;
mixing subscription and api-key in a single dual-judge run is disallowed in
Phase 1 to keep cost/quota accounting clean.

Plan 02-15 Wave E adds **hybrid DOM+vision routing**:

- Each :class:`FeatureDef` carries a ``detection`` mode tag (``dom`` /
  ``visual`` / ``hybrid``).
- ``two_judge`` now consults the DOM intel (when supplied) BEFORE running
  the vision wave. ``dom`` features are answered by :mod:`dom_detect` only;
  ``hybrid`` features take the DOM answer when it's positive (confidence
  ``>= 0.85``), else fall back to vision; ``visual`` features always go to
  the Opus + Sonnet wave.
- The rubric handed to each vision client is FILTERED to the subset that
  still needs vision. The two judges still see an identical sub-rubric
  (D-18 preserved). Cost saving is the primary goal.

Backward compatibility (D-21):
- If ``dom_intel_path`` is omitted, the routing collapses to the pre-15
  behavior: every feature regardless of its ``detection`` tag is routed
  to vision.
- The return-shape contract is preserved: ``{"opus": JudgeResponse,
  "sonnet": JudgeResponse}``. The DOM-derived verdicts are merged into
  BOTH judges' ``results`` so downstream consensus logic doesn't need to
  know about detection-mode plumbing.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from scanner.capture.dom_intel import DomIntel
from scanner.vision.dom_detect import (
    DETECTION_DOM,
    DETECTION_HYBRID,
    DETECTION_VISUAL,
    detect_feature,
)
from scanner.vision.factory import get_client
from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse

OPUS_MODEL = "claude-opus-4-7"
SONNET_MODEL = "claude-sonnet-4-6"

# Hybrid threshold: when a hybrid-mode feature's DOM rule returns True
# with confidence >= this value, the vision call is skipped. False results
# always escalate to vision (DOM cannot prove absence).
HYBRID_DOM_THRESHOLD = 0.85

logger = logging.getLogger(__name__)


def _load_dom_intel(dom_intel_path: Path | None) -> DomIntel | None:
    """Load and validate a DOM intel JSON file. Returns None on miss/error."""
    if dom_intel_path is None:
        return None
    try:
        raw = json.loads(Path(dom_intel_path).read_text(encoding="utf-8"))
        return DomIntel.model_validate(raw)
    except FileNotFoundError:
        logger.warning("dom_intel_path %s not found; vision-only routing", dom_intel_path)
        return None
    except Exception as exc:
        logger.warning(
            "dom_intel_path %s failed to parse (%s); vision-only routing",
            dom_intel_path, exc,
        )
        return None


def _route_features(
    rubric: list[FeatureDef],
    intel: DomIntel | None,
) -> tuple[dict[str, FeatureVerdict], list[FeatureDef], dict[str, str]]:
    """Split the rubric into DOM-resolved verdicts vs vision-bound features.

    Returns
    -------
    (dom_verdicts, vision_rubric, methods)
        - ``dom_verdicts`` maps feature_key -> FeatureVerdict for any
          feature resolved entirely by DOM (mode ``dom`` or hybrid-with-
          high-confidence-positive).
        - ``vision_rubric`` is the filtered list to send to Opus + Sonnet.
        - ``methods`` maps feature_key -> one of:
              "dom"                — DOM-only mode, rule answered.
              "hybrid-dom"         — hybrid mode, DOM rule confirmed presence.
              "hybrid-vision-fallback" — hybrid mode escalated to vision.
              "vision"             — visual mode (or DOM intel missing).
    """
    dom_verdicts: dict[str, FeatureVerdict] = {}
    vision_rubric: list[FeatureDef] = []
    methods: dict[str, str] = {}

    for feature in rubric:
        mode = getattr(feature, "detection", DETECTION_VISUAL)

        if intel is None:
            # No DOM intel — everything goes to vision (D-21 back-compat).
            vision_rubric.append(feature)
            methods[feature.key] = "vision"
            continue

        if mode == DETECTION_DOM:
            v = detect_feature(intel, feature)
            if v is not None:
                dom_verdicts[feature.key] = v
                methods[feature.key] = "dom"
            else:
                # No registered rule for a DOM-tagged feature. Defensive
                # fallback to vision so coverage doesn't silently drop.
                vision_rubric.append(feature)
                methods[feature.key] = "vision"
            continue

        if mode == DETECTION_HYBRID:
            v = detect_feature(intel, feature)
            if v is not None and v.present and v.confidence >= HYBRID_DOM_THRESHOLD:
                dom_verdicts[feature.key] = v
                methods[feature.key] = "hybrid-dom"
            else:
                vision_rubric.append(feature)
                methods[feature.key] = "hybrid-vision-fallback"
            continue

        # mode == DETECTION_VISUAL (or any unknown future tag) → vision.
        vision_rubric.append(feature)
        methods[feature.key] = "vision"

    return dom_verdicts, vision_rubric, methods


def two_judge(
    image_path: Path,
    rubric: list[FeatureDef],
    *,
    api_mode: str = "subscription",
    dom_intel_path: Path | None = None,
) -> dict[str, JudgeResponse]:
    """Run Opus + Sonnet on the same image, with optional DOM short-circuit.

    Args:
        image_path: Full-page screenshot PNG to audit.
        rubric: Frozen list of :class:`FeatureDef` — same list handed to
            both judges so the two checklists are identical (D-18). The
            ``detection`` tag on each FeatureDef drives Wave E routing.
        api_mode: ``"subscription"`` (default, D-28) or ``"api-key"``. Both
            judges use the SAME mode — mixing is disallowed in Phase 1.
        dom_intel_path: Optional path to a DOM intel JSON
            (``{output_dir}/dom/{club}_{step}_intel.json``). When provided,
            DOM-tagged features are answered without a vision call and
            hybrid features take the DOM answer iff it's positive at
            confidence ≥ :data:`HYBRID_DOM_THRESHOLD`. When omitted, every
            feature is routed to vision (pre-15 behavior).

    Returns:
        A dict with two keys: ``"opus"`` and ``"sonnet"``. Each value is a
        :class:`JudgeResponse` whose ``model`` attribute matches the
        corresponding module-level constant. ``results`` merges the DOM-
        derived verdicts (identical for both judges) with the vision
        verdicts (which may differ between judges and feed disagreement
        detection downstream).
    """
    intel = _load_dom_intel(dom_intel_path)

    # Pre-15 fast-path: no DOM intel → forward the rubric list verbatim
    # so the D-18 "both judges see the same list" contract still holds by
    # identity (existing test_two_judge_forwards_rubric_verbatim semantics).
    if intel is None:
        dom_verdicts: dict[str, FeatureVerdict] = {}
        vision_rubric = rubric
        methods = {f.key: "vision" for f in rubric}
    else:
        dom_verdicts, vision_rubric, methods = _route_features(rubric, intel)

    # When there's vision-bound work (or no DOM intel at all), run the
    # vision wave. The pre-15 contract calls get_client + analyze_screenshot
    # unconditionally, so the ``intel is None`` fast-path keeps that
    # semantics — even on an empty rubric — to preserve back-compat with
    # existing test_two_judge_defaults_to_subscription assertions.
    if vision_rubric or intel is None:
        opus = get_client(api_mode, OPUS_MODEL)
        sonnet = get_client(api_mode, SONNET_MODEL)
        opus_results = opus.analyze_screenshot(image_path, vision_rubric)
        sonnet_results = sonnet.analyze_screenshot(image_path, vision_rubric)
    else:
        opus_results = {}
        sonnet_results = {}

    # Merge DOM verdicts into both judges' result maps so downstream
    # consensus / disagreement code sees a single uniform shape.
    opus_merged: dict[str, FeatureVerdict] = {**dom_verdicts, **opus_results}
    sonnet_merged: dict[str, FeatureVerdict] = {**dom_verdicts, **sonnet_results}

    saved = sum(1 for m in methods.values() if m in ("dom", "hybrid-dom"))
    total = len(methods)
    if total:
        logger.info(
            "two_judge routing: %d/%d features answered by DOM (%.0f%% vision saved)",
            saved, total, 100.0 * saved / total,
        )

    return {
        "opus": JudgeResponse(model=OPUS_MODEL, results=opus_merged),
        "sonnet": JudgeResponse(model=SONNET_MODEL, results=sonnet_merged),
    }


__all__ = [
    "HYBRID_DOM_THRESHOLD",
    "OPUS_MODEL",
    "SONNET_MODEL",
    "two_judge",
]
