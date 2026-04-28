"""Tests for ``scanner.capture.capture.capture_flow`` and the ``--flow-map``
CLI flag (Plan 02-10, Task 2).

The orchestrator iterates a FlowMap step-by-step, dispatching each
``FlowStep.action`` to the appropriate Playwright primitive. The four
override branches are:

1. ``skipped`` — recorded with reason, no Playwright work, no PNG.
2. ``manual_chrome_mcp`` — STDOUT-prompts user, awaits ``input()``, no
   Playwright work, no PNG.
3. ``requires_credentials`` — calls ``login.login_to_club`` first; on False,
   step is recorded as ``missing-credentials`` and skipped.
4. None of the above — the step's action runs (navigate / click / fill / wait
   / screenshot), wrapped in try/except for bounded failure.

After the loop, the orchestrator writes a JSON run-log summarising every
step, plus per-status totals.

D-16 invariant: the orchestrator never calls ``submit`` or any equivalent
primitive that would dispatch a real form. Form-fill steps populate values;
the next ``screenshot`` step captures the pre-submit state (D-10).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Fixtures: synthetic FlowMaps
# ---------------------------------------------------------------------------


def _basic_flow_map(area: str = "hospitality", club: str = "tottenham") -> dict[str, Any]:
    """Minimal 3-step flow-map: navigate → wait → screenshot."""
    return {
        "area": area,
        "club": club,
        "entry_url": "https://example.test/",
        "steps": [
            {
                "step_name": "landing",
                "url": "https://example.test/",
                "action": "navigate",
                "hide_selectors": [],
            },
            {
                "step_name": "landing-wait",
                "action": "wait",
                "wait_for": "networkidle",
            },
            {
                "step_name": "landing-shot",
                "action": "screenshot",
            },
        ],
    }


def _override_flow_map(club: str = "tottenham") -> dict[str, Any]:
    """5-step flow-map exercising skipped + manual_chrome_mcp + requires_credentials.

    Step layout:
      0. navigate (clean)
      1. screenshot (clean)
      2. navigate (skipped: requires-paid-account)
      3. navigate (manual_chrome_mcp: true)
      4. screenshot (requires_credentials: true)
    """
    return {
        "area": "hospitality",
        "club": club,
        "entry_url": "https://example.test/",
        "steps": [
            {
                "step_name": "landing",
                "url": "https://example.test/",
                "action": "navigate",
            },
            {
                "step_name": "landing-shot",
                "action": "screenshot",
            },
            {
                "step_name": "paid-only-step",
                "url": "https://example.test/paid",
                "action": "navigate",
                "skipped": "requires-paid-account",
            },
            {
                "step_name": "cloudflare-blocked",
                "url": "https://example.test/blocked",
                "action": "navigate",
                "manual_chrome_mcp": True,
            },
            {
                "step_name": "logged-in-shot",
                "action": "screenshot",
                "requires_credentials": True,
            },
        ],
    }


def _write_flow_map(tmp_path: Path, data: dict[str, Any], name: str = "flow.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Browser / page mocks
# ---------------------------------------------------------------------------


def _patch_browser(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Replace ``scanner.capture.capture.create_browser`` with a mock chain.

    Returns (page, context, pw) so tests can assert calls.
    """
    page = MagicMock(name="Page")
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()
    page.click = MagicMock()
    page.fill = MagicMock()
    page.wait_for_selector = MagicMock()
    page.add_style_tag = MagicMock()
    page.evaluate = MagicMock(return_value=2000)
    page.screenshot = MagicMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    ctx = MagicMock(name="Context")
    ctx.new_page = MagicMock(return_value=page)
    ctx.close = MagicMock()

    pw = MagicMock(name="Playwright")
    pw.stop = MagicMock()

    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(
        capture_mod, "create_browser", MagicMock(return_value=(pw, ctx))
    )
    # Cookie dismissal is irrelevant for the orchestrator — stub it out.
    monkeypatch.setattr(capture_mod, "dismiss_cookies", MagicMock(return_value=True))
    return page, ctx, pw


# ---------------------------------------------------------------------------
# Test 1 — happy path (3-step minimal flow-map, all Playwright)
# ---------------------------------------------------------------------------


