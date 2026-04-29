"""Text-based content fetch for Cloudflare-blocked sites (Plan 02-20).

When stealth, Patchright, and headed-Chromium-with-stealth all fail to bypass
Cloudflare Turnstile (Plan 02-19 negative result), we fall back to gathering
text content from third-party hospitality resellers that describe the
official packages. Their pages are not Turnstile-gated because the resellers
*sell* the packages — they have a commercial incentive to expose the
content publicly to search engines.

Output is shaped to be DomIntel-compatible (``source="synthetic"``,
``text_extracts`` populated). The hybrid pipeline reads it normally;
``dom_detect`` rules consult ``text_extracts`` as a fallback text surface
(see Plan 02-20 dom_detect changes), so most DOM-detectable features fire
on synthetic content the same way they fire on live captures.

What this module does NOT do:
  - It does NOT call the Anthropic WebSearch / WebFetch tools (those are
    agent-side primitives, not available to the running scanner). Instead
    it uses :mod:`urllib.request` for HTTP and :mod:`html.parser` for
    text extraction — both stdlib, no new deps, satisfies D-21.
  - It does NOT attempt to bypass Cloudflare on the official sites — that
    is Plan 02-19's negative-result scope. This module is the alternate
    path forward.
  - It does NOT run on visual-only features. The pipeline marks those as
    ``no-data`` for synthetic-source clubs (see Plan 02-20 Phase 5).

Provenance is preserved:
  - ``DomIntel.source = "synthetic"`` on every record this module emits.
  - The list of reseller URLs ingested is written to a sibling
    ``{club}_aggregated.md`` audit-trail file.
  - Run-log JSON is written so the orchestrator can route synthetic runs
    through the same wave / derive / score pipeline.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scanner.capture.dom_intel import (
    DomBbox,
    DomButton,
    DomCounts,
    DomHeading,
    DomImage,
    DomIntel,
)

logger = logging.getLogger(__name__)

# A plausible desktop Chrome UA — reseller sites generally don't bot-block
# this since they want their pages indexed. We keep it constant so behavior
# is reproducible.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Per-host fetch timeout (s).
HTTP_TIMEOUT = 20.0

# Hard cap on bytes per fetch — defends against pathological pages.
MAX_BYTES = 2_500_000

# Hard cap on text-extract length per URL — keeps DomIntel JSONs sane.
MAX_TEXT_PER_URL = 80_000


# ---------------------------------------------------------------------------
# Stdlib HTML → plain text
# ---------------------------------------------------------------------------


class _TextExtractor(HTMLParser):
    """Strip script/style, collapse whitespace, capture headings + buttons.

    The parser collects:
      - ``buf`` — flat plain-text body (used as the searchable text_extract).
      - ``headings`` — (tag, text) tuples for h1..h4.
      - ``links`` — (text, href) tuples for <a> elements (use to seed the
        ``buttons`` field on the synthetic DomIntel).
    """

    SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "iframe"}
    HEADING_TAGS = {"h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._heading_buf: list[str] = []
        self._heading_tag: str | None = None
        self._anchor_buf: list[str] = []
        self._anchor_href: str | None = None
        self.buf: list[str] = []
        self.headings: list[tuple[str, str]] = []
        self.links: list[tuple[str, str | None]] = []

    def _skipping(self) -> bool:
        return any(t in self.SKIP_TAGS for t in self._stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._stack.append(tag)
        if tag in self.HEADING_TAGS and not self._heading_tag:
            self._heading_tag = tag
            self._heading_buf = []
        if tag == "a":
            self._anchor_buf = []
            href = next((v for (k, v) in attrs if k == "href"), None)
            self._anchor_href = href
        # Insert breaks at block-level boundaries so flowed text doesn't
        # smash words across element edges.
        if tag in {"p", "br", "div", "li", "tr", "section", "article",
                   "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.buf.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
        if tag == self._heading_tag:
            text = " ".join(self._heading_buf).strip()
            if text:
                self.headings.append((tag.upper(), text))
            self._heading_tag = None
            self._heading_buf = []
        if tag == "a":
            text = " ".join(self._anchor_buf).strip()
            if text:
                self.links.append((text, self._anchor_href))
            self._anchor_buf = []
            self._anchor_href = None
        if tag in {"p", "br", "div", "li", "tr", "section", "article",
                   "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.buf.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skipping():
            return
        if not data.strip():
            return
        self.buf.append(data)
        if self._heading_tag:
            self._heading_buf.append(data)
        if self._anchor_href is not None:
            self._anchor_buf.append(data)


_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_NEWLINE_RUN_RE = re.compile(r"\n{3,}")


def _normalize_text(raw: str) -> str:
    """Squash whitespace runs; collapse ≥3 blank lines to 2."""
    raw = _WHITESPACE_RE.sub(" ", raw)
    raw = _NEWLINE_RUN_RE.sub("\n\n", raw)
    # Strip line-leading / line-trailing whitespace.
    return "\n".join(line.strip() for line in raw.split("\n") if line.strip())


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------


@dataclass
class FetchResult:
    """One reseller-page fetch outcome."""

    url: str
    status: int
    text: str
    headings: list[tuple[str, str]] = field(default_factory=list)
    links: list[tuple[str, str | None]] = field(default_factory=list)
    error: str | None = None


def _fetch_url(url: str, *, timeout: float = HTTP_TIMEOUT) -> FetchResult:
    """GET ``url`` with a desktop UA and run the HTML through ``_TextExtractor``.

    Returns a FetchResult with status, normalized text, and structured
    heading/link lists. On error returns a result with status=0 and
    ``error`` populated; never raises.
    """
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — UA-set
            status = resp.status
            raw = resp.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                logger.warning(
                    "text_fetch: %s exceeded MAX_BYTES (%d>%d), truncating",
                    url, len(raw), MAX_BYTES,
                )
                raw = raw[:MAX_BYTES]
            ctype = resp.headers.get("Content-Type", "")
    except HTTPError as exc:
        return FetchResult(url=url, status=exc.code, text="", error=f"HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        return FetchResult(url=url, status=0, text="", error=f"{type(exc).__name__}: {exc}")
    except Exception as exc:  # pragma: no cover — defensive
        return FetchResult(url=url, status=0, text="", error=f"{type(exc).__name__}: {exc}")

    # Decode — try UTF-8, then fall back to latin-1 (always works).
    encoding = "utf-8"
    if "charset=" in ctype:
        encoding = ctype.split("charset=")[-1].split(";")[0].strip() or "utf-8"
    try:
        body = raw.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        body = raw.decode("latin-1", errors="replace")

    parser = _TextExtractor()
    try:
        parser.feed(body)
        parser.close()
    except Exception as exc:  # malformed HTML — accept partial output
        logger.warning("text_fetch: HTMLParser error on %s (%s)", url, exc)

    text = _normalize_text("".join(parser.buf))
    if len(text) > MAX_TEXT_PER_URL:
        text = text[:MAX_TEXT_PER_URL] + "\n…[truncated]"
    return FetchResult(
        url=url,
        status=status,
        text=text,
        headings=parser.headings,
        links=parser.links,
    )


# ---------------------------------------------------------------------------
# Synthesis: FetchResult[] → DomIntel
# ---------------------------------------------------------------------------


def synthesize_dom_intel(
    *,
    club_id: str,
    club_name: str,
    official_url: str,
    fetches: list[FetchResult],
) -> DomIntel:
    """Aggregate reseller fetches into a single synthetic DomIntel.

    Heuristics:
      - ``title``  ← f"{club_name} hospitality (synthetic)"
      - ``url``    ← official_url (so downstream provenance points at the
        club, not at any one reseller)
      - ``headings`` ← merged headings across all successful fetches,
        de-duped by lower-cased text
      - ``buttons`` ← merged anchor texts (use as link surface for
        keyword rules), de-duped, with href preserved
      - ``forms``  ← []  (no live form structure available)
      - ``meta``   ← {"description": short reseller-derived summary,
        "synthetic_sources": ", ".join(urls fetched OK)}
      - ``counts`` ← reflect the synthetic surface only
        (forms=0, inputs=0, buttons=len(buttons), tables=0,
         images=0)
      - ``text_extracts`` ← ordered list — one entry per OK fetch, prefixed
        with ``[source: <url>]`` for in-rule provenance (rules that scan
        the joined string see the URL annotation)
      - ``source`` ← "synthetic"
    """
    ok = [f for f in fetches if f.status == 200 and f.text]
    seen_h: set[str] = set()
    headings: list[DomHeading] = []
    for f in ok:
        for tag, text in f.headings:
            key = text.lower()
            if key in seen_h or len(text) > 200:
                continue
            seen_h.add(key)
            headings.append(DomHeading(tag=tag, text=text, bbox=None))

    seen_b: set[str] = set()
    buttons: list[DomButton] = []
    for f in ok:
        for text, href in f.links:
            key = (text.lower(), href or "")
            if key in seen_b or not text or len(text) > 200:
                continue
            seen_b.add(key)
            buttons.append(DomButton(text=text, tag="A", href=href, bbox=None))

    text_extracts: list[str] = []
    for f in ok:
        text_extracts.append(f"[source: {f.url}]\n{f.text}")

    description_parts: list[str] = []
    for f in ok[:2]:  # short summary from first two sources
        snippet = f.text.split("\n", 1)[0]
        if snippet:
            description_parts.append(snippet[:200])
    description = " — ".join(description_parts)[:500]

    meta = {
        "description": description,
        "synthetic_sources": ", ".join(f.url for f in ok),
        "synthetic_n_sources": str(len(ok)),
        "synthetic_n_failed": str(len(fetches) - len(ok)),
    }

    intel = DomIntel(
        title=f"{club_name} hospitality (synthetic)",
        url=official_url,
        headings=headings,
        buttons=buttons,
        forms=[],
        images=[],
        schema_jsonld=[],
        meta=meta,
        counts=DomCounts(
            forms=0,
            inputs=0,
            buttons=len(buttons),
            tables=0,
            images=0,
        ),
        text_extracts=text_extracts,
        source="synthetic",
    )
    return intel


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def fetch_text_for_club(
    *,
    club_id: str,
    club_name: str,
    official_url: str,
    reseller_urls: list[str],
) -> tuple[DomIntel, list[FetchResult]]:
    """Fetch every reseller URL and synthesize a DomIntel for the club.

    Returns the synthetic DomIntel plus the raw FetchResult list (for
    audit-trail writing).
    """
    fetches: list[FetchResult] = []
    for url in reseller_urls:
        logger.info("text_fetch: GET %s", url)
        fr = _fetch_url(url)
        if fr.error:
            logger.warning(
                "text_fetch: %s failed (%s)", url, fr.error,
            )
        else:
            logger.info(
                "text_fetch: %s -> HTTP %d, %d chars text",
                url, fr.status, len(fr.text),
            )
        fetches.append(fr)
    intel = synthesize_dom_intel(
        club_id=club_id,
        club_name=club_name,
        official_url=official_url,
        fetches=fetches,
    )
    return intel, fetches


def write_synthetic_outputs(
    *,
    intel: DomIntel,
    fetches: list[FetchResult],
    club_id: str,
    intel_dir: Path,
    audit_dir: Path,
    covers_steps: list[str],
) -> dict:
    """Persist synthetic intel + audit trail + per-step intel JSONs.

    For each step in ``covers_steps`` we write a copy of the synthetic
    intel JSON at ``{intel_dir}/{club}_{step}_intel.json``. This lets the
    existing ``run_vision_wave`` orchestrator find intel via the standard
    convention without any code change. All step JSONs are byte-identical
    (same synthetic surface — there's no per-step differentiation when the
    source is reseller prose).

    Audit trail (one ``.md`` per club) records each fetched URL and the
    extracted text, so reviewers can verify what content drove each rule.

    Returns a small summary dict for caller logging.
    """
    intel_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    intel_payload = intel.model_dump(mode="json")

    # Per-step intel files (byte-identical, named by step).
    step_files: list[Path] = []
    for step in covers_steps:
        out = intel_dir / f"{club_id}_{step}_intel.json"
        out.write_text(json.dumps(intel_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        step_files.append(out)

    # Aggregated synthetic intel (one canonical file per club for cross-ref).
    aggregate = intel_dir / f"{club_id}_synthetic_intel.json"
    aggregate.write_text(json.dumps(intel_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Audit trail markdown.
    md_lines: list[str] = []
    md_lines.append(f"# Synthetic hospitality intel — {club_id}")
    md_lines.append("")
    md_lines.append(f"- Source: text_fetch (Plan 02-20)")
    md_lines.append(f"- Official URL (referenced): {intel.url}")
    md_lines.append(f"- Reseller URLs attempted: {len(fetches)}")
    md_lines.append(f"- Reseller URLs OK: {sum(1 for f in fetches if f.status == 200 and f.text)}")
    md_lines.append(f"- Total text_extracts chars: {sum(len(t) for t in intel.text_extracts)}")
    md_lines.append("")
    for fr in fetches:
        md_lines.append(f"## {fr.url}")
        md_lines.append("")
        md_lines.append(f"- HTTP status: {fr.status}")
        if fr.error:
            md_lines.append(f"- Error: {fr.error}")
        if fr.text:
            md_lines.append(f"- Text length: {len(fr.text)} chars")
            md_lines.append(f"- Headings captured: {len(fr.headings)}")
            md_lines.append(f"- Links captured: {len(fr.links)}")
            md_lines.append("")
            md_lines.append("```text")
            md_lines.append(fr.text[:8_000])
            if len(fr.text) > 8_000:
                md_lines.append("…[truncated for audit]")
            md_lines.append("```")
        md_lines.append("")
    audit_path = audit_dir / f"{club_id}_aggregated.md"
    audit_path.write_text("\n".join(md_lines), encoding="utf-8")

    return {
        "club": club_id,
        "intel_aggregate": str(aggregate),
        "intel_step_files": [str(p) for p in step_files],
        "audit_md": str(audit_path),
        "ok_sources": sum(1 for f in fetches if f.status == 200 and f.text),
        "failed_sources": sum(1 for f in fetches if not (f.status == 200 and f.text)),
        "total_text_chars": sum(len(t) for t in intel.text_extracts),
    }


def write_synthetic_run_log(
    *,
    run_log_path: Path,
    club_id: str,
    area: str,
    covers_steps: list[str],
) -> None:
    """Emit a Plan 02-10-shaped run-log JSON so ``run_vision_wave`` can
    process the synthetic capture through the exact same pipeline.

    Key shape constraints:
      - ``status="captured"`` per step so the orchestrator iterates them
      - ``output_path=None`` (no PNG exists for synthetic captures)
      - ``reason="synthetic-text-fetch"`` for provenance

    The wave will note "missing PNG" for each step and skip the vision
    call — but the DOM-routed features still resolve via the per-step
    intel JSON we just wrote alongside.

    Plan 02-20 deferred-vision strategy: synthetic captures DO NOT
    have PNGs; visual-only and hybrid-vision-fallback features fall to
    ``no-data``. That's the intentional honest-data path (Phase 5
    Option A).
    """
    payload = {
        "club": club_id,
        "area": area,
        "flow_map": "scanner/capture/text_fetch.py (synthetic source)",
        "started_at": "synthetic-text-fetch",
        "steps": [
            {
                "step_name": step,
                "status": "synthetic",
                "duration_ms": 0,
                "output_path": None,
                "reason": "synthetic-text-fetch",
            }
            for step in covers_steps
        ],
        "source": "synthetic",
    }
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    run_log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "FetchResult",
    "HTTP_TIMEOUT",
    "MAX_BYTES",
    "MAX_TEXT_PER_URL",
    "USER_AGENT",
    "fetch_text_for_club",
    "synthesize_dom_intel",
    "write_synthetic_outputs",
    "write_synthetic_run_log",
]
