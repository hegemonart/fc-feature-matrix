"""Tests for scanner.flow.validate — owner Plan 06.

Covers D-15 (1-15 steps), D-16 (no submit action), and humanized error
messages per FLOW-03. See `.planning/phases/01-flow-automation-layer/01-CONTEXT.md`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scanner.flow.schema import FlowMap
from scanner.flow.validate import FlowMapValidationError, validate_flow_map


def _valid_step(**overrides) -> dict:
    base = {"step_name": "landing", "action": "navigate", "url": "https://x.test/"}
    base.update(overrides)
    return base


def _valid_map(steps: list[dict] | None = None) -> dict:
    if steps is None:
        steps = [_valid_step()]
    return {
        "area": "hospitality",
        "club": "mancity",
        "entry_url": "https://mancity.com/tickets/hospitality",
        "steps": steps,
    }


def _write(tmp_path: Path, data: dict | str, name: str = "flow.json") -> Path:
    p = tmp_path / name
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data), encoding="utf-8")
    return p


# --- Happy-path load -----------------------------------------------------


def test_valid_flow_map_round_trips(tmp_path: Path):
    path = _write(
        tmp_path,
        _valid_map(
            steps=[
                _valid_step(),
                _valid_step(step_name="detail", action="click", selector="#package-gold"),
            ]
        ),
    )
    fm = validate_flow_map(path)
    assert isinstance(fm, FlowMap)
    assert fm.area == "hospitality"
    assert fm.club == "mancity"
    assert len(fm.steps) == 2
    assert fm.steps[1].action == "click"
    assert fm.steps[1].selector == "#package-gold"


# --- Missing file --------------------------------------------------------


def test_missing_file_raises_with_file_not_found(tmp_path: Path):
    missing = tmp_path / "does-not-exist.json"
    with pytest.raises(FlowMapValidationError) as exc_info:
        validate_flow_map(missing)
    msg = str(exc_info.value)
    assert "file not found" in msg
    assert str(missing) in msg


# --- Malformed JSON ------------------------------------------------------


def test_malformed_json_raises_with_parse_marker(tmp_path: Path):
    # Intentionally invalid JSON (trailing value after "area":)
    path = _write(tmp_path, '{ "area": }', name="broken.json")
    with pytest.raises(FlowMapValidationError) as exc_info:
        validate_flow_map(path)
    msg = str(exc_info.value).lower()
    assert "json" in msg or "parse" in msg
    assert str(path) in str(exc_info.value)


# --- Schema violation: too many steps (D-15) ----------------------------


def test_schema_violation_too_many_steps_humanized(tmp_path: Path):
    path = _write(tmp_path, _valid_map(steps=[_valid_step() for _ in range(16)]))
    with pytest.raises(FlowMapValidationError) as exc_info:
        validate_flow_map(path)
    msg = str(exc_info.value)
    assert "steps" in msg
    # Pydantic v2 emits `too_long` / `max_length` for list bounds.
    assert "max_length" in msg or "too_long" in msg or "at most" in msg


# --- Schema violation: D-16 forbidden action ----------------------------


def test_schema_violation_submit_action_humanized(tmp_path: Path):
    path = _write(
        tmp_path,
        _valid_map(steps=[_valid_step(step_name="bad", action="submit")]),
    )
    with pytest.raises(FlowMapValidationError) as exc_info:
        validate_flow_map(path)
    msg = str(exc_info.value)
    assert "action" in msg
    # Pydantic v2 literal errors echo the offending value.
    assert "submit" in msg


# --- Error message safety: no secret leakage (T-06-03) ------------------


def test_error_message_does_not_echo_full_raw_json(tmp_path: Path):
    # Embed a pseudo-secret in a field and ensure the humanized error does
    # not parrot the full raw JSON body back to the caller.
    secret = "SK_TEST_SECRET_deadbeefcafebabe"
    data = _valid_map(steps=[_valid_step(step_name=secret, action="submit")])
    path = _write(tmp_path, data)
    with pytest.raises(FlowMapValidationError) as exc_info:
        validate_flow_map(path)
    msg = str(exc_info.value)
    # The humanizer should emit only loc+msg, never the raw JSON file body.
    # The step_name value (containing the "secret") must not appear in the error.
    assert secret not in msg
