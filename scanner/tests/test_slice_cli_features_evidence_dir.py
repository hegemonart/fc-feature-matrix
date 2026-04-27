"""Tests for slice CLI features_evidence_dir routing + multi-step iteration.

Plan 02-12 Task 1 — adds an additive override path so per-feature crops can
be written to a canonical analysis/ tree (D-01) instead of scanner/output/.
Also extends ``--step`` to accept ``*`` for multi-step iteration over the
captured-step keys in the per-club result JSON's ``steps`` map (Plan 02-11
shape).

D-21 deviation: only call-site config wiring changes — denormalise_bbox /
slice_feature math is NOT modified.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from scanner.cli import cli
from scanner.config.schema import AreaEntry


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Synthetic repo root that overrides the loader's module-level REPO_ROOT.

    Mirrors the pattern in test_dry_run.py — the CLI subcommands do
    ``from scanner.config.loader import load_area, REPO_ROOT`` inside their
    function bodies, so the loader's module attr must be patched (not just
    the env var) for the CLI to see the tmp root.
    """
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setenv("SCANNER_REPO_ROOT", str(root))
    import scanner.config.loader as loader_mod

    monkeypatch.setattr(loader_mod, "REPO_ROOT", root)
    return root


# ---------------------------------------------------------------------------
# Schema gate
# ---------------------------------------------------------------------------


def test_schema_features_evidence_dir_round_trips() -> None:
    """AreaEntry.features_evidence_dir round-trips a real path string."""
    entry = AreaEntry.model_validate(
        {
            "evidence_dir": "scanner/output/evidence/hospitality/",
            "results_dir": "scanner/output/results/hospitality/",
            "features_evidence_dir": "analysis/hospitality/evidence/features/",
        }
    )
    assert entry.features_evidence_dir == "analysis/hospitality/evidence/features/"


def test_real_areas_json_has_features_evidence_dir_for_hospitality() -> None:
    """scanner/config/areas.json has the canonical analysis/ override for hospitality."""
    from scanner.config.loader import load_areas

    cfg = load_areas()
    hosp = cfg.get("hospitality")
    # Plan 02-12 wires the canonical analysis/ tree per D-01.
    assert hosp.features_evidence_dir == "analysis/hospitality/evidence/features/"


# ---------------------------------------------------------------------------
# Helpers — synthetic mini-area on tmp repo
# ---------------------------------------------------------------------------


