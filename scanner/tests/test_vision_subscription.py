"""Tests for scanner.vision.client_subscription (SubscriptionVisionClient).

All tests mock ``claude_agent_sdk.query`` as an async iterator yielding
``AssistantMessage``-shaped objects. No live SDK calls. Covers:

    - Constructor records the model without opening any resources.
    - analyze_screenshot drives ``query`` and returns a
      ``{feature_key: FeatureVerdict}`` dict.
    - Confidence clamping is shared with the api-key path (T-04-02).
    - ask_yes_no returns lowercased text.
    - Module does NOT import the anthropic SDK (negative dep-graph check).
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from scanner.vision.client_subscription import SubscriptionVisionClient
from scanner.vision.schema import FeatureDef, FeatureVerdict


@pytest.fixture
def image_path(tmp_path: Path) -> Path:
    img = Image.new("RGB", (32, 32), color="blue")
    p = tmp_path / "shot.png"
    img.save(p, format="PNG")
    return p


@pytest.fixture
def rubric() -> list[FeatureDef]:
    return [
        FeatureDef(
            key="has_nav",
            name="Has navigation",
            yes_criterion="primary nav above fold",
        )
    ]


def _fake_text_block(text: str) -> SimpleNamespace:
    """Mimic ``claude_agent_sdk.TextBlock`` — a ``.text`` attribute is enough."""
    return SimpleNamespace(type="text", text=text)


def _fake_assistant_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[_fake_text_block(text)])


def _async_iter(messages):
    async def _gen():
        for m in messages:
            yield m

    return _gen()


def test_constructor_records_model() -> None:
    client = SubscriptionVisionClient(model="claude-opus-4-7")
    assert client.model == "claude-opus-4-7"


def test_analyze_screenshot_parses_json_from_query(
    image_path: Path, rubric: list[FeatureDef]
) -> None:
    """query() yields a single AssistantMessage with JSON text — parse it."""
    payload = {
        "has_nav": {
            "present": True,
            "step": "landing",
            "evidence_bbox": [0.0, 0.0, 10.0, 10.0],
            "confidence": 0.8,
            "notes": "seen",
        }
    }

    def fake_query(*, prompt, options=None, transport=None):
        return _async_iter([_fake_assistant_message(json.dumps(payload))])

    with patch("scanner.vision.client_subscription.query", fake_query):
        client = SubscriptionVisionClient(model="claude-opus-4-7")
        result = client.analyze_screenshot(image_path, rubric)

    assert "has_nav" in result
    assert isinstance(result["has_nav"], FeatureVerdict)
    assert result["has_nav"].present is True
    assert result["has_nav"].confidence == 0.8


def test_analyze_screenshot_clamps_confidence(
    image_path: Path, rubric: list[FeatureDef]
) -> None:
    """Out-of-range confidence from the subscription path is also clamped."""
    payload = {
        "has_nav": {
            "present": True,
            "step": "landing",
            "evidence_bbox": None,
            "confidence": 1.25,
            "notes": "clamped",
        }
    }

    def fake_query(*, prompt, options=None, transport=None):
        return _async_iter([_fake_assistant_message(json.dumps(payload))])

    with patch("scanner.vision.client_subscription.query", fake_query):
        client = SubscriptionVisionClient(model="claude-opus-4-7")
        result = client.analyze_screenshot(image_path, rubric)

    assert result["has_nav"].confidence == 1.0


def test_ask_yes_no_returns_lowercased(image_path: Path) -> None:
    def fake_query(*, prompt, options=None, transport=None):
        return _async_iter([_fake_assistant_message("  NO  \n")])

    with patch("scanner.vision.client_subscription.query", fake_query):
        client = SubscriptionVisionClient(model="claude-haiku-4-5")
        out = client.ask_yes_no(image_path, "is banner visible?")
    assert out == "no"


def test_subscription_module_does_not_import_anthropic() -> None:
    """Negative dep-graph check: the subscription module must not pull in anthropic.

    The imports are read from the module source so that transitive imports
    from other test modules don't confuse the check. The path is resolved via
    ``importlib`` so it works regardless of the pytest CWD.
    """
    import ast
    import importlib.util
    from pathlib import Path as _Path

    spec = importlib.util.find_spec("scanner.vision.client_subscription")
    assert spec is not None and spec.origin, "module must be importable"
    src = _Path(spec.origin).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "anthropic" not in alias.name, (
                    f"client_subscription.py imports {alias.name} (forbidden)"
                )
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or "anthropic" not in node.module, (
                f"client_subscription.py imports from {node.module} (forbidden)"
            )
