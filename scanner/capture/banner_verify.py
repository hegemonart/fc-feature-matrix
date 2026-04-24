"""Post-capture cookie/consent banner verification (Plan 03, Task 2 → D-14).

After every full-page screenshot, send the PNG to Claude Haiku with a binary
yes/no prompt: "is any cookie-consent banner, newsletter popup, or modal
visible?" If Haiku says yes, the caller should re-try dismissal with stronger
handling (per-club strategy or DOM removal).

**Why Haiku?** Lowest-tier model is sufficient because this is a yes/no visual
detection, not feature extraction. Pinning the model here keeps the banner
check cheap even when the main two-judge flow runs on Opus + Sonnet.

**Lazy import of `scanner.vision.factory`:** Plan 04 ships the factory; Plan 03
ships first in dep-graph order. To avoid a circular-import ordering constraint,
the factory is imported inside the function. If it's not importable yet
(isolated plan-03 test runs), the function degrades to a permissive True with
a WARNING log — CI has both plans and gets the real client.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# TODO(01-04): once Plan 04 lands, the `Any` return contract below becomes
# `scanner.vision.factory.VisionClient`. The client protocol must include
# `.ask_yes_no(screenshot_path, prompt) -> str` — see Plan 04 interfaces.
_HAIKU_MODEL = "claude-haiku-4-5"
_PROMPT = (
    "Is there any cookie-consent banner, newsletter signup popup, or modal "
    "dialog visible in this screenshot? Answer with exactly ONE WORD: "
    "'yes' or 'no'."
)


def verify_banner_gone(
    screenshot_path: Path,
    *,
    api_mode: str = "subscription",
) -> bool:
    """Ask Claude Haiku whether a cookie/consent/newsletter banner is visible.

    Returns True when NO banner is visible (capture is clean). False otherwise.

    On `ImportError` (Plan 04 factory not yet available — isolated plan-03
    test runs), returns True with a WARNING — the banner check is skipped
    rather than crashing the capture loop. This is intentionally permissive:
    Plan 04 + the dry-run (Plan 08) are what actually exercise the check.
    """
    try:
        # TODO(01-04): replace this lazy import with the real Plan 04 Protocol.
        from scanner.vision.factory import get_client  # type: ignore[import-not-found]
    except ImportError:
        logger.warning(
            "scanner.vision.factory not importable — banner check skipped "
            "(assumes clean capture). This is expected in Plan 03's isolated "
            "test runs; Plan 04 ships the factory."
        )
        return True

    client = get_client(api_mode=api_mode, model=_HAIKU_MODEL)
    response: str = client.ask_yes_no(
        screenshot_path=screenshot_path, prompt=_PROMPT
    )
    # Normalise: strip whitespace/punctuation, lowercase.
    normalised = response.strip().lower().rstrip(".!?,;:")
    return normalised == "no"


__all__ = ["verify_banner_gone"]
