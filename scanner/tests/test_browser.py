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


# ---------------------------------------------------------------------------
# Plan 02-15 Wave A — playwright-stealth integration
# ---------------------------------------------------------------------------


def test_stealth_enabled_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """Stealth fingerprint masks must be applied to the context by default."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _, _, _, fake_ctx = _patch_sync_playwright(monkeypatch)

    fake_apply = MagicMock(name="_apply_stealth_sync")
    monkeypatch.setattr(browser_mod, "_apply_stealth_sync", fake_apply)

    browser_mod.create_browser(club="mancity", area="hospitality")

    fake_apply.assert_called_once_with(fake_ctx)


def test_stealth_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """``stealth=False`` skips fingerprint mask application (debug/escape hatch)."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _patch_sync_playwright(monkeypatch)

    fake_apply = MagicMock(name="_apply_stealth_sync")
    monkeypatch.setattr(browser_mod, "_apply_stealth_sync", fake_apply)

    browser_mod.create_browser(club="mancity", area="hospitality", stealth=False)

    fake_apply.assert_not_called()


def test_stealth_helper_swallows_import_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    """If playwright_stealth import fails, _apply_stealth_sync is non-fatal."""
    from scanner.capture import browser as browser_mod

    # Force ImportError by making the dynamic import inside the helper fail.
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "playwright_stealth":
            raise ImportError("simulated missing dep")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    fake_ctx = MagicMock(name="BrowserContext")
    # Must not raise — helper must catch and continue.
    browser_mod._apply_stealth_sync(fake_ctx)


# ---------------------------------------------------------------------------
# Plan 02-19 — Patchright engine dispatch
# ---------------------------------------------------------------------------


def _patch_patchright_sync(monkeypatch: pytest.MonkeyPatch):
    """Replace patchright.sync_api.sync_playwright import with a mock chain.

    Patchright is imported lazily INSIDE create_browser when engine="patchright"
    so we patch via sys.modules to intercept the import.
    """
    import sys
    import types

    fake_context = MagicMock(name="PatchrightBrowserContext")
    fake_chromium = MagicMock(name="patchright_chromium")
    fake_chromium.launch_persistent_context = MagicMock(return_value=fake_context)
    fake_pw = MagicMock(name="PatchrightPlaywright")
    fake_pw.chromium = fake_chromium

    fake_factory = MagicMock(name="patchright_sync_playwright_factory")
    fake_factory.start = MagicMock(return_value=fake_pw)

    fake_sync_playwright = MagicMock(return_value=fake_factory)

    fake_module = types.ModuleType("patchright.sync_api")
    fake_module.sync_playwright = fake_sync_playwright  # type: ignore[attr-defined]

    fake_pkg = types.ModuleType("patchright")
    fake_pkg.sync_api = fake_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "patchright", fake_pkg)
    monkeypatch.setitem(sys.modules, "patchright.sync_api", fake_module)

    return fake_sync_playwright, fake_pw, fake_chromium, fake_context


