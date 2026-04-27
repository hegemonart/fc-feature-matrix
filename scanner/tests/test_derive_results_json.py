"""Tests for scanner/scripts/derive_results_json.py — Plan 02-12 Task 2.

The script reads a Plan-02-11-shaped per-club result JSON
(``{steps: {step: {opus, sonnet}}}``) and emits a flat per-club presence map
(``{features: {key: bool}}``) at the canonical analysis/ path, applying the
disagreement resolution policy:

- Opus and Sonnet agree on presence -> use Opus value.
- Disagree -> presence = False AND feature key tracked in ``disputed_features``.

Multi-step OR-flattening: a feature counted as present if ANY captured step
resolves it as present (after applying the agreement policy per step).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures — synthetic per-club result JSONs
# ---------------------------------------------------------------------------


def _verdict(present: bool, *, bbox=None, conf=0.9, notes="syn") -> dict:
    return {
        "present": present,
        "step": "synthetic",
        "evidence_bbox": bbox,
        "confidence": conf,
        "notes": notes,
    }


def _per_club_single_step(features_agreement: dict[str, tuple[bool, bool]]) -> dict:
    """Build a 1-step per-club result.

    features_agreement: ``{feat_key: (opus_present, sonnet_present)}``.
    """
    opus = {k: _verdict(o) for k, (o, s) in features_agreement.items()}
    sonnet = {k: _verdict(s) for k, (o, s) in features_agreement.items()}
    return {
        "club": "syn",
        "area": "hospitality",
        "api_mode": "subscription",
        "steps": {"landing": {"opus": opus, "sonnet": sonnet}},
        "deferred_steps": [],
        "missing_png_steps": [],
    }


# ---------------------------------------------------------------------------
# Test 1 — agree-present uses Opus value (true)
# ---------------------------------------------------------------------------


def test_agree_present_resolves_to_true(tmp_path: Path) -> None:
    """Both judges agree present -> resolved True; not in disputed list."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = _per_club_single_step(
        {"a": (True, True), "b": (False, False), "c": (True, True)}
    )
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    rubric = ["a", "b", "c"]
    derive_results_json(src, out, rubric_keys=rubric, club_name="Synthetic FC")

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["features"]["a"] is True
    assert data["features"]["b"] is False
    assert data["features"]["c"] is True
    assert data["disputed_features"] == []


# ---------------------------------------------------------------------------
# Test 2 — disagreement -> False + disputed
# ---------------------------------------------------------------------------


def test_disagreement_resolves_to_false_and_marks_disputed(tmp_path: Path) -> None:
    """Opus says present, Sonnet absent -> resolved False, key in disputed list."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = _per_club_single_step(
        {"agreed": (True, True), "disputed_a": (True, False), "disputed_b": (False, True)}
    )
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    derive_results_json(
        src, out, rubric_keys=["agreed", "disputed_a", "disputed_b"], club_name="X"
    )

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["features"]["agreed"] is True
    assert data["features"]["disputed_a"] is False
    assert data["features"]["disputed_b"] is False
    assert sorted(data["disputed_features"]) == ["disputed_a", "disputed_b"]


# ---------------------------------------------------------------------------
# Test 3 — multi-step OR flattening
# ---------------------------------------------------------------------------


def test_multi_step_or_flattening(tmp_path: Path) -> None:
    """Feature present in step1 (agree), absent in step2 (agree) -> True (OR)."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = {
        "club": "syn",
        "area": "hospitality",
        "steps": {
            "landing": {
                "opus": {"x": _verdict(True), "y": _verdict(False)},
                "sonnet": {"x": _verdict(True), "y": _verdict(False)},
            },
            "tier_detail": {
                "opus": {"x": _verdict(False), "y": _verdict(True)},
                "sonnet": {"x": _verdict(False), "y": _verdict(True)},
            },
        },
        "deferred_steps": [],
        "missing_png_steps": [],
    }
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    derive_results_json(src, out, rubric_keys=["x", "y"], club_name="X")

    data = json.loads(out.read_text(encoding="utf-8"))
    # x present in landing, absent in tier_detail -> OR -> True
    assert data["features"]["x"] is True
    # y absent in landing, present in tier_detail -> OR -> True
    assert data["features"]["y"] is True


# ---------------------------------------------------------------------------
# Test 4 — feature absent from ALL captured steps -> False + skipped
# ---------------------------------------------------------------------------


