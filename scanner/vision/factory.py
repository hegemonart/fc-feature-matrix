"""Vision-client factory — dispatches on ``api_mode`` (D-26..D-29).

Subscription backend (D-26a, default) is constructed without any env check;
api-key backend (D-26b, fallback) requires ``ANTHROPIC_API_KEY`` and raises
``RuntimeError`` otherwise so the error surfaces BEFORE the first message is
sent (T-04-01 — the key is only read inside this function, never logged).

Imports of the concrete backends are deferred into each branch so that:

1. Test runs for Plan 03's banner-verify module, which does a lazy
   ``from scanner.vision.factory import get_client``, do not pay the
   cost of the anthropic SDK unless the user explicitly asked for it.
2. A missing optional dependency inside one backend does not prevent the
   other from loading.
"""
from __future__ import annotations

import os
from typing import Literal

from scanner.vision.client import VisionClient

ApiMode = Literal["subscription", "api-key"]


def get_client(api_mode: ApiMode, model: str) -> VisionClient:
    """Return the vision client for the requested ``api_mode``.

    Args:
        api_mode: Either ``"subscription"`` (D-26a, default — uses the
            claude-agent-sdk and the user's Max subscription quota) or
            ``"api-key"`` (D-26b, pay-per-token via the anthropic SDK;
            requires ``ANTHROPIC_API_KEY``).
        model: Claude model identifier, e.g. ``"claude-opus-4-7"``,
            ``"claude-sonnet-4-6"``, ``"claude-haiku-4-5"``.

    Returns:
        A :class:`VisionClient` concrete instance.

    Raises:
        RuntimeError: If ``api_mode == "api-key"`` but ``ANTHROPIC_API_KEY``
            is unset in the environment.
        ValueError: If ``api_mode`` is not one of the two supported values.
    """
    if api_mode == "subscription":
        from scanner.vision.client_subscription import SubscriptionVisionClient

        return SubscriptionVisionClient(model=model)
    if api_mode == "api-key":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set — required for --api-mode api-key. "
                "Either export the key or use --api-mode subscription (default)."
            )
        from scanner.vision.client_apikey import APIKeyVisionClient

        return APIKeyVisionClient(api_key=key, model=model)
    raise ValueError(f"Unknown api_mode: {api_mode!r}")


__all__ = ["ApiMode", "get_client"]
