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
import re
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query

from scanner.vision.prompts import build_checklist_prompt
from scanner.vision.schema import FeatureDef, FeatureVerdict

logger = logging.getLogger(__name__)


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json_object(text: str) -> str:
    """Best-effort extraction of a JSON object from a model reply.

    Order of operations:
        1. Strip a leading/trailing markdown fence (``` or ```json) — the
           subscription backend occasionally wraps its output despite the
           prompt's "no markdown fences" instruction (T-08-02).
        2. Otherwise, slice from the first ``{`` to the matching last
           ``}`` so a terse preamble ("Here is the JSON:") does not break
           ``json.loads``.
        3. Otherwise, return the original text unchanged — ``json.loads``
           will raise and the caller retries once.
    """
    stripped = text.strip()
    m = _FENCE_RE.search(stripped)
    if m:
        return m.group(1).strip()
    first = stripped.find("{")
    last = stripped.rfind("}")
    if first != -1 and last != -1 and last > first:
        return stripped[first : last + 1]
    return stripped


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
        # Reuse the api-key client's clamp helper — identical coercion.
        from scanner.vision.client_apikey import _clamp_confidence

        text = asyncio.run(self._collect_text(content=content))
        try:
            raw = json.loads(_extract_json_object(text))
        except json.JSONDecodeError as first_err:
            # T-08-02 mitigation: retry once with an even stricter instruction.
            logger.warning(
                "Subscription backend returned non-JSON (model=%s, len=%d). "
                "Retrying with stricter prompt.",
                self.model,
                len(text),
            )
            stricter = list(content)
            stricter[-1] = {
                "type": "text",
                "text": (
                    prompt_text
                    + "\n\nCRITICAL: your previous response was not valid JSON. "
                    "Reply with ONLY the raw JSON object — no prose, no explanation, "
                    "no markdown fences, no leading or trailing whitespace."
                ),
            }
            text2 = asyncio.run(self._collect_text(content=stricter))
            try:
                raw = json.loads(_extract_json_object(text2))
            except json.JSONDecodeError:
                # Surface both the first and retry responses so the operator
                # can see what the model actually produced.
                preview = (text[:500] + " ...") if len(text) > 500 else text
                preview2 = (text2[:500] + " ...") if len(text2) > 500 else text2
                raise RuntimeError(
                    f"SubscriptionVisionClient({self.model}) returned non-JSON "
                    f"twice. First response:\n{preview!r}\n"
                    f"Retry response:\n{preview2!r}"
                ) from first_err

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
