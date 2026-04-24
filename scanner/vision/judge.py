"""Two-judge orchestrator — runs Opus + Sonnet over the same screenshot.

Per D-19 and user-decision-4 both judges run through the *same* ``api_mode``;
mixing subscription and api-key in a single dual-judge run is disallowed in
Phase 1 to keep cost/quota accounting clean.

The orchestrator is intentionally thin: it calls :func:`get_client` twice,
runs ``analyze_screenshot`` on each, and wraps the results into
:class:`JudgeResponse` objects. Disagreement detection and downstream
routing live in :mod:`scanner.vision.disagreement` / the scoring layer.
"""
from __future__ import annotations

from pathlib import Path

from scanner.vision.factory import get_client
from scanner.vision.schema import FeatureDef, JudgeResponse

OPUS_MODEL = "claude-opus-4-7"
SONNET_MODEL = "claude-sonnet-4-6"


def two_judge(
    image_path: Path,
    rubric: list[FeatureDef],
    *,
    api_mode: str = "subscription",
) -> dict[str, JudgeResponse]:
    """Run Opus + Sonnet on the same image.

    Args:
        image_path: Full-page screenshot PNG to audit.
        rubric: Frozen list of :class:`FeatureDef` — same list handed to
            both judges so the two checklists are identical (D-18).
        api_mode: ``"subscription"`` (default, D-28) or ``"api-key"``. Both
            judges use the SAME mode — mixing is disallowed in Phase 1.

    Returns:
        A dict with two keys: ``"opus"`` and ``"sonnet"``. Each value is a
        :class:`JudgeResponse` whose ``model`` attribute matches the
        corresponding module-level constant and whose ``results`` is the
        ``{feature_key: FeatureVerdict}`` dict returned by the client.
    """
    opus = get_client(api_mode, OPUS_MODEL)
    sonnet = get_client(api_mode, SONNET_MODEL)
    opus_results = opus.analyze_screenshot(image_path, rubric)
    sonnet_results = sonnet.analyze_screenshot(image_path, rubric)
    return {
        "opus": JudgeResponse(model=OPUS_MODEL, results=opus_results),
        "sonnet": JudgeResponse(model=SONNET_MODEL, results=sonnet_results),
    }


__all__ = ["OPUS_MODEL", "SONNET_MODEL", "two_judge"]
