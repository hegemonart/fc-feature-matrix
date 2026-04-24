"""Tests for scanner.config.schema — owner Plan 02.

Validates AreaEntry / AreasConfig. The top-level config is a dict keyed by
area name (hospitality, ticket, sponsorship, ...), implemented via Pydantic
`RootModel[dict[str, AreaEntry]]` so Phase 2-8 additions are zero-migration.

Per D-10, D-25 (Phase-1 seed = empty hospitality entry), FLOW-02.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from scanner.config.schema import AreaEntry, AreasConfig


# --- Phase-1 empty-hospitality seed (D-25) -------------------------------


def test_phase1_empty_hospitality_seed_parses():
    data = {
        "hospitality": {
            "evidence_dir": "scanner/output/evidence/hospitality/",
            "results_dir": "scanner/output/results/hospitality/",
            "rubric_path": None,
            "features_ts": None,
        }
    }
    cfg = AreasConfig.model_validate(data)
    entry = cfg.get("hospitality")
    assert entry.evidence_dir == "scanner/output/evidence/hospitality/"
    assert entry.rubric_path is None
    assert entry.features_ts is None
    # Default status per D-10
    assert entry.status == "pending"


# --- Phase-2 richer hospitality variant ---------------------------------


def test_phase2_full_hospitality_entry_parses():
    data = {
        "hospitality": {
            "evidence_dir": "scanner/output/evidence/hospitality/",
            "results_dir": "scanner/output/results/hospitality/",
            "rubric_path": "analysis/hospitality/HOSPITALITY.md",
            "features_ts": "analysis/hospitality/features.ts",
            "flow_maps_dir": "analysis/hospitality/flow-maps/",
            "status": "pilot",
        }
    }
    cfg = AreasConfig.model_validate(data)
    entry = cfg.get("hospitality")
    assert entry.status == "pilot"
    assert entry.features_ts == "analysis/hospitality/features.ts"
    assert entry.flow_maps_dir == "analysis/hospitality/flow-maps/"


# --- Multi-area (Phase 3+ forward-compat) --------------------------------


def test_multi_area_rootmodel_dict_shape():
    data = {
        "hospitality": {
            "evidence_dir": "scanner/output/evidence/hospitality/",
            "results_dir": "scanner/output/results/hospitality/",
        },
        "ticket": {
            "evidence_dir": "scanner/output/evidence/ticket/",
            "results_dir": "scanner/output/results/ticket/",
            "status": "full",
        },
    }
    cfg = AreasConfig.model_validate(data)
    assert set(cfg.root.keys()) == {"hospitality", "ticket"}
    assert cfg.get("ticket").status == "full"


# --- Error cases ---------------------------------------------------------


def test_missing_evidence_dir_raises():
    with pytest.raises(ValidationError):
        AreaEntry.model_validate(
            {"results_dir": "scanner/output/results/hospitality/"}
        )


def test_missing_results_dir_raises():
    with pytest.raises(ValidationError):
        AreaEntry.model_validate(
            {"evidence_dir": "scanner/output/evidence/hospitality/"}
        )


def test_bogus_status_raises():
    with pytest.raises(ValidationError):
        AreaEntry.model_validate(
            {
                "evidence_dir": "e/",
                "results_dir": "r/",
                "status": "bogus",
            }
        )


def test_status_defaults_to_pending():
    entry = AreaEntry.model_validate({"evidence_dir": "e/", "results_dir": "r/"})
    assert entry.status == "pending"


def test_optional_paths_default_to_none():
    entry = AreaEntry.model_validate({"evidence_dir": "e/", "results_dir": "r/"})
    assert entry.rubric_path is None
    assert entry.features_ts is None
    assert entry.flow_maps_dir is None


def test_get_unknown_area_raises_keyerror():
    cfg = AreasConfig.model_validate(
        {
            "hospitality": {
                "evidence_dir": "e/",
                "results_dir": "r/",
            }
        }
    )
    with pytest.raises(KeyError) as exc:
        cfg.get("unknown_area")
    assert "unknown_area" in str(exc.value)
    assert "hospitality" in str(exc.value)  # helpful "known" list


def test_all_status_literals_accepted():
    for status in ("pending", "pilot", "full", "deprecated"):
        entry = AreaEntry.model_validate(
            {"evidence_dir": "e/", "results_dir": "r/", "status": status}
        )
        assert entry.status == status
