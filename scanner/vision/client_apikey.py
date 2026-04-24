"""APIKeyVisionClient — D-26(b) pay-per-token fallback via the anthropic SDK.

Uses ``anthropic.Anthropic(api_key=...)``. Requires the env var
``ANTHROPIC_API_KEY`` to be set at factory dispatch time (the factory raises
before it ever reaches this module).

Structured Outputs beta (2025-11-13) is enabled via the
``anthropic-beta`` default header and the ``output_config`` parameter on
``messages.create``. See research §3.3.

Threat mitigations carried by this module (per plan threat_model):
    T-04-02: :func:`_clamp_confidence` coerces out-of-range ``confidence``
        into [0.0, 1.0] before Pydantic rejects it at ``FeatureVerdict``
        construction.
    T-04-05: ``max_tokens=4096`` caps response size.
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

import anthropic

from scanner.vision.prompts import OUTPUT_SCHEMA, build_checklist_prompt
from scanner.vision.schema import FeatureDef, FeatureVerdict

logger = logging.getLogger(__name__)


class APIKeyVisionClient:
    """anthropic SDK backend — requires ``ANTHROPIC_API_KEY``.

    Attributes:
        model: The Claude model identifier used for every call.
    """

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = anthropic.Anthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": "structured-outputs-2025-11-13"},
        )

    def analyze_screenshot(
        self,
        image_path: Path,
        rubric: list[FeatureDef],
    ) -> dict[str, FeatureVerdict]:
        """Run checklist-first detection via Structured Outputs beta."""
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
        prompt = build_checklist_prompt(rubric)
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            output_config={
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        raw_text = resp.content[0].text
        raw = json.loads(raw_text)
        return {
            k: FeatureVerdict(**_clamp_confidence(v)) for k, v in raw.items()
        }

    def ask_yes_no(self, screenshot_path: Path, prompt: str) -> str:
        """Single-turn yes/no query used by the banner verifier (Plan 03)."""
        image_b64 = base64.b64encode(
            Path(screenshot_path).read_bytes()
        ).decode("utf-8")
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return resp.content[0].text.strip().lower()


def _clamp_confidence(verdict: dict) -> dict:
    """Coerce ``confidence`` into [0.0, 1.0] before Pydantic rejects it.

    LLMs occasionally return 1.0001 or -0.001; :class:`FeatureVerdict` enforces
    strict bounds via ``Field(ge=0.0, le=1.0)``. Shallow-copy the dict so we
    do not mutate the caller's input.
    """
    if "confidence" in verdict:
        verdict = {
            **verdict,
            "confidence": max(0.0, min(1.0, float(verdict["confidence"]))),
        }
    return verdict


__all__ = ["APIKeyVisionClient"]
