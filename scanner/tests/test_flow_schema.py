"""Tests for scanner.flow.schema — owner Plan 02.

Enforces D-15 (1-15 steps) and D-16 (no submit action) invariants at the
schema type level. See `.planning/phases/01-flow-automation-layer/01-CONTEXT.md`.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from scanner.flow.schema import FlowMap, FlowStep, FormField


def _valid_step(**overrides) -> dict:
    base = {"step_name": "landing", "action": "navigate", "url": "https://x.test/"}
    base.update(overrides)
    return base


def _valid_map(steps: list[dict] | None = None) -> dict:
    # NOTE: use `is None` — an explicit empty list must pass through unchanged
    # so the min_length=1 validator can reject it in the zero-step test.
    if steps is None:
        steps = [_valid_step()]
    return {
        "area": "hospitality",
        "club": "mancity",
        "entry_url": "https://mancity.com/tickets/hospitality",
        "steps": steps,
    }


# --- Happy-path parse ----------------------------------------------------


def test_valid_flow_map_parses():
    data = _valid_map(
        steps=[
            _valid_step(),
            _valid_step(step_name="detail", action="click", selector="#package-gold"),
        ]
    )
    fm = FlowMap.model_validate(data)
    assert fm.area == "hospitality"
    assert fm.club == "mancity"
    assert len(fm.steps) == 2
    assert fm.steps[1].action == "click"
    assert fm.steps[1].selector == "#package-gold"


def test_step_click_with_selector_parses():
    step = FlowStep.model_validate(
        {"step_name": "open-modal", "action": "click", "selector": "#cta"}
    )
    assert step.action == "click"
    assert step.selector == "#cta"


# --- D-16 invariant: no submit action -----------------------------------


def test_rejects_submit_action():
    with pytest.raises(ValidationError):
        FlowStep.model_validate({"step_name": "s", "action": "submit"})


# --- D-15 invariant: 1-15 steps -----------------------------------------


def test_rejects_zero_steps():
    data = _valid_map(steps=[])
    with pytest.raises(ValidationError):
        FlowMap.model_validate(data)


def test_rejects_16_steps():
    data = _valid_map(steps=[_valid_step() for _ in range(16)])
    with pytest.raises(ValidationError):
        FlowMap.model_validate(data)


def test_accepts_exactly_15_steps():
    data = _valid_map(steps=[_valid_step() for _ in range(15)])
    fm = FlowMap.model_validate(data)
    assert len(fm.steps) == 15


# --- FormField -----------------------------------------------------------


def test_form_fields_round_trip():
    step = FlowStep.model_validate(
        {
            "step_name": "fill-form",
            "action": "fill",
            "form_fields": [
                {"selector": "input[name=email]", "value": "test@example.com"},
                {"selector": "input[name=name]", "value": "Test Test"},
            ],
        }
    )
    assert step.form_fields is not None
    assert len(step.form_fields) == 2
    assert step.form_fields[0].selector == "input[name=email]"
    assert step.form_fields[0].value == "test@example.com"


def test_form_field_missing_selector_raises():
    with pytest.raises(ValidationError):
        FormField.model_validate({"value": "oops"})


# --- Default factories (mutable-default trap) ---------------------------


def test_hide_selectors_defaults_to_empty_list():
    step = FlowStep.model_validate({"step_name": "s", "action": "wait"})
    assert step.hide_selectors == []
    # Mutating one instance must not leak into defaults of new instances.
    step.hide_selectors.append(".banner")
    other = FlowStep.model_validate({"step_name": "t", "action": "wait"})
    assert other.hide_selectors == []


# --- Round-trip ----------------------------------------------------------


def test_round_trip_model_dump():
    data = _valid_map(
        steps=[
            _valid_step(),
            _valid_step(step_name="wait-load", action="wait", wait_for="networkidle"),
        ]
    )
    fm = FlowMap.model_validate(data)
    dumped = fm.model_dump(exclude_defaults=False)
    fm2 = FlowMap.model_validate(dumped)
    assert fm2.model_dump() == fm.model_dump()
