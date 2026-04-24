"""PIL crop + model-aware bbox denormalisation (research §3.6 + §4).

Ported from ``analysis/homepage/crosscheck/recapture_round5.py::capture_from_fullpage``
and generalised: the source script captured homepage elements only; this
module is area-agnostic and returns a structured :class:`SliceResult` so
callers can record why a crop failed.

Design notes:

- ``MIN_CROP_PX = 50`` — crops smaller than 50x50 are unusable as visual
  evidence; we reject them with a reason string instead of silently saving
  a blurry thumbnail.
- ``PAD_PX = 10`` — every crop is padded 10 px on each side for context.
  The padding is clamped to the image bounds; a bbox that starts at (0, 0)
  does not underflow into negative coordinates.
- The Opus 4.7 long-edge limit is 2576 px; Sonnet 4.6 / Haiku use 1568 px.
  When the original screenshot exceeds the model's long-edge limit the
  Anthropic vision pipeline resizes down before analysis, so bboxes come
  back in the model's resized coordinate space. ``denormalise_bbox`` scales
  them back up to the original image's pixel space.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

MIN_CROP_PX = 50
PAD_PX = 10


@dataclass
class SliceResult:
    """Outcome of a :func:`slice_feature` call.

    ``ok`` is ``True`` only when a PNG was written to disk; otherwise
    ``reason`` describes why (bbox outside bounds, too small, …).
    """

    ok: bool
    path: Path | None = None
    reason: str | None = None


def denormalise_bbox(
    bbox: tuple[float, float, float, float],
    model: str,
    original_w: int,
    original_h: int,
) -> tuple[float, float, float, float]:
    """Scale a bbox from the model's coordinate space to the source image.

    Args:
        bbox: ``(x, y, w, h)`` as returned by the model.
        model: The Claude model name; Opus 4.7 uses a 2576 px long-edge
            limit, Sonnet / Haiku use 1568 px.
        original_w: Width of the source PNG *before* the vision pipeline's
            internal resize.
        original_h: Height of the source PNG.

    Returns:
        The bbox re-scaled to the source image. If the source image's long
        edge is at or below the model's limit, the bbox is returned
        unchanged (scale = 1).
    """
    long_edge_limit = 2576 if model.startswith("claude-opus") else 1568
    actual_long = max(original_w, original_h)
    if actual_long <= long_edge_limit:
        return bbox
    scale = actual_long / long_edge_limit
    return (
        bbox[0] * scale,
        bbox[1] * scale,
        bbox[2] * scale,
        bbox[3] * scale,
    )


def slice_feature(
    fullpage_png: bytes,
    bbox: tuple[float, float, float, float],
    out_path: Path,
) -> SliceResult:
    """Crop a PNG byte-string along ``bbox``, pad, clamp, and save.

    Args:
        fullpage_png: Raw PNG bytes of the full-page screenshot.
        bbox: ``(x, y, w, h)`` in pixel coordinates of the source image;
            use :func:`denormalise_bbox` first if the source came from a
            vision model that resized the input.
        out_path: Target PNG path. Parent dirs are created if missing.

    Returns:
        A :class:`SliceResult` — ``ok=True`` with ``path=out_path`` on
        success, or ``ok=False`` with ``reason`` describing why.
    """
    img = Image.open(BytesIO(fullpage_png))
    fw, fh = img.size
    x, y, w, h = (int(v) for v in bbox)
    x1 = max(0, x - PAD_PX)
    y1 = max(0, y - PAD_PX)
    x2 = min(fw, x + w + PAD_PX)
    y2 = min(fh, y + h + PAD_PX)
    if x2 <= x1 or y2 <= y1:
        return SliceResult(ok=False, reason="bbox outside image bounds")
    cw, ch = x2 - x1, y2 - y1
    if cw < MIN_CROP_PX or ch < MIN_CROP_PX:
        return SliceResult(
            ok=False,
            reason=f"crop too small: {cw}x{ch} (min {MIN_CROP_PX}px)",
        )
    cropped = img.crop((x1, y1, x2, y2))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path, format="PNG", optimize=True)
    return SliceResult(ok=True, path=out_path)


__all__ = [
    "MIN_CROP_PX",
    "PAD_PX",
    "SliceResult",
    "denormalise_bbox",
    "slice_feature",
]
