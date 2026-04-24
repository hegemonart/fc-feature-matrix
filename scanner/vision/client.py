"""VisionClient Protocol — dual-backend contract (D-26..D-29).

Both :class:`scanner.vision.client_subscription.SubscriptionVisionClient` and
:class:`scanner.vision.client_apikey.APIKeyVisionClient` implement this
Protocol and MUST return identical FeatureVerdict shapes. The factory in
:mod:`scanner.vision.factory` dispatches between them on the user-selected
``api_mode``; every downstream module programs against this interface.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from scanner.vision.schema import FeatureDef, FeatureVerdict


@runtime_checkable
class VisionClient(Protocol):
    """Dual-backend contract (D-26..D-29).

    Attributes:
        model: The underlying Claude model name. One of
            ``"claude-opus-4-7"`` | ``"claude-sonnet-4-6"`` | ``"claude-haiku-4-5"``.
    """

    model: str

    def analyze_screenshot(
        self,
        image_path: Path,
        rubric: list[FeatureDef],
    ) -> dict[str, FeatureVerdict]:
        """Run checklist-first feature detection.

        Returns ``{feature_key: FeatureVerdict}`` keyed by the feature keys
        declared in ``rubric``.
        """
        ...

    def ask_yes_no(self, screenshot_path: Path, prompt: str) -> str:
        """Single-turn raw yes/no query. Used by banner verify (Plan 03)."""
        ...


__all__ = ["VisionClient"]
