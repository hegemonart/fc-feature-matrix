"""Pydantic schemas for flow-map input JSON.

A flow-map is a human-authored JSON document that drives Playwright through a
capture flow. Invariants enforced at the schema level:

- D-15: `FlowMap.steps` must have 1-15 items. Longer flows suggest a re-design
  (the scanner is for focused per-area captures, not full-site crawls).
- D-16: `FlowStep.action` is restricted to a closed Literal of
  navigate / click / fill / wait / screenshot. Any action outside this set is
  rejected at schema load-time so captures can never trigger real form
  dispatch against club sites.

Downstream: `scanner.capture.capture` consumes `FlowStep.hide_selectors`,
`FlowStep.wait_for`, etc. (Plan 03).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FormField(BaseModel):
    """A single form input to fill during a `fill` step."""

    selector: str
    value: str  # e.g. "Test Test", "test@example.com"


class FlowMapMetadata(BaseModel):
    """Crawler-produced metadata about flow-discovery outcomes (Plan 02-05).

    Default-factory initialized on FlowMap so pre-existing Phase-1 flow-map
    JSONs (with no `metadata` key) continue to validate unchanged.

    Fields describe branches the crawler hit but could not fully traverse:

    - `broker_vendor` — allowlisted third-party ticketing/hospitality vendor
      encountered mid-crawl (e.g. seat_unique, keith_prowse). None when the
      flow stays same-origin.
    - `login_gated_steps` — step names/labels where a login wall was
      detected (URL matched login pattern or page had input[type=password]).
      The crawler halts that branch per D-15; credentials are back-half.
    - `external_redirects` — URLs that redirected cross-origin to a
      non-broker destination; the crawler halts that branch.
    - `dead_ends` — URLs that returned HTTP >= 400 or displayed a 404 page.
    - `cookie_dismiss_failed` — True when dismiss_cookies() returned False
      on the landing page (crawl still proceeds but the signal is recorded).
    - `fixture_id` — optional D-09 record tying the crawl to a specific
      match fixture (may be None in front-half).
    - `captcha_encountered` — True when a reCAPTCHA/hCaptcha widget was
      detected; the crawler halts that branch (user decision 7 extends D-15).
    - `bot_challenge_encountered` — True when a Cloudflare-style bot
      challenge ("Just a moment..." interstitial) was detected (Plan 02-08).
      Sibling to captcha_encountered: same halt-and-record contract.
    - `bot_challenge_reason` — Free-form classifier label, e.g. "turnstile"
      for Cloudflare; future-extensible to "arkose", "datadome", etc.
    - `trusted_subdomains_used` — Subdomains that were treated as
      same-origin by the trusted-subdomain allowlist (e.g.
      hospitality.chelseafc.com when crawling chelseafc.com). Distinguished
      from broker_vendor (cross-origin third-party) and external_redirects
      (untrusted cross-origin). Plan 02-08.
    """

    broker_vendor: str | None = None
    login_gated_steps: list[str] = Field(default_factory=list)
    external_redirects: list[str] = Field(default_factory=list)
    dead_ends: list[str] = Field(default_factory=list)
    cookie_dismiss_failed: bool = False
    fixture_id: str | None = None
    captcha_encountered: bool = False
    # Plan 02-08 additive fields — default-factory so pre-existing flow-map
    # JSONs (front-half v1) continue to validate unchanged.
    bot_challenge_encountered: bool = False
    bot_challenge_reason: str | None = None
    trusted_subdomains_used: list[str] = Field(default_factory=list)


class FlowStep(BaseModel):
    """A single step in a flow-map.

    `action` is a strict closed Literal union. Per D-16, any action that would
    dispatch a real form request is intentionally absent from the union so
    ValidationError fires at load-time.

    Plan 02-09 additive fields (default-Falsy so front-half flow-map JSONs
    continue to validate unchanged):

    - ``requires_credentials`` — capture orchestrator (Plan 02-10) calls
      ``credentials.get_credential()`` and authenticates BEFORE running this
      step. Used for login-gated package detail pages (e.g. PSG billetterie).
    - ``manual_chrome_mcp`` — capture orchestrator pauses Playwright and
      prompts the user to drive the step via Chrome MCP. Used for steps
      blocked by Cloudflare Turnstile (MCFC, PSG-billetterie) or CAPTCHA
      (Real Madrid VIP-area).
    - ``skipped`` — free-form reason the step is intentionally skipped (e.g.
      ``"requires-paid-account"`` for Chelsea Option B partial decision,
      2026-04-27). The orchestrator records the skip in coverage output and
      does NOT attempt to execute the step.
    """

    step_name: str
    url: str | None = None
    # D-16 invariant: the Literal union is closed — only the five safe
    # actions below are accepted; anything else fails at load.
    action: Literal["navigate", "click", "fill", "wait", "screenshot"]
    selector: str | None = None
    form_fields: list[FormField] | None = None
    hide_selectors: list[str] = Field(default_factory=list)
    wait_for: str | None = None  # CSS selector or 'networkidle'
    # Plan 02-09 additive override fields — see class docstring above.
    requires_credentials: bool = False
    manual_chrome_mcp: bool = False
    skipped: str | None = None


class FlowMap(BaseModel):
    """Top-level flow-map document.

    `steps` is bounded by the D-15 invariant (1-15 steps) so malformed
    flow-maps fail at load-time rather than part-way through a Playwright run.

    `metadata` (Plan 02-05) carries crawler-produced outcomes from flow
    discovery. Default-factory initialized so pre-existing Phase-1 flow-map
    fixtures without a `metadata` key continue to validate unchanged.
    """

    area: str
    club: str
    entry_url: str
    steps: list[FlowStep] = Field(min_length=1, max_length=15)  # D-15
    metadata: FlowMapMetadata = Field(default_factory=FlowMapMetadata)


__all__ = ["FlowMap", "FlowStep", "FormField", "FlowMapMetadata"]