def test_capture_flow_basic_3_step_runs_navigate_wait_screenshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A FlowMap with no override fields runs end-to-end via Playwright."""
    from scanner.capture.capture import capture_flow

    fm_path = _write_flow_map(tmp_path, _basic_flow_map())
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    page, _, _ = _patch_browser(monkeypatch)

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    # Three steps recorded.
    assert len(result["steps"]) == 3
    statuses = [s["status"] for s in result["steps"]]
    assert statuses == ["captured", "captured", "captured"]
    # Screenshot step produced one PNG.
    png_count = sum(1 for s in result["steps"] if s.get("output_path"))
    assert png_count == 1, f"Expected 1 PNG, got {png_count}: {result['steps']}"
    # Log JSON written.
    assert log_path.exists()
    on_disk = json.loads(log_path.read_text(encoding="utf-8"))
    assert on_disk["totals"]["captured"] == 3


# ---------------------------------------------------------------------------
# Test 2 — skipped step recorded, no PNG, run continues
# ---------------------------------------------------------------------------


def test_capture_flow_skipped_step_records_reason_no_png(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A step with ``skipped: <reason>`` is recorded with the reason and
    produces NO PNG. Subsequent steps still run."""
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)
    # Mock input() (manual_chrome_mcp branch needs it) + login_to_club.
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=True))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    # Find the paid-only step in the log.
    skipped = [s for s in result["steps"] if s["step_name"] == "paid-only-step"]
    assert len(skipped) == 1
    assert skipped[0]["status"] == "skipped"
    assert skipped[0]["reason"] == "requires-paid-account"
    assert skipped[0]["output_path"] is None
    # Totals reflect at least one skipped.
    assert result["totals"]["skipped"] >= 1


# ---------------------------------------------------------------------------
# Test 3 — manual_chrome_mcp prompts user, awaits ENTER, no PNG
# ---------------------------------------------------------------------------


def test_capture_flow_manual_chrome_mcp_prompts_user_and_awaits_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A step with ``manual_chrome_mcp: true`` STDOUT-prints a prompt + awaits
    ``input()`` (mocked) + records ``status="chrome-mcp"`` + writes no PNG."""
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)

    # Track input() invocation.
    input_calls: list[str] = []
    def fake_input(prompt: str = "") -> str:
        input_calls.append(prompt)
        return ""
    monkeypatch.setattr("builtins.input", fake_input)
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=True))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    # input() was called for the manual_chrome_mcp step.
    assert len(input_calls) >= 1
    # The step is recorded with chrome-mcp status, no output_path.
    cm_step = [s for s in result["steps"] if s["step_name"] == "cloudflare-blocked"]
    assert len(cm_step) == 1
    assert cm_step[0]["status"] == "chrome-mcp"
    assert cm_step[0]["output_path"] is None


# ---------------------------------------------------------------------------
# Test 4 — requires_credentials → login fails → missing-credentials status
# ---------------------------------------------------------------------------


def test_capture_flow_requires_credentials_missing_records_env_var_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``login_to_club`` returns False (missing creds), the orchestrator
    records ``status="missing-credentials"`` with the env-var NAME (not value).
    The next step still runs."""
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")

    # Force login failure.
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=False))
    # Ensure env vars unset so reason can reference one of them.
    monkeypatch.delenv("TOTTENHAM_HOSPITALITY_USER", raising=False)
    monkeypatch.delenv("TOTTENHAM_HOSPITALITY_PASS", raising=False)

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    mc_step = [s for s in result["steps"] if s["step_name"] == "logged-in-shot"]
    assert len(mc_step) == 1
    assert mc_step[0]["status"] == "missing-credentials"
    reason = mc_step[0]["reason"] or ""
    assert "TOTTENHAM_HOSPITALITY" in reason, (
        f"Expected env var NAME in reason, got: {reason!r}"
    )
    # Reason MUST NOT contain any actual credential value (we did not set any).
    # Soft check: the reason should end with the env-var pattern.
    assert "USER" in reason or "PASS" in reason


def test_capture_flow_requires_credentials_present_runs_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``login_to_club`` returns True, the requires_credentials step
    actually executes (action runs, not recorded as missing-credentials)."""
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")

    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=True))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    mc_step = [s for s in result["steps"] if s["step_name"] == "logged-in-shot"]
    assert len(mc_step) == 1
    # Login succeeded — status should be captured (it's a screenshot step).
    assert mc_step[0]["status"] == "captured"


# ---------------------------------------------------------------------------
# Test 5 — Playwright failure → error status, run continues
# ---------------------------------------------------------------------------


def test_capture_flow_playwright_error_recorded_run_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If page.goto raises during a navigate step, status is ``error`` and
    the next step still runs."""
    from scanner.capture.capture import capture_flow

    fm = {
        "area": "hospitality",
        "club": "tottenham",
        "entry_url": "https://example.test/",
        "steps": [
            {
                "step_name": "broken",
                "url": "https://example.test/broken",
                "action": "navigate",
            },
            {
                "step_name": "after-broken",
                "action": "screenshot",
            },
        ],
    }
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    page, _, _ = _patch_browser(monkeypatch)

    # Force navigate failure.
    page.goto = MagicMock(side_effect=RuntimeError("navigate failed"))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    broken = [s for s in result["steps"] if s["step_name"] == "broken"]
    assert broken[0]["status"] == "error"
    # The screenshot step that follows still ran.
    after = [s for s in result["steps"] if s["step_name"] == "after-broken"]
    assert after[0]["status"] == "captured"


