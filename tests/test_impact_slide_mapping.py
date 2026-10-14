"""Tests for impact slide mapping loader."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from unittest.mock import MagicMock, patch

import pytest

# Fixture rows standing in for the live "impact_slide_mapping" sheet
# (header row + one row per partner + a blank row that must be skipped).
IMPACT_SHEET_ROWS = [
    ["Partner", "Slide Title"],
    ["GOEX", "Apparel \u2013 Your Impact"],
    ["Jaggery", "Bags \u2013 Your Impact"],
    ["", ""],
]


@pytest.fixture
def mapping():
    """load_impact_slide_mapping() run against the fixture rows instead of Google Sheets."""
    from src.data_loader import load_impact_slide_mapping

    fake_client = MagicMock()
    fake_client.open_by_key.return_value.worksheet.return_value.get_all_values.return_value = IMPACT_SHEET_ROWS
    load_impact_slide_mapping.clear()  # drop any cached live result
    with patch("src.data_loader.connect_to_sheets", return_value=fake_client):
        result = load_impact_slide_mapping()
    load_impact_slide_mapping.clear()
    return result


def test_load_impact_slide_mapping_returns_dict(mapping):
    """load_impact_slide_mapping returns a dict of partner -> slide title, skipping blank rows."""
    assert isinstance(mapping, dict)
    assert len(mapping) == 2


def test_load_impact_slide_mapping_has_expected_partners(mapping):
    """Mapping includes the partners from the sheet rows."""
    assert "GOEX" in mapping
    assert "Jaggery" in mapping


def test_load_impact_slide_mapping_values_contain_your_impact(mapping):
    """Each slide title should contain 'Your Impact'."""
    for partner, slide_title in mapping.items():
        assert "your impact" in slide_title.lower(), \
            f"Partner '{partner}' has unexpected slide title: '{slide_title}'"


def test_resolve_impact_slides_with_matching_titles():
    """resolve_impact_slides matches sheet titles against template slides."""
    from pbp.core.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
        {"slide_index": 100, "slide_title": "Honey Products \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" in result
    assert result["GOEX"]["slide_index"] == 50
    assert result["GOEX"]["slide_title"] == "Apparel \u2013 Your Impact"


def test_resolve_impact_slides_fuzzy_dash_match():
    """resolve_impact_slides handles dash vs em-dash differences."""
    from pbp.core.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel - Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" in result
    assert result["GOEX"]["slide_index"] == 50


def test_resolve_impact_slides_non_breaking_space():
    """resolve_impact_slides handles non-breaking spaces in template titles."""
    from pbp.core.slide_matcher import resolve_impact_slides

    # Sheet has regular spaces, template has non-breaking spaces (\xa0)
    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 68, "slide_title": "Apparel\xa0\u2013\xa0Your Impact"},
        {"slide_index": 219, "slide_title": "Ceramic Goods \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" in result
    assert result["GOEX"]["slide_index"] == 68
    assert "Apparel" in result["GOEX"]["slide_title"]


def test_resolve_impact_slides_partner_not_in_sheet():
    """Partners not in the sheet mapping are skipped."""
    from pbp.core.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["Unknown Partner"], sheet_mapping, template_slides)
    assert "Unknown Partner" not in result


def test_resolve_impact_slides_title_not_in_template():
    """If sheet title doesn't match any template slide, partner is skipped."""
    from pbp.core.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Deleted Slide -- Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" not in result