def _png_bytes(w: int = 400, h: int = 600) -> bytes:
    img = Image.new("RGB", (w, h), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_synthetic_area(
    repo_root: Path,
    *,
    features_evidence_dir: str | None,
) -> dict:
    """Build a tmp scanner/config/areas.json + per-club result JSON + fullpage PNG.

    Returns the per-club result dict so the test can assert on its shape.
    """
    cfg_dir = repo_root / "scanner" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir_rel = "scanner/output/evidence/hosp/"
    results_dir_rel = "scanner/output/results/hosp/"
    area_entry = {
        "evidence_dir": evidence_dir_rel,
        "results_dir": results_dir_rel,
        "bbox_mode": "css",
    }
    if features_evidence_dir is not None:
        area_entry["features_evidence_dir"] = features_evidence_dir
    (cfg_dir / "areas.json").write_text(
        json.dumps({"hosp": area_entry}), encoding="utf-8"
    )

    fullpage_dir = repo_root / evidence_dir_rel / "fullpage"
    fullpage_dir.mkdir(parents=True, exist_ok=True)
    (fullpage_dir / "syn_landing.png").write_bytes(_png_bytes())

    results_dir = repo_root / results_dir_rel
    results_dir.mkdir(parents=True, exist_ok=True)

    # Plan-02-11-shaped result JSON (single step `landing`) with one present feature.
    result = {
        "club": "syn",
        "area": "hosp",
        "api_mode": "subscription",
        "steps": {
            "landing": {
                "opus": {
                    "feat_a": {
                        "present": True,
                        "step": "landing",
                        "evidence_bbox": [50, 50, 200, 200],
                        "confidence": 0.9,
                        "notes": "synthetic",
                    },
                    "feat_b": {
                        "present": False,
                        "step": "landing",
                        "evidence_bbox": None,
                        "confidence": 0.9,
                        "notes": "absent",
                    },
                },
                "sonnet": {
                    "feat_a": {
                        "present": True,
                        "step": "landing",
                        "evidence_bbox": [55, 55, 200, 200],
                        "confidence": 0.85,
                        "notes": "agree",
                    },
                    "feat_b": {
                        "present": False,
                        "step": "landing",
                        "evidence_bbox": None,
                        "confidence": 0.9,
                        "notes": "agree",
                    },
                },
            }
        },
        "deferred_steps": [],
        "missing_png_steps": [],
    }
    (results_dir / "syn_features.json").write_text(json.dumps(result), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Behavioural tests — features_evidence_dir routing
# ---------------------------------------------------------------------------


def test_slice_writes_to_features_evidence_dir_when_set(isolated_repo: Path) -> None:
    """When features_evidence_dir is set in areas.json, crops go THERE (not evidence_dir/features/)."""
    _build_synthetic_area(
        isolated_repo, features_evidence_dir="analysis/hosp/evidence/features/"
    )
    runner = CliRunner()
    result = runner.invoke(
        cli, ["slice", "--area", "hosp", "--club", "syn", "--step", "landing"]
    )
    assert result.exit_code == 0, result.output
    canonical = isolated_repo / "analysis" / "hosp" / "evidence" / "features"
    legacy = isolated_repo / "scanner" / "output" / "evidence" / "hosp" / "features"
    assert (canonical / "syn_feat_a.png").exists()
    assert not (legacy / "syn_feat_a.png").exists(), (
        "Crop must NOT be written to legacy evidence_dir/features/ when override is set"
    )


def test_slice_falls_back_to_evidence_features_when_unset(isolated_repo: Path) -> None:
    """Phase-1 contract preserved: features_evidence_dir unset -> evidence_dir/features/."""
    _build_synthetic_area(isolated_repo, features_evidence_dir=None)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["slice", "--area", "hosp", "--club", "syn", "--step", "landing"]
    )
    assert result.exit_code == 0, result.output
    legacy = isolated_repo / "scanner" / "output" / "evidence" / "hosp" / "features"
    assert (legacy / "syn_feat_a.png").exists()


def test_slice_skips_absent_features(isolated_repo: Path) -> None:
    """A feature with present=False is not sliced (no PNG written)."""
    _build_synthetic_area(
        isolated_repo, features_evidence_dir="analysis/hosp/evidence/features/"
    )
    runner = CliRunner()
    result = runner.invoke(
        cli, ["slice", "--area", "hosp", "--club", "syn", "--step", "landing"]
    )
    assert result.exit_code == 0, result.output
    canonical = isolated_repo / "analysis" / "hosp" / "evidence" / "features"
    # feat_a present -> sliced; feat_b absent -> skipped.
    assert (canonical / "syn_feat_a.png").exists()
    assert not (canonical / "syn_feat_b.png").exists()


# ---------------------------------------------------------------------------
# Multi-step iteration — `--step '*'`
# ---------------------------------------------------------------------------


def _build_multistep_area(repo_root: Path) -> None:
    """A synthetic area with a 2-step result JSON (one feature per step)."""
    cfg_dir = repo_root / "scanner" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "areas.json").write_text(
        json.dumps(
            {
                "hosp": {
                    "evidence_dir": "scanner/output/evidence/hosp/",
                    "results_dir": "scanner/output/results/hosp/",
                    "features_evidence_dir": "analysis/hosp/evidence/features/",
                    "bbox_mode": "css",
                }
            }
        ),
        encoding="utf-8",
    )
    fullpage_dir = repo_root / "scanner" / "output" / "evidence" / "hosp" / "fullpage"
    fullpage_dir.mkdir(parents=True, exist_ok=True)
    # Filename convention: {club}_{step}.png — matches `slice_cmd` lookup.
    (fullpage_dir / "multi_landing.png").write_bytes(_png_bytes())
    (fullpage_dir / "multi_tier_detail.png").write_bytes(_png_bytes())

    results_dir = repo_root / "scanner" / "output" / "results" / "hosp"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "multi_features.json").write_text(
        json.dumps(
            {
                "club": "multi",
                "area": "hosp",
                "steps": {
                    "landing": {
                        "opus": {
                            "feat_step1": {
                                "present": True,
                                "step": "landing",
                                "evidence_bbox": [10, 10, 200, 200],
                                "confidence": 0.9,
                                "notes": "step1 only",
                            }
                        },
                        "sonnet": {
                            "feat_step1": {
                                "present": True,
                                "step": "landing",
                                "evidence_bbox": [10, 10, 200, 200],
                                "confidence": 0.9,
                                "notes": "agree",
                            }
                        },
                    },
                    "tier_detail": {
                        "opus": {
                            "feat_step2": {
                                "present": True,
                                "step": "tier_detail",
                                "evidence_bbox": [60, 60, 200, 200],
                                "confidence": 0.9,
                                "notes": "step2 only",
                            }
                        },
                        "sonnet": {
                            "feat_step2": {
                                "present": True,
                                "step": "tier_detail",
                                "evidence_bbox": [60, 60, 200, 200],
                                "confidence": 0.9,
                                "notes": "agree",
                            }
                        },
                    },
                },
                "deferred_steps": [],
                "missing_png_steps": [],
            }
        ),
        encoding="utf-8",
    )


def test_slice_step_star_iterates_all_captured_steps(isolated_repo: Path) -> None:
    """`--step '*'` slices both feat_step1 (landing) and feat_step2 (tier_detail)."""
    _build_multistep_area(isolated_repo)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["slice", "--area", "hosp", "--club", "multi", "--step", "*"]
    )
    assert result.exit_code == 0, result.output
    canonical = isolated_repo / "analysis" / "hosp" / "evidence" / "features"
    assert (canonical / "multi_feat_step1.png").exists()
    assert (canonical / "multi_feat_step2.png").exists()


def test_slice_default_step_landing_preserved(isolated_repo: Path) -> None:
    """Phase-1 contract: omitting --step still defaults to `landing` and works."""
    _build_synthetic_area(
        isolated_repo, features_evidence_dir="analysis/hosp/evidence/features/"
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["slice", "--area", "hosp", "--club", "syn"])
    assert result.exit_code == 0, result.output
    canonical = isolated_repo / "analysis" / "hosp" / "evidence" / "features"
    assert (canonical / "syn_feat_a.png").exists()


# ---------------------------------------------------------------------------
# D-21 invariant — slice.py math is NOT modified
# ---------------------------------------------------------------------------


def test_slice_module_denormalise_bbox_unchanged_signature() -> None:
    """Sanity: scanner.vision.slice still exports denormalise_bbox + slice_feature."""
    from scanner.vision import slice as slice_mod

    assert callable(slice_mod.denormalise_bbox)
    assert callable(slice_mod.slice_feature)
    # Smoke-test the math hasn't shifted.
    bbox = (100.0, 100.0, 200.0, 200.0)
    out = slice_mod.denormalise_bbox(bbox, "claude-opus-4-7", 1000, 1000)
    assert out == bbox  # 1000 < 2576 long-edge limit -> unchanged