# ---------------------------------------------------------------------------
# Test 6 — totals aggregate every status category
# ---------------------------------------------------------------------------


def test_capture_flow_totals_aggregate_all_categories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run the override flow-map and verify ``totals`` sums each status."""
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=False))
    monkeypatch.delenv("TOTTENHAM_HOSPITALITY_USER", raising=False)
    monkeypatch.delenv("TOTTENHAM_HOSPITALITY_PASS", raising=False)

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
    )

    totals = result["totals"]
    # 5 steps: 2 captured + 1 skipped + 1 chrome-mcp + 1 missing-creds.
    assert totals["captured"] == 2
    assert totals["skipped"] == 1
    assert totals["chrome_mcp"] == 1
    assert totals["missing"] == 1
    assert totals["error"] == 0


# ---------------------------------------------------------------------------
# Test 7 — D-16 invariant: action enum has no `submit`
# ---------------------------------------------------------------------------


def test_capture_flow_never_calls_submit_primitive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Smoke check: the orchestrator's action dispatch covers only the five
    schema-allowed actions; if a malicious flow-map asks for ``submit`` it
    never reaches schema-validation. We assert by inspection that the
    capture_flow source does not contain the literal ``form.submit`` or
    ``button[type=submit]:click`` patterns."""
    import inspect
    from scanner.capture import capture as capture_mod

    src = inspect.getsource(capture_mod.capture_flow)
    # No invocation of form.submit or page.evaluate that submits a form.
    assert "form.submit" not in src.lower()
    # No click on button[type=submit] hardcoded — submission lives in
    # login.py only, where the user opted in via requires_credentials.
    assert 'page.click("button[type=submit]"' not in src.lower()
    assert "page.click('button[type=submit]'" not in src.lower()


# ---------------------------------------------------------------------------
# Test 8 — CLI integration: --flow-map flag drives the orchestrator
# ---------------------------------------------------------------------------


def test_cli_capture_flow_map_flag_invokes_orchestrator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``scanner capture --area hospitality --club tottenham --flow-map FM
    --headless`` exits 0 and the orchestrator was invoked."""
    from scanner.cli import cli

    fm_path = _write_flow_map(tmp_path, _basic_flow_map())

    # Patch capture_flow at the call site (cli.py imports it lazily).
    invoke_log: dict[str, Any] = {}
    def fake_capture_flow(**kwargs: Any) -> dict[str, Any]:
        invoke_log.update(kwargs)
        return {
            "club": kwargs["club"],
            "area": kwargs["area"],
            "started_at": "2026-04-27T00:00:00Z",
            "steps": [],
            "totals": {"captured": 0, "skipped": 0, "chrome_mcp": 0, "missing": 0, "error": 0},
        }
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "capture_flow", fake_capture_flow)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "capture",
            "--area", "hospitality",
            "--club", "tottenham",
            "--flow-map", str(fm_path),
            "--headless",
        ],
    )

    assert result.exit_code == 0, result.output
    # Orchestrator was invoked.
    assert invoke_log["club"] == "tottenham"
    assert invoke_log["area"] == "hospitality"
    # Summary line printed.
    assert "captured" in result.output.lower() or "Captured" in result.output


# ---------------------------------------------------------------------------
# Test 9 — CLI mutual exclusion of --url and --flow-map
# ---------------------------------------------------------------------------


def test_cli_capture_url_and_flow_map_mutually_exclusive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Passing BOTH --url and --flow-map raises a UsageError."""
    from scanner.cli import cli

    fm_path = _write_flow_map(tmp_path, _basic_flow_map())
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "capture",
            "--area", "hospitality",
            "--club", "tottenham",
            "--url", "https://example.test/",
            "--flow-map", str(fm_path),
        ],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower() or "usage" in result.output.lower()


