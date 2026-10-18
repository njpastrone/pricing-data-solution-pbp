"""Tests for save_current_order: the one helper behind every Tab 3 save button.

Uses a fake save_order, so nothing touches Google Sheets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io

import src.order_manager as order_manager
from src.helpers import add_product_photos
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
    photo.size = 9
    photo.read()  # leave the cursor at the end, like after a preview
    state = _state(product_photos={'Mug': [photo], 'Pen': []})

    save_current_order(state, "ABC", "")

    assert calls[0]['photos_by_product'] == {'Mug': [{'bytes': b"png-bytes", 'filename': "mug.png"}]}


# --- Photos survive re-saving a loaded order (fake sheet + fake photo store) ---

class FakeSheet:
    def __init__(self):
        self.rows = [["Order_ID", "Name", "Created_By", "Created_Date", "Dataset", "Order_Data"]]

    def get_all_values(self):
        return [list(row) for row in self.rows]

    def append_row(self, row):
        self.rows.append(list(row))

    def update(self, cell_range, values):
        row_number = int(cell_range.split(":")[0][1:])
        self.rows[row_number - 1] = list(values[0])

    def delete_rows(self, row_number):
        del self.rows[row_number - 1]


def _fake_storage(monkeypatch):
    import src.drive_helper as drive_helper
    sheet = FakeSheet()
    uploads = []

    def fake_upload_photo(file_bytes, filename, order_id=""):
        uploads.append(file_bytes)
        return f"photo-{len(uploads)}"

    monkeypatch.setattr(order_manager, 'initialize_orders_sheet', lambda: sheet)
    monkeypatch.setattr(drive_helper, 'upload_photo', fake_upload_photo)
    return uploads


def _upload(name, data):
    photo = io.BytesIO(data)
    photo.name = name
    photo.size = len(data)
    return photo


def _load_into(state):
    """Do what Tab 3's Load button does with a saved order's photos."""
    order_id = order_manager.load_all_orders()[0]['order_id']
    _, order_data, _ = order_manager.load_order_data(order_id)
    state['product_photos'] = {}
    state['product_photo_metadata'] = order_data.get('product_photos', {})
    return order_data


def _saved_filenames(order_data, product):
    return [p['filename'] for p in order_data['product_photos'][product]]


def test_resave_loaded_order_without_uploads_keeps_photos(monkeypatch):
    uploads = _fake_storage(monkeypatch)
    state = _state(order_items=[], product_photos={'Mug': [_upload("mug.png", b"mug")]})
    save_current_order(state, "ABC", "")

    state = _state(order_items=[])
    _load_into(state)
    save_current_order(state, "ABC", "", overwrite=True, finalize=True)

    assert _saved_filenames(_load_into(_state()), 'Mug') == ["mug.png"]
    assert len(uploads) == 1  # the saved photo is not uploaded again


def test_resave_loaded_order_with_new_upload_keeps_old_and_new(monkeypatch):
    uploads = _fake_storage(monkeypatch)
    state = _state(order_items=[], product_photos={'Mug': [_upload("mug.png", b"mug")]})
    save_current_order(state, "ABC", "")

    state = _state(order_items=[])
    _load_into(state)
    state['product_photos'] = {'Mug': [_upload("logo.png", b"logo")]}
    save_current_order(state, "ABC", "", overwrite=True)

    assert _saved_filenames(_load_into(_state()), 'Mug') == ["mug.png", "logo.png"]
    assert len(uploads) == 2


def test_saving_twice_in_one_session_does_not_duplicate_photos(monkeypatch):
    uploads = _fake_storage(monkeypatch)
    photo = _upload("mug.png", b"mug")
    state = _state(order_items=[], product_photos={'Mug': [photo]})
    save_current_order(state, "ABC", "")
    # The uploader re-sends the same file on the next rerun
    state['product_photos']['Mug'] = add_product_photos(
        state['product_photos'].get('Mug', []), [photo], saved=state['product_photo_metadata']['Mug'])[0]
    save_current_order(state, "ABC", "", overwrite=True)

    assert _saved_filenames(_load_into(_state()), 'Mug') == ["mug.png"]
    assert len(uploads) == 1


def test_cap_counts_saved_photos(monkeypatch):
    _fake_storage(monkeypatch)
    first = [_upload(f"{i}.png", b"x" * (i + 1)) for i in range(4)]
    state = _state(order_items=[], product_photos={'Mug': first})
    save_current_order(state, "ABC", "")

    state = _state(order_items=[])
    _load_into(state)
    # Only one slot is left, so only one of these two is attached
    merged, skipped = add_product_photos([], [_upload("a.png", b"a"), _upload("b.png", b"b")],
                                         saved=state['product_photo_metadata']['Mug'])
    assert [p.name for p in merged] == ["a.png"] and skipped == 1
    # Even if more slip into the session, the save stops at five
    state['product_photos'] = {'Mug': [_upload("a.png", b"a"), _upload("b.png", b"b")]}
    save_current_order(state, "ABC", "", overwrite=True)

    assert len(_load_into(_state())['product_photos']['Mug']) == 5


def test_deleting_one_version_keeps_photos_the_other_still_uses(monkeypatch):
    import src.drive_helper as drive_helper
    _fake_storage(monkeypatch)
    deleted = []
    monkeypatch.setattr(drive_helper, 'delete_photos', lambda ids: deleted.extend(ids) or len(ids))
    state = _state(order_items=[], product_photos={'Mug': [_upload("mug.png", b"mug")]})
    save_current_order(state, "ABC", "")

    state = _state(order_items=[])
    _load_into(state)
    state['product_photos'] = {'Mug': [_upload("logo.png", b"logo")]}
    save_current_order(state, "ABC (v2)", "")

    ids = {o['name']: o['order_id'] for o in order_manager.load_all_orders()}
    order_manager.delete_order(ids["ABC"])
    assert deleted == []  # mug.png is still used by "ABC (v2)"

    order_manager.delete_order(ids["ABC (v2)"])
    assert sorted(deleted) == ["photo-1", "photo-2"]
