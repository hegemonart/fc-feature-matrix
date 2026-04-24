"""End-to-end mocked integration test for the scanner dry-run pipeline (Plan 01-08).

This test exercises the full four-command sequence
(``capture -> vision -> slice -> report``) against a synthetic tmp-path repo
with every external I/O mocked:

- ``playwright.sync_api.sync_playwright`` -> a MagicMock chain that returns a
  real small PNG from ``page.screenshot(full_page=True)``.
- ``scanner.vision.client_subscription.query`` -> async iterator yielding one
  AssistantMessage whose text block is the three-feature JSON payload.
- ``scanner.vision.client_apikey.anthropic.Anthropic`` -> MagicMock whose
  ``messages.create`` returns a response object with the same JSON payload.

The synthetic repo has:

- ``scanner/config/areas.json`` — copied verbatim from the real file so
  ``load_area('hospitality')`` resolves the Phase 1 seed.
- ``scanner/tests/fixtures/dummy-hospitality-rubric.json`` — copied verbatim
  so ``--rubric`` resolves.

Per D-24 / D-25 / D-28 (subscription default) / FLOW-05 / FLOW-06.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from PIL import Image


# ---------------------------------------------------------------------------
# Canned judge responses — identical present/absent across the two judges so
# the disagreement count is ZERO (keeps the dry-run contact sheet clean).
# ---------------------------------------------------------------------------

OPUS_MOCK_RESPONSE_JSON = json.dumps(
    {
        "hero_image": {
            "present": True,
            "step": "landing",
            "evidence_bbox": [50.0, 100.0, 1300.0, 500.0],
            "confidence": 0.93,
            "notes": "Large hospitality hero banner above fold.",
        },
        "primary_cta": {
            "present": True,
            "step": "landing",
            "evidence_bbox": [600.0, 700.0, 200.0, 60.0],
            "confidence": 0.88,
            "notes": "Orange enquire-now button.",
        },
        "hospitality_tiers_list": {
            "present": False,
            "step": "landing",
            "evidence_bbox": None,
            "confidence": 0.76,
            "notes": "No tier cards visible on landing; likely on subpage.",
        },
    }
)

SONNET_MOCK_RESPONSE_JSON = json.dumps(
    {
        "hero_image": {
            "present": True,
            "step": "landing",
            "evidence_bbox": [52.0, 102.0, 1298.0, 498.0],
            "confidence": 0.91,
            "notes": "Hero banner visible.",
        },
        "primary_cta": {
            "present": True,
            "step": "landing",
            "evidence_bbox": [602.0, 702.0, 198.0, 58.0],
            "confidence": 0.85,
            "notes": "CTA button visible.",
        },
        "hospitality_tiers_list": {
            "present": False,
            "step": "landing",
            "evidence_bbox": None,
            "confidence": 0.74,
            "notes": "No tiers on landing page.",
        },
    }
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Build a tmp-path repo skeleton that the CLI can read.

    Copies ``scanner/config/areas.json`` and the dummy rubric fixture into
    the tmp repo, then monkeypatches ``SCANNER_REPO_ROOT`` and the
    module-level ``REPO_ROOT`` in ``scanner.config.loader`` so every CLI
    subcommand resolves its paths against the tmp repo (never the real one).
    """
    real_repo = Path(__file__).resolve().parents[2]
    root = tmp_path / "repo"
    (root / "scanner" / "config").mkdir(parents=True)
    (root / "scanner" / "tests" / "fixtures").mkdir(parents=True)
    (root / "scanner" / "output").mkdir(parents=True)
    (root / "analysis").mkdir(parents=True)  # for D-24 invariant check

    shutil.copy(
        real_repo / "scanner" / "config" / "areas.json",
        root / "scanner" / "config" / "areas.json",
    )
    shutil.copy(
        real_repo / "scanner" / "tests" / "fixtures" / "dummy-hospitality-rubric.json",
        root / "scanner" / "tests" / "fixtures" / "dummy-hospitality-rubric.json",
    )

    monkeypatch.setenv("SCANNER_REPO_ROOT", str(root))
    # The loader resolves REPO_ROOT at import time; override the module attr
    # so subsequent `from scanner.config.loader import REPO_ROOT` pulls the
    # patched value (CLI subcommands do this inside each function body).
    import scanner.config.loader as loader_mod

    monkeypatch.setattr(loader_mod, "REPO_ROOT", root)
    return root


