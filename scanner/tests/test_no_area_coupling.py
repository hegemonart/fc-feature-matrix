"""FLOW-02 invariant: scanner/ must not import or reference analysis.hospitality.

This test implements D-04 / FLOW-02: the scanner package is area-agnostic.
Every subcommand reads ``scanner/config/areas.json`` for its paths
instead of hard-coding ``analysis/hospitality/`` anywhere in the
package. A regression here would re-couple scanner to the homepage
tree and break Phase 3-8 area additions.

The second test asserts the Phase-1 ``areas.json`` seed matches user
decision 1 + D-25: empty hospitality entry writing to
``scanner/output/evidence/hospitality/``, not ``analysis/``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# Walk up from this test file: scanner/tests/test_no_area_coupling.py -> repo.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER_DIR = REPO_ROOT / "scanner"

# Substrings forbidden in any .py file under scanner/ (excluding the
# tests directory itself — tests may legitimately assert *about* these
# strings). The config/areas.json file is skipped by extension filter
# (only .py files are scanned). The README.md is also excluded because
# it documents the scope boundary to human readers.
FORBIDDEN_SUBSTRINGS = (
    "analysis.hospitality",
    "analysis/hospitality",
    "from analysis.hospitality",
    "import analysis.hospitality",
)

# Directories under scanner/ that are allowed to mention the banned
# strings (tests, __pycache__, the venv). Relative to SCANNER_DIR.
ALLOWED_SUBPATHS = ("tests", "__pycache__", ".venv")


def _iter_scanner_py_files() -> list[Path]:
    files: list[Path] = []
    for p in SCANNER_DIR.rglob("*.py"):
        rel = p.relative_to(SCANNER_DIR)
        if any(part in ALLOWED_SUBPATHS for part in rel.parts):
            continue
        files.append(p)
    return files


def test_no_area_coupling_in_scanner_package() -> None:
    """Fail if any scanner/*.py file imports or references analysis.hospitality."""
    offenders: list[tuple[Path, str]] = []
    for py_file in _iter_scanner_py_files():
        text = py_file.read_text(encoding="utf-8")
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle in text:
                offenders.append((py_file, needle))
    if offenders:
        msg_lines = [
            "scanner package references area-specific analysis.hospitality:",
        ]
        for path, needle in offenders:
            rel = path.relative_to(REPO_ROOT)
            msg_lines.append(f"  - {rel}: contains {needle!r}")
        pytest.fail("\n".join(msg_lines))


def test_phase1_areas_json_seed_matches_user_decision_1() -> None:
    """areas.json hospitality entry uses scanner/output/evidence/ (D-25 + user decision 1)."""
    areas_json = SCANNER_DIR / "config" / "areas.json"
    data = json.loads(areas_json.read_text(encoding="utf-8"))
    assert "hospitality" in data, "Phase 1 seed must declare the hospitality area."
    entry = data["hospitality"]
    assert entry["evidence_dir"] == "scanner/output/evidence/hospitality/", (
        f"evidence_dir must route to scanner/output/ (user decision 1), got {entry['evidence_dir']!r}"
    )
    # D-25: Phase 1 does not create analysis/hospitality/ — the rubric
    # and features.ts paths stay null until Phase 2's HOSP-02 plan.
    assert entry["rubric_path"] is None, (
        f"rubric_path must be null in Phase 1 seed (D-25), got {entry['rubric_path']!r}"
    )
    assert entry["features_ts"] is None, (
        f"features_ts must be null in Phase 1 seed (D-25), got {entry['features_ts']!r}"
    )
    # status=pending lets loader warn-not-fail on missing paths (research §6.4).
    assert entry["status"] == "pending"
