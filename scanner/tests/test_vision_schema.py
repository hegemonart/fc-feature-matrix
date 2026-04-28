"""Tests for scanner.vision.schema — owner Plan 02.

Encodes the two-judge vision output contract. Per D-27..D-29, BOTH the
subscription (claude-agent-sdk) and api-key (anthropic SDK) backends produce
this identical schema; the dispatcher in Plan 04 can treat judges
interchangeably.

See `.planning/phases/01-flow-automation-layer/01-CONTEXT.md` D-19, D-27.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from scanner.vision.schema import (
    FeatureDef,
    FeatureResult,
    FeatureVerdict,
    JudgeResponse,
)


def _valid_verdict(**overrides) -> dict:
    base = {
        "present": True,
        "step": "landing",
        "evidence_bbox": [10.0, 20.0, 100.0, 50.0],
        "confidence": 0.9,
        "notes": "logo visible top-left",
    }
    base.update(overrides)
    return base


# --- FeatureVerdict ------------------------------------------------------


def test_verdict_valid_with_bbox_parses():
    v = FeatureVerdict.model_validate(_valid_verdict())
    assert v.present is True
    assert v.evidence_bbox == (10.0, 20.0, 100.0, 50.0)
    assert v.confidence == 0.9


def test_verdict_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        FeatureVerdict.model_validate(_valid_verdict(confidence=1.5))


def test_verdict_rejects_confidence_below_zero():
    with pytest.raises(ValidationError):
        FeatureVerdict.model_validate(_valid_verdict(confidence=-0.01))


def test_verdict_absent_with_null_bbox_parses():
    v = FeatureVerdict.model_validate(
        _valid_verdict(present=False, evidence_bbox=None, notes="not found")
    )
    assert v.present is False
    assert v.evidence_bbox is None


def test_verdict_rejects_notes_over_500_chars():
    too_long = "x" * 501
    with pytest.raises(ValidationError):
        FeatureVerdict.model_validate(_valid_verdict(notes=too_long))


def test_verdict_bbox_list_coerced_to_tuple():
    v = FeatureVerdict.model_validate(_valid_verdict(evidence_bbox=[1, 2, 3, 4]))
    assert v.evidence_bbox == (1.0, 2.0, 3.0, 4.0)
    assert isinstance(v.evidence_bbox, tuple)


# --- JudgeResponse -------------------------------------------------------


def test_judge_response_parses():
    resp = JudgeResponse.model_validate(
        {
            "model": "claude-opus-4-7",
            "results": {
                "hospitality_cta_cta_visible": _valid_verdict(),
                "package_pricing_shown": _valid_verdict(present=False, evidence_bbox=None, notes="n/a"),
            },
        }
    )
    assert resp.model == "claude-opus-4-7"
    assert "hospitality_cta_cta_visible" in resp.results
    assert resp.results["package_pricing_shown"].present is False


def test_judge_response_empty_results_allowed():
    resp = JudgeResponse.model_validate({"model": "claude-sonnet-4-6", "results": {}})
    assert resp.results == {}


# --- FeatureDef (no regex constraint per D-18) ---------------------------


def test_feature_def_snake_case_parses():
    fd = FeatureDef.model_validate(
        {"key": "hero_image_present", "name": "Hero image", "yes_criterion": "hero img tag"}
    )
    assert fd.key == "hero_image_present"


def test_feature_def_non_snake_case_still_parses():
    # D-18: regex constraints intentionally NOT applied at schema level;
    # runtime checks handle key-casing warnings elsewhere.
    fd = FeatureDef.model_validate(
        {"key": "HeroImage", "name": "Hero", "yes_criterion": "hero img tag"}
    )
    assert fd.key == "HeroImage"


# --- FeatureResult -------------------------------------------------------


def test_feature_result_round_trip():
    data = {
        "feature_key": "hospitality_cta_visible",
        "verdict": _valid_verdict(),
    }
    fr = FeatureResult.model_validate(data)
    dumped = fr.model_dump()
    fr2 = FeatureResult.model_validate(dumped)
    assert fr2.model_dump() == fr.model_dump()
    assert fr.feature_key == "hospitality_cta_visible"


# --- Round-trip end-to-end ---------------------------------------------


def test_judge_response_round_trip():
    data = {
        "model": "claude-opus-4-7",
        "results": {"x_y_z": _valid_verdict()},
    }
    resp = JudgeResponse.model_validate(data)
    dumped = resp.model_dump()
    resp2 = JudgeResponse.model_validate(dumped)
    assert resp2.model_dump() == resp.model_dump()


# --- Plan 02-15 Wave D — detection mode tag --------------------------


def test_feature_def_detection_defaults_to_visual():
    """Pre-15 rubric JSONs without ``detection`` keep working as visual-only."""
    from scanner.vision.schema import FeatureDef
    fd = FeatureDef(key="x", name="X", yes_criterion="x")
    assert fd.detection == "visual"


def test_feature_def_detection_accepts_dom_and_hybrid():
    from scanner.vision.schema import FeatureDef
    fd_dom = FeatureDef(key="x", name="X", yes_criterion="x", detection="dom")
    fd_hyb = FeatureDef(key="y", name="Y", yes_criterion="y", detection="hybrid")
    assert fd_dom.detection == "dom"
    assert fd_hyb.detection == "hybrid"


def test_feature_def_detection_rejects_unknown_mode():
    """Literal union must reject anything outside {dom, visual, hybrid}."""
    from pydantic import ValidationError
    from scanner.vision.schema import FeatureDef
    import pytest as _pytest
    with _pytest.raises(ValidationError):
        FeatureDef(key="x", name="X", yes_criterion="x", detection="ml")
