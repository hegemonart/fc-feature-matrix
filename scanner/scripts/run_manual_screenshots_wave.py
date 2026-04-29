"""Manual screenshots wave — dual-judge vision analysis on manually captured
hospitality screenshots.

Reads club screenshot folders under ``--input-dir`` (default:
``{repo_root}/analysis/hospitality/``), runs Opus + Sonnet via
:func:`scanner.vision.judge.two_judge`, merges verdicts across all screenshots
per club, writes updated results JSONs + evidence crops, and logs disagreements.

Folder → canonical club ID mapping
------------------------------------
  man-city   → mancity
  realmadrid → realmadrid
  tottenham  → tottenham
  chelsea    → chelsea
  psg        → psg

Merge policy
------------
- Feature **present** = True if Opus OR Sonnet says ``present=True`` in ANY
  screenshot for that club.  We want maximum recall: if any screenshot shows
  the feature it counts.
- **Best bbox** for the evidence crop: highest-confidence verdict with
  ``present=True`` across all (screenshot × judge) combinations, preferring
  Opus (wider pixel budget = more precise bbox).
- **Disputed** = Opus and Sonnet disagree on the same screenshot.  A feature
  can be disputed in one screenshot but still resolve to present (if another
  screenshot is clean).

Output files
------------
  analysis/hospitality/results/{club_id}.json  — updated flat presence map
  analysis/hospitality/evidence/features/{club_id}_{feature_key}.png — crops
  scanner/output/disagreements-hospitality-manual.json — disagreements log

Usage
-----
::

    # from the worktree root
    python -m scanner.scripts.run_manual_screenshots_wave \\
        --input-dir "D:/AI/fc feature matrix/analysis/hospitality" \\
        [--rubric analysis/hospitality/features.json] \\
        [--results-dir analysis/hospitality/results] \\
        [--evidence-dir analysis/hospitality/evidence/features] \\
        [--disagreements scanner/output/disagreements-hospitality-manual.json] \\
        [--api-mode subscription] \\
        [--clubs mancity,tottenham] \\
        [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Repo-root anchor — script lives at scanner/scripts/run_manual_screenshots_wave.py
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT_DIR = REPO_ROOT / "analysis" / "hospitality"
DEFAULT_RUBRIC = REPO_ROOT / "analysis" / "hospitality" / "features.json"
DEFAULT_RESULTS_DIR = REPO_ROOT / "analysis" / "hospitality" / "results"
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "analysis" / "hospitality" / "evidence" / "features"
DEFAULT_DISAGREEMENTS = REPO_ROOT / "scanner" / "output" / "disagreements-hospitality-manual.json"

# ---------------------------------------------------------------------------
# Club metadata
# ---------------------------------------------------------------------------
CLUB_FOLDER_TO_ID: dict[str, str] = {
    "man-city": "mancity",
    "realmadrid": "realmadrid",
    "tottenham": "tottenham",
    "chelsea": "chelsea",
    "psg": "psg",
}

CLUB_ID_TO_NAME: dict[str, str] = {
    "mancity": "Manchester City",
    "realmadrid": "Real Madrid",
    "tottenham": "Tottenham Hotspur",
    "chelsea": "Chelsea",
    "psg": "Paris Saint-Germain",
}

# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


@dataclass
class BboxCandidate:
    """Tracks the best evidence bbox found for a feature across all screenshots."""
    screenshot: Path
    model: str
    bbox: tuple[float, float, float, float]
    confidence: float


def load_rubric(rubric_path: Path) -> list:
    """Load FeatureDef list from features.json."""
    from scanner.vision.schema import FeatureDef

    raw = json.loads(rubric_path.read_text(encoding="utf-8"))
    return [FeatureDef(**f) for f in raw["features"]]


def load_existing_results(results_path: Path) -> dict[str, bool] | None:
    """Load existing per-club results features map; returns None if missing."""
    if not results_path.exists():
        return None
    try:
        data = json.loads(results_path.read_text(encoding="utf-8"))
        return data.get("features") or {}
    except (json.JSONDecodeError, KeyError):
        return None


def load_existing_disagreements(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def run_club(
    *,
    club_id: str,
    club_name: str,
    png_paths: list[Path],
    rubric: list,
    api_mode: str,
    results_dir: Path,
    evidence_dir: Path,
    dry_run: bool,
) -> tuple[dict[str, Any], list[dict]]:
    """Analyse all screenshots for one club.

    Returns ``(results_doc, disagreement_records)``.
    """
    from scanner.vision.judge import two_judge
    from scanner.vision.schema import FeatureVerdict
    from scanner.vision.slice import denormalise_bbox, slice_feature

    rubric_keys = [f.key for f in rubric]

    # Per-feature aggregation state
    feature_present: dict[str, bool] = {k: False for k in rubric_keys}
    feature_disputed_any: dict[str, bool] = {k: False for k in rubric_keys}
    feature_has_verdict: dict[str, bool] = {k: False for k in rubric_keys}

    # Best bbox tracker: key → BboxCandidate with highest confidence
    best_bbox: dict[str, BboxCandidate] = {}

    disagreement_records: list[dict] = []
    pair_total = 0
    pair_agreed = 0

    for png_path in sorted(png_paths):
        logger.info("[%s] analysing %s", club_id, png_path.name)

        if dry_run:
            logger.info("[%s] DRY RUN — skipping two_judge call", club_id)
            continue

        try:
            judges = two_judge(png_path, rubric, api_mode=api_mode, dom_intel_path=None)
        except Exception as exc:
            logger.error("[%s] two_judge failed on %s: %s", club_id, png_path.name, exc)
            continue

        opus_results = judges["opus"].results
        sonnet_results = judges["sonnet"].results
        opus_model = judges["opus"].model
        sonnet_model = judges["sonnet"].model

        all_keys_this_img = set(opus_results.keys()) | set(sonnet_results.keys())

        for fkey in all_keys_this_img:
            if fkey not in feature_present:
                continue  # not in rubric

            ov: FeatureVerdict | None = opus_results.get(fkey)
            sv: FeatureVerdict | None = sonnet_results.get(fkey)

            # Mark that we have a verdict for this feature
            if ov is not None or sv is not None:
                feature_has_verdict[fkey] = True

            if ov is not None and sv is not None:
                pair_total += 1
                opus_present = ov.present
                sonnet_present = sv.present

                if opus_present == sonnet_present:
                    pair_agreed += 1
                    if opus_present:
                        feature_present[fkey] = True
                else:
                    # Disagreement — record it
                    feature_disputed_any[fkey] = True
                    disagreement_records.append({
                        "club": club_id,
                        "screenshot": png_path.name,
                        "feature_key": fkey,
                        "opus_present": opus_present,
                        "opus_confidence": ov.confidence,
                        "sonnet_present": sonnet_present,
                        "sonnet_confidence": sv.confidence,
                    })
                    # OR logic: if either says present, mark present
                    if opus_present or sonnet_present:
                        feature_present[fkey] = True

            elif ov is not None:
                # Only Opus responded
                if ov.present:
                    feature_present[fkey] = True
            elif sv is not None:
                # Only Sonnet responded
                if sv.present:
                    feature_present[fkey] = True

            # Track best bbox for evidence crop generation.
            # Prefer Opus (larger pixel budget → more precise spatial coords).
            for verdict, model_name in ((ov, opus_model), (sv, sonnet_model)):
                if verdict is None or not verdict.present or verdict.evidence_bbox is None:
                    continue
                cand = best_bbox.get(fkey)
                if cand is None or verdict.confidence > cand.confidence:
                    # Prefer Opus when confidences are equal
                    if cand is not None and verdict.confidence == cand.confidence and model_name != opus_model:
                        continue
                    best_bbox[fkey] = BboxCandidate(
                        screenshot=png_path,
                        model=model_name,
                        bbox=verdict.evidence_bbox,
                        confidence=verdict.confidence,
                    )

    # ---------------------------------------------------------
    # Generate evidence crops
    # ---------------------------------------------------------
    crops_saved = 0
    crops_skipped = 0
    if not dry_run:
        for fkey, cand in best_bbox.items():
            if not feature_present.get(fkey):
                continue  # don't crop absent features
            try:
                raw_png = cand.screenshot.read_bytes()
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(raw_png))
                orig_w, orig_h = img.size
                scaled_bbox = denormalise_bbox(cand.bbox, cand.model, orig_w, orig_h)
                out_path = evidence_dir / f"{club_id}_{fkey}.png"
                result = slice_feature(raw_png, scaled_bbox, out_path)
                if result.ok:
                    crops_saved += 1
                    logger.info("[%s] crop saved: %s", club_id, out_path.name)
                else:
                    crops_skipped += 1
                    logger.warning("[%s] crop skipped for %s: %s", club_id, fkey, result.reason)
            except Exception as exc:
                crops_skipped += 1
                logger.warning("[%s] crop error for %s: %s", club_id, fkey, exc)

    # ---------------------------------------------------------
    # Build results doc (matches existing analysis/hospitality/results/*.json shape)
    # ---------------------------------------------------------
    disputed = sorted(k for k, v in feature_disputed_any.items() if v)
    skipped = sorted(k for k, has in feature_has_verdict.items() if not has)
    agreement_rate = round(pair_agreed / pair_total, 4) if pair_total > 0 else 1.0

    results_doc: dict[str, Any] = {
        "product_id": club_id,
        "club_id": club_id,
        "club_name": club_name,
        "area": "hospitality",
        "features": {k: feature_present[k] for k in rubric_keys},
        "disputed_features": disputed,
        "skipped_features": skipped,
        "judge_agreement_rate": agreement_rate,
        "screenshots_analyzed": len(png_paths),
        "crops_saved": crops_saved,
        "source": "manual_screenshots_wave",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    if not dry_run:
        results_dir.mkdir(parents=True, exist_ok=True)
        out_path = results_dir / f"{club_id}.json"
        out_path.write_text(json.dumps(results_doc, indent=2) + "\n", encoding="utf-8")
        logger.info("[%s] results written -> %s", club_id, out_path)

    n_present = sum(1 for v in results_doc["features"].values() if v)
    print(
        f"  {club_id}: {n_present}/{len(rubric_keys)} present  |  "
        f"disputes={len(disputed)}  skipped={len(skipped)}  "
        f"agreement={agreement_rate:.0%}  crops={crops_saved}  "
        f"screenshots={len(png_paths)}"
    )

    return results_doc, disagreement_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run dual-judge vision analysis on manually captured hospitality screenshots."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Base dir containing per-club screenshot folders (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--rubric",
        type=Path,
        default=DEFAULT_RUBRIC,
        help=f"Path to features.json rubric (default: {DEFAULT_RUBRIC})",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help=f"Where to write per-club result JSONs (default: {DEFAULT_RESULTS_DIR})",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_EVIDENCE_DIR,
        help=f"Where to write evidence crop PNGs (default: {DEFAULT_EVIDENCE_DIR})",
    )
    parser.add_argument(
        "--disagreements",
        type=Path,
        default=DEFAULT_DISAGREEMENTS,
        help=f"Disagreements aggregator JSON (default: {DEFAULT_DISAGREEMENTS})",
    )
    parser.add_argument(
        "--api-mode",
        choices=["subscription", "api-key"],
        default="subscription",
    )
    parser.add_argument(
        "--clubs",
        default=None,
        help="Comma-separated club IDs to run (e.g. mancity,tottenham). Default: all 5.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be processed without calling the vision API.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    # Validate rubric
    if not args.rubric.exists():
        print(f"ERROR: rubric not found: {args.rubric}", file=sys.stderr)
        sys.exit(1)

    rubric = load_rubric(args.rubric)
    print(f"Rubric: {len(rubric)} features loaded from {args.rubric}")

    # Filter clubs if requested
    wanted_ids: set[str] | None = None
    if args.clubs:
        wanted_ids = set(args.clubs.split(","))

    # Discover club folders
    input_dir: Path = args.input_dir
    if not input_dir.exists():
        print(f"ERROR: input-dir not found: {input_dir}", file=sys.stderr)
        print(
            "Pass --input-dir pointing to the directory that contains man-city/, chelsea/, etc.",
            file=sys.stderr,
        )
        sys.exit(1)

    clubs_to_run: list[tuple[str, str, list[Path]]] = []  # (folder_name, club_id, pngs)
    for folder_name, club_id in CLUB_FOLDER_TO_ID.items():
        if wanted_ids and club_id not in wanted_ids:
            continue
        folder = input_dir / folder_name
        if not folder.exists():
            logger.warning("club folder not found: %s — skipping", folder)
            continue
        pngs = sorted(folder.glob("*.png"))
        if not pngs:
            logger.warning("no PNGs in %s — skipping", folder)
            continue
        clubs_to_run.append((folder_name, club_id, pngs))

    if not clubs_to_run:
        print("No club folders found to process.", file=sys.stderr)
        sys.exit(1)

    total_pngs = sum(len(pngs) for _, _, pngs in clubs_to_run)
    print(
        f"\nPlan: {len(clubs_to_run)} clubs  |  {total_pngs} screenshots  |  "
        f"{len(rubric)} features  |  api-mode={args.api_mode}"
        f"{'  [DRY RUN]' if args.dry_run else ''}"
    )
    for _, club_id, pngs in clubs_to_run:
        print(f"  {club_id}: {len(pngs)} screenshots")
        for p in pngs:
            print(f"    {p.name}")
    print()

    if args.dry_run:
        print("DRY RUN — no API calls will be made.")
        return

    # Run
    all_disagreements: list[dict] = load_existing_disagreements(args.disagreements)
    # Remove prior records for clubs we're re-running
    rerun_clubs = {club_id for _, club_id, _ in clubs_to_run}
    all_disagreements = [r for r in all_disagreements if r.get("club") not in rerun_clubs]

    for folder_name, club_id, pngs in clubs_to_run:
        club_name = CLUB_ID_TO_NAME[club_id]
        print(f"\n{'='*60}")
        print(f"  {club_name} ({club_id})  —  {len(pngs)} screenshots")
        print(f"{'='*60}")

        _doc, disagreements = run_club(
            club_id=club_id,
            club_name=club_name,
            png_paths=pngs,
            rubric=rubric,
            api_mode=args.api_mode,
            results_dir=args.results_dir,
            evidence_dir=args.evidence_dir,
            dry_run=args.dry_run,
        )
        all_disagreements.extend(disagreements)

    # Write disagreements
    args.disagreements.parent.mkdir(parents=True, exist_ok=True)
    args.disagreements.write_text(
        json.dumps(all_disagreements, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nDisagreements: {len(all_disagreements)} total -> {args.disagreements}")
    print("\nDone.")


if __name__ == "__main__":
    main()


__all__ = ["run_club", "CLUB_FOLDER_TO_ID", "CLUB_ID_TO_NAME"]
