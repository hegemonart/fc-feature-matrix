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


def test_areas_json_hospitality_entry_matches_user_decision_1() -> None:
    """areas.json hospitality entry uses scanner/output/evidence/ (D-25 + user decision 1).

    Phase 1 seeded this entry with null rubric_path/features_ts and
    status='pending' (D-25). Phase 2 plan 02-03 (HOSP-02) unlocks it:
    rubric_path → analysis/hospitality/HOSPITALITY-FLOW.md,
    features_ts → analysis/hospitality/features.ts,
    status → 'pilot' (5-club pilot per 02-CONTEXT).

    The evidence_dir / results_dir routing is the stable invariant —
    those paths never change between Phase 1 seed and Phase 2
    activation (user decision 1).
    """
    areas_json = SCANNER_DIR / "config" / "areas.json"
    data = json.loads(areas_json.read_text(encoding="utf-8"))
    assert "hospitality" in data, "areas.json must declare the hospitality area."
    entry = data["hospitality"]

    # Stable invariants: I/O routing under scanner/output/ (user decision 1).
    assert entry["evidence_dir"] == "scanner/output/evidence/hospitality/", (
        f"evidence_dir must route to scanner/output/ (user decision 1), got {entry['evidence_dir']!r}"
    )
    assert entry["results_dir"] == "scanner/output/results/hospitality/", (
        f"results_dir must route to scanner/output/, got {entry['results_dir']!r}"
    )

    # Phase 2 plan 02-03: hospitality entry is populated, not a null seed.
    assert entry["rubric_path"] == "analysis/hospitality/HOSPITALITY-FLOW.md", (
        f"rubric_path must point at Phase 2 rubric, got {entry['rubric_path']!r}"
    )
    assert entry["features_ts"] == "analysis/hospitality/features.ts", (
        f"features_ts must point at Phase 2 features module, got {entry['features_ts']!r}"
    )
    # status advances pending → pilot for the 5-club front-half.
    # Valid literals per scanner/config/schema.py: pending | pilot | full | deprecated.
    assert entry["status"] == "pilot", (
        f"status must be 'pilot' for Phase 2 front-half, got {entry['status']!r}"
    )
