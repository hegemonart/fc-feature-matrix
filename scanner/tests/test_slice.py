"""Tests for scanner.vision.slice (PIL crop + denormalise_bbox).

Covers behaviours 1-7 in the plan plus an extra out-of-bounds reject. Uses
the ``sample_fullpage_png`` fixture (400x300 white PNG) from conftest.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from scanner.vision.slice import (
    MIN_CROP_PX,
    PAD_PX,
    SliceResult,
    denormalise_bbox,
    slice_feature,
)


def _img_size(p: Path) -> tuple[int, int]:
    with Image.open(p) as img:
        return img.size


# --- slice_feature happy path + edge cases -------------------------------


def test_slice_feature_happy_path_pads_ten_px(
    sample_fullpage_png: bytes, tmp_path: Path
) -> None:
    """A 100x100 bbox becomes a (100 + 2*PAD_PX) = 120x120 PNG on disk."""
    out = tmp_path / "features" / "xxx_nav.png"
    result = slice_feature(sample_fullpage_png, (50, 50, 100, 100), out)
    assert result.ok is True
    assert result.path == out
    assert out.exists()
    w, h = _img_size(out)
    assert w == 100 + 2 * PAD_PX
    assert h == 100 + 2 * PAD_PX


def test_slice_feature_rejects_tiny_bbox(
    sample_fullpage_png: bytes, tmp_path: Path
) -> None:
    """A 10x10 bbox (even padded to 30x30) is below MIN_CROP_PX and rejected."""
    out = tmp_path / "tiny.png"
    result = slice_feature(sample_fullpage_png, (0, 0, 10, 10), out)
    assert result.ok is False
    assert "too small" in (result.reason or "")
    assert not out.exists()


def test_slice_feature_clamps_oversized_bbox(
    sample_fullpage_png: bytes, tmp_path: Path
) -> None:
    """A 5000x5000 bbox on a 400x300 image clamps to image bounds."""
    out = tmp_path / "big.png"
    result = slice_feature(sample_fullpage_png, (0, 0, 5000, 5000), out)
    assert result.ok is True
    assert out.exists()
    w, h = _img_size(out)
    # Source is 400x300; clamp is inclusive of image bounds.
    assert w <= 400
    assert h <= 300


def test_slice_feature_negative_origin_clamps_then_rejects_if_tiny(
    sample_fullpage_png: bytes, tmp_path: Path
) -> None:
    """bbox (-100, -100, 50, 50) clamps x1/y1 to 0 — final crop too small."""
    out = tmp_path / "neg.png"
    result = slice_feature(sample_fullpage_png, (-100, -100, 50, 50), out)
    # After clamp x1=0, y1=0, x2=min(400, -100+50+10)= -40 -> x2 <= x1 -> outside bounds
    assert result.ok is False
    assert (
        "outside" in (result.reason or "") or "too small" in (result.reason or "")
    )


def test_slice_feature_bbox_entirely_outside_bounds_returns_reason(
    sample_fullpage_png: bytes, tmp_path: Path
) -> None:
    """A bbox fully past the image bounds must return ok=False."""
    out = tmp_path / "past.png"
    result = slice_feature(sample_fullpage_png, (10_000, 10_000, 100, 100), out)
    assert result.ok is False
    assert "outside" in (result.reason or "")


# --- denormalise_bbox math ----------------------------------------------


def test_denormalise_bbox_opus_at_long_edge_limit_is_identity() -> None:
    """Opus long-edge limit is 2576; at-limit is scale=1."""
    bbox = (100.0, 100.0, 200.0, 200.0)
    out = denormalise_bbox(bbox, "claude-opus-4-7", 2576, 2576)
    assert out == bbox


def test_denormalise_bbox_sonnet_above_limit_scales_up() -> None:
    """Sonnet limit is 1568; a 3136-wide source has scale=2."""
    bbox = (100.0, 100.0, 200.0, 200.0)
    out = denormalise_bbox(bbox, "claude-sonnet-4-6", 3136, 3136)
    assert out == (200.0, 200.0, 400.0, 400.0)


def test_denormalise_bbox_under_limit_is_identity() -> None:
    """A small source (1000x500 < 2576) does not get resized; scale=1."""
    bbox = (10.0, 10.0, 20.0, 20.0)
    out = denormalise_bbox(bbox, "claude-opus-4-7", 1000, 500)
    assert out == bbox


def test_denormalise_bbox_haiku_uses_sonnet_limit() -> None:
    """Haiku shares the 1568 px limit with Sonnet (only Opus uses 2576)."""
    bbox = (50.0, 50.0, 100.0, 100.0)
    out = denormalise_bbox(bbox, "claude-haiku-4-5", 3136, 3136)
    assert out == (100.0, 100.0, 200.0, 200.0)


def test_module_exports_required_constants() -> None:
    """Plan acceptance: MIN_CROP_PX == 50 and PAD_PX == 10."""
    assert MIN_CROP_PX == 50
    assert PAD_PX == 10
