"""Tests for scanner.capture.banner_verify (Plan 03, Task 2).

The post-capture vision check (D-14) asks Claude Haiku a binary yes/no:
"is any cookie-consent banner, newsletter popup, or modal still visible?"
Returns True when the capture is clean (no banner).

Imports from `scanner.vision.factory` are LAZY — the factory is shipped by
Plan 04 in the same wave-pair. Plan 03 must degrade gracefully if the factory
isn't importable (isolated plan test runs); CI has both plans and gets the
real client.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _stub_vision_factory(
    monkeypatch: pytest.MonkeyPatch, response: str
) -> MagicMock:
    """Install a fake scanner.vision.factory module with a get_client() that
    returns a MagicMock with .ask_yes_no() returning `response`.

    Returns the MagicMock client so tests can assert on its call args.
    """
    fake_client = MagicMock(name="VisionClient")
    fake_client.ask_yes_no = MagicMock(return_value=response)

    fake_factory = MagicMock(name="factory_module")
    fake_factory.get_client = MagicMock(return_value=fake_client)

    # Ensure the parent package is present too so `from scanner.vision.factory`
    # resolves through it.
    fake_vision_pkg = MagicMock(name="vision_pkg")
    fake_vision_pkg.factory = fake_factory

    monkeypatch.setitem(sys.modules, "scanner.vision", fake_vision_pkg)
    monkeypatch.setitem(sys.modules, "scanner.vision.factory", fake_factory)

    return fake_client


def test_verify_banner_gone_returns_true_when_vision_says_no(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Haiku answers 'no' (no banner visible) → verify returns True."""
    from scanner.capture.banner_verify import verify_banner_gone

    screenshot = tmp_path / "mancity_landing.png"
    screenshot.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    client = _stub_vision_factory(monkeypatch, response="no")

    assert verify_banner_gone(screenshot) is True
    client.ask_yes_no.assert_called_once()


def test_verify_banner_gone_returns_false_when_vision_says_yes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Haiku answers 'yes' (banner still visible) → verify returns False."""
    from scanner.capture.banner_verify import verify_banner_gone

    screenshot = tmp_path / "mancity_landing.png"
    screenshot.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    _stub_vision_factory(monkeypatch, response="yes")

    assert verify_banner_gone(screenshot) is False


def test_verify_banner_gone_passes_haiku_model_to_factory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """The Haiku pin is load-bearing — banner check must never escalate to Opus/Sonnet."""
    from scanner.capture.banner_verify import verify_banner_gone
    # Access the (fake) factory module through sys.modules so we can inspect
    # the get_client kwargs.
    client = _stub_vision_factory(monkeypatch, response="no")
    import scanner.vision.factory as fake_factory  # noqa: F401 (module is the mock)

    screenshot = tmp_path / "mancity_landing.png"
    screenshot.write_bytes(b"\x89PNG")

    verify_banner_gone(screenshot, api_mode="subscription")

    # Assert get_client was called with model="claude-haiku-4-5" kwarg.
    # (The fake factory captures kwargs.)
    call = fake_factory.get_client.call_args
    # Tolerate either positional or keyword depending on impl.
    all_kwargs = dict(call.kwargs) if call else {}
    model = all_kwargs.get("model")
    assert model == "claude-haiku-4-5", f"expected Haiku pin, got {model!r}"


def test_verify_banner_gone_case_insensitive_response(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Haiku may respond 'No.' or 'NO' — normalise before comparing."""
    from scanner.capture.banner_verify import verify_banner_gone

    screenshot = tmp_path / "shot.png"
    screenshot.write_bytes(b"\x89PNG")

    _stub_vision_factory(monkeypatch, response="  NO.  ")
    assert verify_banner_gone(screenshot) is True


def test_verify_banner_gone_permissive_on_import_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    """Plan 04 not yet shipped (isolated plan run) → returns True with WARNING log."""
    from scanner.capture.banner_verify import verify_banner_gone

    # Force the lazy import to fail.
    monkeypatch.setitem(sys.modules, "scanner.vision.factory", None)

    screenshot = tmp_path / "shot.png"
    screenshot.write_bytes(b"\x89PNG")

    with caplog.at_level("WARNING"):
        result = verify_banner_gone(screenshot)

    assert result is True
    assert any(
        "banner check skipped" in rec.message.lower()
        or "factory" in rec.message.lower()
        for rec in caplog.records
    )
