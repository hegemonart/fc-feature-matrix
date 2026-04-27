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
@click.option("--url", required=False, default=None, help="Target page URL (single-page mode, Phase 1).")
@click.option(
    "--flow-map",
    "flow_map",
    type=click.Path(exists=True, path_type=Path),
    required=False,
    default=None,
    help="Path to a FlowMap JSON for multi-step orchestrator mode (Plan 02-10). Mutually exclusive with --url.",
)
@click.option("--step", default="landing", show_default=True, help="Flow-step name for the output filename (single-page mode only).")
@click.option(
    "--headless/--no-headless",
    default=False,
    show_default=True,
    help="Headed by default (developer) — pass --headless for CI.",
)
@click.option(
    "--auto-skip-manual/--no-auto-skip-manual",
    default=False,
    show_default=True,
    help="Flow-map mode only: auto-record manual_chrome_mcp steps without prompting (unattended runs).",
)
def capture(
    area: str,
    club: str,
    url: str | None,
    flow_map: Path | None,
    step: str,
    headless: bool,
    auto_skip_manual: bool,
) -> None:
    """Capture a full-page screenshot with Playwright.

    Two modes (mutually exclusive):
    - ``--url URL``        single-page (Phase 1 behavior).
    - ``--flow-map PATH``  multi-step orchestrator (Plan 02-10).
    """
    # Mutual exclusion gate — exactly one of --url / --flow-map.
    if url and flow_map:
        raise click.UsageError("--url and --flow-map are mutually exclusive.")
    if not url and not flow_map:
        raise click.UsageError("Specify exactly one of --url or --flow-map.")

    from scanner.config.loader import load_area, REPO_ROOT

    entry = load_area(area)
    output_dir = REPO_ROOT / entry.evidence_dir

    if flow_map is not None:
        # Multi-step orchestrator mode.
        from datetime import datetime, timezone
        from scanner.capture.capture import capture_flow

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = (
            REPO_ROOT
            / "scanner"
            / "output"
            / f"capture-run-log-{area}-{club}-{ts}.json"
        )
        result = capture_flow(
            flow_map_path=flow_map,
            club=club,
            area=area,
            output_dir=output_dir,
            log_path=log_path,
            headless=headless,
            auto_skip_manual=auto_skip_manual,
        )
        t = result["totals"]
        click.echo(
            f"Captured {t['captured']} | skipped {t['skipped']} | "
            f"chrome-mcp {t['chrome_mcp']} | missing-creds {t['missing']} | "
            f"errors {t['error']}"
        )
        click.echo(f"Run-log: {log_path}")
    else:
        # Single-page mode (Phase 1 — preserved unchanged).
        from scanner.capture.capture import capture_page

        out = capture_page(
            url=url,  # type: ignore[arg-type]
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
@click.option(
    "--step",
    default="landing",
    show_default=True,
    help=(
        "Flow-step name. Special value '*' iterates every captured step in the "
        "per-club result JSON (Plan 02-11 multi-step shape)."
    ),
)
def slice_cmd(area: str, club: str, step: str) -> None:
    """PIL-crop each present feature from the Opus judgement into the features dir.

    Plan 02-12 changes (D-21 call-site only):

    - Reads optional ``features_evidence_dir`` from the area config; falls back
      to ``evidence_dir/features/`` when unset (Phase 1 contract preserved).
    - Accepts ``--step '*'`` to iterate every step recorded under the
      Plan-02-11 ``{steps: {step: {opus, sonnet}}}`` shape.
    - Backwards-compatible with the Phase-1 single-step ``{opus: {...}}`` shape.

    The denormalise_bbox + slice_feature math in ``scanner.vision.slice`` is
    NOT modified — this is config-passing only.
    """
    from io import BytesIO

    from PIL import Image

    from scanner.config.loader import load_area, REPO_ROOT
    from scanner.vision.judge import OPUS_MODEL
    from scanner.vision.slice import denormalise_bbox, slice_feature

    entry = load_area(area)
    evidence_dir = REPO_ROOT / entry.evidence_dir

    # Plan 02-12: optional canonical-path override. Defaults to the Phase-1
    # `<evidence_dir>/features/` location so single-page Phase-1 callers are
    # untouched.
    features_evidence_dir = (
        REPO_ROOT / entry.features_evidence_dir
        if getattr(entry, "features_evidence_dir", None)
        else evidence_dir / "features"
    )

    results_path = REPO_ROOT / entry.results_dir / f"{club}_features.json"
    if not results_path.exists():
        raise click.ClickException(
            f"Results not found: {results_path}. Run `scanner vision` first."
        )
    results = json.loads(results_path.read_text(encoding="utf-8"))

    # Plan 02-08: per-area bbox_mode config gate. When 'native' AND the model
    # is Opus, SKIP denormalise_bbox. The denormalise math itself is left
    # untouched (D-21 deviation: call-site config gate only).
    bbox_mode = getattr(entry, "bbox_mode", "css")

    # Resolve the (step_name, opus_verdicts) pairs to slice. Two shapes:
    #   - Plan-02-11 multi-step:  results["steps"][step]["opus"]
    #   - Phase-1 single-step:    results["opus"]
    steps_map = results.get("steps")
    if steps_map is not None:
        if step == "*":
            step_pairs = [(s, steps_map[s].get("opus", {})) for s in steps_map]
        else:
            if step not in steps_map:
                raise click.ClickException(
                    f"Step {step!r} not in result JSON. Captured steps: "
                    f"{sorted(steps_map.keys())}. Use --step '*' to iterate all."
                )
            step_pairs = [(step, steps_map[step].get("opus", {}))]
    else:
        # Phase-1 shape — single implicit step.
        step_pairs = [(step, results.get("opus", {}))]

    # Multi-step deduplication: when a feature is present in multiple steps,
    # slice from the FIRST step where its bbox is non-null. Track keys we've
    # already emitted to avoid clobbering.
    sliced_keys: set[str] = set()
    count = 0
    skipped: list[str] = []

    for step_name, opus_verdicts in step_pairs:
        fullpage = evidence_dir / "fullpage" / f"{club}_{step_name}.png"
        if not fullpage.exists():
            click.echo(
                f"  no fullpage PNG for step={step_name}: {fullpage} (skipping)",
                err=True,
            )
            continue
        png_bytes = fullpage.read_bytes()
        img = Image.open(BytesIO(png_bytes))
        fw, fh = img.size

        for fkey, verdict in opus_verdicts.items():
            if fkey in sliced_keys:
                continue
            if not verdict.get("present") or not verdict.get("evidence_bbox"):
                continue
            raw_bbox = tuple(verdict["evidence_bbox"])
            if bbox_mode == "native" and OPUS_MODEL.startswith("claude-opus"):
                bbox = raw_bbox
            else:
                bbox = denormalise_bbox(raw_bbox, OPUS_MODEL, fw, fh)
            out = features_evidence_dir / f"{club}_{fkey}.png"
            res = slice_feature(png_bytes, bbox, out)
            if res.ok:
                count += 1
                sliced_keys.add(fkey)
                click.echo(f"  sliced: {out}")
            else:
                skipped.append(f"{step_name}/{fkey}: {res.reason}")
                click.echo(
                    f"  skipped {step_name}/{fkey}: {res.reason}", err=True
                )

    click.echo(f"Sliced {count} features.")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--area", required=True)
def report(area: str) -> None:
    """Render the HTML contact sheet for an area.

    Plan 02-12 Rule-1 fix: tolerates both per-club JSON shapes:

    - Phase-1 single-step:  ``{opus: {...}, sonnet: {...}}``
    - Plan-02-11 multi-step: ``{steps: {step: {opus, sonnet}}}``

    For the multi-step shape, the per-feature verdict is OR-merged across
    captured steps (a feature is "present" if any step's Opus says present).
    """
    from scanner.config.loader import load_area, REPO_ROOT
    from scanner.report.contact_sheet import render_contact_sheet
    from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse

    entry = load_area(area)
    evidence_dir = REPO_ROOT / entry.evidence_dir
    results_dir = REPO_ROOT / entry.results_dir
    output_path = REPO_ROOT / "scanner" / "output" / f"contact-report-{area}.html"

    # Plan 02-12: prefer canonical features_evidence_dir when set.
    features_evidence_dir = (
        REPO_ROOT / entry.features_evidence_dir
        if getattr(entry, "features_evidence_dir", None)
        else evidence_dir / "features"
    )

    def _merge_multistep_verdicts(
        steps_map: dict[str, dict[str, dict]], judge: str
    ) -> dict[str, dict]:
        """OR-merge per-step verdicts for one judge across captured steps.

        First step wins for the verdict shape; later steps only flip
        ``present`` to True when a present-true reading appears (matches the
        slice CLI's first-bbox-wins semantic).
        """
        merged: dict[str, dict] = {}
        for step_name, judges in steps_map.items():
            j = (judges.get(judge) or {})
            for fkey, verdict in j.items():
                if fkey not in merged:
                    merged[fkey] = dict(verdict)
                elif verdict.get("present") and not merged[fkey].get("present"):
                    # Promote to present using this step's bbox/notes.
                    merged[fkey] = dict(verdict)
        return merged

    judge_responses: dict[str, dict[str, JudgeResponse]] = {}
    rubric: list[FeatureDef] = []
    seen_keys: set[str] = set()
    for f in sorted(results_dir.glob("*_features.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        club = data["club"]
        # Plan 02-12: tolerate both shapes.
        if "steps" in data:
            opus_verdicts = _merge_multistep_verdicts(data["steps"], "opus")
            sonnet_verdicts = _merge_multistep_verdicts(data["steps"], "sonnet")
        else:
            opus_verdicts = data.get("opus", {})
            sonnet_verdicts = data.get("sonnet", {})
        judge_responses[club] = {
            "opus": JudgeResponse(
                model="claude-opus-4-7",
                results={k: FeatureVerdict(**v) for k, v in opus_verdicts.items()},
            ),
            "sonnet": JudgeResponse(
                model="claude-sonnet-4-6",
                results={k: FeatureVerdict(**v) for k, v in sonnet_verdicts.items()},
            ),
        }
        for k in opus_verdicts:
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
        features_evidence_dir=features_evidence_dir,
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
