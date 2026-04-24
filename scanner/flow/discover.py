"""Flow-map click-path discovery — Plan 02-05 implementation.

Sync Playwright crawler rooted at an entry URL. Keyword-ranked link
extraction (hospitality / VIP / premium / tunnel club / corporate / box /
suite / experience / matchday event / loge / palco / area vip / club /
lounge), depth-limited descent (MAX_DEPTH=3, MAX_STEPS=15), and six
per-page detection hooks:

  1. login gate (URL pattern OR input[type=password])
  2. CAPTCHA (reCAPTCHA / hCaptcha / data-sitekey)
  3. broker redirect (allowlisted vendor origin → continue, record vendor)
  4. external redirect (unknown cross-origin → halt branch)
  5. dead-end (HTTP >= 400 or 404 h1 → record + halt branch)
  6. form-fill-pre-submit (>= 3 text/email/tel inputs → fill dummy, halt)

Emits a FlowMap JSON that self-validates via scanner.flow.validate.

Invariants:

- Never emits a `submit` action (schema Literal forbids it — D-16;
  this module additionally never passes the string "submit" to FlowStep).
- Never traverses login-gated pages (D-15; credentials are back-half).
- Never attempts CAPTCHA bypass (user decision 7 extends D-15).
- Dummy form-fill values are CONSTANTS (D-10), never credentials.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from playwright.sync_api import Page

from scanner.capture.cookies import dismiss_cookies
from scanner.flow.schema import FlowMap, FlowMapMetadata, FlowStep, FormField
from scanner.flow.validate import validate_flow_map


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOSPITALITY_LINK_PATTERN = re.compile(
    r"\b(hospitality|vip|premium|tunnel club|corporate|box|suite|"
    r"experience|matchday event|loge|palco|area vip|club|lounge|"
    r"enquiry|enquire|enquiries)\b",
    re.IGNORECASE,
)

LOGIN_URL_PATTERN = re.compile(
    r"/(login|sign[-_]?in|account|auth|sso)\b",
    re.IGNORECASE,
)

NOT_FOUND_PATTERN = re.compile(r"404|not found", re.IGNORECASE)

CAPTCHA_SELECTORS: tuple[str, ...] = (
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    ".g-recaptcha",
    "[data-sitekey]",
)

MAX_DEPTH = 3
MAX_STEPS = 15  # schema cap (D-15)

# Allowlisted third-party hospitality/ticketing vendors. Cross-origin
# redirects into these domains are treated as legitimate broker hops;
# the crawler continues and records `metadata.broker_vendor`. Any other
# cross-origin destination halts the branch (`metadata.external_redirects`).
BROKER_DOMAINS: dict[str, str] = {
    "seatunique.com": "seat_unique",
    "keithprowse.co.uk": "keith_prowse",
    "eventmasters.co.uk": "eventmasters",
    "p1travel.com": "p1_travel",
    "pitchinternational.com": "pitch_international",
}

# D-10 dummy form values — CONSTANTS (never credentials). The crawler never
# submits the form; these exist solely so a `fill` step records what values
# a downstream (back-half) capture run would type.
DUMMY_FORM_FIELDS: list[FormField] = [
    FormField(selector='input[name*="name" i]', value="Test Test"),
    FormField(selector='input[type="email"]', value="test@example.com"),
    FormField(selector='input[type="tel"]', value="+44 0000 000000"),
]


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def _netloc(url: str) -> str:
    """Return lowercased netloc with leading 'www.' stripped."""
    nl = urlparse(url).netloc.lower()
    if nl.startswith("www."):
        nl = nl[4:]
    return nl


def _broker_for(netloc: str) -> str | None:
    """Return broker vendor label if `netloc` matches (or ends with) an
    allowlisted broker domain."""
    for domain, vendor in BROKER_DOMAINS.items():
        if netloc == domain or netloc.endswith("." + domain):
            return vendor
    return None


def _club_from_entry_url(entry_url: str) -> str:
    """Crude fallback when the caller doesn't pass an explicit club slug."""
    netloc = _netloc(entry_url).replace("-", "")
    for known in ("mancity", "tottenham", "realmadrid", "psg", "chelsea"):
        if known in netloc:
            return known
    return "unknown"


# ---------------------------------------------------------------------------
# Per-page detection helpers (each returns bool; never raises)
# ---------------------------------------------------------------------------


def _safe_click(page: "Page", selector: str) -> bool:
    """Click `selector` with a short timeout. Return True on success, False
    on any Playwright exception (bad selector, navigation race, etc.)."""
    try:
        page.click(selector, timeout=5000)
        return True
    except Exception:
        return False


def _detect_login_gate(page: "Page", current_url: str) -> bool:
    """Login gate: URL matches LOGIN_URL_PATTERN OR page has a password input."""
    if LOGIN_URL_PATTERN.search(current_url):
        return True
    try:
        return page.query_selector('input[type="password"]') is not None
    except Exception:
        return False


