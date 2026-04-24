"""Flow-map file loader + humanized error reporting.

Loads a flow-map JSON file from disk, validates against
`scanner.flow.schema.FlowMap`, and raises a `FlowMapValidationError` with a
file-path + field-path + message triple on failure. Used by the Phase-1
`scanner flow validate <path>` CLI subcommand (Plan 07).

Threat notes (01-06 STRIDE register):
- T-06-01: The `submit` action is rejected by the schema (closed Literal in
  FlowStep.action, D-16). This loader surfaces those rejections as
  `FlowMapValidationError`.
- T-06-03: The humanizer emits only `loc + msg` from Pydantic's error list;
  the raw JSON file body is never echoed back to the caller, so secrets
  embedded in field values cannot leak via error strings.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from scanner.flow.schema import FlowMap


class FlowMapValidationError(ValueError):
    """Raised when a flow-map JSON file fails schema validation.

    Message format: `'{path}: {kind}: {detail}'`.

    - `kind` is `file not found`, `JSON parse error`, or `schema validation failed`.
    - `detail` is either the JSON decoder message or a humanized multi-line
      rendering of `pydantic.ValidationError.errors()`.
    """


def _humanize(errors: list[dict]) -> str:
    """Turn Pydantic v2 errors (.errors()) into a human-friendly multi-line string.

    Emits only `loc` and `msg` per-error — intentionally does NOT include
    `input` (which may carry user-supplied data / secrets). See T-06-03.
    """
    lines: list[str] = []
    for e in errors:
        loc = ".".join(str(p) for p in e.get("loc", ()))
        msg = e.get("msg", "unknown error")
        err_type = e.get("type", "")
        # Include the error type (e.g. `too_long`, `literal_error`) so message
        # assertions in tests can match on stable Pydantic v2 error codes.
        if err_type:
            lines.append(f"  - {loc}: {msg} [{err_type}]")
        else:
            lines.append(f"  - {loc}: {msg}")
    return "\n".join(lines)


def validate_flow_map(path: Path) -> FlowMap:
    """Load + validate a flow-map JSON file.

    Args:
        path: Filesystem path to the flow-map JSON document.

    Returns:
        A validated `FlowMap` instance.

    Raises:
        FlowMapValidationError: If the file does not exist, contains
            malformed JSON, or fails schema validation. The message carries
            the file path and the offending field path(s).
    """
    p = Path(path)
    if not p.exists():
        raise FlowMapValidationError(f"{p}: file not found")
    raw = p.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        # Echo only the decoder's positional error, not the raw file body.
        raise FlowMapValidationError(f"{p}: JSON parse error: {e.msg} (line {e.lineno} col {e.colno})") from e
    try:
        return FlowMap.model_validate(data)
    except ValidationError as e:
        raise FlowMapValidationError(
            f"{p}: schema validation failed:\n{_humanize(e.errors())}"
        ) from e


__all__ = ["FlowMapValidationError", "validate_flow_map"]
