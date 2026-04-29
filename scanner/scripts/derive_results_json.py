"""Derive per-club flat presence map from a Plan-02-11 two-judge result JSON.

Plan 02-12 Task 2.

Inputs
------
- ``--per-club-results <path>``  Plan-02-11-shaped JSON:
  ``{club, area, steps: {step: {opus, sonnet}}, deferred_steps, missing_png_steps}``
- ``--rubric <path>``            Vision rubric JSON: ``{features: [{key, name, yes_criterion}, ...]}``
- ``--out <path>``               Destination flat result JSON.
- ``--club-name <str>``          Human-readable club name (e.g. "Manchester City").

Output schema
-------------
::

    {
      "club_id": "mancity",
      "club_name": "Manchester City",
      "area": "hospitality",
      "features": {feat_key: bool, ...},  # ALL rubric keys present
      "disputed_features": [feat_key, ...],
      "skipped_features": [feat_key, ...],
      "captured_steps": [step_name, ...],
      "judge_agreement_rate": 0.92,
      "generated_at": "2026-04-28T..."
    }

Resolution policy
-----------------
- Both judges agree on presence (both True OR both False) -> use Opus value.
- Disagree -> resolved value = False, feature key tracked in ``disputed_features``.

Multi-step flattening
---------------------
- For each rubric key: presence = OR across the resolved per-step value
  in every captured step.
- Steps without a verdict for the key contribute nothing (False) but do not
  flag the feature as skipped *unless* NO captured step has a verdict.

D-21 deviation: this is a new ``scanner/scripts/`` module — no scanner module
internals modified.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click


def derive_results_json(
    per_club_results_path: Path,
    out_path: Path,
    *,
    rubric_keys: list[str],
    club_name: str,
) -> dict:
    """Apply disagreement resolution + step flattening; write JSON.

    See module docstring for I/O contract.
    """
    src = json.loads(Path(per_club_results_path).read_text(encoding="utf-8"))
    club_id = src.get("club", per_club_results_path.stem.replace("_features", ""))
    area = src.get("area", "hospitality")
    steps_map: dict[str, dict[str, dict]] = src.get("steps", {})

    captured_steps = sorted(steps_map.keys())

    # For each (step, feature_key) compute the resolved presence.
    # Tracks: per-feature OR across steps; per-feature any-disagreement; per-feature any-verdict.
    feature_present: dict[str, bool] = {k: False for k in rubric_keys}
    feature_has_verdict: dict[str, bool] = {k: False for k in rubric_keys}
    feature_disputed: dict[str, bool] = {k: False for k in rubric_keys}

    # Aggregate agreement-rate across (step, feature) pairs that BOTH judges
    # rendered a verdict for.
    pair_count = 0
    pair_agreed = 0

    for step_name, judges in steps_map.items():
        opus = judges.get("opus", {}) or {}
        sonnet = judges.get("sonnet", {}) or {}
        # Iterate the union of judges' keys — tolerates schema drift.
        all_keys = set(opus.keys()) | set(sonnet.keys())
        for fkey in all_keys:
            if fkey not in feature_present:
                # Not in the canonical rubric — ignore.
                continue
            opus_v = opus.get(fkey)
            sonnet_v = sonnet.get(fkey)
            if opus_v is None or sonnet_v is None:
                # Only one judge ruled — treat as a single-judge verdict.
                # Use whichever exists; don't flag disputed (no opposition).
                v = opus_v if opus_v is not None else sonnet_v
                feature_has_verdict[fkey] = True
                if bool(v.get("present")):
                    feature_present[fkey] = True
                continue
            opus_present = bool(opus_v.get("present"))
            sonnet_present = bool(sonnet_v.get("present"))
            feature_has_verdict[fkey] = True
            pair_count += 1
            if opus_present == sonnet_present:
                pair_agreed += 1
                if opus_present:
                    feature_present[fkey] = True
                # If both agree absent, leave feature_present[fkey] as-is.
            else:
                # Disagree -> resolved False, mark disputed (sticky across steps).
                feature_disputed[fkey] = True
                # OR semantic still applies: an earlier-step "agree-true" wins.
                # The current step contributes False (the disputed-step resolution).

    disputed = sorted(k for k, v in feature_disputed.items() if v)
    skipped = sorted(k for k, has in feature_has_verdict.items() if not has)
    agreement_rate = (pair_agreed / pair_count) if pair_count > 0 else 1.0

    out_doc: dict[str, Any] = {
        # `product_id` is the canonical homepage-results-JSON identifier consumed
        # by scanner/scoring/recalculate.js (rank/aggregate output keys).
        # Carry `club_id` as the primary semantic name + `product_id` as the
        # alias so both scorer and Plan-02-13 UI consumers find what they need.
        "product_id": club_id,
        "club_id": club_id,
        "club_name": club_name,
        "area": area,
        "features": {k: feature_present[k] for k in rubric_keys},
        "disputed_features": disputed,
        "skipped_features": skipped,
        "captured_steps": captured_steps,
        "judge_agreement_rate": round(agreement_rate, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_doc, indent=2) + "\n", encoding="utf-8")
    return out_doc


@click.command(name="derive-results-json")
@click.option(
    "--per-club-results",
    "per_club_results",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Plan-02-11 per-club result JSON path.",
)
@click.option(
    "--rubric",
    "rubric_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Vision rubric JSON (features.json) path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Destination flat result JSON path.",
)
@click.option(
    "--club-name",
    "club_name",
    required=True,
    help="Human-readable club name for the emitted club_name field.",
)
def main(
    per_club_results: Path,
    rubric_path: Path,
    out_path: Path,
    club_name: str,
) -> None:
    """Derive per-club flat presence map from a two-judge result JSON."""
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    rubric_keys = [f["key"] for f in rubric["features"]]

    out = derive_results_json(
        per_club_results,
        out_path,
        rubric_keys=rubric_keys,
        club_name=club_name,
    )

    n_present = sum(1 for v in out["features"].values() if v)
    n_disputed = len(out["disputed_features"])
    n_skipped = len(out["skipped_features"])
    click.echo(
        f"{out['club_id']}: {n_present} present, {n_disputed} disputed, "
        f"{n_skipped} skipped, agreement={out['judge_agreement_rate']:.2%} "
        f"-> {out_path}"
    )


if __name__ == "__main__":
    main()


__all__ = ["derive_results_json", "main"]
