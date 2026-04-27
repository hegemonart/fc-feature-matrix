"""Tests for scanner.scripts.calibrate_opus_bbox + bbox_mode wiring.

Three layers:

- Pure-geometry: ``decide_mode`` picks 'native' iff IoU gap >= margin,
  else 'css' (default-safe).
- Reply parsing: ``parse_opus_bbox`` extracts a bbox from the model's
  reply, returns None when no JSON is present.
- CLI wiring: scanner.cli slice handler reads bbox_mode from areas.json
  and skips denormalise_bbox when bbox_mode='native' AND model starts
  with claude-opus.
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Geometry / decision logic
# ---------------------------------------------------------------------------


def test_decide_mode_picks_native_when_native_iou_dominates():
    """Plan 02-08: when native_iou - css_iou >= margin, mode flips to native."""
    from scanner.scripts.calibrate_opus_bbox import Bbox, decide_mode

    # Source image: 2880x6778 (real MCFC dimensions). Long edge well above
    # Opus's 2576 limit, so denormalise scales by 2880/2576 ~= 1.118.
    image_w, image_h = 2880, 6778
    # Ground truth: top header band in CSS pixels.
    gt = Bbox(0, 0, 2880, 800)
    # Observed (Opus reply): bbox in CSS-pixel space already (matches GT).
    # css_iou would scale this up further → smaller intersection with GT.
    # native_iou compares observed directly to GT → ~1.0.
    observed = Bbox(0, 0, 2880, 800)

    decided, css_iou, native_iou = decide_mode(
        observed=observed,
        ground_truth=gt,
        model="claude-opus-4-7",
        image_w=image_w,
        image_h=image_h,
        margin=0.20,
    )
    assert decided == "native"
    assert native_iou >= 0.99
    assert (native_iou - css_iou) >= 0.20


def test_decide_mode_picks_css_default_safe_when_no_clear_winner():
    """When neither mode dominates by 0.20 IoU margin, default to 'css'."""
    from scanner.scripts.calibrate_opus_bbox import Bbox, decide_mode

    # Image well below the Opus long-edge limit → denormalise no-ops, so
    # css_iou == native_iou.
    image_w, image_h = 1024, 768
    gt = Bbox(100, 100, 300, 300)
    observed = Bbox(100, 100, 300, 300)

    decided, css_iou, native_iou = decide_mode(
        observed=observed,
        ground_truth=gt,
        model="claude-opus-4-7",
        image_w=image_w,
        image_h=image_h,
        margin=0.20,
    )
    # Both IoUs are 1.0 (or very close); margin not exceeded → css default.
    assert decided == "css"
    assert abs(css_iou - native_iou) < 0.20


def test_iou_disjoint_is_zero():
    from scanner.scripts.calibrate_opus_bbox import Bbox, iou

    a = Bbox(0, 0, 10, 10)
    b = Bbox(100, 100, 110, 110)
    assert iou(a, b) == 0.0


def test_iou_full_overlap_is_one():
    from scanner.scripts.calibrate_opus_bbox import Bbox, iou

    a = Bbox(0, 0, 10, 10)
    assert iou(a, a) == pytest.approx(1.0)


def test_parse_opus_bbox_extracts_simple_json():
    """Reply parser handles a clean JSON object."""
    from scanner.scripts.calibrate_opus_bbox import parse_opus_bbox

    reply = '{"bbox": [10, 20, 100, 200]}'
    bb = parse_opus_bbox(reply)
    assert bb is not None
    assert (bb.x1, bb.y1, bb.x2, bb.y2) == (10.0, 20.0, 100.0, 200.0)


def test_parse_opus_bbox_extracts_from_prose_wrapped_reply():
    """Reply parser tolerates a preamble before the JSON object."""
    from scanner.scripts.calibrate_opus_bbox import parse_opus_bbox

    reply = 'Here is the bbox: {"bbox": [40.5, 20, 200, 60.25]}\nDone.'
    bb = parse_opus_bbox(reply)
    assert bb is not None
    assert bb.x1 == 40.5
    assert bb.y2 == 60.25


def test_parse_opus_bbox_returns_none_when_no_match():
    """No JSON-like 'bbox' in the reply → None."""
    from scanner.scripts.calibrate_opus_bbox import parse_opus_bbox

    assert parse_opus_bbox("I don't know what you mean.") is None
    assert parse_opus_bbox('{"other": [1,2,3,4]}') is None


def test_parse_bbox_arg_rejects_wrong_arity():
    import click

    from scanner.scripts.calibrate_opus_bbox import parse_bbox_arg

    with pytest.raises(click.BadParameter):
        parse_bbox_arg("1,2,3")  # only 3 numbers


# ---------------------------------------------------------------------------
# CLI wiring — slice handler reads bbox_mode from areas.json
# ---------------------------------------------------------------------------


def test_slice_handler_reads_bbox_mode_native_skips_denormalise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan 02-08: when areas.json[area].bbox_mode == 'native' AND the model
    is Opus, the slice CLI skips denormalise_bbox and passes the raw bbox
    through to slice_feature unchanged."""
    from click.testing import CliRunner

    # Build a synthetic repo tree with the new bbox_mode='native' setting.
    repo = tmp_path / "repo"
    (repo / "scanner" / "config").mkdir(parents=True)
    (repo / "scanner" / "output" / "evidence" / "h" / "fullpage").mkdir(parents=True)
    (repo / "scanner" / "output" / "results" / "h").mkdir(parents=True)
    areas = {
        "h": {
            "evidence_dir": "scanner/output/evidence/h/",
            "results_dir": "scanner/output/results/h/",
            "status": "pilot",
            "bbox_mode": "native",
        }
    }
    (repo / "scanner" / "config" / "areas.json").write_text(
        json.dumps(areas), encoding="utf-8"
    )

    # Synth full-page screenshot (3000 x 1000 — exceeds Opus 2576 long-edge
    # limit so denormalise WOULD scale by ~1.165 if invoked).
    img = Image.new("RGB", (3000, 1000), color="white")
    fp = repo / "scanner" / "output" / "evidence" / "h" / "fullpage" / "club_landing.png"
    img.save(fp, format="PNG")

    # Synth vision results: one feature, one evidence_bbox.
    results = {
        "club": "club",
        "area": "h",
        "step": "landing",
        "api_mode": "subscription",
        "opus": {
            "logo": {
                "present": True,
                "confidence": 0.9,
                "evidence_bbox": [10, 20, 100, 60],
            }
        },
        "sonnet": {},
    }
    (repo / "scanner" / "output" / "results" / "h" / "club_features.json").write_text(
        json.dumps(results), encoding="utf-8"
    )

    monkeypatch.setenv("SCANNER_REPO_ROOT", str(repo))
    # Force loader to re-read REPO_ROOT — the loader caches a module-level
    # constant, so reload it.
    import importlib

    import scanner.config.loader as loader_mod
    importlib.reload(loader_mod)

    captured = {}

    def _spy_slice_feature(png_bytes, bbox, out):
        captured["bbox"] = bbox
        # write a stub PNG so res.ok is True
        from PIL import Image as PILImage
        out.parent.mkdir(parents=True, exist_ok=True)
        PILImage.new("RGB", (60, 60)).save(out, format="PNG")
        from scanner.vision.slice import SliceResult
        return SliceResult(ok=True, path=out)

    def _spy_denormalise(*a, **kw):
        captured["denormalise_called"] = True
        from scanner.vision.slice import denormalise_bbox as real
        return real(*a, **kw)

    # Monkeypatch the slice CLI's bound names (cli.py does function-local
    # imports inside slice_cmd, so we patch via the source modules).
    monkeypatch.setattr(
        "scanner.vision.slice.slice_feature", _spy_slice_feature
    )
    monkeypatch.setattr(
        "scanner.vision.slice.denormalise_bbox", _spy_denormalise
    )

    from scanner.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["slice", "--area", "h", "--club", "club", "--step", "landing"],
    )
    assert result.exit_code == 0, result.output

    # Native mode → denormalise NOT called → bbox passed through as raw.
    assert captured.get("denormalise_called") is not True
    assert captured["bbox"] == (10, 20, 100, 60)


