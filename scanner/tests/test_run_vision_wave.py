"""Tests for scanner.scripts.run_vision_wave (Plan 02-11 Task 2).

The wave orchestrator wraps ``scanner.vision.judge.two_judge`` to:

- Read a Plan 02-10 capture run-log JSON for a club.
- For every step with status=='captured', locate the PNG at
  ``{evidence_dir}/fullpage/{club}_{step_name}.png`` and run two_judge.
- Merge per-step verdicts into a single per-club result JSON shaped:
  ``{club, area, api_mode, steps: {step_name: {opus, sonnet}}}``.
- Append disagreements (presence + bbox) to the area-wide
  ``disagreements-{area}.json`` aggregator.
- Skip steps with status in {skipped, chrome-mcp, error} (no PNG to feed).

All tests patch ``two_judge`` — no live SDK calls. The orchestrator is
pure I/O wiring around the Phase-1 judge primitive.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse


def _verdict(present: bool = True, conf: float = 0.9) -> FeatureVerdict:
    return FeatureVerdict(
        present=present,
        step="landing",
        evidence_bbox=(0.0, 0.0, 100.0, 100.0) if present else None,
        confidence=conf,
        notes="mock",
    )


def _judge_pair(
    feature_keys: list[str],
    opus_present: list[bool] | None = None,
    sonnet_present: list[bool] | None = None,
) -> dict[str, JudgeResponse]:
    if opus_present is None:
        opus_present = [True] * len(feature_keys)
    if sonnet_present is None:
        sonnet_present = list(opus_present)
    return {
        "opus": JudgeResponse(
            model="claude-opus-4-7",
            results={
                k: _verdict(p) for k, p in zip(feature_keys, opus_present)
            },
        ),
        "sonnet": JudgeResponse(
            model="claude-sonnet-4-6",
            results={
                k: _verdict(p) for k, p in zip(feature_keys, sonnet_present)
            },
        ),
    }


def _setup_run_log(tmp_path: Path, club: str, steps: list[dict]) -> Path:
    log = {
        "club": club,
        "area": "hospitality",
        "flow_map": "stub.json",
        "started_at": "2026-04-27T15:40:13Z",
        "steps": steps,
        "totals": {
            "captured": sum(1 for s in steps if s["status"] == "captured"),
            "skipped": sum(1 for s in steps if s["status"] == "skipped"),
            "chrome_mcp": sum(1 for s in steps if s["status"] == "chrome-mcp"),
            "missing": 0,
            "error": sum(1 for s in steps if s["status"] == "error"),
        },
    }
    p = tmp_path / f"capture-run-log-hospitality-{club}-20260427T154013Z.json"
    p.write_text(json.dumps(log), encoding="utf-8")
    return p


def _setup_png(evidence_dir: Path, club: str, step: str) -> Path:
    fullpage = evidence_dir / "fullpage"
    fullpage.mkdir(parents=True, exist_ok=True)
    png = fullpage / f"{club}_{step}.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    return png


# ---------------------------------------------------------------------------
# Test 1 — captured-step iteration: only captured steps trigger two_judge
# ---------------------------------------------------------------------------


def test_only_captured_steps_run_two_judge(tmp_path: Path) -> None:
    """Steps with status != 'captured' must not invoke two_judge."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path,
        "tottenham",
        steps=[
            {"step_name": "landing-shot", "status": "captured"},
            {"step_name": "match-selector-shot", "status": "captured"},
            {"step_name": "enquiry-form-prefill", "status": "error", "reason": "Timeout"},
            {"step_name": "billetterie-vip", "status": "chrome-mcp", "reason": "deferred"},
        ],
    )
    _setup_png(evidence_dir, "tottenham", "landing-shot")
    _setup_png(evidence_dir, "tottenham", "match-selector-shot")

    rubric = [FeatureDef(key="hero_image", name="Hero Image", yes_criterion="hero present")]

    with patch("scanner.scripts.run_vision_wave.two_judge") as mock_tj:
        mock_tj.return_value = _judge_pair(["hero_image"])
        result = run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    # Two captured steps -> two_judge invoked twice.
    assert mock_tj.call_count == 2
    assert result["captured_steps"] == 2
    assert result["skipped_steps"] == 2


