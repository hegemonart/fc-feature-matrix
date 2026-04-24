"""Dummy form-fill helper (Plan 03, Task 2 → D-16 invariant).

**D-16: Never dispatch forms against club sites.** This module fills input
fields with innocuous dummy values so the scanner can capture pre-dispatch
state (visual check of the populated form) and then close the page. It does
NOT click a dispatch button anywhere.

The grep-test in `tests/test_browser.py::test_no_dispatch_clicks_in_capture_module`
scans the entire `scanner/capture/` tree for dispatch-click patterns and
fails if any appear — so this invariant is enforced mechanically.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Page

    from scanner.flow.schema import FormField


DUMMY_VALUES: dict[str, str] = {
    "name":    "Test Test",
    "email":   "test@example.com",
    "phone":   "+44 0000 000000",
    "postal":  "SW1A 1AA",
    "default": "Test",
}


def fill_form(page: "Page", form_fields: list["FormField"]) -> None:
    """Fill each form field with its `value` or the default dummy string.

    Never clicks a dispatch button — the caller is responsible for taking
    the screenshot and then closing the page. See `scanner/capture/capture.py`
    for the canonical teardown pattern.
    """
    for field in form_fields:
        value = field.value if field.value else DUMMY_VALUES["default"]
        page.fill(field.selector, value)


__all__ = ["DUMMY_VALUES", "fill_form"]
