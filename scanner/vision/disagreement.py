"""Disagreement detection per D-19 + research §3.4 (three-rule consensus check).

Three-rule consensus:

    1. **Presence:** Opus and Sonnet disagree on ``present``. Always flagged
       and no other rules are checked for that feature (the downstream
       workflow takes the single-judge fallback per user-decision-4).
    2. **Confidence gap:** Both agree on ``present`` but their
       ``confidence`` values differ by more than 0.3. Flagged as a soft
       disagreement (both verdicts are written out for review).
    3. **Bounding-box IoU:** Both report ``present == True`` with non-null
       ``evidence_bbox`` but the boxes' intersection-over-union is < 0.5.
       Flagged as a spatial disagreement (crop guidance is ambiguous).

The output is serialisable to JSON (both fields in :class:`Disagreement` are
``dict``) so writing the per-area ``disagreements-{area}.json`` artefact
is trivial.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from scanner.vision.schema import FeatureVerdict


@dataclass
class Disagreement:
    """A single disagreement between Opus and Sonnet on one feature key."""

    feature_key: str
    kind: str  # "presence" | "confidence" | "bbox"
    opus: dict  # FeatureVerdict.model_dump()
    sonnet: dict  # FeatureVerdict.model_dump()


def bbox_iou(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Return intersection-over-union for two (x, y, w, h) boxes.

    Zero-area boxes and fully disjoint boxes both return 0.0; identical
    boxes return 1.0. Ordering of ``a`` / ``b`` is immaterial.
    """
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def find_disagreements(
    opus_results: dict[str, FeatureVerdict],
    sonnet_results: dict[str, FeatureVerdict],
) -> list[Disagreement]:
    """Compare two judge outputs feature-by-feature and flag mismatches.

    Features present in ``opus_results`` but not in ``sonnet_results`` (or
    vice versa) are silently skipped — upstream schema validation (the
    checklist-first prompt) is expected to keep the key sets aligned.
    """
    out: list[Disagreement] = []
    for fkey in opus_results:
        if fkey not in sonnet_results:
            continue
        o, s = opus_results[fkey], sonnet_results[fkey]
        o_d, s_d = o.model_dump(), s.model_dump()
        if o.present != s.present:
            out.append(Disagreement(fkey, "presence", o_d, s_d))
            continue
        if abs(o.confidence - s.confidence) > 0.3:
            out.append(Disagreement(fkey, "confidence", o_d, s_d))
        if (
            o.present
            and s.present
            and o.evidence_bbox is not None
            and s.evidence_bbox is not None
        ):
            if bbox_iou(o.evidence_bbox, s.evidence_bbox) < 0.5:
                out.append(Disagreement(fkey, "bbox", o_d, s_d))
    return out


def write_disagreements(
    disagreements: list[Disagreement],
    path: Path,
) -> None:
    """Serialise a list of Disagreements to ``path`` as indented JSON.

    The parent directory is created if needed. Output shape is a JSON
    array of objects — each object has keys ``feature_key``, ``kind``,
    ``opus``, ``sonnet`` — ready to be consumed by Plan 08's dry-run
    reviewer or by hand review.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(d) for d in disagreements], indent=2),
        encoding="utf-8",
    )


__all__ = [
    "Disagreement",
    "bbox_iou",
    "find_disagreements",
    "write_disagreements",
]
