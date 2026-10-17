"""Tests for save_current_order: the one helper behind every Tab 3 save button.

Uses a fake save_order, so nothing touches Google Sheets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io

import src.order_manager as order_manager
from src.order_manager import ORDER_STATE_KEYS, save_current_order


def _state(**overrides):
    state = {key: f"value-{key}" for key in ORDER_STATE_KEYS}
    state['order_confirmed'] = False
    state['selected_dataset'] = 'demo'
    state.update(overrides)
    return state


def _fake_save(monkeypatch, success=True):
    calls = []

    def fake_save_order(**kwargs):
        calls.append(kwargs)
        return (success, "Saved" if success else "Name taken", "ORD-1" if success else None)

    monkeypatch.setattr(order_manager, 'save_order', fake_save_order)
    return calls


def test_finalize_saves_and_marks_order_finalized(monkeypatch):
    calls = _fake_save(monkeypatch)
    state = _state()

    success, _, order_id = save_current_order(state, " ABC Order ", " Sam ", overwrite=True, finalize=True)

    assert success and order_id == "ORD-1"
    saved = calls[0]
    assert saved['name'] == "ABC Order" and saved['created_by'] == "Sam"
    assert saved['overwrite'] is True and saved['dataset'] == 'demo'
    assert saved['order_data']['order_confirmed'] is True
    # Every order setting is carried into the saved copy
    for key in ORDER_STATE_KEYS:
        if key != 'order_confirmed':
            assert saved['order_data'][key] == state[key]
    assert state['order_confirmed'] is True


def test_plain_save_keeps_current_finalized_flag(monkeypatch):
    calls = _fake_save(monkeypatch)
    state = _state()

    save_current_order(state, "ABC", "")

    assert calls[0]['order_data']['order_confirmed'] is False
    assert state['order_confirmed'] is False


def test_failed_save_does_not_mark_finalized(monkeypatch):
    _fake_save(monkeypatch, success=False)
    state = _state()

    success, message, _ = save_current_order(state, "ABC", "", finalize=True)

    assert not success and message == "Name taken"
    assert state['order_confirmed'] is False


def test_missing_name_is_rejected_without_saving(monkeypatch):
    calls = _fake_save(monkeypatch)
    state = _state()

    success, message, _ = save_current_order(state, "   ", "", finalize=True)

    assert not success and message == "Please enter an order name"
    assert calls == [] and state['order_confirmed'] is False


def test_product_photos_are_read_for_upload(monkeypatch):
    calls = _fake_save(monkeypatch)
    photo = io.BytesIO(b"png-bytes")
    photo.name = "mug.png"
    photo.read()  # leave the cursor at the end, like after a preview
    state = _state(product_photos={'Mug': [photo], 'Pen': []})

    save_current_order(state, "ABC", "")

    assert calls[0]['photos_by_product'] == {'Mug': [{'bytes': b"png-bytes", 'filename': "mug.png"}]}
