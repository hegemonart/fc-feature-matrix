"""Tests for scanner.capture.browser (Plan 03, Task 1 + Task 2).

Covers:
 - create_browser: persistent context, viewport 1440×900, DPR=2, per-(area,club) user-data dir.
 - scroll_lazy: evaluates window.scrollTo (bounded scroll loop).
 - capture_page: end-to-end mock flow (Task 2) — calls create_browser + dismiss_cookies + screenshot.
 - D-16 runtime invariant (grep-test): no submit clicks in scanner/capture/.
"""
from __future__ import annotations

import pathlib
import re
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Task 1: create_browser + scroll_lazy
# ---------------------------------------------------------------------------


def _patch_sync_playwright(monkeypatch: pytest.MonkeyPatch):
    """Replace playwright.sync_api.sync_playwright with a mock chain.

    Returns (patched_sync_playwright, fake_context) so tests can assert on calls.
    """
    fake_context = MagicMock(name="BrowserContext")
    fake_chromium = MagicMock(name="chromium")
    fake_chromium.launch_persistent_context = MagicMock(return_value=fake_context)
    fake_pw = MagicMock(name="Playwright")
    fake_pw.chromium = fake_chromium

    fake_factory = MagicMock(name="sync_playwright_factory")
    fake_factory.start = MagicMock(return_value=fake_pw)

    fake_sync_playwright = MagicMock(return_value=fake_factory)

    # Patch where scanner.capture.browser imports it
    import scanner.capture.browser as browser_mod
    monkeypatch.setattr(browser_mod, "sync_playwright", fake_sync_playwright)

    return fake_sync_playwright, fake_pw, fake_chromium, fake_context


