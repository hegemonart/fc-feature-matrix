"""Pydantic schemas for flow-map input JSON.

A flow-map is a human-authored JSON document that drives Playwright through a
capture flow. Invariants enforced at the schema level:

- D-15: `FlowMap.steps` must have 1-15 items. Longer flows suggest a re-design
  (the scanner is for focused per-area captures, not full-site crawls).
- D-16: `FlowStep.action` is restricted to a closed Literal of
  navigate / click / fill / wait / screenshot. Any action outside this set is
  rejected at schema load-time so captures can never trigger real form
  dispatch against club sites.

Downstream: `scanner.capture.capture` consumes `FlowStep.hide_selectors`,
`FlowStep.wait_for`, etc. (Plan 03).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FormField(BaseModel):
    """A single form input to fill during a `fill` step."""

    selector: str
    value: str  # e.g. "Test Test", "test@example.com"


class FlowStep(BaseModel):
    """A single step in a flow-map.

    `action` is a strict closed Literal union. Per D-16, any action that would
    dispatch a real form request is intentionally absent from the union so
    ValidationError fires at load-time.
    """

    step_name: str
    url: str | None = None
    # D-16 invariant: the Literal union is closed — only the five safe
    # actions below are accepted; anything else fails at load.
    action: Literal["navigate", "click", "fill", "wait", "screenshot"]
    selector: str | None = None
    form_fields: list[FormField] | None = None
    hide_selectors: list[str] = Field(default_factory=list)
    wait_for: str | None = None  # CSS selector or 'networkidle'


class FlowMap(BaseModel):
    """Top-level flow-map document.

    `steps` is bounded by the D-15 invariant (1-15 steps) so malformed
    flow-maps fail at load-time rather than part-way through a Playwright run.
    """

    area: str
    club: str
    entry_url: str
    steps: list[FlowStep] = Field(min_length=1, max_length=15)  # D-15


__all__ = ["FlowMap", "FlowStep", "FormField"]
