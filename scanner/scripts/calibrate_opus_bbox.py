"""One-shot Opus bbox calibration harness — Plan 02-08 Task 3.

Purpose
-------
Determine which coordinate space the Opus 4.7 vision backend returns
bboxes in:

- "css"     — Opus returns bboxes in the model-resized coordinate space
              (the existing :func:`scanner.vision.slice.denormalise_bbox`
              scaling is correct).
- "native"  — Opus returns bboxes in the source-image's device-pixel
              space already (denormalisation must be SKIPPED to avoid
              off-image crops).

Approach
--------
1. Load a known full-page screenshot (default: the MCFC hospitality
   landing PNG already on disk).
2. Send a single Opus vision query asking for the bbox of "the page
   header logo or wordmark" — a feature whose ground-truth bbox is
   visually-knowable from the source image (top band, ~y=0..800 in CSS
   pixels for the MCFC site).
3. Compute two diff scores:
     css_diff  — IoU(denormalise_bbox(observed), ground_truth)
     native_diff — IoU(observed, ground_truth)  # skip denormalise
4. Decide:
     decided_mode = "native" iff (native_diff - css_diff) >= 0.20 IoU
     decided_mode = "css" otherwise (default-safe fallback)
5. Write the result + reasoning trail to
   ``scanner/output/opus-bbox-calibration.json`` for reproducibility.

The script is best-effort: an SDK / network failure writes a partial
artifact with ``error`` populated and ``decided_mode = "css"`` (safe
default). Exit code is always 0 — calibration is observation, not test.

D-21 deviation note (folded into the artifact's ``decision_notes``):
This harness is the first half of a config-driven gate; the slice CLI
reads ``areas.json[area].bbox_mode`` and skips ``denormalise_bbox`` when
it equals "native". The denormalise math itself is left untouched.

Usage
-----
::

    python -m scanner.scripts.calibrate_opus_bbox \\
        --image scanner/output/evidence/hospitality/fullpage/mancity_landing.png \\
        --ground-truth-bbox 0,0,2880,800

The ``--ground-truth-bbox`` argument is "x1,y1,x2,y2" in CSS pixels of
the source image (NOT the Opus-resized space).
"""
from __future__ import annotations

import datetime
import json
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import click
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


@dataclass
class Bbox:
    """A bounding box in (x1, y1, x2, y2) pixel coordinates of some space."""

    x1: float
    y1: float
    x2: float
    y2: float

    def as_xywh(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1)

    def area(self) -> float:
        w = max(0.0, self.x2 - self.x1)
        h = max(0.0, self.y2 - self.y1)
        return w * h


def iou(a: Bbox, b: Bbox) -> float:
    """Standard IoU over (x1,y1,x2,y2) bboxes. Returns 0.0 when disjoint."""
    ix1 = max(a.x1, b.x1)
    iy1 = max(a.y1, b.y1)
    ix2 = min(a.x2, b.x2)
    iy2 = min(a.y2, b.y2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = a.area() + b.area() - inter
    return inter / union if union > 0 else 0.0


def parse_bbox_arg(s: str) -> Bbox:
    """Parse 'x1,y1,x2,y2' from a CLI string."""
    parts = [float(p.strip()) for p in s.split(",")]
    if len(parts) != 4:
        raise click.BadParameter(
            f"bbox must be 4 comma-separated numbers, got {s!r}"
        )
    return Bbox(*parts)


def decide_mode(
    observed: Bbox,
    ground_truth: Bbox,
    *,
    model: str,
    image_w: int,
    image_h: int,
    margin: float = 0.20,
) -> tuple[str, float, float]:
    """Compare CSS-mode IoU vs native-mode IoU and decide.

    Returns ``(decided_mode, css_iou, native_iou)``. Default-safe fallback
    is ``"css"``: only switch to ``"native"`` when the native-mode IoU
    beats the css-mode IoU by ``margin`` or more.
    """
    from scanner.vision.slice import denormalise_bbox

    obs_xywh = observed.as_xywh()
    css_scaled = denormalise_bbox(obs_xywh, model, image_w, image_h)
    css_bbox = Bbox(
        css_scaled[0],
        css_scaled[1],
        css_scaled[0] + css_scaled[2],
        css_scaled[1] + css_scaled[3],
    )
    css_iou = iou(css_bbox, ground_truth)
    native_iou = iou(observed, ground_truth)
    decided = "native" if (native_iou - css_iou) >= margin else "css"
    return decided, css_iou, native_iou


# ---------------------------------------------------------------------------
# Vision call
# ---------------------------------------------------------------------------


_BBOX_PROMPT_TEMPLATE = (
    "Identify the bounding box of {feature} in this image. "
    "Return ONLY a JSON object on a single line of the form "
    '{{"bbox": [x1, y1, x2, y2]}} where the coordinates are in pixels '
    "of the image as you see it. Do not include any other text or "
    "explanation."
)


_BBOX_RE = re.compile(
    r'"bbox"\s*:\s*\[\s*'
    r"([\-\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\-\d.]+)"
    r"\s*\]"
)


def parse_opus_bbox(reply: str) -> Bbox | None:
    """Extract a bbox from an Opus reply. Returns None if nothing matches."""
    m = _BBOX_RE.search(reply)
    if m is None:
        return None
    return Bbox(*(float(x) for x in m.groups()))


def query_opus_for_bbox(
    image_path: Path,
    feature_text: str,
    *,
    api_mode: str,
    model: str,
) -> tuple[Bbox | None, str]:
    """Send a single Opus vision request asking for the feature bbox.

    Returns ``(parsed_bbox, raw_reply)``. Either may be empty / None on
    failure — callers write the failure into the artifact and bail.
    """
    import asyncio
    import base64

    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    prompt_text = _BBOX_PROMPT_TEMPLATE.format(feature=feature_text)
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_b64,
            },
        },
        {"type": "text", "text": prompt_text},
    ]

    if api_mode == "subscription":
        from scanner.vision.client_subscription import (
            SubscriptionVisionClient,
            _build_streaming_prompt,
        )

        client = SubscriptionVisionClient(model)
        text = asyncio.run(client._collect_text(content=content))
    elif api_mode == "api-key":
        # Future expansion — not used in Plan 02-08 (D-28 default subscription).
        raise click.ClickException(
            "api-key mode not implemented for the calibration harness; "
            "use --api-mode subscription (D-28 default)."
        )
    else:
        raise click.ClickException(f"Unknown api-mode: {api_mode!r}")

    return parse_opus_bbox(text), text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


