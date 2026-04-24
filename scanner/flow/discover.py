"""Flow-map click-path discovery — Phase 2 stub.

Per D-06, automated click-path discovery (crawl an entry URL, identify
ticket / hospitality / purchase CTAs, emit a flow-map JSON) is scoped to
Phase 2. Phase 1 ships only the CLI surface so that `scanner flow discover`
is discoverable, but honest about its current capability.

In Phase 1, flow-maps are authored by hand and validated with
`scanner flow validate <path>` (see `scanner.flow.validate`).
"""
from __future__ import annotations

from pathlib import Path

# TODO(phase-2): implement hospitality/VIP/premium link-text heuristics.
# Planned approach (per D-06 research notes): headless Playwright crawl
# rooted at `entry_url`, ranked link extraction via keyword filters
# ("hospitality", "VIP", "premium", "packages"), produces a FlowMap that
# the user reviews and edits before passing to `scanner flow validate`.


def discover_flow(entry_url: str, out_path: Path) -> None:
    """Phase 2 stub — raises NotImplementedError.

    Phase 2 will crawl the entry URL, identify click targets, and generate a
    flow-map JSON file at `out_path`. Phase 1 ships only the CLI surface.

    Args:
        entry_url: The landing URL to start discovery from.
        out_path: Destination path for the generated flow-map JSON.

    Raises:
        NotImplementedError: Always, with a message that (a) marks the
            feature as Phase 2 scope and (b) points users at the documented
            Phase-1 alternative (`scanner flow validate`).
    """
    raise NotImplementedError(
        "scanner.flow.discover — click-path discovery is Phase 2 scope (D-06). "
        "For Phase 1, author flow-maps by hand and validate with "
        "`scanner flow validate <path>`."
    )


__all__ = ["discover_flow"]
