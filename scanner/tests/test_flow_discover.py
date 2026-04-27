"""Tests for scanner.flow.discover — Plan 02-05 implementation.

The crawler is a sync-Playwright depth-limited click-path discoverer. These
tests mock the Playwright API surface (no real browser) and assert on:

- Happy path: valid FlowMap written + self-validates.
- Detection hooks: login gate, CAPTCHA, broker redirect, external redirect,
  dead-end, form-fill-pre-submit.
- Regression guards: crawler never emits a `submit` action (D-16);
  cookies dismissed before link enumeration (D-15 per Phase 1).

Mock strategy: `_make_page(responses)` builds a MagicMock Page that honors
scripted URL/HTML responses in order for each `page.goto()` call. Link
enumeration and per-page detection queries (`query_selector`,
`query_selector_all`) are driven by the currently-active response.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner.flow.schema import FlowMap


# ---------------------------------------------------------------------------
# Mock page infrastructure
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Scripted response for a single navigation step."""

    def __init__(
        self,
        url: str,
        *,
        status: int = 200,
        links: list[tuple[str, str]] | None = None,  # [(text, href), ...]
        has_password_input: bool = False,
        captcha: bool = False,
        form_inputs: int = 0,
        h1_text: str | None = None,
    ):
        self.url = url
        self.status = status
        self.links = links or []
        self.has_password_input = has_password_input
        self.captcha = captcha
        self.form_inputs = form_inputs
        self.h1_text = h1_text


def _make_page(responses: list[_FakeResponse]) -> MagicMock:
    """Build a MagicMock Page that serves responses in order.

    Each `page.goto()` / `page.click()` advances the "current" response.
    """
    state = {"idx": 0}

    def _current() -> _FakeResponse:
        return responses[min(state["idx"], len(responses) - 1)]

    page = MagicMock(name="Page")

    # page.url dynamically reflects the current response URL.
    type(page).url = property(lambda _self: _current().url)  # type: ignore[misc]

    def _goto(url, **_kwargs):
        # Advance to the response whose URL matches, else keep the next one.
        for i, r in enumerate(responses):
            if r.url == url:
                state["idx"] = i
                break
        else:
            state["idx"] = min(state["idx"] + 1, len(responses) - 1)
        resp = MagicMock(name="Response")
        resp.status = _current().status
        return resp

    page.goto = MagicMock(side_effect=_goto)
    page.wait_for_load_state = MagicMock()

    def _click(selector, **_kwargs):
        # Click advances to the next response.
        state["idx"] = min(state["idx"] + 1, len(responses) - 1)

    page.click = MagicMock(side_effect=_click)

    def _qs(selector):
        r = _current()
        if selector == 'input[type="password"]':
            return MagicMock(name="password-input") if r.has_password_input else None
        if selector == "h1":
            if r.h1_text is not None:
                h1 = MagicMock(name="h1")
                h1.text_content.return_value = r.h1_text
                return h1
            return None
        if selector.startswith("iframe[src*=") or selector in (".g-recaptcha", "[data-sitekey]"):
            return MagicMock(name="captcha") if r.captcha else None
        return None

    page.query_selector = MagicMock(side_effect=_qs)

    def _qsall(selector):
        r = _current()
        if selector == "a[href]":
            out = []
            for text, href in r.links:
                a = MagicMock(name="a")
                a.get_attribute.return_value = href
                a.text_content.return_value = text
                out.append(a)
            return out
        if selector == "form":
            if r.form_inputs >= 3:
                form = MagicMock(name="form")
                inputs = [MagicMock(name=f"input-{i}") for i in range(r.form_inputs)]
                form.query_selector_all.return_value = inputs
                return [form]
            return []
        return []

    page.query_selector_all = MagicMock(side_effect=_qsall)
    # Cookie dismissal: default-success
    page.evaluate = MagicMock(return_value=True)

    return page


