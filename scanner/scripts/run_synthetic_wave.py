"""Plan 02-20 entry-point: run the hybrid DOM-detection wave against
synthetic-source intel for a single club, and emit a Plan-02-11-shaped
per-club results JSON suitable for ``derive_results_json`` to consume.

This is the synthetic-source counterpart to ``run_vision_wave.py``.

What it does
------------
1. Loads ``{club}_synthetic_intel.json`` (the canonical synthetic intel).
2. For every feature in the rubric, evaluates the registered DOM rule (if
   any) against the synthetic intel.
3. For visual-only / hybrid features whose DOM rule failed, emits a
   ``no-data`` synthetic verdict (``present=false``, ``confidence=0.0``,
   ``notes='synthetic-source: no PNG; visual-only feature unresolved'``).
4. Constructs identical opus + sonnet result maps so downstream
   derivation logic processes synthetic captures with the same shape as
   live captures (keeps the agreement-rate computation a no-op for
   synthetic — both judges agree by construction).
5. Writes the per-club merged-results JSON at
   ``{results_dir}/{club}_features.json`` (overwriting any prior live
   data for these step names — that's the intent: synthetic supersedes
   the Cloudflare-interstitial baseline).

What it does NOT do
-------------------
- Does NOT call any vision API. Synthetic captures have no PNG; we
  cannot ground a vision verdict in pixels for a visual-only feature.
  This is Plan 02-20 Phase 5 Option A: honest no-data on visual-only
  features for synthetic-source clubs.
- Does NOT touch the live results for clubs whose intel is live
  (TOT/CHE/RMA). The runner only writes the requested club's results.

Usage
-----
::

    python -m scanner.scripts.run_synthetic_wave --club mancity --area hospitality

Output mirrors run_vision_wave's per-club JSON shape so
``derive_results_json`` is unmodified.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import click

from scanner.capture.dom_intel import DomIntel
from scanner.vision.dom_detect import detect_feature
from scanner.vision.schema import FeatureDef, FeatureVerdict

logger = logging.getLogger(__name__)


def _no_data_verdict(reason: str) -> dict:
    """Return a ``FeatureVerdict``-shaped dict for a visual-only feature
    that synthetic-source intel cannot resolve.

    ``present=False`` so ``derive_results_json`` will mark the feature
    absent — but ``confidence=0.0`` and the explanatory note are visible
    to the verifier and to anyone debugging the per-club JSON.
    """
    return {
        "present": False,
        "step": "synthetic-source",
        "evidence_bbox": None,
        "confidence": 0.0,
        "notes": f"synthetic-source: {reason}"[:500],
    }


def _run_synthetic_for_step(
    *,
    club: str,
    step_name: str,
    intel: DomIntel,
    rubric: list[FeatureDef],
) -> dict[str, dict]:
    """Build a step-level result map for one synthetic step.

    Returns a dict keyed by feature_key with FeatureVerdict-shaped
    values. Identical for opus + sonnet (derive_results_json computes
    agreement on (opus, sonnet) per feature; synthetic is by definition
    agreed because both judges 'see' the same DOM rule output).
    """
    results: dict[str, dict] = {}
    for feature in rubric:
        v = detect_feature(intel, feature)
        if v is not None:
            results[feature.key] = v.model_dump()
            continue
        # No registered rule — visual-only feature on synthetic source.
        # Mark as no-data (present=False, confidence=0.0) with provenance.
        if feature.detection == "visual":
            results[feature.key] = _no_data_verdict(
                "visual-only feature; no PNG available"
            )
        else:
            # 'dom' or 'hybrid' tag with no registered rule: defensive
            # absent + confidence=0 to match the shape downstream expects.
            results[feature.key] = _no_data_verdict(
                f"no DOM rule registered for detection={feature.detection}"
            )
    return results


def run_synthetic_wave(
    *,
    club: str,
    area: str,
    rubric: list[FeatureDef],
    intel_path: Path,
    run_log_path: Path,
    results_dir: Path,
) -> dict[str, Any]:
    """Run the synthetic wave for one club and write the per-club JSON.

    See module docstring for I/O contract. Returns a small summary dict.
    """
    intel = DomIntel.model_validate_json(intel_path.read_text(encoding="utf-8"))
    if intel.source != "synthetic":
        raise ValueError(
            f"Expected source='synthetic' in {intel_path} but got '{intel.source}'"
        )

    run_log = json.loads(run_log_path.read_text(encoding="utf-8"))
    if run_log.get("source") != "synthetic":
        raise ValueError(
            f"Expected synthetic run-log {run_log_path}, source field missing/different"
        )

    steps = run_log["steps"]
    step_names = [s["step_name"] for s in steps]

    merged_steps: dict[str, dict] = {}
    for step_name in step_names:
        step_results = _run_synthetic_for_step(
            club=club, step_name=step_name, intel=intel, rubric=rubric,
        )
        # Plan 02-11 per-club JSON shape: {opus, sonnet} both equal here
        # because synthetic detection is deterministic and judge-free.
        merged_steps[step_name] = {
            "opus": step_results,
            "sonnet": step_results,
        }

    out_doc = {
        "club": club,
        "area": area,
        "api_mode": "synthetic-text-fetch",
        "steps": merged_steps,
        "deferred_steps": [],
        "missing_png_steps": list(step_names),  # all steps lack a PNG
        "source": "synthetic",
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"{club}_features.json"
    out_path.write_text(
        json.dumps(out_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    n_features_resolved = sum(
        1 for v in next(iter(merged_steps.values()))["opus"].values()
        if v["present"]
    )
    n_features_no_data = sum(
        1 for v in next(iter(merged_steps.values()))["opus"].values()
        if not v["present"] and v["notes"].startswith("synthetic-source")
    )

    return {
        "club": club,
        "area": area,
        "steps_processed": len(step_names),
        "rubric_size": len(rubric),
        "features_resolved_present": n_features_resolved,
        "features_marked_no_data": n_features_no_data,
        "out_path": str(out_path),
    }


@click.command()
@click.option("--area", required=True, help="Area slug (hospitality).")
@click.option("--club", required=True, help="Club slug (mancity, psg, ...).")
@click.option(
    "--rubric",
    "rubric_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Vision rubric JSON (area-specific path resolved by caller).",
)
@click.option(
    "--intel-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to {club}_synthetic_intel.json (defaults to standard convention).",
)
@click.option(
    "--run-log",
    "run_log_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Synthetic run-log path (defaults to standard convention).",
)
@click.option(
    "--results-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Per-club results dir (defaults to scanner/output/results/{area}).",
)
def main(
    area: str,
    club: str,
    rubric_path: Path,
    intel_path: Path | None,
    run_log_path: Path | None,
    results_dir: Path | None,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if intel_path is None:
        intel_path = Path(
            f"scanner/output/evidence/{area}/dom/{club}_synthetic_intel.json"
        )
    if run_log_path is None:
        run_log_path = Path(
            f"scanner/output/capture-run-log-{area}-{club}-synthetic.json"
        )
    if results_dir is None:
        results_dir = Path(f"scanner/output/results/{area}")

    rubric_data = json.loads(rubric_path.read_text(encoding="utf-8"))
    rubric = [FeatureDef(**f) for f in rubric_data["features"]]

    summary = run_synthetic_wave(
        club=club,
        area=area,
        rubric=rubric,
        intel_path=intel_path,
        run_log_path=run_log_path,
        results_dir=results_dir,
    )
    click.echo(
        f"synthetic-wave: {club} steps={summary['steps_processed']} "
        f"rubric={summary['rubric_size']} "
        f"resolved-present={summary['features_resolved_present']} "
        f"no-data={summary['features_marked_no_data']} "
        f"-> {summary['out_path']}"
    )


if __name__ == "__main__":
    main()