def _detect_captcha(page: "Page") -> bool:
    """CAPTCHA detection: any of CAPTCHA_SELECTORS present on page."""
    for sel in CAPTCHA_SELECTORS:
        try:
            if page.query_selector(sel) is not None:
                return True
        except Exception:
            continue
    return False


def _detect_dead_end(page: "Page", status: int | None) -> bool:
    """Dead-end: HTTP status >= 400 OR <h1> matches NOT_FOUND_PATTERN."""
    if status is not None and status >= 400:
        return True
    try:
        h1 = page.query_selector("h1")
        if h1 is not None:
            text = h1.text_content() or ""
            if NOT_FOUND_PATTERN.search(text):
                return True
    except Exception:
        pass
    return False


def _detect_form(page: "Page") -> bool:
    """Pre-submit form: any <form> containing >= 3 text/email/tel inputs."""
    try:
        forms = page.query_selector_all("form")
        for f in forms:
            inputs = f.query_selector_all(
                'input[type="text"], input[type="email"], input[type="tel"]'
            )
            if len(inputs) >= 3:
                return True
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Link ranking
# ---------------------------------------------------------------------------


def _rank_links(
    page: "Page",
    entry_origin: str,
    visited: set[str],
) -> list[tuple[str, str]]:
    """Return [(full_url, selector), ...] ranked by hospitality keyword match.

    - Same-origin OR allowlisted broker domain only.
    - Link text matches HOSPITALITY_LINK_PATTERN worth +2; href match worth +1.
    - Already-visited URLs excluded.
    - Zero-score links dropped.
    """
    try:
        anchors = page.query_selector_all("a[href]")
    except Exception:
        return []

    ranked: list[tuple[int, str, str]] = []
    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
            text = (a.text_content() or "").strip()
        except Exception:
            continue
        if not href:
            continue
        full_url = urljoin(page.url, href)
        if full_url in visited:
            continue
        netloc = _netloc(full_url)
        same_origin = netloc == entry_origin or netloc == ""
        is_broker = _broker_for(netloc) is not None
        if not (same_origin or is_broker):
            # Non-broker cross-origin links are dropped at the ranking stage —
            # the crawler is same-origin + allowlisted-broker only.
            continue
        score = 0
        if HOSPITALITY_LINK_PATTERN.search(text):
            score += 2
        if HOSPITALITY_LINK_PATTERN.search(href):
            score += 1
        if score == 0:
            continue
        selector = f'a[href="{href}"]'
        ranked.append((score, full_url, selector))

    ranked.sort(reverse=True, key=lambda t: t[0])
    return [(url, sel) for _, url, sel in ranked]


# ---------------------------------------------------------------------------
# Cross-origin inspection (broker vs external-unknown)
# ---------------------------------------------------------------------------


