"""Tests for scanner.vision.dom_detect (Plan 02-15 Wave C).

Each rule gets a synthetic DomIntel fixture exercising the positive AND
negative branches. Edge cases (empty forms, no buttons, mixed case in price
patterns) are interleaved.
"""
from __future__ import annotations

from scanner.capture.dom_intel import (
    DomBbox,
    DomButton,
    DomCounts,
    DomForm,
    DomFormInput,
    DomHeading,
    DomImage,
    DomIntel,
)
from scanner.vision.dom_detect import (
    DETECTION_DOM,
    DETECTION_HYBRID,
    DETECTION_VISUAL,
    DOM_CONFIDENCE,
    RULES,
    detect_feature,
    detect_features,
)
from scanner.vision.schema import FeatureDef


def _intel(**overrides) -> DomIntel:
    """Build a DomIntel with sensible defaults; overrides replace fields."""
    base = dict(
        title="",
        url="https://example.test/",
        headings=[],
        buttons=[],
        forms=[],
        images=[],
        schema_jsonld=[],
        meta={},
        counts=DomCounts(),
    )
    base.update(overrides)
    return DomIntel(**base)


def _heading(tag="H2", text="", bbox=None) -> DomHeading:
    return DomHeading(tag=tag, text=text, bbox=bbox)


def _button(text="", href=None, tag="BUTTON") -> DomButton:
    return DomButton(text=text, tag=tag, href=href, bbox=None)


def _form(*, inputs: list[DomFormInput] | None = None, action="", method="post") -> DomForm:
    return DomForm(action=action, method=method, inputs=inputs or [])


def _input(type_="text", name="", required=False) -> DomFormInput:
    return DomFormInput(type=type_, name=name, placeholder="", required=required)


# ---------------------------------------------------------------------------
# Constants & registry
# ---------------------------------------------------------------------------


def test_detection_constants_exposed():
    assert DETECTION_DOM == "dom"
    assert DETECTION_VISUAL == "visual"
    assert DETECTION_HYBRID == "hybrid"


def test_dom_confidence_is_high_but_not_one():
    assert 0.9 <= DOM_CONFIDENCE < 1.0


def test_rules_registry_has_at_least_15_rules():
    """Plan 02-15 Wave C target: 15+ rules covering the highest-volume features."""
    assert len(RULES) >= 15, f"only {len(RULES)} rules registered"


# ---------------------------------------------------------------------------
# Pricing rules
# ---------------------------------------------------------------------------


def test_price_per_person_visible_positive():
    intel = _intel(
        headings=[_heading(text="Tunnel Club Premier — £499 per person")]
    )
    assert RULES["price_per_person_visible"](intel) is True


def test_price_per_person_visible_negative_no_currency():
    intel = _intel(headings=[_heading(text="Tunnel Club Premier")])
    assert RULES["price_per_person_visible"](intel) is False


def test_price_per_person_alt_phrasing_pp():
    intel = _intel(buttons=[_button(text="From £350pp")])
    assert RULES["price_per_person_visible"](intel) is True


# Plan 02-18 regression tests — v1→v2 absences fixed by widening the rule.

def test_price_per_person_visible_tickets_from_phrasing():
    """TOT matchday-options page shows 'TICKETS FROM £249' / 'Tickets from £25'.

    Hospitality tier prices are de-facto per-person (you book a single seat at
    a tier). v1 vision read these as present; v2's narrower DOM rule missed
    them. Plan 02-18 reinstates the tier-from pattern.
    """
    intel = _intel(buttons=[_button(text="TICKETS FROM £249")])
    assert RULES["price_per_person_visible"](intel) is True


def test_price_per_person_visible_prices_from_phrasing():
    intel = _intel(headings=[_heading(text="Prices from £450")])
    assert RULES["price_per_person_visible"](intel) is True


def test_price_per_person_visible_bare_from_phrasing():
    """Real-world TOT button: 'Tickets from £25' (mixed case)."""
    intel = _intel(buttons=[_button(text="Tickets from £25")])
    assert RULES["price_per_person_visible"](intel) is True


def test_price_per_person_visible_negative_no_currency_post_widen():
    """Widening must not match plain 'from £' without digits or other 'from' copy."""
    intel = _intel(headings=[_heading(text="Watch the latest videos from Spurs.")])
    assert RULES["price_per_person_visible"](intel) is False


def test_fixture_category_tiers_positive_letter():
    intel = _intel(headings=[_heading(text="Cat A pricing applies")])
    assert RULES["fixture_category_tiers"](intel) is True


