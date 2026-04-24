"""SubscriptionVisionClient — D-26(a) default backend over claude-agent-sdk.

Uses the ``claude_agent_sdk.query`` async iterator. No API key is required
at runtime; the ``claude`` CLI must be on PATH (the factory layer does not
validate this — the SDK raises a clear ``CLINotFoundError`` on first call,
and Plan 03/Plan 08 pre-flight ``claude --version`` per T-04-06).

The public synchronous surface (``analyze_screenshot`` and ``ask_yes_no``)
is identical to :class:`scanner.vision.client_apikey.APIKeyVisionClient` so
that :func:`scanner.vision.factory.get_client` can treat the two backends
as fully interchangeable (D-27..D-29). The async hop is contained inside
``_collect_text`` and driven via ``asyncio.run``.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query

from scanner.vision.prompts import build_checklist_prompt
from scanner.vision.schema import FeatureDef, FeatureVerdict

logger = logging.getLogger(__name__)


class SubscriptionVisionClient:
    """claude-agent-sdk backend — consumes Max 20x subscription quota.

    Attributes:
        model: The Claude model identifier passed via
            :class:`ClaudeAgentOptions`. Every call reuses this value.
    """

    def __init__(self, model: str):
        self.model = model

    def analyze_screenshot(
        self,
        image_path: Path,
        rubric: list[FeatureDef],
    ) -> dict[str, FeatureVerdict]:
        """Run checklist-first detection against the subscription backend.

        The prompt is augmented with an explicit "no markdown fences"
        instruction (T-04-03 mitigation) because the subscription backend
        does not offer a native Structured Outputs parameter.
        """
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
        prompt_text = build_checklist_prompt(rubric)
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64,
                },
            },
            {
                "type": "text",
                "text": (
                    prompt_text
                    + "\n\nReturn ONLY valid JSON — no surrounding text, no markdown fences."
                ),
            },
        ]
        text = asyncio.run(self._collect_text(content=content))
        raw = json.loads(text)
        # Reuse the api-key client's clamp helper — identical coercion.
        from scanner.vision.client_apikey import _clamp_confidence

        return {
            k: FeatureVerdict(**_clamp_confidence(v)) for k, v in raw.items()
        }

    def ask_yes_no(self, screenshot_path: Path, prompt: str) -> str:
        """Single-turn yes/no query used by the banner verifier (Plan 03)."""
        image_b64 = base64.b64encode(
            Path(screenshot_path).read_bytes()
        ).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64,
                },
            },
            {"type": "text", "text": prompt},
        ]
        text = asyncio.run(self._collect_text(content=content))
        return text.strip().lower()

    async def _collect_text(self, content: list[dict[str, Any]]) -> str:
        """Drain the ``query`` async iterator into a single text string.

        The SDK streams messages; each ``AssistantMessage`` carries a
        ``content`` list of blocks (``TextBlock``, ``ThinkingBlock``, tool
        blocks, …). We concatenate only the text blocks. User messages,
        system messages and result messages are ignored.
        """
        streaming_prompt = _build_streaming_prompt(content)
        options = ClaudeAgentOptions(model=self.model)
        out_parts: list[str] = []
        async for message in query(prompt=streaming_prompt, options=options):
            for block in getattr(message, "content", []) or []:
                if getattr(block, "type", None) == "text" or hasattr(block, "text"):
                    text_val = getattr(block, "text", None)
                    if isinstance(text_val, str):
                        out_parts.append(text_val)
        return "".join(out_parts)


def _build_streaming_prompt(content: list[dict[str, Any]]):
    """Build a single-turn async iterator for :func:`claude_agent_sdk.query`.

    ``query()`` accepts either a ``str`` or an ``AsyncIterable[dict]``.
    In streaming mode each yielded dict follows the shape
    ``{"type": "user", "message": {"role": "user", "content": [...]}}``.
    This helper yields exactly one such dict so the iterator closes after
    a single user turn.
    """

    async def _gen():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": content,
            },
        }

    return _gen()


__all__ = ["SubscriptionVisionClient"]
