"""Tests for scanner.vision.client_apikey (APIKeyVisionClient).

All tests mock ``anthropic.Anthropic`` — no live SDK calls. Covers:
    - Constructor builds an anthropic.Anthropic with the Structured Outputs
      beta header.
    - analyze_screenshot sends a user message with an image block + text block
      and the ``output_config`` structured-outputs parameter.
    - Response JSON is parsed into {feature_key: FeatureVerdict} and values
      with out-of-range ``confidence`` are clamped (T-04-02).
    - ask_yes_no sends a short text+image prompt and returns lowercased text.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from scanner.vision.client_apikey import APIKeyVisionClient, _clamp_confidence
from scanner.vision.schema import FeatureDef, FeatureVerdict


@pytest.fixture
def image_path(tmp_path: Path) -> Path:
    """Write a tiny PNG to disk and return its path."""
    img = Image.new("RGB", (32, 32), color="red")
    p = tmp_path / "shot.png"
    img.save(p, format="PNG")
    return p


@pytest.fixture
def rubric() -> list[FeatureDef]:
    return [
        FeatureDef(
            key="has_nav",
            name="Has navigation",
            yes_criterion="primary nav visible above fold",
        )
    ]


def _mock_structured_response(payload: dict) -> MagicMock:
    """Build a mock messages.create response whose content[0].text is ``payload``."""
    resp = MagicMock()
    block = MagicMock()
    block.text = json.dumps(payload)
    resp.content = [block]
    return resp


def test_constructor_sets_structured_outputs_beta_header() -> None:
    """The anthropic client must be built with the 2025-11-13 beta header."""
    with patch("scanner.vision.client_apikey.anthropic.Anthropic") as mock_anth:
        APIKeyVisionClient(api_key="sk-ant-test", model="claude-opus-4-7")
        mock_anth.assert_called_once()
        kwargs = mock_anth.call_args.kwargs
        assert kwargs["api_key"] == "sk-ant-test"
        assert kwargs["default_headers"] == {
            "anthropic-beta": "structured-outputs-2025-11-13"
        }


def test_analyze_screenshot_sends_image_and_text(
    image_path: Path, rubric: list[FeatureDef]
) -> None:
    """Request body must contain an image block + a text block."""
    with patch("scanner.vision.client_apikey.anthropic.Anthropic") as mock_anth:
        mock_client = MagicMock()
        mock_anth.return_value = mock_client
        mock_client.messages.create.return_value = _mock_structured_response(
            {
                "has_nav": {
                    "present": True,
                    "step": "landing",
                    "evidence_bbox": [0.0, 0.0, 10.0, 10.0],
                    "confidence": 0.9,
                    "notes": "nav bar detected",
                }
            }
        )
        client = APIKeyVisionClient(api_key="sk-ant-test", model="claude-opus-4-7")
        result = client.analyze_screenshot(image_path, rubric)

        assert "has_nav" in result
        assert isinstance(result["has_nav"], FeatureVerdict)
        assert result["has_nav"].present is True

        # Inspect the request:
        call = mock_client.messages.create.call_args.kwargs
        assert call["model"] == "claude-opus-4-7"
        assert call["max_tokens"] == 4096
        assert call["output_config"]["format"]["type"] == "json_schema"
        user_content = call["messages"][0]["content"]
        kinds = [c["type"] for c in user_content]
        assert "image" in kinds and "text" in kinds


def test_analyze_screenshot_clamps_out_of_range_confidence(
    image_path: Path, rubric: list[FeatureDef]
) -> None:
    """A confidence of 1.0001 must not reach Pydantic's strict bounds check."""
    with patch("scanner.vision.client_apikey.anthropic.Anthropic") as mock_anth:
        mock_client = MagicMock()
        mock_anth.return_value = mock_client
        mock_client.messages.create.return_value = _mock_structured_response(
            {
                "has_nav": {
                    "present": True,
                    "step": "landing",
                    "evidence_bbox": None,
                    "confidence": 1.0001,  # over the top
                    "notes": "clamped",
                }
            }
        )
        client = APIKeyVisionClient(api_key="sk-ant-test", model="claude-opus-4-7")
        result = client.analyze_screenshot(image_path, rubric)
        assert result["has_nav"].confidence == 1.0


def test_ask_yes_no_returns_lowercased_text(image_path: Path) -> None:
    """Yes/no responses must be trimmed and lowercased."""
    with patch("scanner.vision.client_apikey.anthropic.Anthropic") as mock_anth:
        mock_client = MagicMock()
        mock_anth.return_value = mock_client
        block = MagicMock()
        block.text = "  YES  "
        mock_client.messages.create.return_value = MagicMock(content=[block])

        client = APIKeyVisionClient(
            api_key="sk-ant-test", model="claude-haiku-4-5"
        )
        out = client.ask_yes_no(image_path, "is banner visible?")
        assert out == "yes"

        # max_tokens should be low for yes/no.
        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["max_tokens"] == 10


def test_clamp_confidence_helper_bounds() -> None:
    """Directly exercise the clamp helper (T-04-02)."""
    assert _clamp_confidence({"confidence": 2.0})["confidence"] == 1.0
    assert _clamp_confidence({"confidence": -0.5})["confidence"] == 0.0
    assert _clamp_confidence({"confidence": 0.5})["confidence"] == 0.5
    # Missing key is a no-op.
    v = {"no_conf": True}
    out = _clamp_confidence(v)
    assert out == v