def test_fixture_category_tiers_negative():
    intel = _intel(headings=[_heading(text="Premier seating")])
    assert RULES["fixture_category_tiers"](intel) is False


def test_price_range_by_match_positive():
    intel = _intel(headings=[_heading(text="£269 – £699")])
    assert RULES["price_range_by_match"](intel) is True


# ---------------------------------------------------------------------------
# Package discovery rules
# ---------------------------------------------------------------------------


def test_tier_comparison_table_positive():
    intel = _intel(counts=DomCounts(tables=2))
    assert RULES["tier_comparison_table"](intel) is True


def test_tier_comparison_table_no_tables():
    intel = _intel(counts=DomCounts(tables=0))
    assert RULES["tier_comparison_table"](intel) is False


def test_package_tier_list_via_h2_count():
    intel = _intel(
        headings=[
            _heading(text="Tunnel Club Premier"),
            _heading(text="The 1894 Suite"),
            _heading(text="Mancunian Suite"),
            _heading(text="Members Club"),
        ]
    )
    assert RULES["package_tier_list"](intel) is True


def test_package_tier_list_via_price_buttons():
    intel = _intel(
        buttons=[_button(text="From £350"), _button(text="From £499"), _button(text="From £799")]
    )
    assert RULES["package_tier_list"](intel) is True


# ---------------------------------------------------------------------------
# Food & beverage rules
# ---------------------------------------------------------------------------


def test_menu_preview_positive():
    intel = _intel(headings=[_heading(text="Five-course tasting menu")])
    assert RULES["menu_preview"](intel) is True


def test_menu_preview_negative():
    intel = _intel(headings=[_heading(text="Welcome to hospitality")])
    assert RULES["menu_preview"](intel) is False


def test_vegetarian_options_positive():
    intel = _intel(buttons=[_button(text="Vegan starter available")])
    assert RULES["vegetarian_options"](intel) is True


def test_allergen_info_via_meta():
    intel = _intel(meta={"description": "Includes allergen information"})
    assert RULES["allergen_info"](intel) is True


def test_chef_attribution_positive():
    intel = _intel(headings=[_heading(text="Created by Michelin-starred chef")])
    assert RULES["chef_attribution"](intel) is True


# ---------------------------------------------------------------------------
# Premium amenities rules
# ---------------------------------------------------------------------------


def test_parking_included_indicator_positive():
    intel = _intel(headings=[_heading(text="Includes parking")])
    assert RULES["parking_included_indicator"](intel) is True


def test_pitchside_or_tunnel_access_positive():
    intel = _intel(buttons=[_button(text="Tunnel Club walk")])
    assert RULES["pitchside_or_tunnel_access"](intel) is True


def test_concierge_service_via_button():
    intel = _intel(buttons=[_button(text="Speak to your concierge")])
    assert RULES["concierge_service"](intel) is True


def test_stadium_tour_inclusion_positive():
    intel = _intel(headings=[_heading(text="Includes stadium tour")])
    assert RULES["stadium_tour_inclusion"](intel) is True


# ---------------------------------------------------------------------------
# Enquiry friction rules
# ---------------------------------------------------------------------------


def test_enquiry_form_field_count_le_7_positive():
    intel = _intel(
        forms=[_form(inputs=[_input("text", "name"), _input("email", "email"), _input("tel", "phone")])],
        counts=DomCounts(forms=1, inputs=3),
    )
    assert RULES["enquiry_form_field_count_le_7"](intel) is True


def test_enquiry_form_field_count_le_7_negative_too_many():
    inputs = [_input("text", f"f{i}") for i in range(12)]
    intel = _intel(
        forms=[_form(inputs=inputs)],
        counts=DomCounts(forms=1, inputs=12),
    )
    assert RULES["enquiry_form_field_count_le_7"](intel) is False


def test_enquiry_form_field_count_le_7_negative_no_form():
    intel = _intel(forms=[], counts=DomCounts(forms=0))
    assert RULES["enquiry_form_field_count_le_7"](intel) is False


def test_buy_now_without_enquiry_positive():
    intel = _intel(buttons=[_button(text="Book Now")])
    assert RULES["buy_now_without_enquiry"](intel) is True


def test_buy_now_without_enquiry_negative_only_enquiry():
    intel = _intel(buttons=[_button(text="Make an enquiry")])
    assert RULES["buy_now_without_enquiry"](intel) is False


# Plan 02-18 regression tests for buy_now_without_enquiry.

