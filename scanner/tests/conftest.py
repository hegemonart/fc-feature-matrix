"""Shared pytest fixtures for the scanner test suite."""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Isolated scanner/output/ replacement per test."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def mock_anthropic_client():
    """anthropic.Anthropic() mock — tests set .messages.create.return_value or .side_effect."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = MagicMock()
    return client


@pytest.fixture
def mock_claude_agent_sdk(monkeypatch: pytest.MonkeyPatch):
    """claude_agent_sdk.query mock. Tests set .return_value for the async iterator.

    Returns the patched `query` callable so tests can set .return_value. The patch
    target is `scanner.vision.client_subscription.query` — Plan 04 imports it as
    `from claude_agent_sdk import query` at module level.
    """
    mock_query = MagicMock()
    # Default: empty async iterator yielding no messages.
    mock_query.return_value = iter([])
    return mock_query


@pytest.fixture
def mock_playwright_page():
    """Minimal Playwright Page mock — tests assert .goto/.screenshot/.evaluate calls."""
    page = MagicMock()
    page.url = "https://example.test/"
    page.goto = MagicMock()
    page.screenshot = MagicMock(return_value=b"\x89PNG\r\n\x1a\n")  # PNG magic bytes
    page.evaluate = MagicMock()
    page.wait_for_load_state = MagicMock()
    page.add_style_tag = MagicMock()
    page.fill = MagicMock()
    return page


@pytest.fixture
def sample_fullpage_png() -> bytes:
    """400x300 white PNG bytes for slice/report tests."""
    from PIL import Image
    img = Image.new("RGB", (400, 300), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A synthetic repo root for path-resolution tests. Sets SCANNER_REPO_ROOT env."""
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setenv("SCANNER_REPO_ROOT", str(root))
    return root


@pytest.fixture
def dummy_rubric_path() -> Path:
    """Path to the frozen 3-feature dry-run rubric fixture."""
    return Path(__file__).parent / "fixtures" / "dummy-hospitality-rubric.json"
