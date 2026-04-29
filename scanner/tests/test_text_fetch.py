"""Tests for scanner.capture.text_fetch (Plan 02-20).

We do NOT make live HTTP calls here — :func:`_fetch_url` is monkey-patched
to return canned ``FetchResult`` objects. The intent of these tests is:

1. The HTML→text parser strips script/style and captures headings + anchors.
2. ``synthesize_dom_intel`` produces a DomIntel with ``source="synthetic"``,
   non-empty ``text_extracts``, and merged headings/buttons.
3. ``fetch_text_for_club`` glues fetcher + synthesizer correctly.
4. ``write_synthetic_outputs`` lays files in the expected places.
5. The hybrid pipeline's DOM rules fire on synthetic intel (smoke test
   bridging Plan 02-20 Phases 1–2).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scanner.capture import text_fetch
from scanner.capture.dom_intel import DomIntel
from scanner.capture.text_fetch import (
    FetchResult,
    _fetch_url,
    _normalize_text,
    _TextExtractor,
    fetch_text_for_club,
    synthesize_dom_intel,
    write_synthetic_outputs,
    write_synthetic_run_log,
)


# ---------------------------------------------------------------------------
# HTML extractor
# ---------------------------------------------------------------------------


def test_text_extractor_strips_script_and_style():
    p = _TextExtractor()
    p.feed(
        """
        <html><head><title>T</title>
        <script>var x = 1; alert('boom');</script>
        <style>.x { display: none; }</style>
        </head>
        <body>
        <h1>Manchester City Tunnel Club</h1>
        <p>From £550 per person, includes parking.</p>
        <a href="/book">Book Now</a>
        </body></html>
        """
    )
    p.close()
    text = "".join(p.buf)
    assert "var x = 1" not in text
    assert "alert" not in text
    assert "display: none" not in text
    assert "Tunnel Club" in text
    assert any(t == "H1" and "Tunnel Club" in s for (t, s) in p.headings)
    assert any(t == "Book Now" for (t, _) in p.links)


def test_normalize_text_collapses_whitespace():
    raw = "Hello   world\n\n\n\n    foo\n  \n bar"
    out = _normalize_text(raw)
    # No 3+ consecutive newlines.
    assert "\n\n\n" not in out
    # Single-spaces between tokens.
    assert "Hello world" in out
    # Trailing whitespace stripped per-line.
    assert out.endswith("bar")


# ---------------------------------------------------------------------------
# Synthesize DomIntel
# ---------------------------------------------------------------------------


def test_synthesize_dom_intel_marks_synthetic_source():
    fetches = [
        FetchResult(
            url="https://example.com/mancity",
            status=200,
            text="Tunnel Club — from £550 per person",
            headings=[("H1", "Manchester City Hospitality")],
            links=[("Book Now", "/book")],
        ),
    ]
    intel = synthesize_dom_intel(
        club_id="mancity",
        club_name="Manchester City",
        official_url="https://www.mancity.com/hospitality",
        fetches=fetches,
    )
    assert intel.source == "synthetic"
    assert intel.url == "https://www.mancity.com/hospitality"
    assert "synthetic" in intel.title.lower()
    assert any("Tunnel Club" in t for t in intel.text_extracts)
    assert any(h.text == "Manchester City Hospitality" for h in intel.headings)
    assert any(b.text == "Book Now" for b in intel.buttons)
    assert intel.meta["synthetic_n_sources"] == "1"
    # No live form / table data.
    assert intel.forms == []
    assert intel.counts.tables == 0


def test_synthesize_dom_intel_dedups_headings_and_buttons():
    fr1 = FetchResult(
        url="https://a.example/", status=200, text="Hi",
        headings=[("H1", "VIP Hospitality")], links=[("Book", "/x")],
    )
    fr2 = FetchResult(
        url="https://b.example/", status=200, text="Hi",
        headings=[("H1", "VIP HOSPITALITY")], links=[("Book", "/x")],
    )
    intel = synthesize_dom_intel(
        club_id="x", club_name="X",
        official_url="https://x.example/",
        fetches=[fr1, fr2],
    )
    assert len(intel.headings) == 1
    assert len(intel.buttons) == 1


def test_synthesize_dom_intel_skips_failed_fetches():
    fetches = [
        FetchResult(url="ok", status=200, text="content here",
                    headings=[("H1", "t")], links=[]),
        FetchResult(url="fail", status=403, text="", error="HTTP 403"),
    ]
    intel = synthesize_dom_intel(
        club_id="x", club_name="X",
        official_url="https://x.example/",
        fetches=fetches,
    )
    assert intel.meta["synthetic_n_sources"] == "1"
    assert intel.meta["synthetic_n_failed"] == "1"
    # Only the OK fetch contributes to text_extracts.
    assert len(intel.text_extracts) == 1


# ---------------------------------------------------------------------------
# Top-level glue
# ---------------------------------------------------------------------------


def test_fetch_text_for_club_uses_fetch_url_per_url(monkeypatch):
    calls: list[str] = []

    def fake_fetch(url: str, *, timeout: float = 0):
        calls.append(url)
        return FetchResult(
            url=url, status=200, text=f"text for {url}",
            headings=[("H2", "tier name")], links=[],
        )

    monkeypatch.setattr(text_fetch, "_fetch_url", fake_fetch)
    intel, fetches = fetch_text_for_club(
        club_id="mancity",
        club_name="Manchester City",
        official_url="https://www.mancity.com/hospitality",
        reseller_urls=[
            "https://a.example/", "https://b.example/", "https://c.example/",
        ],
    )
    assert calls == ["https://a.example/", "https://b.example/", "https://c.example/"]
    assert intel.source == "synthetic"
    assert len(fetches) == 3
    assert all(f.status == 200 for f in fetches)


# ---------------------------------------------------------------------------
# Persisted outputs
# ---------------------------------------------------------------------------


def test_write_synthetic_outputs_creates_per_step_files(tmp_path: Path):
    intel = DomIntel(
        title="x", url="u", source="synthetic",
        text_extracts=["lorem ipsum"],
    )
    fetches = [FetchResult(url="https://a/", status=200, text="lorem ipsum",
                           headings=[], links=[])]
    summary = write_synthetic_outputs(
        intel=intel,
        fetches=fetches,
        club_id="psg",
        intel_dir=tmp_path / "dom",
        audit_dir=tmp_path / "text",
        covers_steps=["landing-shot", "match-selector-shot"],
    )
    assert (tmp_path / "dom" / "psg_landing-shot_intel.json").exists()
    assert (tmp_path / "dom" / "psg_match-selector-shot_intel.json").exists()
    assert (tmp_path / "dom" / "psg_synthetic_intel.json").exists()
    assert (tmp_path / "text" / "psg_aggregated.md").exists()
    # Per-step intel JSON is valid + carries source=synthetic.
    payload = json.loads(
        (tmp_path / "dom" / "psg_landing-shot_intel.json").read_text(encoding="utf-8")
    )
    assert payload["source"] == "synthetic"
    assert payload["text_extracts"] == ["lorem ipsum"]
    # Audit MD references the source URL.
    md = (tmp_path / "text" / "psg_aggregated.md").read_text(encoding="utf-8")
    assert "https://a/" in md
    assert summary["ok_sources"] == 1
    assert summary["failed_sources"] == 0


def test_write_synthetic_run_log_uses_status_synthetic(tmp_path: Path):
    out = tmp_path / "run-log.json"
    write_synthetic_run_log(
        run_log_path=out,
        club_id="mancity",
        area="hospitality",
        covers_steps=["landing-shot", "tier-tunnel-club-shot"],
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["club"] == "mancity"
    assert payload["area"] == "hospitality"
    assert payload["source"] == "synthetic"
    assert all(s["status"] == "synthetic" for s in payload["steps"])
    assert {s["step_name"] for s in payload["steps"]} == {
        "landing-shot", "tier-tunnel-club-shot",
    }


# ---------------------------------------------------------------------------
# Bridge: dom_detect rules fire on synthetic intel
# ---------------------------------------------------------------------------


def test_dom_detect_buy_now_fires_on_text_extract():
    """Smoke test: the Plan 02-20 dom_detect text_extracts fallback works.

    A synthetic intel whose only buy-now signal lives in text_extracts (no
    button) should still register buy_now_without_enquiry as present.
    """
    from scanner.vision.dom_detect import RULES
    intel = DomIntel(
        title="x",
        text_extracts=[
            "Manchester City Tunnel Club — book online for £550 per person."
        ],
        source="synthetic",
    )
    rule = RULES["buy_now_without_enquiry"]
    assert rule(intel) is True


def test_dom_detect_package_tier_list_fires_on_text_keyword_count():
    from scanner.vision.dom_detect import RULES
    intel = DomIntel(
        title="x",
        text_extracts=[
            "Tunnel Club is the showcase tier. Backstage offers smaller groups. "
            "Premium Seats sit higher. Centenary Suite is mid-tier."
        ],
        source="synthetic",
    )
    rule = RULES["package_tier_list"]
    assert rule(intel) is True


def test_dom_detect_phone_booking_fires_on_reseller_phone():
    from scanner.vision.dom_detect import RULES
    intel = DomIntel(
        title="x",
        text_extracts=["Call us to book +44 20 7946 0123 (hospitality team)"],
        source="synthetic",
    )
    rule = RULES["phone_booking_option"]
    assert rule(intel) is True


def test_dom_detect_enquiry_form_synthetic_fallback():
    from scanner.vision.dom_detect import RULES
    intel = DomIntel(
        title="x",
        text_extracts=["Fill out the enquiry form to request a quote"],
        source="synthetic",
    )
    rule = RULES["enquiry_form_field_count_le_7"]
    assert rule(intel) is True