def test_feature_absent_from_all_captured_steps_is_skipped(tmp_path: Path) -> None:
    """A rubric feature with NO verdict in any step -> False AND in skipped list."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = {
        "club": "syn",
        "area": "hospitality",
        "steps": {
            "landing": {
                "opus": {"x": _verdict(True)},
                "sonnet": {"x": _verdict(True)},
            }
        },
        "deferred_steps": [],
        "missing_png_steps": [],
    }
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    # rubric has 'x' (captured) AND 'y' (never captured -> skipped)
    derive_results_json(src, out, rubric_keys=["x", "y"], club_name="X")

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["features"]["x"] is True
    assert data["features"]["y"] is False
    assert "y" in data["skipped_features"]
    assert "x" not in data["skipped_features"]


# ---------------------------------------------------------------------------
# Test 5 — emitted shape matches homepage results-JSON pattern
# ---------------------------------------------------------------------------


def test_emitted_shape_includes_required_keys(tmp_path: Path) -> None:
    """Output JSON has the canonical fields Plan 02-13 will consume."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = _per_club_single_step({"a": (True, True)})
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    derive_results_json(src, out, rubric_keys=["a"], club_name="Synthetic FC")
    data = json.loads(out.read_text(encoding="utf-8"))

    for key in (
        "club_id",
        "club_name",
        "area",
        "features",
        "disputed_features",
        "skipped_features",
        "captured_steps",
        "judge_agreement_rate",
        "generated_at",
    ):
        assert key in data, f"Output JSON missing required field: {key!r}"
    assert data["area"] == "hospitality"
    assert data["club_id"] == "syn"
    assert data["club_name"] == "Synthetic FC"
    assert data["captured_steps"] == ["landing"]


# ---------------------------------------------------------------------------
# Test 6 — judge_agreement_rate computation
# ---------------------------------------------------------------------------


def test_judge_agreement_rate_is_correct(tmp_path: Path) -> None:
    """4 features: 3 agree + 1 disagree -> agreement = 0.75."""
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = _per_club_single_step(
        {
            "p": (True, True),
            "q": (False, False),
            "r": (True, True),
            "s": (True, False),  # disputed
        }
    )
    src = tmp_path / "syn_features.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "syn.json"

    derive_results_json(src, out, rubric_keys=["p", "q", "r", "s"], club_name="X")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["judge_agreement_rate"] == 0.75


# ---------------------------------------------------------------------------
# Test 7 — CLI smoke (Click invocation)
# ---------------------------------------------------------------------------


def test_cli_invocation_writes_output(tmp_path: Path) -> None:
    """`python -m scanner.scripts.derive_results_json` end-to-end."""
    from click.testing import CliRunner

    from scanner.scripts.derive_results_json import main

    per_club = _per_club_single_step({"a": (True, True), "b": (False, False)})
    src = tmp_path / "src.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "out.json"
    rubric_path = tmp_path / "rubric.json"
    rubric_path.write_text(
        json.dumps(
            {
                "features": [
                    {"key": "a", "name": "A", "yes_criterion": "x"},
                    {"key": "b", "name": "B", "yes_criterion": "y"},
                ]
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--per-club-results",
            str(src),
            "--rubric",
            str(rubric_path),
            "--out",
            str(out),
            "--club-name",
            "Synthetic FC",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["club_name"] == "Synthetic FC"
    assert data["features"] == {"a": True, "b": False}


# ---------------------------------------------------------------------------
# Test 8 — chelsea-style: skipped step in deferred_steps does NOT contribute
# ---------------------------------------------------------------------------


def test_deferred_steps_do_not_contribute_to_presence(tmp_path: Path) -> None:
    """A step listed in deferred_steps but absent from `steps` map yields no verdicts.

    Captured steps drive presence; deferred steps are recorded for audit.
    """
    from scanner.scripts.derive_results_json import derive_results_json

    per_club = {
        "club": "chelsea",
        "area": "hospitality",
        "steps": {
            "landing-shot": {
                "opus": {"x": _verdict(True)},
                "sonnet": {"x": _verdict(True)},
            }
        },
        "deferred_steps": [
            {"step_name": "match-selector", "status": "skipped", "reason": "requires-paid-account"}
        ],
        "missing_png_steps": [],
    }
    src = tmp_path / "src.json"
    src.write_text(json.dumps(per_club), encoding="utf-8")
    out = tmp_path / "out.json"

    derive_results_json(src, out, rubric_keys=["x", "y"], club_name="Chelsea")
    data = json.loads(out.read_text(encoding="utf-8"))

    # captured_steps reflects only the steps map (deferred steps not included)
    assert data["captured_steps"] == ["landing-shot"]
    # y not in any captured step -> skipped
    assert "y" in data["skipped_features"]
