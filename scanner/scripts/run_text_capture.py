"""Plan 02-20 entry-point: run text-based capture for a club using
the reseller_urls.json config.

Usage::

    python -m scanner.scripts.run_text_capture --area hospitality --club mancity

Writes:
  - scanner/output/evidence/{area}/dom/{club}_synthetic_intel.json
  - scanner/output/evidence/{area}/dom/{club}_{step}_intel.json (one per
    step in covers_steps)
  - scanner/output/text/{area}/{club}_aggregated.md
  - scanner/output/capture-run-log-{area}-{club}-synthetic.json

This is a thin wrapper around :mod:`scanner.capture.text_fetch`. The
heavy lifting is in that module; this script just resolves config
paths and dispatches.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from scanner.capture.text_fetch import (
    fetch_text_for_club,
    write_synthetic_outputs,
    write_synthetic_run_log,
)

logger = logging.getLogger(__name__)


@click.command()
@click.option("--area", required=True, help="Area slug (hospitality).")
@click.option("--club", required=True, help="Club slug (mancity, psg, ...).")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("scanner/config/reseller_urls.json"),
    help="Path to reseller_urls.json.",
)
@click.option(
    "--output-root",
    type=click.Path(path_type=Path),
    default=Path("scanner/output"),
    help="Root output directory (matches existing scanner output layout).",
)
def main(area: str, club: str, config_path: Path, output_root: Path) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if area not in cfg:
        click.echo(f"ERR: area '{area}' not in {config_path}", err=True)
        sys.exit(2)
    if club not in cfg[area]:
        click.echo(
            f"ERR: club '{club}' not in {config_path} for area '{area}'",
            err=True,
        )
        sys.exit(2)

    entry = cfg[area][club]
    intel, fetches = fetch_text_for_club(
        club_id=club,
        club_name=entry["club_name"],
        official_url=entry["official_url"],
        reseller_urls=entry["reseller_urls"],
    )

    intel_dir = output_root / "evidence" / area / "dom"
    audit_dir = output_root / "text" / area
    summary = write_synthetic_outputs(
        intel=intel,
        fetches=fetches,
        club_id=club,
        intel_dir=intel_dir,
        audit_dir=audit_dir,
        covers_steps=entry["covers_steps"],
    )

    # Emit a synthetic run-log so run_vision_wave can iterate.
    run_log_path = output_root / f"capture-run-log-{area}-{club}-synthetic.json"
    write_synthetic_run_log(
        run_log_path=run_log_path,
        club_id=club,
        area=area,
        covers_steps=entry["covers_steps"],
    )

    # Status line.
    ok = sum(1 for f in fetches if f.status == 200 and f.text)
    failed = len(fetches) - ok
    click.echo(
        f"text-capture: {club} area={area} ok={ok}/{len(fetches)} "
        f"failed={failed} text-chars={summary['total_text_chars']} "
        f"intel-files={len(summary['intel_step_files'])} "
        f"run-log={run_log_path.name} "
        f"audit={Path(summary['audit_md']).name}"
    )
    # Per-source breakdown to stdout for run-log forensics.
    click.echo("Per-source results:")
    for fr in fetches:
        line = f"  HTTP {fr.status} ({len(fr.text)} chars)"
        if fr.error:
            line += f" ERROR: {fr.error}"
        click.echo(f"  {fr.url} -> {line}")
    click.echo(f"completed_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
