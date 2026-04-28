"""Plan 02-16 Phase 1 — stealth probe for previously Cloudflare-blocked clubs.

Quick, side-effect-free reachability check against the 3 clubs whose v1 capture
runs hit Cloudflare Turnstile / CAPTCHA: MCFC, RMA, PSG-billetterie. Loads the
target URL through the stealth-enabled persistent Chromium context (Plan 02-15
Wave A) and reports whether the response shows real content versus a challenge
interstitial.

Outputs a JSON record per probe to ``scanner/output/stealth-probe-results.json``
which Phase 2 of the recapture wave reads to decide whether ``manual_chrome_mcp``
flags should be overridden for that club.

Run::

    uv run python -m scanner.scripts.recapture.stealth_probe

Subscription cost: $0 (pure capture / DOM read; no vision calls).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scanner.capture.browser import create_browser

logger = logging.getLogger(__name__)


# (club_slug, label, url) tuples — labels match the run-log keys downstream.
PROBES: list[tuple[str, str, str]] = [
    ("mancity", "landing", "https://www.mancity.com/hospitality"),
    ("realmadrid", "matchday-hospitality", "https://www.realmadrid.com/en-US/vip-area/matchday-hospitality"),
    ("psg", "billetterie-home-vip", "https://billetterie.psg.fr/en/home-vip"),
]


CHALLENGE_TOKENS: tuple[str, ...] = (
    # Cloudflare Turnstile / interstitial markers.
    "challenges.cloudflare.com",
    "cf-turnstile",
    "cf-chl-",
    "_cf_chl_opt",
    "just a moment",
    # reCAPTCHA / hCaptcha markers (RMA path).
    "g-recaptcha",
    "hcaptcha",
    "captcha-bypass",
    # PSG vendor-script markers used on billetterie's auth wall.
    "datadome",
    "px-captcha",
)


def _probe_one(club: str, label: str, url: str, *, timeout_ms: int = 25_000) -> dict[str, Any]:
    """Run a single stealth probe. Returns a structured result dict.

    Keys:
        club, step, url, status, http_status, page_title, final_url,
        challenge_detected, challenge_tokens, content_size_bytes, error.

    ``status`` is one of ``"unblocked"``, ``"challenged"``, ``"error"``.
    Never re-raises — failures land in ``status="error"`` with a bounded
    ``error`` string.
    """
    out: dict[str, Any] = {
        "club": club,
        "step": label,
        "url": url,
        "status": None,
        "http_status": None,
        "page_title": None,
        "final_url": None,
        "challenge_detected": False,
        "challenge_tokens": [],
        "content_size_bytes": 0,
        "error": None,
    }

    pw = None
    ctx = None
    try:
        pw, ctx = create_browser(club=club, area="hospitality", headless=True, stealth=True)
        page = ctx.new_page()
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as exc:
            msg = str(exc)
            if len(msg) > 200:
                msg = msg[:200] + "..."
            out["status"] = "error"
            out["error"] = f"goto raised: {msg}"
            return out

        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            # Many real pages never reach networkidle — non-fatal.
            pass

        try:
            out["http_status"] = response.status if response else None
        except Exception:
            out["http_status"] = None

        try:
            out["page_title"] = page.title()
        except Exception:
            out["page_title"] = None

        try:
            out["final_url"] = page.url
        except Exception:
            out["final_url"] = None

        try:
            content = page.content().lower()
        except Exception:
            content = ""

        out["content_size_bytes"] = len(content)
        hits = [tok for tok in CHALLENGE_TOKENS if tok in content]
        out["challenge_tokens"] = hits
        out["challenge_detected"] = bool(hits)

        # Decide status: if challenge tokens fired OR HTTP non-2xx OR title
        # screams "Just a moment" we treat it as challenged. Otherwise unblocked.
        title_lower = (out["page_title"] or "").lower()
        if hits or "just a moment" in title_lower or "attention required" in title_lower:
            out["status"] = "challenged"
        elif out["http_status"] is not None and out["http_status"] >= 400:
            out["status"] = "challenged"
        elif out["content_size_bytes"] < 4_000:
            # Page bodies under ~4 KB are almost always interstitials.
            out["status"] = "challenged"
        else:
            out["status"] = "unblocked"

        return out

    finally:
        try:
            if ctx is not None:
                ctx.close()
        except Exception:
            pass
        try:
            if pw is not None:
                pw.stop()
        except Exception:
            pass


def main() -> int:
    """Run all probes and write results JSON. Returns 0 on success."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    results: list[dict[str, Any]] = []
    for club, label, url in PROBES:
        logger.info("probing %s — %s", club, url)
        rec = _probe_one(club, label, url)
        results.append(rec)
        logger.info(
            "  -> status=%s http=%s title=%r challenge_tokens=%s",
            rec["status"], rec["http_status"], rec["page_title"], rec["challenge_tokens"],
        )

    out_path = Path("scanner/output/stealth-probe-results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stealth": True,
        "probes": results,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("wrote %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