def test_slice_handler_default_css_mode_calls_denormalise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backward-compat: areas.json without bbox_mode (or with 'css') still
    invokes denormalise_bbox as the pre-08 behavior."""
    from click.testing import CliRunner

    repo = tmp_path / "repo"
    (repo / "scanner" / "config").mkdir(parents=True)
    (repo / "scanner" / "output" / "evidence" / "h" / "fullpage").mkdir(parents=True)
    (repo / "scanner" / "output" / "results" / "h").mkdir(parents=True)
    areas = {
        "h": {
            "evidence_dir": "scanner/output/evidence/h/",
            "results_dir": "scanner/output/results/h/",
            "status": "pilot",
            # bbox_mode omitted → defaults to 'css'.
        }
    }
    (repo / "scanner" / "config" / "areas.json").write_text(
        json.dumps(areas), encoding="utf-8"
    )
    img = Image.new("RGB", (3000, 1000), color="white")
    fp = repo / "scanner" / "output" / "evidence" / "h" / "fullpage" / "club_landing.png"
    img.save(fp, format="PNG")
    results = {
        "club": "club",
        "area": "h",
        "step": "landing",
        "api_mode": "subscription",
        "opus": {
            "logo": {
                "present": True,
                "confidence": 0.9,
                "evidence_bbox": [10, 20, 100, 60],
            }
        },
        "sonnet": {},
    }
    (repo / "scanner" / "output" / "results" / "h" / "club_features.json").write_text(
        json.dumps(results), encoding="utf-8"
    )

    monkeypatch.setenv("SCANNER_REPO_ROOT", str(repo))
    import importlib
    import scanner.config.loader as loader_mod
    importlib.reload(loader_mod)

    captured = {"denormalise_called": False}

    from scanner.vision.slice import denormalise_bbox as real_denorm

    def _spy_denormalise(bbox, model, w, h):
        captured["denormalise_called"] = True
        return real_denorm(bbox, model, w, h)

    def _spy_slice_feature(png_bytes, bbox, out):
        captured["bbox"] = bbox
        from PIL import Image as PILImage
        out.parent.mkdir(parents=True, exist_ok=True)
        PILImage.new("RGB", (60, 60)).save(out, format="PNG")
        from scanner.vision.slice import SliceResult
        return SliceResult(ok=True, path=out)

    monkeypatch.setattr(
        "scanner.vision.slice.slice_feature", _spy_slice_feature
    )
    monkeypatch.setattr(
        "scanner.vision.slice.denormalise_bbox", _spy_denormalise
    )

    from scanner.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["slice", "--area", "h", "--club", "club", "--step", "landing"],
    )
    assert result.exit_code == 0, result.output

    # CSS mode (default) → denormalise IS called.
    assert captured["denormalise_called"] is True


# ---------------------------------------------------------------------------
# Module-level integrity
# ---------------------------------------------------------------------------


def test_calibration_artifact_format_required_fields(tmp_path: Path):
    """If/when the calibration ran on disk, its artifact has the contractually-
    required fields (so downstream consumers know what to read)."""
    artifact_path = (
        Path(__file__).resolve().parents[1]
        / "output"
        / "opus-bbox-calibration.json"
    )
    if not artifact_path.exists():
        pytest.skip("Calibration artifact not yet produced (best-effort run)")
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    for required in (
        "schema_version",
        "timestamp",
        "image_path",
        "model",
        "decision_notes",
        "decided_mode",
    ):
        assert required in data, f"Missing required field {required!r}"
    assert data["decided_mode"] in ("css", "native")
    # D-21 deviation note must be reproduced verbatim in the artifact.
    assert "D-21 deviation note" in data["decision_notes"]
