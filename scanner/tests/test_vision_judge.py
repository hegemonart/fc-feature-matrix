"""Tests for scanner.vision.judge (two-judge orchestrator).

All tests patch ``scanner.vision.judge.get_client`` — the orchestrator's only
external contact point. No live SDK calls. Covers:

    - Orchestrator calls get_client twice, once per model, with the same api_mode
    - Returned dict has keys "opus" and "sonnet" with correct .model attributes
    - Rubric argument is forwarded verbatim to both clients
    - api_mode parameter defaults to "subscription" (D-28)
    - Module exports OPUS_MODEL and SONNET_MODEL constants
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from scanner.vision.judge import OPUS_MODEL, SONNET_MODEL, two_judge
from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse


def _verdict(confidence: float = 0.9) -> FeatureVerdict:
    return FeatureVerdict(
        present=True,
        step="landing",
        evidence_bbox=(0.0, 0.0, 10.0, 10.0),
        confidence=confidence,
        notes="mock",
    )


def test_two_judge_calls_get_client_twice_with_both_models(tmp_path: Path) -> None:
    """Orchestrator must dispatch to both models exactly once."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric = [
        FeatureDef(key="x", name="X", yes_criterion="yes if x"),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {"x": _verdict(0.9)}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {"x": _verdict(0.7)}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        out = two_judge(img, rubric, api_mode="subscription")

    assert mock_get.call_count == 2
    # Both calls must use the same api_mode; models differ.
    modes = [c.args[0] for c in mock_get.call_args_list]
    models = [c.args[1] for c in mock_get.call_args_list]
    assert modes == ["subscription", "subscription"]
    assert OPUS_MODEL in models and SONNET_MODEL in models

    # Returned dict has the right shape.
    assert set(out.keys()) == {"opus", "sonnet"}
    assert isinstance(out["opus"], JudgeResponse)
    assert isinstance(out["sonnet"], JudgeResponse)
    assert out["opus"].model == OPUS_MODEL
    assert out["sonnet"].model == SONNET_MODEL
    assert out["opus"].results["x"].confidence == 0.9
    assert out["sonnet"].results["x"].confidence == 0.7


def test_two_judge_defaults_to_subscription(tmp_path: Path) -> None:
    """Omitting api_mode uses the D-28 default ``"subscription"``."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric: list[FeatureDef] = []

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        two_judge(img, rubric)

    modes = [c.args[0] for c in mock_get.call_args_list]
    assert modes == ["subscription", "subscription"]


def test_two_judge_forwards_rubric_verbatim(tmp_path: Path) -> None:
    """Both clients must see the SAME rubric list (D-18 checklist equality)."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric = [
        FeatureDef(key="a", name="A", yes_criterion="a"),
        FeatureDef(key="b", name="B", yes_criterion="b"),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {"a": _verdict(), "b": _verdict()}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {"a": _verdict(), "b": _verdict()}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ):
        two_judge(img, rubric, api_mode="api-key")

    # Both clients received the same rubric list (by identity).
    opus_rubric = opus_client.analyze_screenshot.call_args.args[1]
    sonnet_rubric = sonnet_client.analyze_screenshot.call_args.args[1]
    assert opus_rubric is rubric
    assert sonnet_rubric is rubric


def test_two_judge_exports_expected_model_constants() -> None:
    """D-29 pins the model identifiers as module-level constants."""
    assert OPUS_MODEL == "claude-opus-4-7"
    assert SONNET_MODEL == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Plan 02-15 Wave E — hybrid DOM+vision routing
# ---------------------------------------------------------------------------


def _write_dom_intel_json(
    tmp_path: Path,
    *,
    headings_text: list[str] | None = None,
    button_text: list[str] | None = None,
    forms_inputs: int = 0,
) -> Path:
    """Write a DomIntel JSON file under tmp_path and return the path."""
    import json as _json

    headings = [{"tag": "H2", "text": t, "bbox": None} for t in (headings_text or [])]
    buttons = [{"text": t, "tag": "BUTTON", "href": None, "bbox": None} for t in (button_text or [])]
    forms = (
        [{"action": "/x", "method": "post", "inputs": [
            {"type": "text", "name": f"f{i}", "placeholder": "", "required": False}
            for i in range(forms_inputs)
        ]}]
        if forms_inputs
        else []
    )
    payload = {
        "title": "T",
        "url": "https://example.test/",
        "headings": headings,
        "buttons": buttons,
        "forms": forms,
        "images": [],
        "schema_jsonld": [],
        "meta": {},
        "counts": {
            "forms": 1 if forms else 0,
            "inputs": forms_inputs,
            "buttons": len(buttons),
            "tables": 0,
            "images": 0,
        },
    }
    p = tmp_path / "dom_intel.json"
    p.write_text(_json.dumps(payload), encoding="utf-8")
    return p