_DECISION_NOTES = (
    "D-21 deviation note: bbox_mode is read at the slice CLI call-site, "
    "not by modifying denormalise_bbox internals. Approved per Plan 02-08 "
    "deviation entry; denormalise_bbox math is untouched."
)


@click.command()
@click.option(
    "--image",
    "image_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("scanner/output/evidence/hospitality/fullpage/mancity_landing.png"),
    show_default=True,
    help="Path to a full-page screenshot for calibration.",
)
@click.option(
    "--ground-truth-bbox",
    "ground_truth",
    type=str,
    default="0,0,2880,800",
    show_default=True,
    help="Manually-known bbox of the target feature, x1,y1,x2,y2 in source-image pixels.",
)
@click.option(
    "--prompt-feature",
    "prompt_feature",
    type=str,
    default="the page header logo or wordmark",
    show_default=True,
    help="Feature description sent to Opus.",
)
@click.option(
    "--api-mode",
    type=click.Choice(["subscription", "api-key"]),
    default="subscription",
    show_default=True,
    help="Vision backend (D-28 default: subscription).",
)
@click.option(
    "--model",
    default="claude-opus-4-7",
    show_default=True,
    help="Claude model identifier.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("scanner/output/opus-bbox-calibration.json"),
    show_default=True,
    help="Where to write the calibration artifact.",
)
@click.option(
    "--margin",
    type=float,
    default=0.20,
    show_default=True,
    help="IoU margin required to flip from 'css' default to 'native'.",
)
def main(
    image_path: Path,
    ground_truth: str,
    prompt_feature: str,
    api_mode: str,
    model: str,
    out_path: Path,
    margin: float,
) -> None:
    """Run one Opus bbox query and write a calibration JSON artifact."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    img = Image.open(image_path)
    image_w, image_h = img.size

    gt_bbox = parse_bbox_arg(ground_truth)

    artifact: dict[str, Any] = {
        "schema_version": 1,
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "image_path": str(image_path).replace("\\", "/"),
        "original_w": image_w,
        "original_h": image_h,
        "model": model,
        "api_mode": api_mode,
        "prompt_feature": prompt_feature,
        "ground_truth_bbox_x1y1x2y2": [gt_bbox.x1, gt_bbox.y1, gt_bbox.x2, gt_bbox.y2],
        "iou_margin_for_native": margin,
        "decision_notes": _DECISION_NOTES,
    }

    try:
        observed, raw_reply = query_opus_for_bbox(
            image_path,
            prompt_feature,
            api_mode=api_mode,
            model=model,
        )
    except Exception as e:  # noqa: BLE001 — best-effort observation
        artifact["error"] = f"{type(e).__name__}: {e}"
        artifact["decided_mode"] = "css"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        click.echo(
            f"Calibration FAILED ({artifact['error']!r}); wrote default-safe "
            f"artifact at {out_path}"
        )
        return

    artifact["raw_reply_preview"] = (raw_reply[:500] + "...") if len(raw_reply) > 500 else raw_reply

    if observed is None:
        artifact["error"] = "Could not parse a bbox from Opus reply"
        artifact["decided_mode"] = "css"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        click.echo(
            f"Calibration unparsed; wrote default-safe artifact at {out_path}"
        )
        return

    artifact["observed_bbox_x1y1x2y2"] = [
        observed.x1, observed.y1, observed.x2, observed.y2,
    ]

    decided, css_iou, native_iou = decide_mode(
        observed=observed,
        ground_truth=gt_bbox,
        model=model,
        image_w=image_w,
        image_h=image_h,
        margin=margin,
    )
    artifact["css_iou"] = round(css_iou, 4)
    artifact["native_iou"] = round(native_iou, 4)
    artifact["decided_mode"] = decided

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    click.echo(
        f"Calibration: mode={decided}, css_iou={css_iou:.3f}, "
        f"native_iou={native_iou:.3f}; wrote {out_path}"
    )


if __name__ == "__main__":
    main()
