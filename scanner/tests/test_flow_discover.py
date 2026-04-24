"""Tests for scanner.flow.discover (Phase-2 stub) — owner Plan 06.

Per D-06, Phase 1 ships only the CLI surface. The stub must raise
NotImplementedError with a Phase-2 marker and a pointer to the documented
Phase-1 alternative (`scanner flow validate`).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scanner.flow.discover import discover_flow


def test_discover_flow_raises_not_implemented(tmp_path: Path):
    with pytest.raises(NotImplementedError) as exc_info:
        discover_flow("https://example.test/", tmp_path / "out.json")
    assert "Phase 2" in str(exc_info.value)


def test_discover_flow_error_points_to_phase_1_alternative(tmp_path: Path):
    with pytest.raises(NotImplementedError) as exc_info:
        discover_flow("https://example.test/", tmp_path / "out.json")
    # The raised message should point users at the CLI validate subcommand
    # so they know how to proceed in Phase 1.
    assert "scanner flow validate" in str(exc_info.value)