def test_engine_defaults_to_playwright(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """Default engine is 'playwright' — preserves Plan 02-15 Wave A behavior."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    fake_sync_pw, _, _, _ = _patch_sync_playwright(monkeypatch)

    browser_mod.create_browser(club="mancity", area="hospitality")

    fake_sync_pw.assert_called_once()


def test_engine_patchright_uses_patchright_sync(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """engine='patchright' must call patchright.sync_api.sync_playwright, NOT playwright's."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    fake_pw_sync, _, _, _ = _patch_sync_playwright(monkeypatch)
    fake_patch_sync, _, _, fake_ctx = _patch_patchright_sync(monkeypatch)

    pw, ctx = browser_mod.create_browser(
        club="mancity", area="hospitality", engine="patchright"
    )

    fake_patch_sync.assert_called_once()
    fake_pw_sync.assert_not_called()
    assert ctx is fake_ctx


def test_engine_patchright_skips_playwright_stealth(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """Patchright ships its own stealth — don't double-apply playwright-stealth."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")
    _patch_patchright_sync(monkeypatch)

    fake_apply = MagicMock(name="_apply_stealth_sync")
    monkeypatch.setattr(browser_mod, "_apply_stealth_sync", fake_apply)

    browser_mod.create_browser(
        club="mancity", area="hospitality", engine="patchright"
    )

    fake_apply.assert_not_called()


def test_engine_invalid_value_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
):
    """Unknown engine value fails fast with ValueError."""
    from scanner.capture import browser as browser_mod

    monkeypatch.setattr(browser_mod, "USER_DATA_ROOT", tmp_path / ".scanner" / "user-data")

    with pytest.raises(ValueError, match="Unknown browser engine"):
        browser_mod.create_browser(
            club="mancity", area="hospitality", engine="not-a-real-engine"  # type: ignore[arg-type]
        )


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


def _make_dom_intel_page(
    *,
    screenshot_bytes: bytes = b"\x89PNG\r\n\x1a\nFAKEPNG",
    page_height: int = 1200,
    html_content: str = "<html><body>ok</body></html>",
    intel_payload: dict | None = None,
) -> MagicMock:
    """Build a Page mock that returns DOM intel from page.evaluate.

    The mock disambiguates page.evaluate calls: the bounded scroll_lazy
    helper passes integer-arg expressions ("document.body.scrollHeight"
    or "window.scrollTo(0, NNN)"), the DOM intel call passes the
    EXTRACT_DOM_INTEL_JS string. We dispatch via the first arg.
    """
    intel_payload = intel_payload if intel_payload is not None else {
        "title": "T", "url": "u", "headings": [], "buttons": [],
        "forms": [], "images": [], "schema_jsonld": [], "meta": {},
        "counts": {"forms": 0, "inputs": 0, "buttons": 0, "tables": 0, "images": 0},
    }
    page = MagicMock(name="Page")
    page.screenshot = MagicMock(return_value=screenshot_bytes)
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()
    page.add_style_tag = MagicMock()
    page.content = MagicMock(return_value=html_content)

    def _evaluate(expr, *a, **kw):
        if isinstance(expr, str) and "EXTRACT" in expr.replace(" ", "").upper():
            return intel_payload
        # The dom_intel JS starts with `() =>` — detect that too.
        if isinstance(expr, str) and "document.title" in expr and "headings" in expr:
            return intel_payload
        return page_height

    page.evaluate = MagicMock(side_effect=_evaluate)
    return page


def test_capture_page_writes_fullpage_png_to_expected_path(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    from scanner.capture import capture as capture_mod

    fake_page = _make_dom_intel_page()

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

    fake_page = _make_dom_intel_page(page_height=1000)

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


# ---------------------------------------------------------------------------
# Plan 02-15 Wave B — DOM capture in capture_page
# ---------------------------------------------------------------------------


def test_dom_intel_captured_after_screenshot(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    """capture_page writes both html/ and dom/ artifacts alongside the PNG."""
    import json as _json
    from scanner.capture import capture as capture_mod

    intel_payload = {
        "title": "Hospitality | Mancity",
        "url": "https://www.mancity.com/hospitality",
        "headings": [{"tag": "H1", "text": "Hospitality", "bbox": None}],
        "buttons": [{"text": "Book Now", "tag": "A", "href": "/book", "bbox": None}],
        "forms": [],
        "images": [],
        "schema_jsonld": [],
        "meta": {},
        "counts": {"forms": 0, "inputs": 0, "buttons": 1, "tables": 0, "images": 0},
    }
    fake_page = _make_dom_intel_page(intel_payload=intel_payload, html_content="<html>ok</html>")

    fake_ctx = MagicMock(name="BrowserContext")
    fake_ctx.new_page = MagicMock(return_value=fake_page)
    fake_pw = MagicMock(name="Playwright")
    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(fake_pw, fake_ctx))
    )
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock())
    monkeypatch.setattr(capture_mod, "scroll_lazy", MagicMock())
    monkeypatch.setattr(capture_mod.time, "sleep", MagicMock())

    capture_mod.capture_page(
        url="https://www.mancity.com/hospitality",
        club="mancity",
        area="hospitality",
        step_name="landing",
        output_dir=tmp_output_dir,
    )

    html_file = tmp_output_dir / "html" / "mancity_landing.html"
    dom_file = tmp_output_dir / "dom" / "mancity_landing_intel.json"
    assert html_file.is_file(), "expected raw HTML alongside PNG"
    assert dom_file.is_file(), "expected DOM intel JSON alongside PNG"
    intel = _json.loads(dom_file.read_text(encoding="utf-8"))
    assert intel["title"] == "Hospitality | Mancity"
    assert intel["counts"]["buttons"] == 1


def test_dom_intel_schema_round_trip(tmp_path: pathlib.Path):
    """The intel JS payload validates against DomIntel pydantic schema."""
    from scanner.capture.dom_intel import DomIntel

    payload = {
        "title": "T",
        "url": "https://example.test/",
        "headings": [{"tag": "H1", "text": "Hi", "bbox": {"x": 0, "y": 0, "w": 10, "h": 10}}],
        "buttons": [{"text": "Click", "tag": "BUTTON", "href": None, "bbox": None}],
        "forms": [
            {
                "action": "/submit",
                "method": "post",
                "inputs": [
                    {"type": "email", "name": "email", "placeholder": "you@x", "required": True}
                ],
            }
        ],
        "images": [{"src": "a.png", "alt": "alt", "bbox": None}],
        "schema_jsonld": [{"@type": "Product"}],
        "meta": {"og:title": "x"},
        "counts": {"forms": 1, "inputs": 1, "buttons": 1, "tables": 0, "images": 1},
    }
    intel = DomIntel.model_validate(payload)
    assert intel.title == "T"
    assert intel.forms[0].inputs[0].type == "email"
    assert intel.forms[0].inputs[0].required is True
    assert intel.counts.images == 1


def test_dom_capture_failure_does_not_break_screenshot(
    monkeypatch: pytest.MonkeyPatch, tmp_output_dir: pathlib.Path
):
    """If page.evaluate raises during DOM intel, the PNG still lands cleanly."""
    from scanner.capture import capture as capture_mod

    fake_page = _make_dom_intel_page()

    def _broken_evaluate(expr, *a, **kw):
        if isinstance(expr, str) and "document.title" in expr:
            raise RuntimeError("page closed")
        return 1000

    fake_page.evaluate = MagicMock(side_effect=_broken_evaluate)
    # Make page.content also fail to test both legs.
    fake_page.content = MagicMock(side_effect=RuntimeError("content failed"))

    fake_ctx = MagicMock(name="BrowserContext")
    fake_ctx.new_page = MagicMock(return_value=fake_page)
    fake_pw = MagicMock()
    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(fake_pw, fake_ctx))
    )
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock())
    monkeypatch.setattr(capture_mod, "scroll_lazy", MagicMock())
    monkeypatch.setattr(capture_mod.time, "sleep", MagicMock())

    out = capture_mod.capture_page(
        url="https://example.test/",
        club="mancity",
        area="hospitality",
        step_name="landing",
        output_dir=tmp_output_dir,
    )
    assert out.is_file()
    # html/ and dom/ may not exist OR be empty — but PNG must.
    assert out.read_bytes().startswith(b"\x89PNG")
