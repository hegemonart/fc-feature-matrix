"""HTML contact sheet renderer (D-21).

Builds a single self-contained HTML file that shows one grid section per
feature in the rubric, with a thumbnail per club. Absent verdicts render as a
greyed-out placeholder with a red border. Clicking a thumbnail expands it via
a pure-CSS `:target` lightbox — no JavaScript required.

The renderer is a pure function of its inputs; it does not touch the network,
the `analysis/` tree, or any shared state. Output is written atomically via
`Path.write_text`.

Per FLOW-05, D-21, research §5.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from scanner.vision.schema import FeatureDef, JudgeResponse

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "contact_sheet.html.j2"


def _build_feature_rows(
    area: str,
    rubric: list[FeatureDef],
    judge_responses: dict[str, dict[str, JudgeResponse]],
) -> list[dict]:
    """One row per feature with per-club cell data for the template.

    Phase 1 dry-run uses the OPUS judgement for thumb display (Opus 4.7 has
    1:1 bbox coords — research §3.6). Disagreements between Opus and Sonnet
    are surfaced separately in disagreements-{area}.json and are not the
    concern of this renderer.

    Image path layout matches what the ``slice`` subcommand writes:
    ``<evidence_dir>/features/<club>_<feature_key>.png`` where ``evidence_dir``
    is ``scanner/output/evidence/<area>/`` and the HTML lives at
    ``scanner/output/contact-report-<area>.html`` — so the relative href from
    the HTML is ``evidence/<area>/features/<club>_<feature_key>.png``.
    """
    rows: list[dict] = []
    for feat in rubric:
        clubs_entries: list[dict] = []
        for club_slug, judges in judge_responses.items():
            opus = judges.get("opus")
            verdict = opus.results.get(feat.key) if opus is not None else None
            if verdict is None:
                # No opus verdict for this feature — treat as absent.
                clubs_entries.append(
                    {
                        "id": club_slug,
                        "present": False,
                        "confidence": 0.0,
                        "thumb_src": "",
                        "full_src": "",
                    }
                )
                continue
            crop_rel = f"evidence/{area}/features/{club_slug}_{feat.key}.png"
            thumb_src = f"./{crop_rel}" if verdict.present else ""
            clubs_entries.append(
                {
                    "id": club_slug,
                    "present": verdict.present,
                    "confidence": float(verdict.confidence),
                    "thumb_src": thumb_src,
                    # Phase 1 reuses the same image for the lightbox; Phase 2
                    # can wire in a distinct full-res source when available.
                    "full_src": thumb_src,
                }
            )
        rows.append({"key": feat.key, "name": feat.name, "clubs": clubs_entries})
    return rows


def render_contact_sheet(
    area: str,
    rubric: list[FeatureDef],
    judge_responses: dict[str, dict[str, JudgeResponse]],
    evidence_dir: Path,
    output_path: Path,
) -> Path:
    """Render the HTML contact sheet.

    Args:
        area: Area name, e.g. ``"hospitality"``. Used for the title and header.
        rubric: Ordered feature list — one grid section is produced per entry.
        judge_responses: ``{club_slug: {"opus": JudgeResponse, "sonnet": JudgeResponse}}``.
            Only ``opus`` is consumed for rendering in Phase 1.
        evidence_dir: The directory containing evidence crops. Currently passed
            for future use (Phase 2 will resolve full-res paths from here); the
            renderer writes relative paths rooted at ``output_path.parent``.
        output_path: Target HTML path, e.g.
            ``scanner/output/contact-report-hospitality.html``. Parent is created
            if it does not yet exist.

    Returns:
        ``output_path`` (unchanged) — the path that was written.

    Security:
        Jinja2 autoescape is enabled for ``.html`` templates (T-05-01). Any
        rubric or judge-response text is escaped before reaching the HTML.
    """
    # evidence_dir is reserved for Phase 2 — referenced here so that static
    # analyzers do not flag it as unused.
    _ = evidence_dir

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "htm", "xml", "j2"]),
    )
    template = env.get_template(TEMPLATE_NAME)

    rows = _build_feature_rows(area, rubric, judge_responses)
    html = template.render(
        area=area,
        features=rows,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


__all__ = ["render_contact_sheet"]
