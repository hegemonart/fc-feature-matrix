"""Full-page capture orchestrator (Plan 03, Task 2 + Plan 02-10, Task 2).

Phase 1 ``capture_page`` is the one function Plan 07's CLI and Plan 08's
dry-run call. Coordinates `scanner.capture.browser.create_browser`, cookie
dismissal, lazy-load scrolling, optional selector hiding (D-17), and the
final full-page PNG.

Plan 02-10 ADDS ``capture_flow`` — a multi-step orchestrator that consumes
a FlowMap JSON and dispatches each step to the appropriate Playwright
primitive. The Phase-1 ``capture_page`` signature is preserved unchanged.

**D-16 invariant:** this module contains no form dispatch. Form-fill lives
in `scanner.capture.form_dummy` and is purely `page.fill(...)` — never a
dispatch-button click. The grep-test in `tests/test_browser.py` enforces
that across the whole `scanner/capture/` tree. ``capture_flow``'s action
dispatch covers only the five schema-allowed actions (navigate / click /
fill / wait / screenshot); ``submit`` is intentionally absent.

**D-21 deviation note (Plan 02-10):** This module is in the ``scanner/capture/``
tree which Plan 02-09's HANDOFF flagged as "Phase 1 territory." The deviation
is approved per ``.planning/phases/02-hospitality-pilot/02-BACK-HALF-HANDOFF.md``
"Risks carried into back-half" — HOSP-01 cannot complete without flow-map
orchestration, and that capability did not exist in Phase 1. ``capture_flow``
is purely additive: it does not modify ``capture_page``'s signature or body.

**Output location (D-25, user decision 1):** writes to
`output_dir / 'fullpage' / '{club}_{step_name}.png'`. The caller chooses
`output_dir` — typically `scanner/output/evidence/{area}/` — NEVER `analysis/`.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scanner.capture.browser import create_browser, scroll_lazy
from scanner.capture.cookies import dismiss_cookies
from scanner.capture.login import login_to_club
from scanner.flow.schema import FlowMap, FlowStep
from scanner.flow.validate import validate_flow_map

logger = logging.getLogger(__name__)


def capture_page(
    url: str,
    club: str,
    area: str,
    step_name: str,
    output_dir: Path,
    *,
    headless: bool = False,
    hide_selectors: list[str] | None = None,
) -> Path:
    """Navigate, dismiss cookies, hide dynamic content, scroll lazy, screenshot.

    Parameters
    ----------
    url :
        Target page URL.
    club :
        Club slug — used for per-club cookie strategy dispatch and filename.
    area :
        Area slug — used for the persistent user-data dir (D-13).
    step_name :
        Flow-step name — appears in the output filename.
    output_dir :
        Parent dir. The PNG lands at `{output_dir}/fullpage/{club}_{step_name}.png`.
    headless :
        Defaults to False (headed). Passed through to `create_browser`.
    hide_selectors :
        Optional list of CSS selectors to hide via injected style tag (D-17).

    Returns
    -------
    Path
        Absolute path to the saved PNG. File is guaranteed non-empty on return.
    """
    out_file = output_dir / "fullpage" / f"{club}_{step_name}.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    pw, ctx = create_browser(club=club, area=area, headless=headless)
    try:
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
        time.sleep(2)  # settle for lazy-load images

        # Cookies FIRST per CLAUDE.md trap — before scroll, hide, or screenshot.
        dismiss_cookies(page, club=club)

        # Hide dynamic content (live chat, promo rotators) before scrolling so
        # injected CSS applies during the lazy-load walk too.
        if hide_selectors:
            css = "".join(
                f"{sel}{{display:none !important}}" for sel in hide_selectors
            )
            page.add_style_tag(content=css)

        scroll_lazy(page)

        png_bytes = page.screenshot(full_page=True)
        out_file.write_bytes(png_bytes)
        logger.info(
            f"Captured {club} {step_name} -> {out_file} ({len(png_bytes)} bytes)"
        )
        return out_file
    finally:
        ctx.close()
        pw.stop()


# ---------------------------------------------------------------------------
# Plan 02-10 — capture_flow orchestrator
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """ISO-8601 UTC timestamp (used for run-log started_at + filenames)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hide_selectors(page: Any, selectors: list[str]) -> None:
    """Inject a style tag hiding the given selectors. Best-effort, never raises."""
    if not selectors:
        return
    css = "".join(f"{sel}{{display:none !important}}" for sel in selectors)
    try:
        page.add_style_tag(content=css)
    except Exception:
        # Hide failures are non-fatal — the screenshot still captures whatever
        # rendered.
        pass


