"""Tests for scanner.vision.disagreement (three-rule consensus check).

Covers each rule in research §3.4:

    - bbox_iou returns 1.0 / 0.0 / known-intermediate value
    - presence mismatch is flagged as kind="presence"
    - confidence gap > 0.3 (with matching presence) is flagged as kind="confidence"
    - bbox IoU < 0.5 (with matching presence + non-null bboxes) is flagged as kind="bbox"
    - Agreement on all three rules returns an empty list
    - Features missing from one side are silently skipped
    - write_disagreements produces round-trippable JSON
"""
from __future__ import annotations

import json
from pathlib import Path

from scanner.vision.disagreement import (
    Disagreement,
    bbox_iou,
    find_disagreements,
    write_disagreements,
)
from scanner.vision.schema import FeatureVerdict


def _verdict(
    *,
    present: bool = True,
    confidence: float = 0.8,
    bbox: tuple[float, float, float, float] | None = (0.0, 0.0, 10.0, 10.0),
    notes: str = "",
) -> FeatureVerdict:
    return FeatureVerdict(
        present=present,
        step="landing",
        evidence_bbox=bbox,
        confidence=confidence,
        notes=notes,
    )


# --- bbox_iou math --------------------------------------------------------


def test_bbox_iou_identical_boxes_is_one() -> None:
    assert bbox_iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0


def test_bbox_iou_disjoint_boxes_is_zero() -> None:
    assert bbox_iou((0, 0, 10, 10), (20, 20, 10, 10)) == 0.0


def test_bbox_iou_partial_overlap_is_known_fraction() -> None:
    """Two 10x10 squares offset by (5,5) share a 5x5 = 25 px^2 intersection.

    Union = 100 + 100 - 25 = 175. IoU = 25/175 ≈ 0.1428...
    """
    iou = bbox_iou((0, 0, 10, 10), (5, 5, 10, 10))
    assert abs(iou - (25 / 175)) < 1e-9


def test_bbox_iou_zero_area_box_returns_zero() -> None:
    """Degenerate (zero-area) boxes must not blow up."""
    assert bbox_iou((0, 0, 0, 0), (0, 0, 0, 0)) == 0.0


# --- find_disagreements rules -------------------------------------------


def test_presence_mismatch_is_flagged() -> None:
    """Opus says present, Sonnet says absent — flag as presence."""
    opus = {"f": _verdict(present=True)}
    sonnet = {"f": _verdict(present=False, bbox=None)}
    d = find_disagreements(opus, sonnet)
    assert len(d) == 1
    assert d[0].kind == "presence"
    assert d[0].feature_key == "f"
    assert d[0].opus["present"] is True
    assert d[0].sonnet["present"] is False


def test_confidence_gap_flagged_when_present_matches() -> None:
    """Both present=True but Δconfidence > 0.3 — flag as confidence."""
    opus = {"f": _verdict(confidence=0.9)}
    sonnet = {"f": _verdict(confidence=0.4)}  # gap 0.5 > 0.3
    d = find_disagreements(opus, sonnet)
    kinds = [x.kind for x in d]
    assert "confidence" in kinds


def test_bbox_iou_low_flagged() -> None:
    """Both present with non-null bboxes but IoU < 0.5 — flag as bbox."""
    opus = {"f": _verdict(bbox=(0, 0, 10, 10))}
    sonnet = {"f": _verdict(bbox=(20, 20, 10, 10))}  # IoU = 0.0
    d = find_disagreements(opus, sonnet)
    kinds = [x.kind for x in d]
    assert "bbox" in kinds


def test_full_agreement_returns_empty_list() -> None:
    """If Opus and Sonnet agree on all three rules, no disagreements emit."""
    opus = {"f": _verdict(confidence=0.8, bbox=(0, 0, 10, 10))}
    sonnet = {"f": _verdict(confidence=0.85, bbox=(0, 0, 10, 10))}
    assert find_disagreements(opus, sonnet) == []


def test_missing_key_on_sonnet_is_skipped() -> None:
    """Features in Opus but not in Sonnet are silently skipped."""
    opus = {"f": _verdict(), "g": _verdict()}
    sonnet = {"f": _verdict()}
    d = find_disagreements(opus, sonnet)
    assert d == []  # no disagreement for 'g' because it's missing


# --- write_disagreements serialisation ----------------------------------


def test_write_disagreements_round_trip(tmp_path: Path) -> None:
    """JSON written by write_disagreements parses back to a list of dicts."""
    disagreements = [
        Disagreement(
            feature_key="f",
            kind="presence",
            opus={
                "present": True,
                "step": "landing",
                "evidence_bbox": None,
                "confidence": 0.9,
                "notes": "",
            },
            sonnet={
                "present": False,
                "step": "landing",
                "evidence_bbox": None,
                "confidence": 0.7,
                "notes": "",
            },
        )
    ]
    out_path = tmp_path / "output" / "disagreements-hospitality.json"
    write_disagreements(disagreements, out_path)

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["feature_key"] == "f"
    assert data[0]["kind"] == "presence"
    assert data[0]["opus"]["present"] is True
    assert data[0]["sonnet"]["present"] is False


def test_write_disagreements_creates_parent_dir(tmp_path: Path) -> None:
    """write_disagreements must mkdir -p the parent dir."""
    out_path = tmp_path / "a" / "b" / "c" / "dis.json"
    write_disagreements([], out_path)
    assert out_path.exists()
    assert json.loads(out_path.read_text(encoding="utf-8")) == []