@pytest.fixture
def patched_playwright():
    """Patch `scanner.flow.discover.sync_playwright` so tests do not launch a
    real browser. The caller sets the `page` object via the returned handle.
    """

    class _Handle:
        page: MagicMock | None = None

    handle = _Handle()

    def _make_sync_pw():
        ctx_mgr = MagicMock(name="sync_pw_ctx")
        pw = MagicMock(name="Playwright")
        browser = MagicMock(name="Browser")
        context = MagicMock(name="Context")
        pw.chromium.launch = MagicMock(return_value=browser)
        browser.new_context = MagicMock(return_value=context)
        context.new_page = MagicMock(side_effect=lambda: handle.page)
        browser.close = MagicMock()
        ctx_mgr.__enter__ = MagicMock(return_value=pw)
        ctx_mgr.__exit__ = MagicMock(return_value=None)
        return ctx_mgr

    with patch("scanner.flow.discover.sync_playwright", side_effect=_make_sync_pw):
        yield handle


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_discover_emits_valid_flow_map_against_stub_page(tmp_path: Path, patched_playwright):
    """Happy path: a landing page + one dead-end hospitality link produces a
    schema-valid FlowMap."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("VIP Tier", "/hospitality/vip-tier")],
        ),
        _FakeResponse(
            "https://mancity.com/hospitality/vip-tier",
            status=404,
            h1_text="Page not found",
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    assert isinstance(fm, FlowMap)
    assert fm.area == "hospitality"
    assert fm.club == "mancity"
    assert fm.entry_url == "https://mancity.com/hospitality"
    assert len(fm.steps) >= 3
    assert fm.metadata is not None
    assert out.exists()
    # Dead-end must have been recorded.
    assert any("vip-tier" in u for u in fm.metadata.dead_ends)


def test_discover_detects_login_gate(tmp_path: Path, patched_playwright):
    """Login-gated detection halts the branch and records to metadata."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("Members VIP", "/account/login")],
        ),
        _FakeResponse(
            "https://mancity.com/account/login",
            has_password_input=True,
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    assert len(fm.metadata.login_gated_steps) >= 1
    # No click step emitted AFTER login detection (branch halted).
    click_indices = [i for i, s in enumerate(fm.steps) if s.action == "click"]
    # There should be at most 1 click step (the one that led to the login page),
    # and no screenshots past it that imply continued descent.
    assert len(click_indices) <= 1


def test_discover_detects_broker_redirect(tmp_path: Path, patched_playwright):
    """Broker-redirect (allowlisted) sets broker_vendor and continues."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("Hospitality Packages", "https://seatunique.com/mancity-vip")],
        ),
        _FakeResponse(
            "https://seatunique.com/mancity-vip",
            links=[("VIP Suite", "/suite/gold")],
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    assert fm.metadata.broker_vendor == "seat_unique"
    # At least one screenshot after the cross-origin hop — crawl continued.
    screenshot_steps = [s for s in fm.steps if s.action == "screenshot"]
    assert len(screenshot_steps) >= 2


def test_discover_detects_external_unknown_redirect(tmp_path: Path, patched_playwright):
    """Non-broker cross-origin redirect halts the branch.

    Scenario: a same-origin hospitality link that (when clicked) lands on a
    non-broker third-party domain — the way a real club's `/hospitality/partner`
    link often server-redirects into a tracking domain.
    """
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("VIP Hospitality Partner", "/hospitality/partner")],
        ),
        # Same-origin href but post-click .url reflects a cross-origin
        # (non-broker) redirect.
        _FakeResponse(
            "https://randomtracker.example/",
            links=[("Deeper", "/deeper")],
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    assert any("randomtracker.example" in u for u in fm.metadata.external_redirects)
    assert fm.metadata.broker_vendor is None


def test_discover_detects_dead_end(tmp_path: Path, patched_playwright):
    """Dead-end (HTTP 404 or 'Page not found' h1) recorded; branch halted."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("VIP Experience", "/hospitality/broken")],
        ),
        _FakeResponse(
            "https://mancity.com/hospitality/broken",
            status=404,
            h1_text="404 Not Found",
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    assert any("broken" in u for u in fm.metadata.dead_ends)
    # Crawler did not crash — FlowMap file exists and is valid.
    assert out.exists()
    FlowMap.model_validate_json(out.read_text(encoding="utf-8"))


def test_discover_detects_captcha(tmp_path: Path, patched_playwright):
    """CAPTCHA widget sets captcha_encountered; branch halts (user decision 7)."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://psg.fr/hospitality",
            links=[("VIP Loge", "/hospitality/loge")],
        ),
        _FakeResponse(
            "https://psg.fr/hospitality/loge",
            captcha=True,
        ),
    ])
    out = tmp_path / "psg.json"
    fm = discover_flow("https://psg.fr/hospitality", out, club="psg")

    assert fm.metadata.captcha_encountered is True


def test_discover_never_emits_submit_action(tmp_path: Path, patched_playwright):
    """Regression guard (D-16): across all scenarios, no FlowStep.action == 'submit'.

    The schema Literal would reject it, but defense-in-depth — the crawler
    code must never pass the string 'submit' to FlowStep(action=...).
    """
    from scanner.flow.discover import discover_flow

    # Scenario with a form — the crawler should emit `fill` + `screenshot`,
    # never `submit`.
    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("Enquire", "/hospitality/enquire")],
        ),
        _FakeResponse(
            "https://mancity.com/hospitality/enquire",
            form_inputs=5,
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    for step in fm.steps:
        assert step.action != "submit", f"Submit leaked into flow: {step}"


def test_discover_output_passes_validate_flow_map(tmp_path: Path, patched_playwright):
    """Emitted JSON round-trips through validate_flow_map without raising."""
    from scanner.flow.discover import discover_flow
    from scanner.flow.validate import validate_flow_map

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("Premium Lounge", "/hospitality/lounge")],
        ),
        _FakeResponse(
            "https://mancity.com/hospitality/lounge",
            links=[],
        ),
    ])
    out = tmp_path / "mancity.json"
    discover_flow("https://mancity.com/hospitality", out, club="mancity")

    fm_reloaded = validate_flow_map(out)
    assert fm_reloaded.area == "hospitality"
    assert fm_reloaded.club == "mancity"


def test_discover_detects_form_and_fills_with_dummy_data(tmp_path: Path, patched_playwright):
    """Form-fill pre-submit: crawler emits a `fill` step using D-10 dummy values
    and does NOT proceed past the form."""
    from scanner.flow.discover import discover_flow

    patched_playwright.page = _make_page([
        _FakeResponse(
            "https://mancity.com/hospitality",
            links=[("Hospitality Enquiry", "/hospitality/enquiry")],
        ),
        _FakeResponse(
            "https://mancity.com/hospitality/enquiry",
            form_inputs=4,
        ),
    ])
    out = tmp_path / "mancity.json"
    fm = discover_flow("https://mancity.com/hospitality", out, club="mancity")

    fill_steps = [s for s in fm.steps if s.action == "fill"]
    assert len(fill_steps) >= 1
    # D-10: dummy values are Test Test / test@example.com / +44 0000 000000.
    values = []
    for s in fill_steps:
        if s.form_fields:
            values.extend(f.value for f in s.form_fields)
    assert "Test Test" in values
    assert "test@example.com" in values
    assert "+44 0000 000000" in values


# ---------------------------------------------------------------------------
# Plan 02-08 — Cloudflare Turnstile detector + trusted_subdomains + dedupe
# ---------------------------------------------------------------------------


class _CFFakePage:
    """Minimal page mock for the standalone _detect_bot_challenge unit tests.

    Keeps the surface tiny: ``content()`` returns the body text and
    ``query_selector(sel)`` resolves Cloudflare selectors.
    """

    def __init__(
        self,
        body: str = "",
        cf_selectors: tuple[str, ...] = (),
        raise_content: bool = False,
    ):
        self._body = body
        self._cf_selectors = cf_selectors
        self._raise_content = raise_content

    def content(self):  # noqa: D401 — Playwright API parity
        if self._raise_content:
            raise RuntimeError("nav-race during content()")
        return self._body

    def query_selector(self, selector: str):
        if selector in self._cf_selectors:
            return MagicMock(name=f"cf-match-{selector}")
        return None


def test_detect_bot_challenge_403_with_just_a_moment_text_returns_turnstile():
    """Plan 02-08 Test 1: HTTP 403 + 'Just a moment' body text → 'turnstile'."""
    from scanner.flow.discover import _detect_bot_challenge

    page = _CFFakePage(body="<html><head></head><body>Just a moment...</body></html>")
    assert _detect_bot_challenge(page, status=403) == "turnstile"


def test_detect_bot_challenge_403_with_cf_selector_returns_turnstile():
    """Plan 02-08 Test 2: HTTP 403 + Cloudflare selector → 'turnstile'.

    Tests the selector-only signal path: body has neither marker but
    the DOM contains ``#cf-challenge-running``.
    """
    from scanner.flow.discover import _detect_bot_challenge

    page = _CFFakePage(
        body="<html><body>nothing recognizable here</body></html>",
        cf_selectors=("#cf-challenge-running",),
    )
    assert _detect_bot_challenge(page, status=403) == "turnstile"


def test_detect_bot_challenge_403_with_no_cf_signal_returns_none():
    """Plan 02-08 Test 3: HTTP 403 with neither text nor selector signal → None.

    Regression: a generic 403 (e.g. an auth-protected admin page) must
    NOT classify as a bot challenge.
    """
    from scanner.flow.discover import _detect_bot_challenge

    page = _CFFakePage(body="<html><body>Forbidden</body></html>")
    assert _detect_bot_challenge(page, status=403) is None


def test_detect_bot_challenge_non_403_returns_none():
    """Status != 403 short-circuits regardless of body content."""
    from scanner.flow.discover import _detect_bot_challenge

    page = _CFFakePage(body="<html><body>Just a moment...</body></html>")
    # 200 — no Cloudflare interstitial would ever come back with this status.
    assert _detect_bot_challenge(page, status=200) is None
    # None status (e.g. response was null) — also no detection.
    assert _detect_bot_challenge(page, status=None) is None


def test_detect_bot_challenge_swallows_content_exceptions():
    """Defensive: page.content() raising must NOT raise out of detector."""
    from scanner.flow.discover import _detect_bot_challenge

    page = _CFFakePage(
        body="",
        raise_content=True,
        cf_selectors=("#cf-challenge-running",),
    )
    # Content threw; selector still positive → still classifies.
    assert _detect_bot_challenge(page, status=403) == "turnstile"


def test_inspect_origin_trusted_subdomain_records_and_returns_trusted():
    """Plan 02-08 Test 4: a trusted subdomain returns 'trusted', appends to
    meta.trusted_subdomains_used, and does NOT touch external_redirects."""
    from scanner.flow.discover import _inspect_origin
    from scanner.flow.schema import FlowMapMetadata

    meta = FlowMapMetadata()
    kind = _inspect_origin(
        current_url="https://hospitality.chelseafc.com/packages",
        entry_origin="chelseafc.com",
        meta=meta,
        trusted_subdomains=["hospitality.chelseafc.com"],
    )
    assert kind == "trusted"
    assert "hospitality.chelseafc.com" in meta.trusted_subdomains_used
    assert meta.external_redirects == []


def test_inspect_origin_untrusted_subdomain_falls_through_to_external():
    """Plan 02-08 Test 5: a non-allowlisted cross-origin still falls into
    external_redirects (regression — no allowlist bypass)."""
    from scanner.flow.discover import _inspect_origin
    from scanner.flow.schema import FlowMapMetadata

    meta = FlowMapMetadata()
    kind = _inspect_origin(
        current_url="https://random-tracker.example/",
        entry_origin="chelseafc.com",
        meta=meta,
        trusted_subdomains=["hospitality.chelseafc.com"],
    )
    assert kind == "external"
    assert "https://random-tracker.example/" in meta.external_redirects
    assert meta.trusted_subdomains_used == []


def test_inspect_origin_no_trusted_list_preserves_pre08_behavior():
    """Backward-compat: no trusted_subdomains kwarg → identical to pre-08."""
    from scanner.flow.discover import _inspect_origin
    from scanner.flow.schema import FlowMapMetadata

    meta = FlowMapMetadata()
    kind = _inspect_origin(
        current_url="https://hospitality.chelseafc.com/",
        entry_origin="chelseafc.com",
        meta=meta,
    )
    assert kind == "external"
    assert "https://hospitality.chelseafc.com/" in meta.external_redirects


def test_dedupe_meta_collapses_repeat_dead_ends_preserving_order():
    """Plan 02-08 Test 6: revisiting the same URL multiple times yields one
    entry; insertion order is preserved via dict.fromkeys."""
    from scanner.flow.discover import _dedupe_meta
    from scanner.flow.schema import FlowMapMetadata

    meta = FlowMapMetadata()
    meta.dead_ends = ["a", "b", "a", "c", "b", "a"]
    meta.external_redirects = ["x", "x", "y"]
    meta.login_gated_steps = ["depth-0", "depth-0"]
    meta.trusted_subdomains_used = ["s.example", "s.example"]

    _dedupe_meta(meta)

    assert meta.dead_ends == ["a", "b", "c"]
    assert meta.external_redirects == ["x", "y"]
    assert meta.login_gated_steps == ["depth-0"]
    assert meta.trusted_subdomains_used == ["s.example"]


def test_existing_flow_maps_still_validate_after_schema_extension():
    """Plan 02-08 regression: the 5 front-half flow-map JSONs continue to
    parse cleanly under the extended FlowMapMetadata schema (additive
    default-factory contract)."""
    from scanner.flow.validate import validate_flow_map

    flow_maps_dir = Path(__file__).resolve().parents[1] / "flow-maps" / "hospitality"
    expected = {"chelsea", "mancity", "psg", "realmadrid", "tottenham"}
    found = {p.stem for p in flow_maps_dir.glob("*.json")}
    assert expected.issubset(found), (
        f"Missing front-half flow-maps: expected {expected}, found {found}"
    )
    for fm_path in flow_maps_dir.glob("*.json"):
        fm = validate_flow_map(fm_path)
        # New additive fields are present with their defaults.
        assert fm.metadata.bot_challenge_encountered is False
        assert fm.metadata.bot_challenge_reason is None
        assert fm.metadata.trusted_subdomains_used == []