def _record(
    log_steps: list[dict[str, Any]],
    *,
    step_name: str,
    status: str,
    duration_ms: int,
    output_path: Path | None = None,
    reason: str | None = None,
) -> None:
    """Append a structured step entry to the run-log list."""
    log_steps.append(
        {
            "step_name": step_name,
            "status": status,
            "duration_ms": duration_ms,
            "output_path": str(output_path) if output_path else None,
            "reason": reason,
        }
    )


def _missing_credential_reason(club: str, area: str) -> str:
    """Build a reason string referencing the env-var NAME (never a value).

    Inspects which of the user / pass env vars is unset and reports the
    first missing one. Both unset → reports the user var.
    """
    import os

    user_var = f"{club.upper()}_{area.upper()}_USER"
    pass_var = f"{club.upper()}_{area.upper()}_PASS"
    if not os.environ.get(user_var):
        return f"env var {user_var} not set"
    if not os.environ.get(pass_var):
        return f"env var {pass_var} not set"
    # Both env vars present but login_to_club returned False — selector miss
    # or marker timeout. Report it as a generic auth failure (no values).
    return "login_to_club returned False (selector miss or marker timeout)"


def _execute_action(
    page: Any,
    step: FlowStep,
    club: str,
    output_dir: Path,
) -> tuple[str, Path | None, str | None]:
    """Dispatch a single FlowStep action.

    Returns ``(status, output_path, reason)``. ``status`` is one of
    ``"captured"`` (action ran cleanly) or ``"error"`` (any exception).

    The action Literal here mirrors ``FlowStep.action`` exactly (D-16):
    navigate / click / fill / wait / screenshot. ``submit`` is intentionally
    absent — the schema rejects it at load-time and this dispatch never
    introduces it.
    """
    try:
        if step.action == "navigate":
            if not step.url:
                return ("error", None, "navigate step missing url")
            page.goto(step.url, wait_until="domcontentloaded", timeout=15_000)
            try:
                page.wait_for_load_state("networkidle", timeout=5_000)
            except Exception:
                # Best-effort settle — many sites never reach networkidle.
                pass
            _hide_selectors(page, step.hide_selectors)
            return ("captured", None, None)

        elif step.action == "click":
            if not step.selector:
                return ("error", None, "click step missing selector")
            page.click(step.selector, timeout=5_000)
            return ("captured", None, None)

        elif step.action == "fill":
            if not step.form_fields:
                return ("error", None, "fill step missing form_fields")
            for ff in step.form_fields:
                page.fill(ff.selector, ff.value)
            return ("captured", None, None)

        elif step.action == "wait":
            target = step.wait_for
            if not target:
                return ("error", None, "wait step missing wait_for")
            if target in ("networkidle", "load", "domcontentloaded"):
                page.wait_for_load_state(target, timeout=5_000)
            else:
                page.wait_for_selector(target, timeout=5_000)
            return ("captured", None, None)

        elif step.action == "screenshot":
            _hide_selectors(page, step.hide_selectors)
            try:
                scroll_lazy(page)
            except Exception:
                pass
            out_file = output_dir / "fullpage" / f"{club}_{step.step_name}.png"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            png_bytes = page.screenshot(full_page=True)
            out_file.write_bytes(png_bytes)
            return ("captured", out_file, None)

        else:  # pragma: no cover — schema Literal blocks anything else.
            return ("error", None, f"unknown action {step.action!r}")
    except Exception as exc:
        # Truncate the error message — never echo a stack trace into the
        # run-log (T-10-01 disclosure mitigation; nothing in step.action
        # output should carry user-supplied data, but defensively bound it).
        msg = str(exc)
        if len(msg) > 200:
            msg = msg[:200] + "..."
        return ("error", None, msg)


