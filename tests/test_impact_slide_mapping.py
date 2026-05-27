"""Tests for impact slide mapping loader."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_load_impact_slide_mapping_returns_dict():
    """load_impact_slide_mapping returns a dict of partner -> slide title."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    assert isinstance(result, dict)
    # Should have at least one entry (sheet has 7 partners)
    assert len(result) > 0


def test_load_impact_slide_mapping_has_expected_partners():
    """Mapping includes known partners from the sheet."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    # Check a few known partners exist
    assert "GOEX" in result
    assert "Jaggery" in result


def test_load_impact_slide_mapping_values_contain_your_impact():
    """Each slide title should contain 'Your Impact'."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    for partner, slide_title in result.items():
        assert "Your Impact" in slide_title or "your impact" in slide_title.lower(), \
            f"Partner '{partner}' has unexpected slide title: '{slide_title}'"
