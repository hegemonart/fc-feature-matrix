"""FC Benchmark scanner CLI — Click group (D-03 + D-04 + D-27).

Single entry point for every Phase-1 module:

- ``scanner capture``  -> Plan 03 full-page capture
- ``scanner vision``   -> Plan 04 two-judge (Opus + Sonnet) feature mapping
- ``scanner slice``    -> Plan 04 PIL crop per feature bbox
- ``scanner report``   -> Plan 05 HTML contact sheet
- ``scanner score``    -> scanner/scoring/recalculate.js (Node)
- ``scanner flow``     -> Plan 06 flow-map validate + discover

Design notes:

- Every subcommand defers its heavy imports (Playwright, anthropic SDK,
  claude-agent-sdk, PIL, Jinja2) into the function body so that
  ``python -m scanner --help`` responds in ~tens of ms and so that a
  missing optional backend does not break an unrelated subcommand.
- ``--api-mode`` defaults to ``subscription`` per D-28 (Claude Max 20x
  quota via ``claude-agent-sdk``). Fallback is ``api-key`` — requires
  ``ANTHROPIC_API_KEY`` in env (checked by :func:`scanner.vision.factory.get_client`).
- ``--headless`` defaults to ``False`` per user decision 2 — developers
  run headed; CI flips it with ``--headless``.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("scanner")


@click.group()
@click.version_option("0.1.0")
def cli() -> None:
    """FC Benchmark scanner — area-agnostic flow capture tooling."""


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--area", required=True, help="Area slug (e.g. hospitality).")
@click.option("--club", required=True, help="Club slug (e.g. mancity).")
@click.option("--url", required=True, help="Target page URL.")
@click.option("--step", default="landing", show_default=True, help="Flow-step name for the output filename.")
@click.option(
    "--headless/--no-headless",
    default=False,
    show_default=True,
    help="Headed by default (developer) — pass --headless for CI.",
)
def capture(area: str, club: str, url: str, step: str, headless: bool) -> None:
    """Capture a full-page screenshot with Playwright."""
    from scanner.capture.capture import capture_page
    from scanner.config.loader import load_area, REPO_ROOT

    entry = load_area(area)
    output_dir = REPO_ROOT / entry.evidence_dir
    out = capture_page(
        url=url,
        club=club,
        area=area,
        step_name=step,
        output_dir=output_dir,
        headless=headless,
    )
    click.echo(f"Captured: {out}")


# ---------------------------------------------------------------------------
# vision
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--area", required=True)
@click.option("--club", required=True)
@click.option(
    "--rubric",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to a rubric JSON file (list of FeatureDef under `features`).",
)
@click.option(
    "--api-mode",
    type=click.Choice(["subscription", "api-key"]),
    default="subscription",
    show_default=True,
    help="Vision backend. subscription=claude-agent-sdk (Max 20x quota, DEFAULT); api-key=anthropic SDK.",
)
@click.option("--step", default="landing", show_default=True)
def vision(area: str, club: str, rubric: Path, api_mode: str, step: str) -> None:
    """Run two-judge (Opus + Sonnet) feature mapping on captured screenshots."""
    from scanner.config.loader import load_area, REPO_ROOT
    from scanner.vision.judge import two_judge
    from scanner.vision.disagreement import find_disagreements, write_disagreements
    from scanner.vision.schema import FeatureDef

    entry = load_area(area)
    evidence_dir = REPO_ROOT / entry.evidence_dir
    image_path = evidence_dir / "fullpage" / f"{club}_{step}.png"
    if not image_path.exists():
        raise click.ClickException(
            f"Screenshot not found: {image_path}. Run `scanner capture` first."
        )

    rubric_data = json.loads(Path(rubric).read_text(encoding="utf-8"))
    features = [FeatureDef(**f) for f in rubric_data["features"]]

    judges = two_judge(image_path, features, api_mode=api_mode)
    results_dir = REPO_ROOT / entry.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"{club}_features.json"
    out.write_text(
        json.dumps(
            {
                "club": club,
                "area": area,
                "step": step,
                "api_mode": api_mode,
                "opus": {k: v.model_dump() for k, v in judges["opus"].results.items()},
                "sonnet": {k: v.model_dump() for k, v in judges["sonnet"].results.items()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    disagreements = find_disagreements(
        judges["opus"].results, judges["sonnet"].results
    )
    write_disagreements(
        disagreements,
        REPO_ROOT / "scanner" / "output" / f"disagreements-{area}.json",
    )
    click.echo(f"Vision complete: {out}  disagreements={len(disagreements)}")


# ---------------------------------------------------------------------------
# slice
# ---------------------------------------------------------------------------


@cli.command(name="slice")
@click.option("--area", required=True)
@click.option("--club", required=True)
@click.option("--step", default="landing", show_default=True)
def slice_cmd(area: str, club: str, step: str) -> None:
    """PIL-crop each present feature from the Opus judgement into evidence/features/."""
    from io import BytesIO

    from PIL import Image

    from scanner.config.loader import load_area, REPO_ROOT
    from scanner.vision.judge import OPUS_MODEL
    from scanner.vision.slice import denormalise_bbox, slice_feature

    entry = load_area(area)
    evidence_dir = REPO_ROOT / entry.evidence_dir
    fullpage = evidence_dir / "fullpage" / f"{club}_{step}.png"
    results_path = REPO_ROOT / entry.results_dir / f"{club}_features.json"
    if not fullpage.exists():
        raise click.ClickException(
            f"Screenshot not found: {fullpage}. Run `scanner capture` first."
        )
    if not results_path.exists():
        raise click.ClickException(
            f"Results not found: {results_path}. Run `scanner vision` first."
        )

    results = json.loads(results_path.read_text(encoding="utf-8"))
    png_bytes = fullpage.read_bytes()
    img = Image.open(BytesIO(png_bytes))
    fw, fh = img.size

    count = 0
    for fkey, verdict in results["opus"].items():
        if not verdict.get("present") or not verdict.get("evidence_bbox"):
            continue
        bbox = denormalise_bbox(tuple(verdict["evidence_bbox"]), OPUS_MODEL, fw, fh)
        out = evidence_dir / "features" / f"{club}_{fkey}.png"
        res = slice_feature(png_bytes, bbox, out)
        if res.ok:
            count += 1
            click.echo(f"  sliced: {out}")
        else:
            click.echo(f"  skipped {fkey}: {res.reason}", err=True)
    click.echo(f"Sliced {count} features.")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--area", required=True)
def report(area: str) -> None:
    """Render the HTML contact sheet for an area."""
    from scanner.config.loader import load_area, REPO_ROOT
    from scanner.report.contact_sheet import render_contact_sheet
    from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse

    entry = load_area(area)
    evidence_dir = REPO_ROOT / entry.evidence_dir
    results_dir = REPO_ROOT / entry.results_dir
    output_path = REPO_ROOT / "scanner" / "output" / f"contact-report-{area}.html"

    judge_responses: dict[str, dict[str, JudgeResponse]] = {}
    rubric: list[FeatureDef] = []
    seen_keys: set[str] = set()
    for f in sorted(results_dir.glob("*_features.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        club = data["club"]
        judge_responses[club] = {
            "opus": JudgeResponse(
                model="claude-opus-4-7",
                results={k: FeatureVerdict(**v) for k, v in data["opus"].items()},
            ),
            "sonnet": JudgeResponse(
                model="claude-sonnet-4-6",
                results={k: FeatureVerdict(**v) for k, v in data["sonnet"].items()},
            ),
        }
        for k in data["opus"]:
            if k not in seen_keys:
                seen_keys.add(k)
                rubric.append(
                    FeatureDef(
                        key=k,
                        name=k.replace("_", " ").title(),
                        yes_criterion="(Phase 2)",
                    )
                )

    out = render_contact_sheet(
        area=area,
        rubric=rubric,
        judge_responses=judge_responses,
        evidence_dir=evidence_dir,
        output_path=output_path,
    )
    click.echo(f"Report: {out}")


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--area", required=True)
def score(area: str) -> None:
    """Re-compute scores via scanner/scoring/recalculate.js (Node)."""
    import subprocess

    script = Path(__file__).resolve().parent / "scoring" / "recalculate.js"
    result = subprocess.run(["node", str(script), "--area", area], check=False)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# flow
# ---------------------------------------------------------------------------


@cli.group()
def flow() -> None:
    """Flow-map operations: validate, discover."""


@flow.command("validate")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def flow_validate_cmd(path: Path) -> None:
    """Validate a flow-map JSON file against the FlowMap schema."""
    from scanner.flow.validate import FlowMapValidationError, validate_flow_map

    try:
        fm = validate_flow_map(path)
    except FlowMapValidationError as e:
        raise click.ClickException(str(e))
    click.echo(f"Valid: {fm.area}/{fm.club} — {len(fm.steps)} step(s).")


@flow.command("discover")
@click.argument("entry_url")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Destination path for the generated flow-map JSON.",
)
@click.option(
    "--area",
    default="hospitality",
    show_default=True,
    help="Area slug recorded in the emitted FlowMap.",
)
@click.option(
    "--club",
    default=None,
    help="Club slug for cookie-strategy dispatch. Inferred from entry_url if omitted.",
)
@click.option(
    "--headless/--headed",
    default=True,
    show_default=True,
    help="Run Chromium headless (default) or with a visible window.",
)
def flow_discover_cmd(
    entry_url: str,
    out_path: Path,
    area: str,
    club: str | None,
    headless: bool,
) -> None:
    """Discover click-paths from an entry URL.

    Launches a sync-Playwright Chromium session, dismisses cookie banners,
    and performs a keyword-ranked depth-limited crawl (max 3 deep, 15 steps).
    Emits a schema-valid FlowMap JSON at --out. Records login-gated,
    CAPTCHA-gated, broker-redirected, externally-redirected, and dead-end
    branches in FlowMap.metadata (see scanner.flow.schema.FlowMapMetadata).

    Never submits forms (D-16); never bypasses login or CAPTCHA (D-15).
    """
    from scanner.flow.discover import discover_flow

    fm = discover_flow(entry_url, out_path, area=area, club=club, headless=headless)
    click.echo(
        f"Wrote {out_path} — {fm.area}/{fm.club} {len(fm.steps)} step(s); "
        f"broker={fm.metadata.broker_vendor or '-'}, "
        f"login_gates={len(fm.metadata.login_gated_steps)}, "
        f"external={len(fm.metadata.external_redirects)}, "
        f"dead_ends={len(fm.metadata.dead_ends)}, "
        f"captcha={fm.metadata.captcha_encountered}"
    )


__all__ = ["cli"]