def capture_flow(
    flow_map_path: Path,
    club: str,
    area: str,
    output_dir: Path,
    log_path: Path,
    *,
    headless: bool = False,
    auto_skip_manual: bool = False,
) -> dict[str, Any]:
    """Multi-step capture orchestrated by a FlowMap (Plan 02-10).

    Iterates ``flow_map.steps`` in order, dispatching each step to the
    appropriate handler. Four override branches short-circuit Playwright
    work for cases that cannot or should not be automated:

    - ``step.skipped`` → recorded with reason; no Playwright work, no PNG.
    - ``step.manual_chrome_mcp`` → STDOUT-prompts the user, calls
      ``input()`` to await an ENTER, then records the step as ``chrome-mcp``.
    - ``step.requires_credentials`` → calls ``login_to_club`` first; on
      False, records ``missing-credentials`` with the env-var NAME (never
      a value) and skips the step.
    - Default → executes the step's action via Playwright, wrapped in
      try/except for bounded failure.

    Returns a run-log dict and writes it to ``log_path``.

    Parameters
    ----------
    flow_map_path :
        Path to a FlowMap JSON file. Validated via ``validate_flow_map``.
    club :
        Club slug (e.g. ``"tottenham"``). Drives login + filename + cookie
        strategy dispatch.
    area :
        Area slug (e.g. ``"hospitality"``). Drives env-var convention.
    output_dir :
        Parent of the ``fullpage/`` PNG output dir. Per-step PNGs land at
        ``output_dir / "fullpage" / "{club}_{step_name}.png"``.
    log_path :
        Where the run-log JSON is written.
    headless :
        Forwarded to ``create_browser``. Default False (headed).

    Returns
    -------
    dict
        ``{
          "club": str, "area": str, "started_at": ISO8601,
          "steps": [
            {"step_name": str, "status": str, "duration_ms": int,
             "output_path": str | None, "reason": str | None},
            ...
          ],
          "totals": {"captured": int, "skipped": int, "chrome_mcp": int,
                     "missing": int, "error": int}
        }``
    """
    flow_map: FlowMap = validate_flow_map(flow_map_path)
    log_steps: list[dict[str, Any]] = []
    started_at = _utc_now_iso()

    pw, ctx = create_browser(club=club, area=area, headless=headless)
    try:
        page = ctx.new_page()
        for step in flow_map.steps:
            t0 = time.perf_counter()

            # 1) Explicit skip first — never engages Playwright.
            if step.skipped is not None:
                _record(
                    log_steps,
                    step_name=step.step_name,
                    status="skipped",
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    reason=step.skipped,
                )
                continue

            # 2) Chrome MCP handoff — prompt the user, wait for ENTER.
            #    In auto_skip_manual mode (unattended capture wave) we record
            #    the step as chrome-mcp WITHOUT prompting; downstream
            #    deferred-manual-handoff doc captures the URL + action so
            #    the user can drive Chrome MCP later. This unblocks
            #    headless batch runs over Cloudflare-blocked clubs (Plan 02-10
            #    execution_protocol strategy).
            if step.manual_chrome_mcp:
                if auto_skip_manual:
                    _record(
                        log_steps,
                        step_name=step.step_name,
                        status="chrome-mcp",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        reason="auto-skipped (unattended run); deferred to manual Chrome MCP handoff",
                    )
                    continue
                print(f"\n=== CHROME MCP STEP: {step.step_name} ===")
                if step.url:
                    print(f"URL: {step.url}")
                print(f"Action: {step.action}")
                if step.selector:
                    print(f"Selector: {step.selector}")
                input(">>> Press ENTER to continue (after you've completed this step in Chrome MCP)... ")
                _record(
                    log_steps,
                    step_name=step.step_name,
                    status="chrome-mcp",
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    reason="manual_chrome_mcp",
                )
                continue

            # 3) Credentials gate — login_to_club must return True.
            if step.requires_credentials:
                ok = login_to_club(page, club)
                if not ok:
                    _record(
                        log_steps,
                        step_name=step.step_name,
                        status="missing-credentials",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        reason=_missing_credential_reason(club, area),
                    )
                    continue
                # Login succeeded — fall through to action dispatch.

            # 4) Default — execute the step's action.
            #    Cookie dismissal happens AFTER the first navigate (matches
            #    Phase 1 capture_page invariant: dismiss before scroll/screenshot).
            status, out_path, reason = _execute_action(page, step, club, output_dir)
            if status == "captured" and step.action == "navigate":
                # Best-effort cookie dismissal after every navigate (idempotent).
                try:
                    dismiss_cookies(page, club=club)
                except Exception:
                    pass
            _record(
                log_steps,
                step_name=step.step_name,
                status=status,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                output_path=out_path,
                reason=reason,
            )
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass

    # Aggregate totals — buckets keyed by status string.
    totals = {
        "captured": sum(1 for s in log_steps if s["status"] == "captured"),
        "skipped": sum(1 for s in log_steps if s["status"] == "skipped"),
        "chrome_mcp": sum(1 for s in log_steps if s["status"] == "chrome-mcp"),
        "missing": sum(1 for s in log_steps if s["status"] == "missing-credentials"),
        "error": sum(1 for s in log_steps if s["status"] == "error"),
    }

    run_log = {
        "club": club,
        "area": area,
        "flow_map": str(flow_map_path),
        "started_at": started_at,
        "steps": log_steps,
        "totals": totals,
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    logger.info(
        "capture_flow %s/%s done — captured=%d skipped=%d chrome-mcp=%d missing=%d error=%d",
        area, club, totals["captured"], totals["skipped"],
        totals["chrome_mcp"], totals["missing"], totals["error"],
    )

    return run_log


__all__ = ["capture_page", "capture_flow"]