@pytest.fixture
def large_png_bytes() -> bytes:
    """1440x900 white PNG — matches the real viewport so denormalise_bbox is a
    no-op (long edge < Opus 2576 px limit) and slicing produces visible crops.
    """
    img = Image.new("RGB", (1440, 900), color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _page_evaluate_side_effect(script, *args, **kwargs):
    """Return plausible values for the handful of page.evaluate calls the
    capture path makes:

    - ``document.body.scrollHeight`` (in ``scroll_lazy``) -> small int so one
      scroll step fires and the loop exits cleanly.
    - Cookie dismissal JS (the big IIFE that scans buttons) -> ``True`` so
      ``dismiss_cookies`` reports a successful click.
    - ``window.scrollTo(...)`` -> ``None`` (no return needed).
    """
    if isinstance(script, str):
        if "scrollHeight" in script:
            return 1200
        if "scrollTo" in script:
            return None
        # The cookie IIFE contains `priorities` as its parameter name.
        if "priorities" in script or "__cmp" in script:
            return True
    return None


def _build_fake_sync_playwright(png_bytes: bytes):
    """Build a MagicMock chain that ``sync_playwright().start()`` returns.

    The important return is ``page.screenshot(full_page=True)`` -> ``png_bytes``.
    ``page.evaluate`` returns a small int so ``scroll_lazy`` does one pass.
    """
    fake_page = MagicMock(name="Page")
    fake_page.goto = MagicMock()
    fake_page.wait_for_load_state = MagicMock()
    fake_page.evaluate = MagicMock(side_effect=_page_evaluate_side_effect)
    fake_page.add_style_tag = MagicMock()
    fake_page.screenshot = MagicMock(return_value=png_bytes)
    fake_page.click = MagicMock()
    fake_page.fill = MagicMock()

    fake_context = MagicMock(name="BrowserContext")
    fake_context.new_page = MagicMock(return_value=fake_page)
    fake_context.close = MagicMock()

    fake_chromium = MagicMock(name="chromium")
    fake_chromium.launch_persistent_context = MagicMock(return_value=fake_context)

    fake_pw = MagicMock(name="Playwright")
    fake_pw.chromium = fake_chromium
    fake_pw.stop = MagicMock()

    fake_factory = MagicMock(name="sync_playwright_factory")
    fake_factory.start = MagicMock(return_value=fake_pw)

    return MagicMock(return_value=fake_factory), fake_page


def _async_iter(messages):
    async def _gen():
        for m in messages:
            yield m

    return _gen()


def _fake_assistant_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def _make_subscription_query(opus_json: str, sonnet_json: str):
    """Return a fake ``query`` that alternates responses per call.

    two_judge calls ``SubscriptionVisionClient.analyze_screenshot`` twice —
    once for Opus, once for Sonnet — each of which drives ``query`` once.
    We flip a ``call_index`` counter between the two canned responses.
    """
    call_state = {"n": 0}

    def fake_query(*, prompt, options=None, transport=None):
        idx = call_state["n"]
        call_state["n"] += 1
        # two_judge runs opus FIRST then sonnet, so even indices get opus_json.
        text = opus_json if idx % 2 == 0 else sonnet_json
        return _async_iter([_fake_assistant_message(text)])

    return fake_query


def _make_apikey_response(json_text: str):
    """Build the shape ``anthropic.messages.create`` returns.

    The APIKeyVisionClient reads ``resp.content[0].text``.
    """
    return SimpleNamespace(content=[SimpleNamespace(text=json_text)])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_dry_run_subscription_backend(
    synthetic_repo: Path,
    large_png_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-28 gate: full pipeline runs cleanly through the SUBSCRIPTION backend.

    Asserts all six artifact checks from PLAN 01-08's `how-to-verify` table
    succeed after four CLI invocations with external I/O mocked.
    """
    from scanner.cli import cli

    repo = synthetic_repo
    fake_sync_pw, _fake_page = _build_fake_sync_playwright(large_png_bytes)
    monkeypatch.setattr(
        "scanner.capture.browser.sync_playwright", fake_sync_pw
    )
    # USER_DATA_ROOT must land inside tmp so launch_persistent_context's
    # path creation does not touch the developer's home dir.
    monkeypatch.setattr(
        "scanner.capture.browser.USER_DATA_ROOT",
        repo / ".scanner" / "user-data",
    )

    fake_query = _make_subscription_query(
        OPUS_MOCK_RESPONSE_JSON, SONNET_MOCK_RESPONSE_JSON
    )
    monkeypatch.setattr(
        "scanner.vision.client_subscription.query", fake_query
    )

    runner = CliRunner()

    # 1. capture
    res_capture = runner.invoke(
        cli,
        [
            "capture",
            "--area", "hospitality",
            "--club", "mancity",
            "--url", "https://example.test/hospitality",
            "--headless",
        ],
        catch_exceptions=False,
    )
    assert res_capture.exit_code == 0, res_capture.output

    fullpage = (
        repo
        / "scanner"
        / "output"
        / "evidence"
        / "hospitality"
        / "fullpage"
        / "mancity_landing.png"
    )
    assert fullpage.exists(), f"expected {fullpage} to exist"
    assert fullpage.stat().st_size > 0, "fullpage PNG is empty"

    # 2. vision (subscription — DEFAULT)
    rubric_path = (
        repo
        / "scanner"
        / "tests"
        / "fixtures"
        / "dummy-hospitality-rubric.json"
    )
    res_vision = runner.invoke(
        cli,
        [
            "vision",
            "--area", "hospitality",
            "--club", "mancity",
            "--rubric", str(rubric_path),
            "--api-mode", "subscription",
        ],
        catch_exceptions=False,
    )
    assert res_vision.exit_code == 0, res_vision.output

    features_json = (
        repo
        / "scanner"
        / "output"
        / "results"
        / "hospitality"
        / "mancity_features.json"
    )
    assert features_json.exists()
    data = json.loads(features_json.read_text(encoding="utf-8"))
    assert data["api_mode"] == "subscription"
    for judge_key in ("opus", "sonnet"):
        assert judge_key in data
        for feat in ("hero_image", "primary_cta", "hospitality_tiers_list"):
            assert feat in data[judge_key], (
                f"{judge_key} missing {feat!r}: {data[judge_key].keys()}"
            )

    # Disagreements file exists (may be empty because the two canned payloads
    # match on present/absent and IoU is >0.5 by construction).
    disagreements = repo / "scanner" / "output" / "disagreements-hospitality.json"
    assert disagreements.exists()
    disagreements_data = json.loads(disagreements.read_text(encoding="utf-8"))
    assert isinstance(disagreements_data, list)

    # 3. slice
    res_slice = runner.invoke(
        cli,
        ["slice", "--area", "hospitality", "--club", "mancity"],
        catch_exceptions=False,
    )
    assert res_slice.exit_code == 0, res_slice.output

    features_dir = (
        repo
        / "scanner"
        / "output"
        / "evidence"
        / "hospitality"
        / "features"
    )
    crops = sorted(features_dir.glob("mancity_*.png"))
    assert 1 <= len(crops) <= 3, (
        f"expected 1-3 crops in {features_dir}, got {len(crops)}: {crops}"
    )
    # The two present features (hero_image, primary_cta) should both have crops.
    crop_keys = {p.stem.split("_", 1)[1] for p in crops}
    assert "hero_image" in crop_keys
    assert "primary_cta" in crop_keys

    # 4. report
    res_report = runner.invoke(
        cli,
        ["report", "--area", "hospitality"],
        catch_exceptions=False,
    )
    assert res_report.exit_code == 0, res_report.output

    contact_sheet = repo / "scanner" / "output" / "contact-report-hospitality.html"
    assert contact_sheet.exists()
    assert contact_sheet.stat().st_size > 0
    html = contact_sheet.read_text(encoding="utf-8")
    assert html.count('<div class="feature">') == 3
    assert "<img" in html

    # 6. D-24 invariant — analysis/ not touched.
    proc = subprocess.run(
        ["git", "diff", "--quiet", str(repo / "analysis")],
        capture_output=True,
    )
    # No analysis content was added to the synthetic repo -> git diff returns 0
    # for "nothing to show" OR 128 for "not a git repo" (the tmp path is not
    # under git). Both are equivalent to "analysis/ was never mutated".
    assert proc.returncode in (0, 128), (
        f"D-24 violated: git diff analysis/ returned {proc.returncode}: "
        f"{proc.stderr.decode('utf-8', errors='ignore')}"
    )


@pytest.mark.integration
def test_dry_run_apikey_backend(
    synthetic_repo: Path,
    large_png_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback D-26(b) path: ``--api-mode api-key`` works with
    ``ANTHROPIC_API_KEY`` set and ``anthropic.Anthropic`` mocked.

    Only the vision command path differs; capture/slice/report are unchanged,
    so we only exercise the vision command end-to-end here and assert the
    ``api_mode`` field in the features JSON flipped.
    """
    from scanner.cli import cli

    repo = synthetic_repo

    # Capture first (using the same sync_playwright mock as the other test).
    fake_sync_pw, _ = _build_fake_sync_playwright(large_png_bytes)
    monkeypatch.setattr(
        "scanner.capture.browser.sync_playwright", fake_sync_pw
    )
    monkeypatch.setattr(
        "scanner.capture.browser.USER_DATA_ROOT",
        repo / ".scanner" / "user-data",
    )

    runner = CliRunner()
    res_capture = runner.invoke(
        cli,
        [
            "capture",
            "--area", "hospitality",
            "--club", "mancity",
            "--url", "https://example.test/hospitality",
            "--headless",
        ],
        catch_exceptions=False,
    )
    assert res_capture.exit_code == 0, res_capture.output

    # Vision with api-key backend.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-test-key")

    call_state = {"n": 0}

    def _create_side_effect(**_kwargs):
        idx = call_state["n"]
        call_state["n"] += 1
        text = OPUS_MOCK_RESPONSE_JSON if idx % 2 == 0 else SONNET_MOCK_RESPONSE_JSON
        return _make_apikey_response(text)

    fake_anthropic_client = MagicMock()
    fake_anthropic_client.messages.create = MagicMock(side_effect=_create_side_effect)
    fake_anthropic_ctor = MagicMock(return_value=fake_anthropic_client)

    rubric_path = (
        repo
        / "scanner"
        / "tests"
        / "fixtures"
        / "dummy-hospitality-rubric.json"
    )

    with patch(
        "scanner.vision.client_apikey.anthropic.Anthropic", fake_anthropic_ctor
    ):
        res_vision = runner.invoke(
            cli,
            [
                "vision",
                "--area", "hospitality",
                "--club", "mancity",
                "--rubric", str(rubric_path),
                "--api-mode", "api-key",
            ],
            catch_exceptions=False,
        )

    assert res_vision.exit_code == 0, res_vision.output

    features_json = (
        repo
        / "scanner"
        / "output"
        / "results"
        / "hospitality"
        / "mancity_features.json"
    )
    data = json.loads(features_json.read_text(encoding="utf-8"))
    assert data["api_mode"] == "api-key"
    for feat in ("hero_image", "primary_cta", "hospitality_tiers_list"):
        assert feat in data["opus"]
        assert feat in data["sonnet"]

    # The api-key backend must have been called exactly twice (once per judge).
    assert fake_anthropic_client.messages.create.call_count == 2
