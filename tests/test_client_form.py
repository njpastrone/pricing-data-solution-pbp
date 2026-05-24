"""Tests for src/client_form.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client_form import generate_session_token, load_proposal_for_client


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


if __name__ == "__main__":
    test_generate_session_token_is_unique()
    test_generate_session_token_is_url_safe()
    print("All tests passed!")
