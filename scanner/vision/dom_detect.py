"""DOM-based feature detection (Plan 02-15 Wave C).

The vision wave (Opus + Sonnet) is expensive: ~$0.30-0.50 per screenshot at
retail rates. Many hospitality features are programmatically obvious from
the DOM — counting form inputs, finding email/phone fields, scanning
heading text for keywords. Detecting these via DOM rules first saves
roughly 60% of the vision spend in the projected re-run of Plan 02-11.

Architecture
------------
This module owns a static :data:`RULES` registry — keyed by feature_key,
each rule is a callable ``(DomIntel) -> bool``. Hybrid features (where the
DOM signal is informative but not authoritative) call into the rule first
and fall back to vision when the rule returns ``False`` or is absent.

The detection function returns a dict of ``feature_key -> FeatureVerdict``
matching the contract used by :mod:`scanner.vision.judge`. Each DOM-derived
verdict carries ``confidence=0.95`` and ``notes="dom-detect: <rule>"`` so
downstream consensus / dispute logic can identify the provenance.

D-21 deviation note: Phase 2 normally doesn't introduce new vision
modules, but the 88% absence rate in Plan 02-11 strongly implicates
vision-only detection missing programmatically-obvious features. See
``scanner/CHANGELOG-V2.md``.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable

from scanner.capture.dom_intel import DomIntel
from scanner.vision.schema import FeatureDef, FeatureVerdict


# Detection-mode literal — added to FeatureDef in Wave D as a metadata field.
# Kept here (rather than imported from schema) so the constants are module-
# local and rule authors can reference them without circular imports.
DETECTION_DOM = "dom"
DETECTION_VISUAL = "visual"
DETECTION_HYBRID = "hybrid"

# Confidence pinned for any DOM-only verdict — high but not absolute, so
# hybrid routing in judge.py can still treat a "missing" DOM signal as
# inconclusive when the rule returns False.
DOM_CONFIDENCE = 0.95

# ---------------------------------------------------------------------------
# Rule helpers — small predicates the rules below compose.
# ---------------------------------------------------------------------------


def _all_text_blobs(intel: DomIntel) -> str:
    """Concatenated lower-cased text from headings + buttons + title.

    Used by keyword-presence rules. Covers the tier-1 evidence surfaces
    without dragging the entire DOM into the regex.
    """
    parts = [intel.title]
    parts.extend(h.text for h in intel.headings)
    parts.extend(b.text for b in intel.buttons)
    parts.extend(b.alt for b in intel.images)
    return "\n".join(parts).lower()


def _meta_blob(intel: DomIntel) -> str:
    """Lower-cased meta tag values + jsonld text — coarser keyword surface."""
    parts = list(intel.meta.values())
    for entry in intel.schema_jsonld:
        try:
            parts.append(json.dumps(entry, default=str))
        except Exception:
            pass
    return "\n".join(parts).lower()


def _has_input_type(intel: DomIntel, type_: str) -> bool:
    """Any form has an input whose ``type`` attribute matches ``type_``."""
    return any(
        any(i.type == type_ for i in f.inputs) for f in intel.forms
    )


def _input_count(intel: DomIntel) -> int:
    """Sum of inputs across all forms (matches counts.inputs from JS)."""
    return sum(len(f.inputs) for f in intel.forms)


_PRICE_RE = re.compile(
    r"(?:£|€|\$|usd|gbp|eur)\s*\d+(?:[.,]\d+)?", re.IGNORECASE
)
_PRICE_PER_PERSON_RE = re.compile(
    r"(?:£|€|\$)\s*\d+(?:[.,]\d+)?\s*(?:per\s+|/\s*)?(?:person|guest|head|pp\b)",
    re.IGNORECASE,
)
# Plan 02-18 widening: hospitality tier-landing pages routinely use
# "from £NNN" / "tickets from £NNN" / "prices from £NNN" copy where the
# per-person semantics is implicit (a tier price is by definition per-seat).
# v1 vision interpreted these as price_per_person_visible:true; we restore
# that interpretation in DOM detection here.
_PRICE_TIER_RE = re.compile(
    r"(?:tickets?|prices?|packages?)?\s*from\s+(?:£|€|\$)\s*\d+",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

#: Each rule is a single-arg callable ``DomIntel -> bool``. ``True`` means
#: "feature present"; ``False`` means "DOM did NOT find evidence" — for
#: hybrid features judge.py escalates that to vision instead of treating it
#: as a confirmed absence.
RULES: dict[str, Callable[[DomIntel], bool]] = {
    # -- Pricing Transparency ----------------------------------------------
    "price_per_person_visible": lambda intel: bool(
        # Plan 02-18: accept both explicit per-person phrasing AND
        # tier-landing "from £NNN" copy. Hospitality tier prices are
        # de-facto per-person (you book a single seat at a tier).
        _PRICE_PER_PERSON_RE.search(_all_text_blobs(intel))
        or _PRICE_TIER_RE.search(_all_text_blobs(intel))
    ),
    "fixture_category_tiers": lambda intel: any(
        re.search(r"\bcat(egory)?\s*[abc1-3]\b", t.lower())
        for t in [intel.title] + [h.text for h in intel.headings] + [b.text for b in intel.buttons]
    ),
    "price_range_by_match": lambda intel: (
        # Look for a price range pattern: £X – £Y or £X to £Y
        bool(re.search(r"(?:£|€|\$)\s*\d+\s*[–\-to]+\s*(?:£|€|\$)?\s*\d+",
                       _all_text_blobs(intel)))
    ),
    # -- Package Discovery -------------------------------------------------
    "tier_comparison_table": lambda intel: intel.counts.tables >= 1,
    "package_tier_list": lambda intel: (
        # 2+ tier-name buttons OR 2+ price patterns OR 2+ table rows
        len(re.findall(r"(?:£|€)\s*\d+", " ".join(b.text for b in intel.buttons))) >= 2
        or len([h for h in intel.headings if h.tag in ("H2", "H3")]) >= 3
    ),
    # -- Food & Beverage ---------------------------------------------------
    "menu_preview": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["menu", "starter", "course", "dish", "à la carte", "tasting"]
    ),
    "vegetarian_options": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["vegetarian", "vegan", "plant-based", "veggie"]
    ),
    "allergen_info": lambda intel: any(
        kw in _all_text_blobs(intel) + _meta_blob(intel)
        for kw in ["allergen", "allergy", "gluten-free", "dairy-free", "nut-free"]
    ),
    "kids_menu": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["kids menu", "children's menu", "child menu", "kids' menu"]
    ),
    "chef_attribution": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["chef", "michelin", "executive chef", "head chef"]
    ),
    # -- Premium Amenities -------------------------------------------------
    "parking_included_indicator": lambda intel: (
        "parking" in _all_text_blobs(intel)
    ),
    "stadium_tour_inclusion": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["stadium tour", "behind-the-scenes tour", "stadium walkthrough"]
    ),
    "pitchside_or_tunnel_access": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["pitchside", "tunnel", "tunnel club", "trackside", "dugout"]
    ),
    "concierge_service": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["concierge", "hostess", "host service", "dedicated host"]
    ),
    # -- Match Selector UX -------------------------------------------------
    "fixture_list_visible": lambda intel: (
        # 2+ headings/buttons that look like fixture rows (date + opponent or vs)
        sum(1 for t in [h.text for h in intel.headings] + [b.text for b in intel.buttons]
            if re.search(r"\bvs\.?\s+\w+|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
                         t.lower())) >= 2
    ),
    "competition_filter": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["premier league", "champions league", "europa", "fa cup", "carabao", "ucl", "epl"]
    ),
    # -- Enquiry Friction --------------------------------------------------
    "enquiry_form_field_count_le_7": lambda intel: (
        intel.counts.forms >= 1 and 1 <= _input_count(intel) <= 7
    ),
    "buy_now_without_enquiry": lambda intel: any(
        # Plan 02-18: broadened to include hospitality-specific buy
        # phrasing. v1 saw RMA's "Buy Hospitality tickets" button as
        # present; v2's narrower keyword list missed it.
        # Spanish/French equivalents added for international clubs.
        kw in (b.text or "").lower()
        for b in intel.buttons
        for kw in [
            "book now", "buy now", "buy ticket", "purchase",
            "buy hospitality", "buy seat", "checkout",
            "comprar", "reservar",  # ES (RMA, ATM)
            "réserver", "acheter",  # FR (PSG)
        ]
    ),
    "phone_booking_option": lambda intel: (
        # tel: link or phone-number-shaped string near "call"
        any((b.href or "").startswith("tel:") for b in intel.buttons)
        or bool(re.search(r"(?:call|phone|tel)[:\s]+\+?\d", _all_text_blobs(intel)))
    ),
    # -- Post-Booking Comms (text-keyword heuristics) ----------------------
    "booking_change_policy_visible": lambda intel: any(
        kw in _all_text_blobs(intel) + _meta_blob(intel)
        for kw in ["cancellation policy", "change policy", "amend booking", "refund policy"]
    ),
    "cancellation_refund_window": lambda intel: bool(
        re.search(
            r"(?:cancellation|refund).{0,40}(?:\d+\s*(?:day|week|month))",
            _all_text_blobs(intel) + _meta_blob(intel),
        )
    ),
    "fixture_change_notification": lambda intel: any(
        kw in _all_text_blobs(intel) + _meta_blob(intel)
        for kw in ["fixture change", "schedule change", "rearranged", "kick-off time may change"]
    ),
    # -- Booking Confirmation ---------------------------------------------
    "receipt_download": lambda intel: any(
        kw in _all_text_blobs(intel)
        for kw in ["download receipt", "vat invoice", "download invoice"]
    ),
}


def detect_feature(intel: DomIntel, feature: FeatureDef) -> FeatureVerdict | None:
    """Run the registered rule for ``feature`` (if any) against ``intel``.

    Returns
    -------
    FeatureVerdict | None
        ``None`` if no rule is registered. Otherwise a verdict whose
        ``present`` attribute is the rule's bool result, ``confidence`` is
        :data:`DOM_CONFIDENCE`, and ``notes`` carries the rule provenance.
    """
    rule = RULES.get(feature.key)
    if rule is None:
        return None
    try:
        present = bool(rule(intel))
    except Exception as exc:  # pragma: no cover — defensive only
        return FeatureVerdict(
            present=False,
            step="dom-detect",
            evidence_bbox=None,
            confidence=0.0,
            notes=f"dom-detect: rule error: {exc!s}"[:500],
        )
    return FeatureVerdict(
        present=present,
        step="dom-detect",
        evidence_bbox=None,
        confidence=DOM_CONFIDENCE,
        notes=f"dom-detect: rule={feature.key}",
    )


def detect_features(
    intel: DomIntel, rubric: list[FeatureDef]
) -> dict[str, FeatureVerdict]:
    """Run all registered rules against ``intel``.

    Skips features without a registered rule — judge.py routes those to
    vision per their ``detection`` mode. Returns a dict keyed by
    ``feature_key``.
    """
    out: dict[str, FeatureVerdict] = {}
    for feature in rubric:
        verdict = detect_feature(intel, feature)
        if verdict is not None:
            out[feature.key] = verdict
    return out


__all__ = [
    "DETECTION_DOM",
    "DETECTION_HYBRID",
    "DETECTION_VISUAL",
    "DOM_CONFIDENCE",
    "RULES",
    "detect_feature",
    "detect_features",
]
