"""Multi-step vision wave orchestrator — Plan 02-11 Task 2.

Wraps :func:`scanner.vision.judge.two_judge` for a per-club capture run
where multiple step PNGs exist (Plan 02-10 emits a run-log JSON listing
every step's status).

What this orchestrator adds on top of the Phase-1 ``scanner vision``
single-step CLI:

- **Multi-step iteration:** for each step in the run-log with
  status=='captured', locate the PNG at
  ``{evidence_dir}/fullpage/{club}_{step_name}.png`` and run two_judge.
- **Per-club result merging:** verdicts for all steps are merged into a
  single ``{club}_features.json`` shaped:
  ``{club, area, api_mode, steps: {step_name: {opus, sonnet}}, deferred_steps: [...]}``.
- **Disagreement aggregation:** each disagreement record gains a
  ``club`` and ``step`` provenance tag so the area-wide
  ``disagreements-{area}.json`` JSON can be partitioned downstream.
- **Skip handling:** steps with status in {error, skipped, chrome-mcp,
  missing-creds} have no PNG and are recorded in ``deferred_steps`` so
  Plan 02-12 can mark those features absent (Chelsea paid-account paths).

The orchestrator is **area-agnostic** (FLOW-02 invariant): all paths
arrive via arguments. It is NOT a Click CLI — it is a Python function
called from a small entry-point script (or directly from a test).

Failure semantics:

- Missing PNG for a captured step is logged + recorded in
  ``missing_png_steps`` but does not abort the wave.
- A two_judge exception (network, schema-validation, malformed reply)
  PROPAGATES — the wave is interrupted and the caller decides whether
  to retry. Phase 1 plan 01-08 added retry-once for malformed JSON
  inside the client layer; uncaught exceptions here are unexpected.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scanner.vision.disagreement import find_disagreements
from scanner.vision.judge import two_judge
from scanner.vision.schema import FeatureDef

logger = logging.getLogger(__name__)


def _load_existing_disagreements(path: Path) -> list[dict]:
    """Read the area-wide disagreements JSON if it exists, else return []."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        logger.warning("disagreements file %s unparseable; starting fresh", path)
        return []


