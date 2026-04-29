"""Tests for scanner.vision.client (VisionClient Protocol).

Covers:
    - runtime_checkable isinstance() passes for any duck-typed implementation
    - Missing a required method fails the check
    - Both concrete backends satisfy the Protocol at runtime
"""
from __future__ import annotations

from pathlib import Path

from scanner.vision.client import VisionClient
from scanner.vision.schema import FeatureDef, FeatureVerdict


class _ConformingClient:
    """Minimal duck-typed implementation of the VisionClient Protocol."""

    model: str = "claude-opus-4-7"

    def analyze_screenshot(
        self,
        image_path: Path,
        rubric: list[FeatureDef],
    ) -> dict[str, FeatureVerdict]:
        return {}

    def ask_yes_no(self, screenshot_path: Path, prompt: str) -> str:
        return "no"


class _MissingMethodClient:
    """Has ``model`` and ``analyze_screenshot`` but no ``ask_yes_no``."""

    model: str = "claude-opus-4-7"

    def analyze_screenshot(
        self,
        image_path: Path,
        rubric: list[FeatureDef],
    ) -> dict[str, FeatureVerdict]:
        return {}


def test_conforming_duck_type_passes_isinstance() -> None:
    """A class with the right shape is a ``VisionClient`` without inheriting it."""
    assert isinstance(_ConformingClient(), VisionClient)


def test_missing_method_is_rejected() -> None:
    """``runtime_checkable`` detects absent methods."""
    assert not isinstance(_MissingMethodClient(), VisionClient)


def test_concrete_subscription_client_satisfies_protocol() -> None:
    """SubscriptionVisionClient must satisfy the Protocol at runtime."""
    from scanner.vision.client_subscription import SubscriptionVisionClient

    sub = SubscriptionVisionClient(model="claude-opus-4-7")
    assert isinstance(sub, VisionClient)


def test_concrete_apikey_client_satisfies_protocol() -> None:
    """APIKeyVisionClient must satisfy the Protocol at runtime."""
    from scanner.vision.client_apikey import APIKeyVisionClient

    api = APIKeyVisionClient(api_key="sk-ant-test-dummy", model="claude-sonnet-4-6")
    assert isinstance(api, VisionClient)
