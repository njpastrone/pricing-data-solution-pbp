"""Tests for src/client_form.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client_form import generate_session_token, load_proposal_for_client, _serialize_form_data, _deserialize_form_data


def test_generate_session_token_is_unique():
    """Each call produces a unique token."""
    token1 = generate_session_token()
    token2 = generate_session_token()
    assert token1 != token2
    assert len(token1) == 12  # Short, URL-friendly


def test_generate_session_token_is_url_safe():
    """Token contains only URL-safe characters."""
    token = generate_session_token()
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789")
    assert all(c in allowed for c in token)


def test_serialize_form_data_roundtrip():
    """Form data serializes and deserializes cleanly."""
    form_data = {
        'client_info': {
            'client_type': 'New',
            'company_name': 'Acme Corp',
            'contact_name': 'John Smith',
            'contact_email': 'john@acme.com',
            'contact_phone': '555-1234',
        },
        'products': [
            {'name': '9 oz Hot Honey', 'quantity': 100, 'customization_notes': 'Custom label'},
        ],
        'shipping_info': {
            'shipping_address': '123 Main St',
            'billing_address': '',
            'drop_shipping': 'No',
            'drop_shipping_instructions': '',
            'in_hands_date': '2026-07-01',
        },
        'payment_info': {
            'impact_cards': 'Yes',
            'impact_card_selection': 'Story Card',
            'payment_preference': 'Net 30',
            'payment_method': 'ACH',
        },
        'notes': 'Please rush this order',
    }
    serialized = _serialize_form_data(form_data)
    assert isinstance(serialized, str)

    deserialized = _deserialize_form_data(serialized)
    assert deserialized == form_data


def test_deserialize_form_data_handles_empty():
    """Empty/invalid JSON returns empty dict."""
    assert _deserialize_form_data('') == {}
    assert _deserialize_form_data('invalid json') == {}


if __name__ == "__main__":
    test_generate_session_token_is_unique()
    test_generate_session_token_is_url_safe()
    test_serialize_form_data_roundtrip()
    test_deserialize_form_data_handles_empty()
    print("All tests passed!")