def test_cli_capture_neither_url_nor_flow_map_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Passing NEITHER --url nor --flow-map raises a UsageError."""
    from scanner.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["capture", "--area", "hospitality", "--club", "tottenham"],
    )
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Test 9b — auto_skip_manual records chrome-mcp WITHOUT prompting input()
# ---------------------------------------------------------------------------


def test_capture_flow_auto_skip_manual_does_not_prompt_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unattended-run flag: ``auto_skip_manual=True`` records manual_chrome_mcp
    steps as ``chrome-mcp`` WITHOUT calling ``input()`` — so headless batch
    runs over Cloudflare-blocked clubs (MCFC, RMA-VIP, PSG-billetterie) do
    not hang waiting on a human.
    """
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)

    # If input() gets called we want to fail loudly (the whole point of
    # auto_skip_manual is to suppress it).
    def boom(prompt: str = "") -> str:
        raise AssertionError(
            f"auto_skip_manual=True must not call input(); got prompt={prompt!r}"
        )
    monkeypatch.setattr("builtins.input", boom)
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=True))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
        auto_skip_manual=True,
    )

    cm_step = [s for s in result["steps"] if s["step_name"] == "cloudflare-blocked"]
    assert len(cm_step) == 1
    assert cm_step[0]["status"] == "chrome-mcp"
    assert "auto-skipped" in (cm_step[0]["reason"] or "")


# ---------------------------------------------------------------------------
# Test 9c — Plan 02-16: stealth_override_manual executes manual_chrome_mcp
#            steps via Playwright instead of deferring
# ---------------------------------------------------------------------------


def test_capture_flow_stealth_override_manual_executes_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan 02-16 — when ``stealth_override_manual=True``, a step with
    ``manual_chrome_mcp: true`` runs through the normal action dispatch.
    The run-log records ``status="captured"`` (not ``"chrome-mcp"``) and
    ``reason="stealth-override-unblocked"`` so the recapture summary can
    count stealth-unblocked steps.
    """
    from scanner.capture.capture import capture_flow

    fm = _override_flow_map()
    fm_path = _write_flow_map(tmp_path, fm)
    output_dir = tmp_path / "output"
    log_path = tmp_path / "run-log.json"
    _patch_browser(monkeypatch)

    # input() must NEVER be called when stealth_override_manual=True.
    def boom(prompt: str = "") -> str:
        raise AssertionError(
            f"stealth_override_manual=True must not call input(); got {prompt!r}"
        )
    monkeypatch.setattr("builtins.input", boom)
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "login_to_club", MagicMock(return_value=True))

    result = capture_flow(
        flow_map_path=fm_path,
        club="tottenham",
        area="hospitality",
        output_dir=output_dir,
        log_path=log_path,
        headless=True,
        stealth_override_manual=True,
    )

    cm_step = [s for s in result["steps"] if s["step_name"] == "cloudflare-blocked"]
    assert len(cm_step) == 1
    assert cm_step[0]["status"] == "captured", (
        f"stealth-override should run the step via Playwright, got status="
        f"{cm_step[0]['status']!r}"
    )
    assert cm_step[0]["reason"] == "stealth-override-unblocked"
    # auto_skip_manual must not interfere — totals.captured includes the
    # override step but totals.chrome_mcp must be 0.
    assert result["totals"]["chrome_mcp"] == 0


# ---------------------------------------------------------------------------
# Test 10 — single-page CLI mode (Phase 1) preserved
# ---------------------------------------------------------------------------


def test_cli_capture_single_url_mode_still_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 1 behaviour: ``scanner capture --area X --club Y --url U`` still
    invokes ``capture_page`` (not ``capture_flow``) and exits 0."""
    from scanner.cli import cli

    invoke_log: dict[str, Any] = {}
    def fake_capture_page(**kwargs: Any) -> Path:
        invoke_log.update(kwargs)
        return tmp_path / "fake.png"
    import scanner.capture.capture as capture_mod
    monkeypatch.setattr(capture_mod, "capture_page", fake_capture_page)
    # Don't actually go to disk for area config.
    from scanner.config import loader as loader_mod
    fake_entry = MagicMock()
    fake_entry.evidence_dir = "scanner/output/evidence/hospitality"
    monkeypatch.setattr(loader_mod, "load_area", MagicMock(return_value=fake_entry))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "capture",
            "--area", "hospitality",
            "--club", "tottenham",
            "--url", "https://example.test/",
            "--headless",
        ],
    )

    assert result.exit_code == 0, result.output
    assert invoke_log["url"] == "https://example.test/"
    assert invoke_log["club"] == "tottenham"