def test_create_browser_returns_playwright_and_context_tuple(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, fake_pw, _, fake_ctx = _patch_sync_playwright(monkeypatch)

    pw, ctx = browser_mod.create_browser(club="mancity", area="hospitality")

    assert pw is fake_pw
    assert ctx is fake_ctx


def test_create_browser_uses_1440x900_viewport_and_dpr2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, _, fake_chromium, _ = _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality")

    fake_chromium.launch_persistent_context.assert_called_once()
    kwargs = fake_chromium.launch_persistent_context.call_args.kwargs
    assert kwargs["viewport"] == {"width": 1440, "height": 900}
    assert kwargs["device_scale_factor"] == 2


def test_create_browser_creates_per_area_per_club_user_data_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    from scanner.capture import browser as browser_mod

    fake_root = tmp_path / ".scanner" / "user-data"
    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", fake_root)
    _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality")

    expected_dir = fake_root / "hospitality" / "mancity"
    assert expected_dir.is_dir(), f"expected {expected_dir} to be created"


def test_create_browser_defaults_to_headless_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """User decision 2: headed by default; CI passes headless=True explicitly."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, _, fake_chromium, _ = _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality")

    kwargs = fake_chromium.launch_persistent_context.call_args.kwargs
    assert kwargs["headless"] is False


def test_create_browser_accepts_headless_true_opt_in(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, _, fake_chromium, _ = _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality", headless=True)

    kwargs = fake_chromium.launch_persistent_context.call_args.kwargs
    assert kwargs["headless"] is True


def test_create_browser_sets_chromium_user_agent_and_no_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, _, fake_chromium, _ = _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality")

    kwargs = fake_chromium.launch_persistent_context.call_args.kwargs
    assert "Chrome/" in kwargs["user_agent"]
    assert "--no-sandbox" in kwargs["args"]


def test_scroll_lazy_evaluates_window_scrollto(mock_playwright_page):
    """scroll_lazy ports recapture_round5.py::scroll_lazy — bounded scroll via page.evaluate."""
    from scanner.capture.browser import scroll_lazy

    # Simulate 4800px page (would trigger 8 scroll steps at 600px each)
    mock_playwright_page.evaluate.return_value = 4800
    scroll_lazy(mock_playwright_page)

    # Should have invoked at least one scrollTo or scrollBy
    called_scripts = [
        call.args[0] for call in mock_playwright_page.evaluate.call_args_list
    ]
    assert any(
        isinstance(s, str) and ("scrollTo" in s or "scrollBy" in s)
        for s in called_scripts
    ), f"scroll_lazy never invoked scrollTo/scrollBy; got: {called_scripts}"


def test_scroll_lazy_is_bounded(mock_playwright_page):
    """scroll_lazy must not loop forever — even on 1Mpx pages, capped at 15 steps."""
    from scanner.capture.browser import scroll_lazy

    mock_playwright_page.evaluate.return_value = 10_000_000  # ridiculous page height
    scroll_lazy(mock_playwright_page)

    # recapture_round5.py caps steps at min(h // 600, 15). With settle + reset
    # we get at most: 1 scrollHeight + 15 scrollBy + 1 reset = 17 evaluate calls.
    assert mock_playwright_page.evaluate.call_count <= 20


# ---------------------------------------------------------------------------
# Task 2: capture_page (uses create_browser mock + dismiss_cookies mock)
# ---------------------------------------------------------------------------


def test_capture_page_writes_fullpage_png_to_expected_path(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    from scanner.capture import capture as capture_mod

    fake_page = MagicMock(name="Page")
    fake_page.screenshot = MagicMock(return_value=b"\x89PNG\r\n\x1a\nFAKEPNG")
    fake_page.goto = MagicMock()
    fake_page.wait_for_load_state = MagicMock()
    fake_page.evaluate = MagicMock(return_value=1200)
    fake_page.add_style_tag = MagicMock()

    fake_ctx = MagicMock(name="BrowserContext")
    fake_ctx.new_page = MagicMock(return_value=fake_page)
    fake_ctx.close = MagicMock()

    fake_pw = MagicMock(name="Playwright")
    fake_pw.stop = MagicMock()

    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(fake_pw, fake_ctx))
    )
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock(return_value=True))
    monkeypatch.setattr(capture_mod, "scroll_lazy", MagicMock())
    monkeypatch.setattr(capture_mod.time, "sleep", MagicMock())

    out = capture_mod.capture_page(
        url="https://www.mancity.com/hospitality",
        club="mancity",
        area="hospitality",
        step_name="landing",
        output_dir=tmp_output_dir,
    )

    expected = tmp_output_dir / "fullpage" / "mancity_landing.png"
    assert out == expected
    assert out.is_file()
    assert out.read_bytes().startswith(b"\x89PNG")


def test_capture_page_closes_context_and_stops_playwright_on_error(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    from scanner.capture import capture as capture_mod

    fake_page = MagicMock()
    fake_page.goto = MagicMock(side_effect=RuntimeError("nav blew up"))
    fake_page.evaluate = MagicMock(return_value=100)

    fake_ctx = MagicMock()
    fake_ctx.new_page = MagicMock(return_value=fake_page)
    fake_ctx.close = MagicMock()

    fake_pw = MagicMock()
    fake_pw.stop = MagicMock()

    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(fake_pw, fake_ctx))
    )
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock())
    monkeypatch.setattr(capture_mod, "scroll_lazy", MagicMock())
    monkeypatch.setattr(capture_mod.time, "sleep", MagicMock())

    with pytest.raises(RuntimeError, match="nav blew up"):
        capture_mod.capture_page(
            url="https://example.test/",
            club="mancity",
            area="hospitality",
            step_name="landing",
            output_dir=tmp_output_dir,
        )

    fake_ctx.close.assert_called_once()
    fake_pw.stop.assert_called_once()


def test_capture_page_applies_hide_selectors_as_css(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    from scanner.capture import capture as capture_mod

    fake_page = MagicMock(name="Page")
    fake_page.screenshot = MagicMock(return_value=b"\x89PNG\r\n\x1a\n")
    fake_page.evaluate = MagicMock(return_value=1000)

    fake_ctx = MagicMock()
    fake_ctx.new_page = MagicMock(return_value=fake_page)

    fake_pw = MagicMock()

    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(fake_pw, fake_ctx))
    )
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock())
    monkeypatch.setattr(capture_mod, "scroll_lazy", MagicMock())
    monkeypatch.setattr(capture_mod.time, "sleep", MagicMock())

    capture_mod.capture_page(
        url="https://example.test/",
        club="mancity",
        area="hospitality",
        step_name="landing",
        output_dir=tmp_output_dir,
        hide_selectors=["#livechat", ".promo-banner"],
    )

    fake_page.add_style_tag.assert_called_once()
    css_arg = fake_page.add_style_tag.call_args.kwargs["content"]
    assert "#livechat" in css_arg and ".promo-banner" in css_arg
    assert "display:none" in css_arg.replace(" ", "")


# ---------------------------------------------------------------------------
# D-16 runtime invariant — grep-test across scanner/capture/
# ---------------------------------------------------------------------------


def test_no_submit_clicks_in_capture_module():
    """D-16 runtime invariant: scanner/capture/ must NEVER call page.click on a
    submit selector — EXCEPT in ``login.py`` where the click submits the user's
    own login form, gated by an explicit ``FlowStep.requires_credentials: true``
    opt-in (Plan 02-10).

    The intent of D-16 is to prevent the orchestrator from dispatching forms
    on club hospitality pages (enquiry forms, ticketing carts, etc.) without
    user authorization. The login form is the user-authorized exception:
    ``capture_flow`` only invokes ``login_to_club`` when a step is marked
    ``requires_credentials: true`` in a committed, schema-validated FlowMap.
    """
    capture_dir = pathlib.Path(__file__).resolve().parents[1] / "capture"
    # login.py is the explicit, user-opt-in authentication path — see Plan
    # 02-10 D-21 deviation note in scanner/capture/capture.py.
    ALLOWLIST = {"login.py"}
    offenders = []
    pat = re.compile(r"\.click\([^)]*submit", re.IGNORECASE)
    for py in capture_dir.glob("*.py"):
        if py.name in ALLOWLIST:
            continue
        if pat.search(py.read_text(encoding="utf-8")):
            offenders.append(str(py))
    assert not offenders, f"D-16 violation — submit clicks found in: {offenders}"