def test_two_judge_dom_only_feature_skips_vision(tmp_path: Path) -> None:
    """A ``detection='dom'`` feature is answered without the vision wave."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    intel_path = _write_dom_intel_json(tmp_path, headings_text=["£499 per person"])

    rubric = [
        FeatureDef(
            key="price_per_person_visible",
            name="Price Per Person Visible",
            yes_criterion="A per-person price is shown",
            detection="dom",
        ),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        out = two_judge(img, rubric, dom_intel_path=intel_path)

    # Vision wave is skipped entirely (no client constructed).
    assert mock_get.call_count == 0
    # DOM verdict surfaces in BOTH judges' results.
    assert "price_per_person_visible" in out["opus"].results
    assert "price_per_person_visible" in out["sonnet"].results
    assert out["opus"].results["price_per_person_visible"].present is True
    assert out["sonnet"].results["price_per_person_visible"].present is True


def test_two_judge_visual_feature_routes_to_vision(tmp_path: Path) -> None:
    """A ``detection='visual'`` feature still goes through Opus + Sonnet."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    intel_path = _write_dom_intel_json(tmp_path)

    rubric = [
        FeatureDef(
            key="hero_image_quality",
            name="Hero Image Quality",
            yes_criterion="Premium hero image",
            detection="visual",
        ),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {"hero_image_quality": _verdict()}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {"hero_image_quality": _verdict()}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        two_judge(img, rubric, dom_intel_path=intel_path)

    assert mock_get.call_count == 2
    # The vision call received exactly the visual feature.
    sub_rubric = opus_client.analyze_screenshot.call_args.args[1]
    assert [f.key for f in sub_rubric] == ["hero_image_quality"]


def test_two_judge_hybrid_dom_positive_short_circuits(tmp_path: Path) -> None:
    """Hybrid feature with positive DOM signal at high confidence skips vision."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    intel_path = _write_dom_intel_json(tmp_path, headings_text=["Five-course tasting menu"])

    rubric = [
        FeatureDef(
            key="menu_preview",
            name="Menu Preview",
            yes_criterion="Representative menu shown",
            detection="hybrid",
        ),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        out = two_judge(img, rubric, dom_intel_path=intel_path)

    # DOM rule fired with high confidence → vision wave skipped.
    assert mock_get.call_count == 0
    assert out["opus"].results["menu_preview"].present is True
    assert out["sonnet"].results["menu_preview"].present is True


def test_two_judge_hybrid_dom_negative_falls_back_to_vision(tmp_path: Path) -> None:
    """Hybrid feature with no DOM signal escalates to the vision wave."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    intel_path = _write_dom_intel_json(tmp_path, headings_text=["Welcome"])

    rubric = [
        FeatureDef(
            key="menu_preview",
            name="Menu Preview",
            yes_criterion="Representative menu shown",
            detection="hybrid",
        ),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {"menu_preview": _verdict()}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {"menu_preview": _verdict()}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        two_judge(img, rubric, dom_intel_path=intel_path)

    # Vision was called; sub-rubric contains the hybrid feature.
    assert mock_get.call_count == 2
    sub = opus_client.analyze_screenshot.call_args.args[1]
    assert [f.key for f in sub] == ["menu_preview"]


def test_two_judge_no_dom_intel_path_runs_full_vision_wave(tmp_path: Path) -> None:
    """Omitting dom_intel_path falls back to pre-15 behavior — every feature
    regardless of detection mode goes through Opus + Sonnet."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    rubric = [
        FeatureDef(key="price_per_person_visible", name="x", yes_criterion="x", detection="dom"),
        FeatureDef(key="menu_preview", name="x", yes_criterion="x", detection="hybrid"),
        FeatureDef(key="hero", name="x", yes_criterion="x", detection="visual"),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {f.key: _verdict() for f in rubric}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {f.key: _verdict() for f in rubric}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        two_judge(img, rubric)

    assert mock_get.call_count == 2
    # Sub-rubric is the full rubric (no filtering), preserved by identity.
    assert opus_client.analyze_screenshot.call_args.args[1] is rubric


def test_two_judge_missing_dom_intel_file_falls_back_to_vision(tmp_path: Path) -> None:
    """Missing intel file logs a warning and routes everything to vision."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    bogus = tmp_path / "no-such.json"

    rubric = [
        FeatureDef(key="hero", name="H", yes_criterion="H", detection="visual"),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {"hero": _verdict()}
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {"hero": _verdict()}

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ) as mock_get:
        two_judge(img, rubric, dom_intel_path=bogus)

    assert mock_get.call_count == 2  # vision wave still ran


def test_two_judge_dom_threshold_export() -> None:
    """The hybrid threshold is exposed as a module constant."""
    from scanner.vision.judge import HYBRID_DOM_THRESHOLD
    assert 0.5 < HYBRID_DOM_THRESHOLD < 1.0


def test_two_judge_mixed_rubric_partial_save(tmp_path: Path) -> None:
    """Mixed rubric: dom + visual + hybrid → only the visual + hybrid-fallback
    items reach vision; the dom item is answered by the rule."""
    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    # Provide intel that triggers the dom rule but not the hybrid rule.
    intel_path = _write_dom_intel_json(tmp_path, headings_text=["£499 per person"])

    rubric = [
        FeatureDef(key="price_per_person_visible", name="P", yes_criterion="x", detection="dom"),
        FeatureDef(key="menu_preview", name="M", yes_criterion="x", detection="hybrid"),
        FeatureDef(key="hero", name="H", yes_criterion="x", detection="visual"),
    ]

    opus_client = MagicMock(model=OPUS_MODEL)
    opus_client.analyze_screenshot.return_value = {
        "menu_preview": _verdict(), "hero": _verdict()
    }
    sonnet_client = MagicMock(model=SONNET_MODEL)
    sonnet_client.analyze_screenshot.return_value = {
        "menu_preview": _verdict(), "hero": _verdict()
    }

    with patch(
        "scanner.vision.judge.get_client",
        side_effect=[opus_client, sonnet_client],
    ):
        out = two_judge(img, rubric, dom_intel_path=intel_path)

    # Vision called only for menu_preview + hero.
    sub = opus_client.analyze_screenshot.call_args.args[1]
    assert {f.key for f in sub} == {"menu_preview", "hero"}
    # All three keys present in merged result.
    assert {"price_per_person_visible", "menu_preview", "hero"} <= set(out["opus"].results.keys())
