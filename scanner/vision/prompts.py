"""Checklist-first prompts per D-18 and OUTPUT_SCHEMA per research §3.3.

``OUTPUT_SCHEMA`` is the JSON Schema fed to the Structured Outputs beta for
the api-key backend, *and* repeated in the prompt text for the subscription
backend (which does not expose a native schema parameter but is constrained
by prompt + Pydantic validation on return).

``build_checklist_prompt`` produces a single prompt string listing the rubric
features by key so the model cannot invent features outside the checklist
(D-18). The output is JSON-only — no prose, no markdown fences.
"""
from __future__ import annotations

from scanner.vision.schema import FeatureDef


# Structured Outputs schema per research §3.3 + scanner/vision/schema.py::FeatureVerdict.
OUTPUT_SCHEMA: dict = {
    "type": "object",
    "patternProperties": {
        "^[a-z_]+$": {
            "type": "object",
            "properties": {
                "present": {"type": "boolean"},
                "step": {"type": "string"},
                "evidence_bbox": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "maxItems": 4,
                        },
                    ]
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "notes": {"type": "string", "maxLength": 500},
            },
            "required": [
                "present",
                "step",
                "evidence_bbox",
                "confidence",
                "notes",
            ],
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}


def build_checklist_prompt(
    features: list[FeatureDef],
    step_name: str = "landing",
) -> str:
    """Build a checklist-first prompt (D-18) bound to the provided rubric.

    Args:
        features: The frozen feature rubric for this run. The model is told
            to return a verdict for EACH of these feature keys — and ONLY
            these keys.
        step_name: Label for the flow-map step the screenshot was captured
            at. Embedded into every ``step`` field in the output.

    Returns:
        A plain-string prompt (no Jinja) suitable for injection into either
        a ``claude_agent_sdk.query`` message or an ``anthropic.messages.create``
        text block.
    """
    rubric_lines = "\n".join(
        f"- key: {f.key}\n  name: {f.name}\n  qualifies_as_yes_if: {f.yes_criterion}"
        for f in features
    )
    return (
        "You are auditing a web page screenshot against a frozen feature checklist.\n"
        "Do NOT identify features not on the list. For EACH feature, return a JSON\n"
        "object with: present (bool), step (string — use the provided step name),\n"
        "evidence_bbox ([x, y, w, h] in pixel coordinates of the attached screenshot; null if absent),\n"
        "confidence (0.0-1.0), notes (brief, max 500 chars).\n\n"
        f'step = "{step_name}"\n\n'
        "Feature checklist:\n"
        f"{rubric_lines}\n\n"
        "Return ONE JSON object keyed by feature_key. No prose."
    )


__all__ = ["OUTPUT_SCHEMA", "build_checklist_prompt"]
