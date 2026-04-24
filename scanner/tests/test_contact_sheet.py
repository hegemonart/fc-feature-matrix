"""Tests for scanner.report.contact_sheet (Jinja2 render).

Covers six behaviours per 01-05-PLAN Task 1:

    1. HTML file is written to the given output_path.
    2. One `<div class="feature">` block per rubric entry.
    3. Absent verdict -> `thumb absent` CSS class.
    4. Present verdict -> `<img src=...>` tag + confidence label.
    5. Grid styling sanity (`grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))`).
    6. File is non-empty and ends with `</html>`.

Fixtures are constructed directly from the Pydantic schema in scanner.vision.schema;
no SDK mocking is required because the renderer is a pure function.

Per D-21 (contact sheet), FLOW-05, research §5.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scanner.report.contact_sheet import render_contact_sheet
from scanner.vision.schema import FeatureDef, FeatureVerdict, JudgeResponse


# ---------------------------------------------------------------------------
# Fixtures — pure data, no mocks.
# ---------------------------------------------------------------------------


@pytest.fixture
def rubric() -> list[FeatureDef]:
    """Three-feature rubric mirroring the frozen dry-run fixture."""
    return [
        FeatureDef(
            key="hero_image",
            name="Hero image / banner",
            yes_criterion="Large above-the-fold hero image or video banner.",
        ),
        FeatureDef(
            key="primary_cta",
            name="Primary CTA button",
            yes_criterion="Visually-primary call-to-action button leading to enquiry or booking.",
        ),
        FeatureDef(
            key="hospitality_tiers_list",
            name="Hospitality tiers or packages list",
            yes_criterion="Two or more distinct hospitality packages or tiers with structural distinction.",
        ),
    ]


@pytest.fixture
def judge_responses() -> dict[str, dict[str, JudgeResponse]]:
    """One club ('mancity') with opus+sonnet verdicts.

    - hero_image: present (confidence 0.92) in opus.
    - primary_cta: present (confidence 0.80) in opus.
    - hospitality_tiers_list: ABSENT in opus (thumb absent path).

    Sonnet data included for symmetry though Phase 1 contact sheet uses opus.
    """
    opus = JudgeResponse(
        model="claude-opus-4-7",
        results={
            "hero_image": FeatureVerdict(
                present=True,
                step="step_1",
                evidence_bbox=(0.0, 0.0, 400.0, 300.0),
                confidence=0.92,
                notes="Hero banner shown.",
            ),
            "primary_cta": FeatureVerdict(
                present=True,
                step="step_1",
                evidence_bbox=(10.0, 400.0, 200.0, 60.0),
                confidence=0.80,
                notes="Primary CTA present.",
            ),
            "hospitality_tiers_list": FeatureVerdict(
                present=False,
                step="step_1",
                evidence_bbox=None,
                confidence=0.10,
                notes="No tiers list detected.",
            ),
        },
    )
    sonnet = JudgeResponse(
        model="claude-sonnet-4-6",
        results={
            "hero_image": FeatureVerdict(
                present=True,
                step="step_1",
                evidence_bbox=(0.0, 0.0, 400.0, 300.0),
                confidence=0.88,
                notes="",
            ),
            "primary_cta": FeatureVerdict(
                present=True,
                step="step_1",
                evidence_bbox=(10.0, 400.0, 200.0, 60.0),
                confidence=0.75,
                notes="",
            ),
            "hospitality_tiers_list": FeatureVerdict(
                present=False,
                step="step_1",
                evidence_bbox=None,
                confidence=0.12,
                notes="",
            ),
        },
    )
    return {"mancity": {"opus": opus, "sonnet": sonnet}}


@pytest.fixture
def evidence_dir(tmp_path: Path) -> Path:
    d = tmp_path / "evidence" / "hospitality"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def rendered(
    tmp_path: Path,
    rubric: list[FeatureDef],
    judge_responses: dict[str, dict[str, JudgeResponse]],
    evidence_dir: Path,
) -> tuple[Path, str]:
    """Render once; return (path, html_text)."""
    out = tmp_path / "contact-report-hospitality.html"
    written = render_contact_sheet(
        area="hospitality",
        rubric=rubric,
        judge_responses=judge_responses,
        evidence_dir=evidence_dir,
        output_path=out,
    )
    assert written == out
    return out, out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Behaviour 1 — file exists.
# ---------------------------------------------------------------------------


def test_renders_html_file_to_output_path(rendered: tuple[Path, str]) -> None:
    path, _ = rendered
    assert path.exists()
    assert path.is_file()


# ---------------------------------------------------------------------------
# Behaviour 2 — one feature div per rubric entry.
# ---------------------------------------------------------------------------


def test_one_feature_block_per_rubric_entry(rendered: tuple[Path, str]) -> None:
    _, html = rendered
    # Jinja autoescape doesn't touch class names; simple count is safe.
    assert html.count('<div class="feature">') == 3


# ---------------------------------------------------------------------------
# Behaviour 3 — absent verdict -> thumb absent class.
# ---------------------------------------------------------------------------


def test_absent_verdict_renders_thumb_absent_div(rendered: tuple[Path, str]) -> None:
    _, html = rendered
    # hospitality_tiers_list is absent in the fixture.
    assert "thumb absent" in html


# ---------------------------------------------------------------------------
# Behaviour 4 — present verdict -> img tag + confidence label.
# ---------------------------------------------------------------------------


def test_present_verdict_renders_img_tag_and_confidence(rendered: tuple[Path, str]) -> None:
    _, html = rendered
    # Thumb src is relative to HTML parent, points into evidence tree.
    assert "mancity_hero_image.png" in html
    assert "<img src=" in html
    # Confidence rendered with 2 decimals per template.
    assert "0.92" in html


# ---------------------------------------------------------------------------
# Behaviour 5 — grid styling sanity.
# ---------------------------------------------------------------------------


def test_grid_template_columns_present(rendered: tuple[Path, str]) -> None:
    _, html = rendered
    assert "grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))" in html


# ---------------------------------------------------------------------------
# Behaviour 6 — non-empty file ending in </html>.
# ---------------------------------------------------------------------------


def test_html_file_is_nonzero_and_ends_with_closing_tag(rendered: tuple[Path, str]) -> None:
    path, html = rendered
    assert path.stat().st_size > 0
    # Trim trailing whitespace/newlines before asserting the closing tag.
    assert html.rstrip().endswith("</html>")


# ---------------------------------------------------------------------------
# Bonus coverage — CSS-only :target lightbox anchor (research §5.3).
# ---------------------------------------------------------------------------


def test_lightbox_target_selector_present(rendered: tuple[Path, str]) -> None:
    _, html = rendered
    # Pure-CSS lightbox requires :target rule AND a matching anchor per present verdict.
    assert ":target" in html
    assert 'href="#lb-hero_image-mancity"' in html


# ---------------------------------------------------------------------------
# Bonus coverage — autoescape enabled (XSS safety, T-05-01).
# ---------------------------------------------------------------------------


def test_autoescape_escapes_rubric_content(
    tmp_path: Path,
    judge_responses: dict[str, dict[str, JudgeResponse]],
    evidence_dir: Path,
) -> None:
    """A malicious feature name must render as escaped text, not raw HTML."""
    malicious = [
        FeatureDef(
            key="hero_image",
            name="<script>alert('xss')</script>",
            yes_criterion="",
        )
    ]
    out = tmp_path / "xss.html"
    render_contact_sheet(
        area="hospitality",
        rubric=malicious,
        judge_responses=judge_responses,
        evidence_dir=evidence_dir,
        output_path=out,
    )
    html = out.read_text(encoding="utf-8")
    # Literal <script> must not appear; the escaped form must.
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;" in html