def _write_disagreements(path: Path, records: list[dict]) -> None:
    """Write disagreement records (already-tagged dicts) to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def run_wave_for_club(
    *,
    run_log_path: Path,
    evidence_dir: Path,
    results_dir: Path,
    disagreements_path: Path,
    rubric: list[FeatureDef],
    api_mode: str = "subscription",
) -> dict[str, Any]:
    """Run the two-judge vision wave for one club.

    Args:
        run_log_path: Path to the Plan 02-10 capture run-log JSON for the
            club. Used to discover step names and statuses.
        evidence_dir: Area evidence dir; PNGs live under
            ``{evidence_dir}/fullpage/{club}_{step}.png``.
        results_dir: Per-area results dir; the per-club JSON is written
            to ``{results_dir}/{club}_features.json``.
        disagreements_path: Path to the area-wide disagreements aggregator.
            New records are appended to whatever already exists.
        rubric: Frozen list of :class:`FeatureDef` (the same rubric is
            handed to both judges, D-18).
        api_mode: Forwarded to :func:`two_judge`. Default ``subscription``
            per D-28.

    Returns:
        A summary dict with keys ``club``, ``captured_steps``,
        ``skipped_steps``, ``missing_png_steps``, ``vision_calls``,
        ``new_disagreements``.
    """
    run_log = json.loads(run_log_path.read_text(encoding="utf-8"))
    club = run_log["club"]
    area = run_log.get("area", "hospitality")
    steps = run_log.get("steps", [])

    # Existing per-club result JSON (if present) — preserve old steps,
    # overwrite for re-run idempotence.
    out_path = results_dir / f"{club}_features.json"
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_steps = existing.get("steps", {}) or {}
        except json.JSONDecodeError:
            existing_steps = {}
    else:
        existing_steps = {}
    merged_steps: dict[str, dict] = dict(existing_steps)

    deferred: list[dict] = []
    missing_png: list[str] = []
    new_disagreement_records: list[dict] = []
    vision_calls = 0

    for step in steps:
        step_name = step.get("step_name") or step.get("name")
        status = step.get("status")
        if not step_name:
            continue

        if status != "captured":
            deferred.append(
                {
                    "step_name": step_name,
                    "status": status,
                    "reason": step.get("reason"),
                }
            )
            continue

        png_path = evidence_dir / "fullpage" / f"{club}_{step_name}.png"
        if not png_path.exists():
            logger.warning("missing PNG for %s/%s: %s", club, step_name, png_path)
            missing_png.append(step_name)
            continue

        logger.info("vision: %s/%s (%s)", club, step_name, png_path.name)
        judges = two_judge(png_path, rubric, api_mode=api_mode)
        vision_calls += 2  # opus + sonnet

        merged_steps[step_name] = {
            "opus": {k: v.model_dump() for k, v in judges["opus"].results.items()},
            "sonnet": {k: v.model_dump() for k, v in judges["sonnet"].results.items()},
        }

        # Per-step disagreements (presence + confidence + bbox) — tag
        # with club/step provenance for cross-club aggregation.
        disagreements = find_disagreements(
            judges["opus"].results, judges["sonnet"].results
        )
        for d in disagreements:
            rec = asdict(d)
            rec["club"] = club
            rec["step"] = step_name
            new_disagreement_records.append(rec)

    # Write per-club merged JSON.
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "club": club,
                "area": area,
                "api_mode": api_mode,
                "steps": merged_steps,
                "deferred_steps": deferred,
                "missing_png_steps": missing_png,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Append disagreements to the area-wide aggregator.
    existing_disagreements = _load_existing_disagreements(disagreements_path)
    # Drop any prior records for this (club, step) tuple — re-run idempotence.
    seen_keys = {(r["club"], r["step"]) for r in new_disagreement_records}
    filtered = [
        r
        for r in existing_disagreements
        if (r.get("club"), r.get("step")) not in seen_keys
    ]
    combined = filtered + new_disagreement_records
    _write_disagreements(disagreements_path, combined)

    captured_count = sum(1 for s in steps if s.get("status") == "captured")
    skipped_count = sum(1 for s in steps if s.get("status") != "captured")

    return {
        "club": club,
        "captured_steps": captured_count,
        "skipped_steps": skipped_count,
        "vision_calls": vision_calls,
        "missing_png_steps": missing_png,
        "deferred_steps": [d["step_name"] for d in deferred],
        "new_disagreements": len(new_disagreement_records),
    }


def _cli() -> None:
    """Click CLI entry-point — invoke the wave for one club's run-log.

    Usage::

        python -m scanner.scripts.run_vision_wave \\
          --run-log <path/to/capture-run-log-{area}-{club}-...json> \\
          --evidence-dir <scanner/output/evidence/{area}> \\
          --results-dir <scanner/output/results/{area}> \\
          --disagreements <scanner/output/disagreements-{area}.json> \\
          --rubric <path/to/features.json> \\
          --api-mode subscription

    All paths are arguments — the orchestrator is area-agnostic (FLOW-02).
    """
    import sys
    import time

    import click

    @click.command()
    @click.option("--run-log", type=click.Path(exists=True, path_type=Path), required=True)
    @click.option("--evidence-dir", type=click.Path(path_type=Path), required=True)
    @click.option("--results-dir", type=click.Path(path_type=Path), required=True)
    @click.option("--disagreements", type=click.Path(path_type=Path), required=True)
    @click.option("--rubric", type=click.Path(exists=True, path_type=Path), required=True)
    @click.option("--api-mode", type=click.Choice(["subscription", "api-key"]), default="subscription")
    def _run(
        run_log: Path,
        evidence_dir: Path,
        results_dir: Path,
        disagreements: Path,
        rubric: Path,
        api_mode: str,
    ) -> None:
        rubric_data = json.loads(Path(rubric).read_text(encoding="utf-8"))
        rubric_list = [FeatureDef(**f) for f in rubric_data["features"]]

        t0 = time.time()
        click.echo(f"Wave start: run-log={run_log.name} api-mode={api_mode} rubric={len(rubric_list)} features")
        summary = run_wave_for_club(
            run_log_path=run_log,
            evidence_dir=evidence_dir,
            results_dir=results_dir,
            disagreements_path=disagreements,
            rubric=rubric_list,
            api_mode=api_mode,
        )
        elapsed = time.time() - t0
        click.echo(
            f"Wave done: {summary['club']} captured_steps={summary['captured_steps']} "
            f"vision_calls={summary['vision_calls']} new_disagreements={summary['new_disagreements']} "
            f"missing_png={len(summary['missing_png_steps'])} elapsed={elapsed:.1f}s"
        )

    _run()


if __name__ == "__main__":
    _cli()


__all__ = ["run_wave_for_club"]
