"""DOM intel extraction (Plan 02-15 Wave B).

The :data:`EXTRACT_DOM_INTEL_JS` string is evaluated inside the page via
``page.evaluate(...)`` after the screenshot is taken. The returned dict
matches the :class:`DomIntel` Pydantic schema below 1:1 — capture writes it
to ``{output_dir}/dom/{club}_{step}_intel.json`` for later consumption by
:mod:`scanner.vision.dom_detect`.

Design notes
------------
- Pure JS string with no template substitution → no injection surface.
- Image lists are capped at 50 items to avoid bloating the JSON for image-
  heavy hospitality pages.
- ``schema_jsonld`` swallows JSON.parse errors (ld+json blocks routinely
  carry trailing commas / NBSP that ``JSON.parse`` rejects); failed entries
  are dropped, the rest are kept.
- ``meta`` is a flat string→string dict; nothing fancier (we don't need
  multi-value support for hospitality scoring).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# JS string passed to page.evaluate(). Pure DOM read — no event dispatch,
# no localStorage, no cookie touch. Side-effect-free per D-16 spirit.
EXTRACT_DOM_INTEL_JS = r"""
() => {
  const text = el => (el && el.innerText ? el.innerText : '').trim();
  const bbox = el => {
    if (!el || !el.getBoundingClientRect) return null;
    const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  };
  return {
    title: document.title || '',
    url: location.href,
    headings: [...document.querySelectorAll('h1,h2,h3,h4')].map(h => ({
      tag: h.tagName, text: text(h), bbox: bbox(h)
    })),
    buttons: [...document.querySelectorAll('button, a, [role="button"]')]
      .filter(el => text(el))
      .slice(0, 200)
      .map(el => ({
        text: text(el),
        tag: el.tagName,
        href: el.getAttribute('href') || null,
        bbox: bbox(el)
      })),
    forms: [...document.querySelectorAll('form')].map(f => ({
      action: f.getAttribute('action') || '',
      method: (f.getAttribute('method') || 'get').toLowerCase(),
      inputs: [...f.querySelectorAll('input, select, textarea')].map(i => ({
        type: (i.getAttribute('type') || i.tagName || '').toLowerCase(),
        name: i.getAttribute('name') || '',
        placeholder: i.getAttribute('placeholder') || '',
        required: i.hasAttribute('required')
      }))
    })),
    images: [...document.querySelectorAll('img')].slice(0, 50).map(img => ({
      src: img.getAttribute('src') || '',
      alt: img.getAttribute('alt') || '',
      bbox: bbox(img)
    })),
    schema_jsonld: [...document.querySelectorAll('script[type="application/ld+json"]')]
      .map(s => { try { return JSON.parse(s.innerText || s.textContent || 'null'); } catch (e) { return null; } })
      .filter(x => x !== null),
    meta: Object.fromEntries(
      [...document.querySelectorAll('meta[property], meta[name]')].map(m => [
        m.getAttribute('property') || m.getAttribute('name'),
        m.getAttribute('content') || ''
      ])
    ),
    counts: {
      forms: document.querySelectorAll('form').length,
      inputs: document.querySelectorAll('input, select, textarea').length,
      buttons: document.querySelectorAll('button').length,
      tables: document.querySelectorAll('table').length,
      images: document.querySelectorAll('img').length
    }
  };
}
"""


class DomBbox(BaseModel):
    """A bounding box in CSS pixels (origin top-left, viewport-relative)."""

    x: float
    y: float
    w: float
    h: float


class DomHeading(BaseModel):
    """A single heading element (h1..h4)."""

    tag: str
    text: str
    bbox: DomBbox | None = None


class DomButton(BaseModel):
    """A clickable element — button, anchor, or role=button."""

    text: str
    tag: str
    href: str | None = None
    bbox: DomBbox | None = None


class DomFormInput(BaseModel):
    """A single input/select/textarea inside a form."""

    type: str = ""
    name: str = ""
    placeholder: str = ""
    required: bool = False


class DomForm(BaseModel):
    """A form element with its enumerable inputs."""

    action: str = ""
    method: str = "get"
    inputs: list[DomFormInput] = Field(default_factory=list)


class DomImage(BaseModel):
    """An ``<img>`` element."""

    src: str = ""
    alt: str = ""
    bbox: DomBbox | None = None


class DomCounts(BaseModel):
    """Cheap structural counts for fast heuristics."""

    forms: int = 0
    inputs: int = 0
    buttons: int = 0
    tables: int = 0
    images: int = 0


class DomIntel(BaseModel):
    """Structured snapshot of a captured page's DOM.

    Mirrors the shape returned by :data:`EXTRACT_DOM_INTEL_JS`. Pydantic
    coerces the JS object → these models at validation time; downstream
    detection rules consume the typed surface.

    Plan 02-20 additive fields:
      - ``text_extracts`` — raw text content blocks aggregated from third-
        party reseller pages or search snippets when the official site is
        Cloudflare-blocked. Live captures leave this empty; synthetic
        captures populate it. ``dom_detect`` rules consult this as a
        fallback text surface so the rule set is text-source-agnostic.
      - ``source`` — provenance marker. ``"live"`` (default) is a real
        Playwright + DOM-evaluate capture; ``"synthetic"`` is built from
        text-fetched reseller content via ``scanner.capture.text_fetch``.
        Downstream consumers (analysis, contact sheet, coverage report)
        use this to distinguish reseller-described content from live
        page state.
    """

    title: str = ""
    url: str = ""
    headings: list[DomHeading] = Field(default_factory=list)
    buttons: list[DomButton] = Field(default_factory=list)
    forms: list[DomForm] = Field(default_factory=list)
    images: list[DomImage] = Field(default_factory=list)
    schema_jsonld: list[Any] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)
    counts: DomCounts = Field(default_factory=DomCounts)
    text_extracts: list[str] = Field(default_factory=list)
    source: Literal["live", "synthetic"] = "live"


__all__ = [
    "EXTRACT_DOM_INTEL_JS",
    "DomBbox",
    "DomButton",
    "DomCounts",
    "DomForm",
    "DomFormInput",
    "DomHeading",
    "DomImage",
    "DomIntel",
]