# ---------------------------------------------------------------------------
# Test 2 — per-club result JSON has 'steps' key with per-step opus/sonnet
# ---------------------------------------------------------------------------


def test_result_json_shape_steps_keyed(tmp_path: Path) -> None:
    """Output shape: {club, area, api_mode, steps: {name: {opus, sonnet}}}."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path,
        "tottenham",
        steps=[
            {"step_name": "landing-shot", "status": "captured"},
            {"step_name": "match-selector-shot", "status": "captured"},
        ],
    )
    _setup_png(evidence_dir, "tottenham", "landing-shot")
    _setup_png(evidence_dir, "tottenham", "match-selector-shot")

    rubric = [FeatureDef(key="hero_image", name="Hero", yes_criterion="hero")]

    with patch("scanner.scripts.run_vision_wave.two_judge") as mock_tj:
        mock_tj.return_value = _judge_pair(["hero_image"])
        run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    out_path = results_dir / "tottenham_features.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["club"] == "tottenham"
    assert data["area"] == "hospitality"
    assert data["api_mode"] == "subscription"
    assert "steps" in data
    assert set(data["steps"].keys()) == {"landing-shot", "match-selector-shot"}
    for step_name, step_data in data["steps"].items():
        assert "opus" in step_data
        assert "sonnet" in step_data
        assert "hero_image" in step_data["opus"]
        assert step_data["opus"]["hero_image"]["present"] is True


# ---------------------------------------------------------------------------
# Test 3 — disagreements aggregated across steps with club tag
# ---------------------------------------------------------------------------


def test_disagreements_tagged_with_club_and_step(tmp_path: Path) -> None:
    """Each disagreement record has `club` and `step` so multi-club aggregation works."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path,
        "psg",
        steps=[{"step_name": "landing-shot", "status": "captured"}],
    )
    _setup_png(evidence_dir, "psg", "landing-shot")

    rubric = [
        FeatureDef(key="hero_image", name="Hero", yes_criterion="hero"),
        FeatureDef(key="primary_cta", name="CTA", yes_criterion="cta"),
    ]

    # Disagreement: opus says present, sonnet says absent on hero_image.
    pair = _judge_pair(
        ["hero_image", "primary_cta"],
        opus_present=[True, True],
        sonnet_present=[False, True],
    )
    with patch("scanner.scripts.run_vision_wave.two_judge", return_value=pair):
        run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    assert disagreements_path.exists()
    data = json.loads(disagreements_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    presence_disagreements = [d for d in data if d.get("kind") == "presence"]
    assert len(presence_disagreements) >= 1
    # Each disagreement carries club + step provenance.
    for d in presence_disagreements:
        assert d.get("club") == "psg"
        assert "step" in d


# ---------------------------------------------------------------------------
# Test 4 — second-club run appends to disagreements (does not overwrite)
# ---------------------------------------------------------------------------


def test_disagreements_accumulate_across_clubs(tmp_path: Path) -> None:
    """Running the wave for a second club appends to the same disagreements JSON."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    rubric = [FeatureDef(key="hero_image", name="Hero", yes_criterion="hero")]

    # Club 1
    log1 = _setup_run_log(
        tmp_path, "tottenham",
        steps=[{"step_name": "landing-shot", "status": "captured"}],
    )
    _setup_png(evidence_dir, "tottenham", "landing-shot")
    pair1 = _judge_pair(["hero_image"], opus_present=[True], sonnet_present=[False])
    with patch("scanner.scripts.run_vision_wave.two_judge", return_value=pair1):
        run_wave_for_club(
            run_log_path=log1,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    # Club 2
    log2 = _setup_run_log(
        tmp_path, "psg",
        steps=[{"step_name": "landing-shot", "status": "captured"}],
    )
    _setup_png(evidence_dir, "psg", "landing-shot")
    pair2 = _judge_pair(["hero_image"], opus_present=[True], sonnet_present=[False])
    with patch("scanner.scripts.run_vision_wave.two_judge", return_value=pair2):
        run_wave_for_club(
            run_log_path=log2,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    data = json.loads(disagreements_path.read_text(encoding="utf-8"))
    clubs = sorted({d.get("club") for d in data if d.get("club")})
    assert clubs == ["psg", "tottenham"]


# ---------------------------------------------------------------------------
# Test 5 — missing PNG for a captured step is logged but does not crash
# ---------------------------------------------------------------------------


def test_missing_png_logged_skipped(tmp_path: Path) -> None:
    """If a captured step's PNG is missing on disk, skip it gracefully."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path, "chelsea",
        steps=[
            {"step_name": "landing-shot", "status": "captured"},
            {"step_name": "missing-png-step", "status": "captured"},
        ],
    )
    # Only one PNG exists.
    _setup_png(evidence_dir, "chelsea", "landing-shot")

    rubric = [FeatureDef(key="hero_image", name="Hero", yes_criterion="hero")]

    with patch("scanner.scripts.run_vision_wave.two_judge") as mock_tj:
        mock_tj.return_value = _judge_pair(["hero_image"])
        result = run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    # Only landing-shot should have triggered two_judge.
    assert mock_tj.call_count == 1
    assert "missing-png-step" in result["missing_png_steps"]


