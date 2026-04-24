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
