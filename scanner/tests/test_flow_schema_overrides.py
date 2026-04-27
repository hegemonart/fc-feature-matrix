"""Tests for Plan 02-09 additive FlowStep override fields.

The plan extends FlowStep with three optional fields used by the back-half
capture orchestrator (Plan 02-10):

- ``requires_credentials`` (bool, default False) — orchestrator authenticates
  before running this step.
- ``manual_chrome_mcp`` (bool, default False) — orchestrator pauses and asks
  the user to drive Chrome MCP for this step instead of Playwright.
- ``skipped`` (str | None, default None) — reason the step is intentionally
  skipped (e.g. ``"requires-paid-account"`` for Chelsea Option B partial).

D-15 / D-16 invariants (1-15 steps; closed Literal of safe actions) remain
unchanged. The new fields are pure metadata — additive, default-Falsy, so
all front-half flow-map JSONs continue to validate without edits.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scanner.flow.schema import FlowMap, FlowStep
from scanner.flow.validate import validate_flow_map


# Resolve the on-disk hospitality flow-maps once (relative to this file).
HOSPITALITY_DIR = (
    Path(__file__).resolve().parent.parent / "flow-maps" / "hospitality"
)
HOSPITALITY_CLUBS = ("mancity", "tottenham", "realmadrid", "psg", "chelsea")


# --- Schema-level: additive fields default-Falsy, round-trip preserved ---


def test_flowstep_without_new_fields_validates_with_defaults():
    """Pre-existing FlowStep JSON (no new fields) still validates and the new
    fields take their default values."""
    step = FlowStep.model_validate(
        {"step_name": "landing", "action": "navigate", "url": "https://x.test/"}
    )
    assert step.requires_credentials is False
    assert step.manual_chrome_mcp is False
    assert step.skipped is None


def test_flowstep_with_requires_credentials_round_trips():
    """``requires_credentials: true`` validates and survives model_dump()."""
    step = FlowStep.model_validate(
        {
            "step_name": "login",
            "action": "navigate",
            "url": "https://billetterie.psg.fr/en/account/login",
            "requires_credentials": True,
        }
    )
    assert step.requires_credentials is True
    dumped = step.model_dump()
    assert dumped["requires_credentials"] is True


def test_flowstep_with_manual_chrome_mcp_round_trips():
    """``manual_chrome_mcp: true`` validates and survives model_dump()."""
    step = FlowStep.model_validate(
        {
            "step_name": "cloudflare-bypass",
            "action": "navigate",
            "url": "https://www.mancity.com/hospitality",
            "manual_chrome_mcp": True,
        }
    )
    assert step.manual_chrome_mcp is True
    dumped = step.model_dump()
    assert dumped["manual_chrome_mcp"] is True


def test_flowstep_with_skipped_reason_string_preserved():
    """``skipped`` accepts free-form strings (e.g. Chelsea Option B partial)."""
    step = FlowStep.model_validate(
        {
            "step_name": "match-selector",
            "action": "click",
            "selector": ".select-match",
            "skipped": "requires-paid-account",
        }
    )
    assert step.skipped == "requires-paid-account"
    dumped = step.model_dump()
    assert dumped["skipped"] == "requires-paid-account"


def test_d16_invariant_submit_action_still_rejected():
    """Plan 02-09 must NOT loosen D-16: ``action: "submit"`` still fails the
    closed Literal even when the new override fields are also present."""
    with pytest.raises(ValidationError):
        FlowStep.model_validate(
            {
                "step_name": "send",
                "action": "submit",
                "requires_credentials": True,
            }
        )


def test_skipped_field_accepts_none_explicitly():
    """Explicit ``skipped: null`` is the same as omission — both are valid."""
    step = FlowStep.model_validate(
        {
            "step_name": "x",
            "action": "navigate",
            "url": "https://x.test/",
            "skipped": None,
        }
    )
    assert step.skipped is None


# --- Disk-level: all 5 hospitality flow-maps validate ---


@pytest.mark.parametrize("club", HOSPITALITY_CLUBS)
def test_hospitality_flow_map_validates(club: str):
    """Every committed hospitality flow-map JSON validates against FlowMap.

    Regression guard: a Plan 02-09 schema additive change must NOT break any
    of the 5 pilot flow-maps. Pre-existing maps (front-half v1) and the new
    extended maps (back-half v2) must all load cleanly.
    """
    fm = validate_flow_map(HOSPITALITY_DIR / f"{club}.json")
    assert fm.area == "hospitality"
    assert fm.club == club
    assert 1 <= len(fm.steps) <= 15  # D-15


# --- Plan-level: per-club extended flow-map shape ---


def _load_map(club: str) -> FlowMap:
    return validate_flow_map(HOSPITALITY_DIR / f"{club}.json")


def test_mancity_extended_flow_has_at_least_8_steps():
    fm = _load_map("mancity")
    assert len(fm.steps) >= 8, (
        f"mancity must have >= 8 steps after Plan 02-09 extension; "
        f"got {len(fm.steps)}"
    )


def test_mancity_extended_flow_marks_chrome_mcp_steps():
    """MCFC's Cloudflare Turnstile blocks Playwright on every page — at least
    one step must be marked manual_chrome_mcp so Plan 02-10 routes correctly."""
    fm = _load_map("mancity")
    chrome_mcp_steps = [s for s in fm.steps if s.manual_chrome_mcp]
    assert len(chrome_mcp_steps) >= 1, (
        "mancity: at least one step must be manual_chrome_mcp=True "
        "(Cloudflare Turnstile per 02-06-CRAWL-LOG.md)"
    )


def test_mancity_fixture_id_placeholder_set():
    """D-09: match-selector uses first available fixture; record placeholder
    in metadata so the capture orchestrator surfaces the actual ID later."""
    fm = _load_map("mancity")
    assert fm.metadata.fixture_id == "FIRST_AVAILABLE"


def test_tottenham_extended_flow_has_at_least_10_steps():
    fm = _load_map("tottenham")
    assert len(fm.steps) >= 10, (
        f"tottenham must have >= 10 steps after Plan 02-09 extension; "
        f"got {len(fm.steps)}"
    )


def test_tottenham_extended_flow_includes_enquiry_form_prefill():
    """D-10: enquiry form filled with dummy values, never submitted.
    Tottenham has no CAPTCHA so it's the canonical example of a clean
    pre-submit fill step."""
    fm = _load_map("tottenham")
    fill_steps = [s for s in fm.steps if s.action == "fill"]
    assert len(fill_steps) >= 1, "tottenham: must have at least one fill step"

    # The first fill step must have D-10 dummy values, NOT submit
    enquiry = fill_steps[0]
    assert enquiry.form_fields is not None
    assert len(enquiry.form_fields) >= 1
    values = {ff.value for ff in enquiry.form_fields}
    # D-10 dummy values family
    assert any(v in {"Test Test", "test@example.com", "+44 0000 000000"} for v in values), (
        f"tottenham enquiry form must use D-10 dummy values; got values={values!r}"
    )


def test_tottenham_fixture_id_placeholder_set():
    fm = _load_map("tottenham")
    assert fm.metadata.fixture_id == "FIRST_AVAILABLE"


# --- D-16 still respected on disk: no committed flow-map has a submit ---


@pytest.mark.parametrize("club", HOSPITALITY_CLUBS)
def test_no_submit_action_in_committed_flow_maps(club: str):
    """Belt-and-braces: scan every committed JSON for ``"action": "submit"``
    pre-validate. If a future edit ever introduces one, this test fires
    BEFORE schema validation rejects it."""
    raw = (HOSPITALITY_DIR / f"{club}.json").read_text(encoding="utf-8")
    parsed = json.loads(raw)
    actions = {step.get("action") for step in parsed.get("steps", [])}
    assert "submit" not in actions, (
        f"{club}: committed flow-map must NOT contain action=submit (D-16)"
    )


# --- Plan 02-09 Task 2: Real Madrid + PSG extended flow-maps ---


def test_realmadrid_extended_flow_has_at_least_8_steps():
    fm = _load_map("realmadrid")
    assert len(fm.steps) >= 8, (
        f"realmadrid must have >= 8 steps after Plan 02-09 extension; "
        f"got {len(fm.steps)}"
    )


def test_realmadrid_includes_both_vip_branches():
    """RMA flow-map must cover BOTH /vip-area/matchday-hospitality AND
    /vip-area/seasonal-vip/palcos-vip — the two distinct purchase branches
    surfaced in research §5."""
    fm = _load_map("realmadrid")
    urls = " ".join(s.url or "" for s in fm.steps).lower()
    assert "matchday-hospitality" in urls, (
        "realmadrid: must include matchday-hospitality branch"
    )
    assert "palcos-vip" in urls, (
        "realmadrid: must include seasonal-vip/palcos-vip branch"
    )


def test_realmadrid_post_captcha_steps_marked_chrome_mcp():
    """The CAPTCHA halts Playwright after the landing per 02-06-CRAWL-LOG.md.
    Every step that descends past it must be marked manual_chrome_mcp=true."""
    fm = _load_map("realmadrid")
    chrome_mcp_steps = [s for s in fm.steps if s.manual_chrome_mcp]
    assert len(chrome_mcp_steps) >= 4, (
        f"realmadrid: at least 4 steps must be manual_chrome_mcp=True "
        f"(post-CAPTCHA descent); got {len(chrome_mcp_steps)}"
    )


def test_realmadrid_fixture_id_placeholder_set():
    fm = _load_map("realmadrid")
    assert fm.metadata.fixture_id == "FIRST_AVAILABLE"


def test_psg_extended_flow_has_at_least_10_steps():
    fm = _load_map("psg")
    assert len(fm.steps) >= 10, (
        f"psg must have >= 10 steps after Plan 02-09 extension; "
        f"got {len(fm.steps)}"
    )


def test_psg_dual_domain_coverage():
    """PSG flow-map must include BOTH www.psg.fr (Playwright-reachable) AND
    billetterie.psg.fr (Cloudflare-gated, manual_chrome_mcp). The dual-domain
    coverage is the whole point of the back-half extension."""
    fm = _load_map("psg")
    urls = " ".join(s.url or "" for s in fm.steps)
    assert "www.psg.fr" in urls, "psg: must include www.psg.fr step"
    assert "billetterie.psg.fr" in urls, (
        "psg: must include billetterie.psg.fr step"
    )

    # Every billetterie step must be manual_chrome_mcp=true
    billetterie_steps = [
        s for s in fm.steps if s.url and "billetterie.psg.fr" in s.url
    ]
    for s in billetterie_steps:
        assert s.manual_chrome_mcp is True, (
            f"psg: billetterie step {s.step_name!r} must be "
            f"manual_chrome_mcp=true (Cloudflare gate)"
        )


def test_psg_login_step_requires_credentials():
    """PSG hospitality enquiry on billetterie typically requires login per
    research §5 — at least one step must carry requires_credentials=true so
    the capture orchestrator authenticates BEFORE the step."""
    fm = _load_map("psg")
    cred_steps = [s for s in fm.steps if s.requires_credentials]
    assert len(cred_steps) >= 1, (
        "psg: at least one step must be requires_credentials=true "
        "(billetterie login wall per research §5)"
    )


def test_psg_fixture_id_placeholder_set():
    fm = _load_map("psg")
    assert fm.metadata.fixture_id == "FIRST_AVAILABLE"


# --- Plan 02-09 Task 3: Chelsea Option B partial flow-map ---


def test_chelsea_extended_flow_has_at_least_8_steps():
    fm = _load_map("chelsea")
    assert len(fm.steps) >= 8, (
        f"chelsea must have >= 8 steps after Plan 02-09 extension; "
        f"got {len(fm.steps)}"
    )


def test_chelsea_has_at_least_one_skipped_paid_account_step():
    """Per Option B partial decision (2026-04-27, 02-BACK-HALF-HANDOFF.md):
    hospitality.chelseafc.com requires an existing paid-customer status to
    access the booking flow. At least one step must carry
    skipped='requires-paid-account' so the capture orchestrator records the
    skip in coverage output."""
    fm = _load_map("chelsea")
    skipped_steps = [s for s in fm.steps if s.skipped == "requires-paid-account"]
    assert len(skipped_steps) >= 1, (
        "chelsea: at least one step must be marked "
        "skipped='requires-paid-account' (Option B partial)"
    )


def test_chelsea_dead_ends_deduplicated():
    """Plan 02-08 dedupe fix: meta.dead_ends must NOT contain duplicate URLs
    after the Plan 02-09 author pass touches the metadata."""
    fm = _load_map("chelsea")
    assert len(set(fm.metadata.dead_ends)) == len(fm.metadata.dead_ends), (
        f"chelsea: dead_ends must be deduplicated; "
        f"got {fm.metadata.dead_ends}"
    )


def test_chelsea_broker_vendor_set_to_keith_prowse():
    """Per 02-RESEARCH.md §5: hospitality.chelseafc.com is suspected
    Keith Prowse whitelabel. Plan 02-09 records the inference in the
    flow-map metadata so Plan 02-12 can confirm or correct."""
    fm = _load_map("chelsea")
    assert fm.metadata.broker_vendor == "keith_prowse", (
        f"chelsea: broker_vendor must be 'keith_prowse' (suspected per "
        f"research §5); got {fm.metadata.broker_vendor!r}"
    )


def test_chelsea_fixture_id_placeholder_set():
    fm = _load_map("chelsea")
    assert fm.metadata.fixture_id == "FIRST_AVAILABLE"


# --- End-of-plan smoke test: all 5 maps validate ---


def test_all_five_hospitality_flow_maps_validate_via_validator():
    """Regression: loop over all hospitality flow-maps and run the public
    validate_flow_map() entrypoint. Guards against any future change that
    might break one map while leaving the others intact."""
    for club in HOSPITALITY_CLUBS:
        fm = validate_flow_map(HOSPITALITY_DIR / f"{club}.json")
        assert fm.area == "hospitality"
        assert fm.club == club
        # Every map must have the D-09 fixture_id placeholder set after
        # Plan 02-09 (capture orchestrator records actual ID at run time).
        assert fm.metadata.fixture_id == "FIRST_AVAILABLE", (
            f"{club}: fixture_id must be 'FIRST_AVAILABLE' after Plan 02-09"
        )