# ---------------------------------------------------------------------------
# Test 6 — Chelsea skipped-paid steps are tracked in result manifest
# ---------------------------------------------------------------------------


def test_chelsea_skipped_steps_recorded_in_manifest(tmp_path: Path) -> None:
    """Chelsea's `skipped: requires-paid-account` steps are listed in the result JSON."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path, "chelsea",
        steps=[
            {"step_name": "landing-shot", "status": "captured"},
            {"step_name": "match-selector", "status": "skipped",
             "reason": "requires-paid-account"},
            {"step_name": "enquiry-form-prefill", "status": "skipped",
             "reason": "requires-paid-account"},
        ],
    )
    _setup_png(evidence_dir, "chelsea", "landing-shot")

    rubric = [FeatureDef(key="hero_image", name="Hero", yes_criterion="hero")]

    with patch("scanner.scripts.run_vision_wave.two_judge") as mock_tj:
        mock_tj.return_value = _judge_pair(["hero_image"])
        run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    out_path = results_dir / "chelsea_features.json"
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "deferred_steps" in data
    deferred = data["deferred_steps"]
    deferred_names = {d["step_name"] for d in deferred}
    assert "match-selector" in deferred_names
    assert "enquiry-form-prefill" in deferred_names
    # Reasons preserved for downstream Plan 02-12 to mark absent.
    for d in deferred:
        assert "reason" in d


# ---------------------------------------------------------------------------
# Test 7 — schema-permissive rubric (FeatureDef) reaches two_judge unmodified
# ---------------------------------------------------------------------------


def test_rubric_passed_verbatim_to_two_judge(tmp_path: Path) -> None:
    """The rubric list of FeatureDef is forwarded verbatim to two_judge."""
    from scanner.scripts.run_vision_wave import run_wave_for_club

    evidence_dir = tmp_path / "evidence"
    results_dir = tmp_path / "results"
    disagreements_path = tmp_path / "disagreements.json"

    run_log = _setup_run_log(
        tmp_path, "realmadrid",
        steps=[{"step_name": "landing-shot", "status": "captured"}],
    )
    _setup_png(evidence_dir, "realmadrid", "landing-shot")

    rubric = [
        FeatureDef(key="hero_image", name="Hero", yes_criterion="hero"),
        FeatureDef(key="primary_cta", name="CTA", yes_criterion="cta"),
    ]

    captured_rubric: list = []

    def _spy_two_judge(image_path, the_rubric, *, api_mode, dom_intel_path=None):  # noqa: D401
        captured_rubric.append(the_rubric)
        return _judge_pair([f.key for f in the_rubric])

    with patch("scanner.scripts.run_vision_wave.two_judge", side_effect=_spy_two_judge):
        run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements_path,
            rubric=rubric,
            api_mode="subscription",
        )

    assert len(captured_rubric) == 1
    assert captured_rubric[0] is rubric  # same object passed through