def test_buy_now_without_enquiry_buy_hospitality_phrasing():
    """RMA's 'Buy Hospitality tickets' button — v1 saw this as present; v2's
    'buy now / buy ticket / book now / purchase' keyword list missed it
    because RMA writes 'Buy Hospitality' (no 'now' / no 'ticket' singular).
    """
    intel = _intel(buttons=[_button(text="Buy Hospitality tickets")])
    assert RULES["buy_now_without_enquiry"](intel) is True


def test_buy_now_without_enquiry_spanish_comprar():
    """Atletico Madrid / RMA Spanish equivalent."""
    intel = _intel(buttons=[_button(text="Comprar entrada VIP")])
    assert RULES["buy_now_without_enquiry"](intel) is True


def test_buy_now_without_enquiry_french_acheter():
    """PSG French equivalent."""
    intel = _intel(buttons=[_button(text="Acheter maintenant")])
    assert RULES["buy_now_without_enquiry"](intel) is True


def test_phone_booking_option_via_tel_link():
    intel = _intel(buttons=[_button(text="Call us", href="tel:+441614449400")])
    assert RULES["phone_booking_option"](intel) is True


def test_phone_booking_option_via_text():
    intel = _intel(headings=[_heading(text="Call: +44 161 444 9400")])
    assert RULES["phone_booking_option"](intel) is True


# ---------------------------------------------------------------------------
# Match selector rules
# ---------------------------------------------------------------------------


def test_competition_filter_positive():
    intel = _intel(buttons=[_button(text="Premier League")])
    assert RULES["competition_filter"](intel) is True


def test_fixture_list_visible_positive():
    intel = _intel(
        headings=[
            _heading(text="3 Sep vs Liverpool"),
            _heading(text="17 Sep vs Arsenal"),
            _heading(text="1 Oct vs Chelsea"),
        ]
    )
    assert RULES["fixture_list_visible"](intel) is True


def test_fixture_list_visible_negative():
    intel = _intel(headings=[_heading(text="Welcome")])
    assert RULES["fixture_list_visible"](intel) is False


# ---------------------------------------------------------------------------
# Post-booking comms rules
# ---------------------------------------------------------------------------


def test_booking_change_policy_visible_positive():
    intel = _intel(meta={"description": "See cancellation policy in T&Cs"})
    assert RULES["booking_change_policy_visible"](intel) is True


def test_cancellation_refund_window_positive():
    intel = _intel(headings=[_heading(text="Refund within 14 days of booking")])
    assert RULES["cancellation_refund_window"](intel) is True


# ---------------------------------------------------------------------------
# detect_feature wrapper
# ---------------------------------------------------------------------------


def test_detect_feature_returns_none_for_unregistered_feature():
    intel = _intel()
    feature = FeatureDef(key="some_brand_new_key", name="X", yes_criterion="x")
    assert detect_feature(intel, feature) is None


def test_detect_feature_positive_returns_high_confidence_verdict():
    intel = _intel(headings=[_heading(text="£499 per person")])
    feature = FeatureDef(
        key="price_per_person_visible",
        name="Price Per Person Visible",
        yes_criterion="A per-person price is shown",
    )
    verdict = detect_feature(intel, feature)
    assert verdict is not None
    assert verdict.present is True
    assert verdict.confidence == DOM_CONFIDENCE
    assert verdict.step == "dom-detect"
    assert "price_per_person_visible" in verdict.notes


def test_detect_feature_negative_returns_present_false():
    intel = _intel(headings=[_heading(text="Welcome to hospitality")])
    feature = FeatureDef(
        key="price_per_person_visible",
        name="Price Per Person Visible",
        yes_criterion="A per-person price is shown",
    )
    verdict = detect_feature(intel, feature)
    assert verdict is not None
    assert verdict.present is False


def test_detect_features_skips_features_without_rules():
    intel = _intel(headings=[_heading(text="Includes parking")])
    rubric = [
        FeatureDef(key="parking_included_indicator", name="P", yes_criterion="x"),
        FeatureDef(key="visual_only_feature", name="V", yes_criterion="y"),
    ]
    out = detect_features(intel, rubric)
    assert "parking_included_indicator" in out
    assert "visual_only_feature" not in out
    assert out["parking_included_indicator"].present is True


def test_detect_features_empty_rubric_returns_empty_dict():
    assert detect_features(_intel(), []) == {}


def test_detect_features_handles_empty_intel():
    """All rules must return False (not raise) on a fully-empty intel."""
    rubric = [FeatureDef(key=k, name=k, yes_criterion="x") for k in RULES]
    out = detect_features(_intel(), rubric)
    assert len(out) == len(RULES)
    assert all(v.present is False for v in out.values())
