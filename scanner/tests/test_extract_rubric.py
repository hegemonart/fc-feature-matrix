"""Tests for scanner.scripts.extract_rubric (Plan 02-11 Task 1).

Three layers:

- Pure parsing: ``extract_rubric_to_json`` regex-parses ``feat(...)`` calls
  from a fixture features.ts and emits a schema-valid JSON.
- Schema validation: emitted features round-trip through
  ``scanner.vision.schema.FeatureDef`` without error.
- CLI wiring: invoking the script as a module exits 0 and writes the
  expected JSON to disk.

Test 3 (real-file 55-feature count) is marked ``integration`` so it skips
cleanly when the analysis/ tree is unavailable (e.g. wheel-only test runs).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixture content — 3-feature mini features.ts
# ---------------------------------------------------------------------------

FIXTURE_TS = """\
import type { Feature, CategoryId, TierId, PresenceStatus } from '../types';

function feat(
  id: string,
  key: string,
  name: string,
  desc: string,
  cat: CategoryId,
  tier: TierId,
  weightYes: number,
  weightNo: number,
): Feature {
  return { id, key, name, desc, cat, tier, weightYes, weightNo, weight: weightYes, presence: {} };
}

export const FEATURES: Feature[] = [
  feat('HP01', 'package_tier_list', 'Package Tier List',
    'Landing page lists all packages with distinguishing copy in one view',
    'package_discovery', 'A', 1, -3),
  feat('HP02', 'per_tier_landing_page', 'Per-Tier Landing Page',
    'Clicking a tier opens its own description landing page',
    'package_discovery', 'A', 1, -3),
  feat('HP03', 'tier_comparison_table', 'Tier Comparison Table',
    'Side-by-side feature matrix across tiers on a single page',
    'package_discovery', 'C', 5, -2),
];
"""


# ---------------------------------------------------------------------------
# Test 1 — basic parse: 3 features in order
# ---------------------------------------------------------------------------


def test_extract_three_feature_fixture(tmp_path: Path) -> None:
    """Parses a 3-feature fixture and writes JSON with 3 features in order."""
    from scanner.scripts.extract_rubric import extract_rubric_to_json

    ts = tmp_path / "features.ts"
    ts.write_text(FIXTURE_TS, encoding="utf-8")
    out = tmp_path / "features.json"

    count = extract_rubric_to_json(ts, out)
    assert count == 3

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "features" in data
    assert len(data["features"]) == 3
    keys = [f["key"] for f in data["features"]]
    assert keys == ["package_tier_list", "per_tier_landing_page", "tier_comparison_table"]


# ---------------------------------------------------------------------------
# Test 2 — required fields present
# ---------------------------------------------------------------------------


def test_each_feature_has_required_fields(tmp_path: Path) -> None:
    """Each emitted feature has key, name, yes_criterion fields."""
    from scanner.scripts.extract_rubric import extract_rubric_to_json

    ts = tmp_path / "features.ts"
    ts.write_text(FIXTURE_TS, encoding="utf-8")
    out = tmp_path / "features.json"

    extract_rubric_to_json(ts, out)
    data = json.loads(out.read_text(encoding="utf-8"))

    for f in data["features"]:
        assert "key" in f
        assert "name" in f
        assert "yes_criterion" in f
        assert isinstance(f["key"], str)
        assert isinstance(f["name"], str)
        assert isinstance(f["yes_criterion"], str)

    # yes_criterion is the literal description text.
    first = data["features"][0]
    assert first["yes_criterion"] == (
        "Landing page lists all packages with distinguishing copy in one view"
    )


# ---------------------------------------------------------------------------
# Test 3 — real-file produces 55 features (integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_real_features_ts_yields_55_entries(tmp_path: Path) -> None:
    """Running against the real analysis/hospitality/features.ts → 55 features."""
    from scanner.scripts.extract_rubric import extract_rubric_to_json

    repo_root = Path(__file__).resolve().parents[2]
    ts = repo_root / "analysis" / "hospitality" / "features.ts"
    if not ts.exists():
        pytest.skip(f"Real features.ts not present at {ts}")

    out = tmp_path / "features.json"
    count = extract_rubric_to_json(ts, out)
    assert count == 55

    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["features"]) == 55


# ---------------------------------------------------------------------------
# Test 4 — schema-validates against FeatureDef
# ---------------------------------------------------------------------------


def test_output_validates_against_feature_def(tmp_path: Path) -> None:
    """Emitted features parse as ``FeatureDef`` without raising."""
    from scanner.scripts.extract_rubric import extract_rubric_to_json
    from scanner.vision.schema import FeatureDef

    ts = tmp_path / "features.ts"
    ts.write_text(FIXTURE_TS, encoding="utf-8")
    out = tmp_path / "features.json"
    extract_rubric_to_json(ts, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    parsed = [FeatureDef(**f) for f in data["features"]]
    assert len(parsed) == 3
    assert parsed[0].key == "package_tier_list"
    assert parsed[0].name == "Package Tier List"
    assert "Landing page lists" in parsed[0].yes_criterion


# ---------------------------------------------------------------------------
# Test 5 — CLI wiring (run as module)
# ---------------------------------------------------------------------------


def test_cli_module_invocation(tmp_path: Path) -> None:
    """``python -m scanner.scripts.extract_rubric ...`` exits 0 and writes JSON."""
    ts = tmp_path / "features.ts"
    ts.write_text(FIXTURE_TS, encoding="utf-8")
    out = tmp_path / "features.json"

    repo_root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.scripts.extract_rubric",
            "--features-ts",
            str(ts),
            "--out",
            str(out),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["features"]) == 3


# ---------------------------------------------------------------------------
# Test 6 — output JSON is gitignored
# ---------------------------------------------------------------------------


def test_features_json_is_gitignored() -> None:
    """`analysis/hospitality/features.json` matches a gitignore rule.

    Verified via ``git check-ignore`` exit code 0 (path is ignored).
    """
    repo_root = Path(__file__).resolve().parents[2]
    target = "analysis/hospitality/features.json"
    proc = subprocess.run(
        ["git", "check-ignore", target],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"{target} is NOT gitignored — git check-ignore "
        f"exit={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
