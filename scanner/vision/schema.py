"""Pydantic schemas for vision-judge JSON output.

Both vision backends (claude-agent-sdk subscription and anthropic api-key SDK)
MUST produce the shape defined here. Per D-27..D-29 the Plan 04 dispatcher
treats the two judges as interchangeable — identical schema is the contract
that makes that possible.

Key design notes:

- `FeatureVerdict.confidence` is bounded [0.0, 1.0] via Field(ge, le). Models
  that occasionally return 1.0001 or -0.01 are rejected at parse-time; Plan
  04's client layer is responsible for any clamping it wants to apply before
  constructing the verdict.
- `FeatureVerdict.notes` is capped at 500 chars per Research §3.3 OUTPUT_SCHEMA
  (threat T-02-04 — sensitive-essay info disclosure).
- `evidence_bbox` is a 4-float tuple (x, y, w, h) or None. Pydantic v2 coerces
  list -> tuple automatically; JSON lists round-trip cleanly.
- `FeatureDef.key` has NO regex constraint at schema level (D-18 leaves
  snake_case enforcement to runtime checks — the schema is intentionally
  permissive so that mis-keyed features surface as warnings, not load errors).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Plan 02-15 Wave D — detection mode tag.
# - "dom":    Programmatic DOM detection only (e.g. count form inputs).
# - "visual": Vision-judge only (e.g. hero-image impactfulness).
# - "hybrid": Try DOM first; fall back to vision when DOM is inconclusive.
# Defaults to "visual" for backward compatibility with pre-15 rubric files.
DetectionMode = Literal["dom", "visual", "hybrid"]


class FeatureDef(BaseModel):
    """A feature in the rubric — key, human-readable name, and YES criterion."""

    key: str  # snake_case by convention; not enforced at schema level (D-18).
    name: str
    yes_criterion: str
    # Plan 02-15 Wave D additive — defaults to "visual" so pre-15 rubric
    # JSONs (front-half) continue to validate unchanged. judge.py routes by
    # this field after Wave E.
    detection: DetectionMode = "visual"


class FeatureVerdict(BaseModel):
    """A single judge's verdict on a single feature.

    `evidence_bbox` is (x, y, w, h) in pixels relative to the full-page
    screenshot, or None when the feature is absent / no bbox was produced.
    """

    present: bool
    step: str
    evidence_bbox: tuple[float, float, float, float] | None
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = Field(max_length=500)


class FeatureResult(BaseModel):
    """Pairing of a feature key and its verdict.

    Used in contexts where verdicts flow as a list (e.g. when reporting
    per-feature results to downstream scorers); the `JudgeResponse` container
    prefers a dict keyed by feature_key to avoid redundancy.
    """

    feature_key: str
    verdict: FeatureVerdict


class JudgeResponse(BaseModel):
    """Output of a single judge (opus OR sonnet).

    The dispatcher in Plan 04 calls this exact shape from both the
    subscription and api-key backends — if a backend cannot produce this,
    its client code is responsible for the translation.
    """

    model: str  # e.g. "claude-opus-4-7" | "claude-sonnet-4-6"
    results: dict[str, FeatureVerdict]  # keyed by feature_key


__all__ = [
    "DetectionMode",
    "FeatureDef",
    "FeatureResult",
    "FeatureVerdict",
    "JudgeResponse",
]