def _inspect_origin(
    current_url: str,
    entry_origin: str,
    meta: FlowMapMetadata,
) -> str:
    """Return 'same', 'broker', or 'external'; mutate meta for broker/external.

    - 'same'     — netloc matches entry_origin (or is empty).
    - 'broker'   — netloc matches an allowlisted broker domain; meta.broker_vendor set.
    - 'external' — cross-origin, non-broker; meta.external_redirects appended.
    """
    netloc = _netloc(current_url)
    if not netloc or netloc == entry_origin:
        return "same"
    broker = _broker_for(netloc)
    if broker is not None:
        # First broker encountered wins; subsequent hops do not overwrite.
        if meta.broker_vendor is None:
            meta.broker_vendor = broker
        return "broker"
    meta.external_redirects.append(current_url)
    return "external"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def discover_flow(
    entry_url: str,
    out_path: Path,
    *,
    area: str = "hospitality",
    club: str | None = None,
    headless: bool = True,
) -> FlowMap:
    """Crawl `entry_url` and write a FlowMap JSON at `out_path`.

    Args:
        entry_url: Landing URL to start discovery from.
        out_path: Destination path for the generated flow-map JSON.
        area: Area slug (default "hospitality").
        club: Club slug for cookie-strategy dispatch. If None, inferred from
            `entry_url`.
        headless: Run Chromium headless (default True — CI posture).

    Returns:
        The validated FlowMap written to disk.

    Raises:
        FlowMapValidationError: if the emitted JSON fails schema validation
            (should not happen — internal construction uses the same models).
    """
    club_slug = club or _club_from_entry_url(entry_url)
    entry_origin = _netloc(entry_url)
    steps: list[FlowStep] = []
    meta = FlowMapMetadata()
    visited: set[str] = {entry_url}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # --- Landing ---
        # Bounded-timeout landing: `networkidle` on its own never completes on
        # club sites running long-poll analytics (observed on MCFC 2026-04-24).
        # Mirror the _descend pattern: wait for DOM first, then best-effort
        # networkidle with the same 10 s cap used in _descend.
        response = page.goto(entry_url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        status = response.status if response is not None else None
        steps.append(FlowStep(
            step_name="landing",
            action="navigate",
            url=entry_url,
        ))
        steps.append(FlowStep(
            step_name="landing-wait",
            action="wait",
            wait_for="networkidle",
        ))
        steps.append(FlowStep(
            step_name="landing-shot",
            action="screenshot",
        ))

        # Cookie dismissal BEFORE any link enumeration (D-15 carryover).
        if not dismiss_cookies(page, club=club_slug):
            meta.cookie_dismiss_failed = True

        # Landing-level dead-end shortcut.
        if _detect_dead_end(page, status):
            meta.dead_ends.append(entry_url)
            browser.close()
            return _write_and_validate(
                out_path, area, club_slug, entry_url, steps, meta,
            )

        # --- Depth-limited descent ---
        _descend(
            page=page,
            depth=1,
            entry_origin=entry_origin,
            visited=visited,
            steps=steps,
            meta=meta,
        )

        browser.close()

    return _write_and_validate(out_path, area, club_slug, entry_url, steps, meta)


# ---------------------------------------------------------------------------
# Descent loop (module-level helper — recursion with shared state)
# ---------------------------------------------------------------------------


def _descend(
    *,
    page: "Page",
    depth: int,
    entry_origin: str,
    visited: set[str],
    steps: list[FlowStep],
    meta: FlowMapMetadata,
) -> None:
    """Depth-limited greedy descent: rank links on the current page, click the
    highest-scoring unvisited one, emit FlowSteps, check detection hooks on
    the new page, and recurse. Stops the branch on any halt condition.
    """
    if depth > MAX_DEPTH:
        return
    # Leave room for at least one more (click, wait, shot) triple.
    if len(steps) >= MAX_STEPS - 2:
        return

    current_url = page.url

    # 1. CAPTCHA — halt branch (user decision 7).
    if _detect_captcha(page):
        meta.captcha_encountered = True
        return

    # 2. Origin inspection (broker/external).
    origin_kind = _inspect_origin(current_url, entry_origin, meta)
    if origin_kind == "external":
        return

    # 3. Login gate — halt branch (D-15).
    if _detect_login_gate(page, current_url):
        meta.login_gated_steps.append(f"depth-{depth - 1}")
        return

    # 4. Form pre-submit — fill with dummy data and halt (never submit).
    if _detect_form(page):
        if len(steps) < MAX_STEPS:
            steps.append(FlowStep(
                step_name=f"fill-form-depth-{depth - 1}",
                action="fill",
                form_fields=list(DUMMY_FORM_FIELDS),
            ))
        if len(steps) < MAX_STEPS:
            steps.append(FlowStep(
                step_name=f"form-shot-depth-{depth - 1}",
                action="screenshot",
            ))
        return

    # 5. Rank links and greedily follow the best one.
    for target_url, selector in _rank_links(page, entry_origin, visited):
        if len(steps) >= MAX_STEPS - 2:
            return
        visited.add(target_url)
        if not _safe_click(page, selector):
            meta.dead_ends.append(target_url)
            continue
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # Emit the click/wait/shot triple.
        steps.append(FlowStep(
            step_name=f"click-depth-{depth}",
            action="click",
            selector=selector,
        ))
        steps.append(FlowStep(
            step_name=f"wait-depth-{depth}",
            action="wait",
            wait_for="networkidle",
        ))
        steps.append(FlowStep(
            step_name=f"shot-depth-{depth}",
            action="screenshot",
        ))

        # Per-page detection on the NEW page.
        new_url = page.url

        # Dead-end on the landed page.
        try:
            h1 = page.query_selector("h1")
            h1_text = (h1.text_content() if h1 is not None else "") or ""
        except Exception:
            h1_text = ""
        if NOT_FOUND_PATTERN.search(h1_text):
            meta.dead_ends.append(new_url)
            return

        # Recurse one level deeper (greedy — one branch per depth).
        _descend(
            page=page,
            depth=depth + 1,
            entry_origin=entry_origin,
            visited=visited,
            steps=steps,
            meta=meta,
        )
        return


# ---------------------------------------------------------------------------
# Disk write + self-check
# ---------------------------------------------------------------------------


def _write_and_validate(
    out_path: Path,
    area: str,
    club: str,
    entry_url: str,
    steps: list[FlowStep],
    meta: FlowMapMetadata,
) -> FlowMap:
    """Write the FlowMap JSON and round-trip through validate_flow_map.

    Preserves `steps[0]` (landing navigate) and `steps[-1]` under truncation.
    """
    if len(steps) > MAX_STEPS:
        # Preserve first and last; trim middle.
        keep = [steps[0]] + steps[1 : MAX_STEPS - 1] + [steps[-1]]
        steps = keep[:MAX_STEPS]

    fm = FlowMap(
        area=area,
        club=club,
        entry_url=entry_url,
        steps=steps,
        metadata=meta,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(fm.model_dump_json(indent=2), encoding="utf-8")
    # Self-check — raises FlowMapValidationError if something slipped.
    validate_flow_map(out_path)
    return fm


__all__ = [
    "discover_flow",
    "BROKER_DOMAINS",
    "HOSPITALITY_LINK_PATTERN",
    "LOGIN_URL_PATTERN",
    "CAPTCHA_SELECTORS",
    "MAX_DEPTH",
    "MAX_STEPS",
]
