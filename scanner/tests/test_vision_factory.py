"""Tests for scanner.vision.factory.get_client.

Covers every dispatch branch per the plan's acceptance criteria:

    1. subscription mode does NOT require an API key
    2. api-key mode WITHOUT env var raises RuntimeError
    3. api-key mode WITH env var returns APIKeyVisionClient
    4. bogus mode raises ValueError
    5. Both returned objects satisfy the VisionClient Protocol
"""
from __future__ import annotations

import pytest

from scanner.vision.client import VisionClient
from scanner.vision.factory import get_client


def test_subscription_mode_returns_subscription_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """subscription path works even when ANTHROPIC_API_KEY is missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = get_client("subscription", "claude-opus-4-7")
    from scanner.vision.client_subscription import SubscriptionVisionClient

    assert isinstance(client, SubscriptionVisionClient)
    assert client.model == "claude-opus-4-7"


def test_api_key_mode_without_env_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """api-key path raises RuntimeError if env var is absent (T-04-01)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_client("api-key", "claude-sonnet-4-6")


def test_api_key_mode_with_env_returns_apikey_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """api-key path returns APIKeyVisionClient when env var is set."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-dummy")
    client = get_client("api-key", "claude-sonnet-4-6")
    from scanner.vision.client_apikey import APIKeyVisionClient

    assert isinstance(client, APIKeyVisionClient)
    assert client.model == "claude-sonnet-4-6"


def test_bogus_api_mode_raises_value_error() -> None:
    """Unknown api_mode values must raise ValueError (closed-enum contract)."""
    with pytest.raises(ValueError, match="Unknown api_mode"):
        get_client("bogus-mode", "claude-opus-4-7")  # type: ignore[arg-type]


def test_both_backends_satisfy_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both dispatched backends are ``VisionClient`` instances at runtime."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-dummy")

    sub = get_client("subscription", "claude-opus-4-7")
    api = get_client("api-key", "claude-sonnet-4-6")

    assert isinstance(sub, VisionClient)
    assert isinstance(api, VisionClient)
