"""Tests for src/client_form.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import base64
from unittest.mock import MagicMock, patch

import gspread

from src.client_form import (generate_session_token, load_proposal_for_client, _serialize_form_data, _deserialize_form_data,
                             submit_form, save_draft, sync_submission, retry_pending_syncs, DRAFTS_SHEET_NAME, BACKUP_RETRY_WAITS,
                             STATUS_PENDING, STATUS_SUBMITTED, _open_worksheet, _open_drafts_sheet)
from pbp.core.forms_config import GOOGLE_FORM_CONFIG, find_response_column
from pbp.core.forms_helper import parse_form_response, mark_response_imported, form_response_to_order


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


# ------------------------------------------------------------
# Submit / import against the LIVE response sheet headers.
# Copied from "Form Responses 1" on 2026-10-09. All sheets are mocked:
# these tests never touch a real Google Sheet.
# ------------------------------------------------------------
LIVE_HEADERS = [
    'Timestamp', 'Email Address', 'Client Type *', 'Company Name *', 'Contact Name *',
    'Contact Email *', 'Contact Phone',
    'Gift Item 1 - Product Name', 'Gift 1 Quantity', 'Gift 1 Customization Notes',
    'Gift Item 2 - Product Name', 'Gift 2 Quantity', 'Gift 2 Customization Notes',
    'Gift Item 3 - Product Name', 'Gift 3 Quantity', 'Gift 3 Customization Notes',
    'Gift Item 4 - Product Name', 'Gift 4 Quantity', 'Gift 4 Customization Notes',
    'Gift Item 5 - Product Name', 'Gift 5 Quantity', 'Gift Item 5 - Customization Notes',
    'Gift Item 6 - Product Name', 'Gift 6 Quantity', 'Gift 6 - Customization Notes',
    'Gift Item 7 - Product Name', 'Gift 7 Quantity', 'Gift 7 - Customization Notes',
    'Gift Item 8 - Product Name', 'Gift 8 Quantity', 'Gift 8 - Customization Notes',
    'Gift Item 9 - Product Name', 'Gift 9 Quantity', 'Gift 9 - Customization Notes',
    'Gift Item 10 - Product Name', 'Gift 10 Quantity', 'Gift 10 - Customization Notes',
    'Shipping Address *', 'Billing Address (if different from shipping)',
    'Will this order be drop-shipped to individual recipients? *', 'Drop-Shipping Instructions',
    'In-Hands Date (When do you need this order?) *', 'Impact Cards Add-Ons', 'Impact Card Selection',
    'Payment Preference *', 'Payment Method *', 'Special Requests, Notes, or Questions',
    'Is there a specific platform or email address we need to send the invoice to (i.e. BillPay.com)?',
    'Column 47', 'Imported?', 'Order ID', 'Imported By', 'Import Date',
]

SAMPLE_FORM = {
    'client_info': {'client_type': 'New', 'company_name': 'Acme Corp', 'contact_name': 'Jo Smith',
                    'contact_email': 'jo@acme.com', 'contact_phone': '555-1234'},
    'products': [
        {'name': 'Unisex Fleece Hoodie', 'quantity': 25, 'customization_notes': 'Navy, white logo'},
        {'name': '9 oz Hot Honey', 'quantity': 100, 'customization_notes': ''},
    ],
    'shipping_info': {'shipping_address': '123 Main St', 'billing_address': '', 'drop_shipping': 'No',
                      'drop_shipping_instructions': '', 'in_hands_date': '2026-11-01'},
    'payment_info': {'impact_cards': 'Yes', 'impact_card_selection': '', 'payment_preference': 'Net 30',
                     'payment_method': 'ACH'},
    'notes': 'Rush please',
}


class FakeSheet:
    """A tiny in-memory worksheet. Put exceptions in fail['method'] to make the next calls fail."""

    def __init__(self, rows, row_count=1000):
        self.rows = [list(r) for r in rows]
        self.row_count = row_count  # grid size as cached on the handle, like gspread
        self.grid_rows = row_count  # real grid size on Google's side
        self.fail = {}

    def _maybe_fail(self, method):
        if self.fail.get(method):
            raise self.fail[method].pop(0)

    def get_all_values(self):
        self._maybe_fail('get_all_values')
        return [list(r) for r in self.rows]

    def batch_get(self, ranges):  # whole-column ranges like 'A:C'
        self._maybe_fail('batch_get')
        result = []
        for cell_range in ranges:
            first, last = (ord(c) - ord('A') for c in cell_range.split(':'))
            result.append([r[first:last + 1] for r in self.rows])
        return result

    def row_values(self, number):
        return list(self.rows[number - 1])

    def append_row(self, row):
        self._maybe_fail('append_row')
        if any(len(str(v)) > 50000 for v in row):
            raise Exception("cell over 50000 characters")
        self.rows.append(list(row))

    def update_cell(self, row_number, col_number, value):
        self._maybe_fail('update_cell')
        while len(self.rows) < row_number:
            self.rows.append([])
        row = self.rows[row_number - 1]
        row.extend([''] * (col_number - len(row)))
        row[col_number - 1] = value

    def resize(self, rows):
        self.row_count = self.grid_rows = rows

    def update(self, range_name, values):  # e.g. 'C2' or 'G2:H2'
        self._maybe_fail('update')
        first = range_name.split(':')[0]
        col_number = ord(first[0]) - ord('A') + 1
        if int(first[1:]) > self.grid_rows:
            raise Exception("exceeds grid limits")
        for offset, value in enumerate(values[0]):
            if len(str(value)) > 50000:
                raise Exception("cell over 50000 characters")
            self.update_cell(int(first[1:]), col_number + offset, value)


DRAFT_HEADERS = ['Proposal_ID', 'Session_ID', 'Draft_Data_JSON', 'File_Data_Base64',
                 'File_Name', 'Created_Date', 'Updated_Date', 'Status']


def _mock_sheets(response_headers, drafts_exists=True, draft_rows=(), response=None):
    """Build a fake gspread client with a response sheet and a drafts (backup) sheet."""
    # Forget worksheets cached by an earlier test
    _open_worksheet.clear()
    _open_drafts_sheet.clear()

    response = response or FakeSheet([response_headers])
    drafts = FakeSheet([DRAFT_HEADERS] + [list(r) for r in draft_rows])

    response_book = MagicMock()
    response_book.worksheet.return_value = response

    drafts_book = MagicMock()
    if drafts_exists:
        drafts_book.worksheet.return_value = drafts
    else:
        drafts_book.worksheet.side_effect = gspread.exceptions.WorksheetNotFound(DRAFTS_SHEET_NAME)
        drafts_book.add_worksheet.return_value = drafts

    client = MagicMock()
    client.open_by_key.side_effect = lambda key: (
        response_book if key == GOOGLE_FORM_CONFIG['response_sheet_id'] else drafts_book
    )
    return client, response, drafts, drafts_book


def _submit(client, *args):
    """Submit with the background sync run right away (one attempt), and no real sleeping."""
    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form.time.sleep'), \
         patch('src.client_form._sync_in_background', side_effect=sync_submission):
        return submit_form(*args)


def _backup(drafts):
    """Return (form JSON without its submit stamp, status) of the single backup row."""
    assert len(drafts.rows) == 2, drafts.rows
    form = json.loads(drafts.rows[1][2])
    assert form.pop('submitted_at')
    return form, drafts.rows[1][7]


def _response_rows(response):
    return [dict(zip(LIVE_HEADERS, r)) for r in response.rows[1:]]


def test_find_response_column_matches_live_headers():
    """Every product line and renamed field resolves to the live sheet header."""
    for i in range(1, 11):
        assert find_response_column(LIVE_HEADERS, f'line_{i}_name') == f'Gift Item {i} - Product Name'
        assert find_response_column(LIVE_HEADERS, f'line_{i}_qty') == f'Gift {i} Quantity'
        assert 'Customization Notes' in find_response_column(LIVE_HEADERS, f'line_{i}_notes')
    # Line 1 must not grab line 10's columns (and vice versa)
    assert find_response_column(LIVE_HEADERS, 'line_1_notes') == 'Gift 1 Customization Notes'
    assert find_response_column(LIVE_HEADERS, 'drop_shipping') == 'Will this order be drop-shipped to individual recipients? *'
    assert find_response_column(LIVE_HEADERS, 'impact_cards') == 'Impact Cards Add-Ons'
    assert find_response_column(LIVE_HEADERS, 'company_name') == 'Company Name *'
    # Original names and small wording/asterisk differences still work
    assert find_response_column(['Product Line 3 - Quantity'], 'line_3_qty') == 'Product Line 3 - Quantity'
    assert find_response_column(['company name'], 'company_name') == 'company name'
    assert find_response_column(['Shipping Address'], 'shipping_address') == 'Shipping Address'
    assert find_response_column(['Something Else'], 'line_1_name') is None


def test_submit_form_writes_items_to_live_headers():
    """Items land in the 'Gift ...' columns; a full backup is saved first and marked submitted."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success and msg == "Order received"
    rows = _response_rows(response)
    assert len(rows) == 1
    cell = rows[0]
    assert cell['Gift Item 1 - Product Name'] == 'Unisex Fleece Hoodie'
    assert cell['Gift 1 Quantity'] == '25'
    assert cell['Gift 1 Customization Notes'] == 'Navy, white logo'
    assert cell['Gift Item 2 - Product Name'] == '9 oz Hot Honey'
    assert cell['Gift 2 Quantity'] == '100'
    assert cell['Will this order be drop-shipped to individual recipients? *'] == 'No'
    assert cell['Impact Cards Add-Ons'] == 'Yes'
    assert cell['Company Name *'] == 'Acme Corp'
    assert cell['Timestamp'] == json.loads(drafts.rows[1][2])['submitted_at']

    assert _backup(drafts) == (SAMPLE_FORM, STATUS_SUBMITTED)


def test_submit_form_sheets_down_client_still_sees_order_received():
    """Form Responses unreachable at submit: client sees 'Order received', order waits in the backup tab."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['get_all_values'] = [Exception("503 Service Unavailable")]
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success and msg == "Order received"
    assert _response_rows(response) == []
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_PENDING)


def test_pending_order_syncs_on_next_app_run():
    """A pending order is copied into Form Responses by the next-run retry, exactly once."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['update'] = [Exception("503 Service Unavailable")]
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)
    assert _backup(drafts)[1] == STATUS_PENDING

    with patch('src.client_form.connect_to_sheets', return_value=client):
        stuck = retry_pending_syncs()
        retry_pending_syncs()  # a second run finds nothing left to do

    assert stuck == []
    assert len(_response_rows(response)) == 1
    assert _response_rows(response)[0]['Gift Item 1 - Product Name'] == 'Unisex Fleece Hoodie'
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_SUBMITTED)


def test_background_sync_retries_until_it_succeeds():
    """The background sync keeps retrying; once Sheets is back, exactly one row lands."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['update'] = [Exception("503"), Exception("503")]

    class RunNow:
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form.time.sleep'), \
         patch('src.client_form.threading.Thread', RunNow):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert success
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED


def test_repeated_sync_does_not_duplicate_rows():
    """If the row was written but the backup could not be marked, a retry does not write it twice."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    drafts.fail['update_cell'] = [Exception("503 Service Unavailable")]
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_PENDING  # marking failed

    with patch('src.client_form.connect_to_sheets', return_value=client):
        assert sync_submission('PROP_1', 'sess1')[0]
        assert sync_submission('PROP_1', 'sess1')[0]
        retry_pending_syncs()

    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED


def test_stuck_order_is_reported_to_staff():
    """An order that still cannot sync after a while is returned for the staff warning."""
    old_form = dict(SAMPLE_FORM, submitted_at='01/01/2026 09:00:00')
    pending = ['PROP_1', 'sess1', json.dumps(old_form), '', '', '', '', STATUS_PENDING]
    headers_without_items = [h for h in LIVE_HEADERS if 'Gift' not in h]
    client, response, _, _ = _mock_sheets(headers_without_items, draft_rows=[pending])
    with patch('src.client_form.connect_to_sheets', return_value=client):
        stuck = retry_pending_syncs()

    assert len(stuck) == 1
    assert stuck[0]['proposal_id'] == 'PROP_1'
    assert stuck[0]['company_name'] == 'Acme Corp'
    assert stuck[0]['submitted_at'] == '01/01/2026 09:00:00'
    assert 'Product Line 1 - Product Name' in stuck[0]['reason']  # staff can see why
    assert len(response.rows) == 1  # nothing written


def test_save_progress_does_not_undo_a_received_order():
    """'Save Progress' from an old browser tab must not turn a pending order back into a draft."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['get_all_values'] = [Exception("503 Service Unavailable")]
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)
    assert _backup(drafts)[1] == STATUS_PENDING

    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, _ = save_draft('PROP_1', 'sess1', dict(SAMPLE_FORM, notes='old tab'))
        assert success
        assert _backup(drafts) == (SAMPLE_FORM, STATUS_PENDING)
        retry_pending_syncs()

    assert len(_response_rows(response)) == 1
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_SUBMITTED)


def test_submit_form_header_mismatch_keeps_order_pending():
    """If item columns are missing, nothing is written; the order is kept and stays pending."""
    headers_without_items = [h for h in LIVE_HEADERS if 'Gift' not in h]
    client, response, drafts, _ = _mock_sheets(headers_without_items)
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success
    assert len(response.rows) == 1
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_PENDING)


def test_submit_form_fails_if_backup_never_saves():
    """No backup, no 'Order received': the client is asked to retry, without technical detail."""
    client, response, _, _ = _mock_sheets(LIVE_HEADERS)
    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form._get_drafts_sheet', return_value=None), \
         patch('src.client_form.time.sleep') as fake_sleep:
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert not success
    assert 'drafts sheet' not in msg
    assert fake_sleep.call_count == len(BACKUP_RETRY_WAITS)
    assert len(response.rows) == 1


def test_submit_form_backup_retries_after_sheets_error():
    """A failing backup save is retried; the order then goes through."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    drafts.fail['append_row'] = [Exception("503"), Exception("503")]
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_SUBMITTED)
    assert len(_response_rows(response)) == 1


def test_submit_form_retries_backup_without_file():
    """A file too big for a sheet cell must not block the order."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM, b'x' * 60000, 'addresses.xlsx')

    assert success, msg
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[0] == SAMPLE_FORM
    assert drafts.rows[1][3] == ''
    assert drafts.rows[1][4] == 'addresses.xlsx'


def test_submit_form_too_big_file_keeps_stored_draft_file():
    """Leaving out a too-big file must not wipe a file already saved in the draft."""
    stored = ['PROP_1', 'sess1', '{}', 'c3RvcmVk', 'addresses.xlsx', 'created', 'updated', 'draft']
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS, draft_rows=[stored])
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM, b'x' * 60000, 'addresses.xlsx')

    assert success, msg
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[0] == SAMPLE_FORM
    assert drafts.rows[1][3] == 'c3RvcmVk'  # stored file kept


def test_transient_error_keeps_dropship_file():
    """One Sheets error while saving must not silently drop the drop-ship file (it is retried with it)."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    drafts.fail['append_row'] = [Exception("503 Service Unavailable")]
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM, b'name,address', 'addr.csv')

    assert success and msg == "Order received"
    assert base64.b64decode(drafts.rows[1][3]) == b'name,address'
    assert drafts.rows[1][4] == 'addr.csv'


def test_resubmit_after_synced_does_not_duplicate():
    """Submitting again (e.g. from an old browser tab) after the order synced adds no second row."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)
    first_backup = list(drafts.rows[1])
    success, msg = _submit(client, 'PROP_1', 'sess1', dict(SAMPLE_FORM, notes='Changed my mind'))

    assert success and msg == "Order received"
    assert len(_response_rows(response)) == 1
    assert drafts.rows[1] == first_backup  # received order left untouched


def test_submit_form_creates_drafts_tab_if_missing():
    """The backup tab is created when it doesn't exist yet."""
    client, response, drafts, drafts_book = _mock_sheets(LIVE_HEADERS, drafts_exists=False)
    drafts.rows = []  # brand-new tab: add_worksheet + header write fill it
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success, msg
    drafts_book.add_worksheet.assert_any_call(title=DRAFTS_SHEET_NAME, rows=100, cols=8)
    assert drafts.rows[0] == DRAFT_HEADERS
    assert _backup(drafts) == (SAMPLE_FORM, STATUS_SUBMITTED)


def _quota_error():
    """A gspread APIError like the real 'Quota exceeded ... Read requests per minute' (HTTP 429)."""
    response = MagicMock()
    response.json.return_value = {'error': {'code': 429, 'message': 'Quota exceeded', 'status': 'RESOURCE_EXHAUSTED'}}
    return gspread.exceptions.APIError(response)


def test_submit_form_retries_after_quota_error():
    """A 429 on the response write waits and retries; exactly one row lands."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['get_all_values'] = [_quota_error()]
    response.fail['update'] = [_quota_error()]  # 429 = rejected, nothing written
    success, msg = _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert success, msg
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED


def test_submit_form_does_not_reopen_sheets_every_time():
    """Spreadsheets are opened once and reused, saving read quota on later submits."""
    client, response, _, _ = _mock_sheets(LIVE_HEADERS)
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)
    _submit(client, 'PROP_2', 'sess2', dict(SAMPLE_FORM, notes='Second order'))

    assert client.open_by_key.call_count == 2  # response sheet + drafts sheet, once each
    assert len(_response_rows(response)) == 2


class TableSheet(FakeSheet):
    """A response sheet with a Google Sheets Table over rows 1-7: append_row always lands on row 8."""

    def append_row(self, row):
        while len(self.rows) < 8:
            self.rows.append([])
        self.rows[7] = list(row)


def test_sync_does_not_overwrite_when_sheet_has_table():
    """Two orders both land in Form Responses; the second must not replace the first."""
    old_rows = [[f'old {n}'] for n in range(2, 8)]
    table = TableSheet([LIVE_HEADERS] + old_rows)
    client, response, _, _ = _mock_sheets(LIVE_HEADERS, response=table)
    first = dict(SAMPLE_FORM, client_info=dict(SAMPLE_FORM['client_info'], company_name='First Co'))
    second = dict(SAMPLE_FORM, client_info=dict(SAMPLE_FORM['client_info'], company_name='Second Co'))
    _submit(client, 'PROP_1', 'sess1', first)
    _submit(client, 'PROP_2', 'sess2', second)

    assert response.rows[1:7] == old_rows
    assert [r['Company Name *'] for r in _response_rows(response)[6:]] == ['First Co', 'Second Co']


def test_sync_adds_rows_when_grid_is_full():
    """A sheet with no empty rows left still takes the order (rows are added first)."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS, response=FakeSheet([LIVE_HEADERS], row_count=1))
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED


def test_sync_works_when_cached_row_count_is_stale():
    """Staff deleted rows while the app ran: the cached row_count is too high but the order still lands."""
    sheet = FakeSheet([LIVE_HEADERS], row_count=1000)
    sheet.grid_rows = 1
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS, response=sheet)
    _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)

    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED


def test_mark_response_imported_targets_tracking_columns():
    """Tracking values go to Imported?..Import Date (AX-BA), not the Gift 4/5 columns."""
    worksheet = MagicMock()
    worksheet.row_values.return_value = LIVE_HEADERS
    gc = MagicMock()
    gc.open_by_key.return_value.worksheet.return_value = worksheet

    assert mark_response_imported(gc, 8, 'ORD-1', 'staff')
    updates = worksheet.batch_update.call_args[0][0]
    assert [u['range'] for u in updates] == ['AX8', 'AY8', 'AZ8', 'BA8']


def test_parse_form_response_reads_live_headers():
    """Tab 3 import ('Load All Form Responses') reads items from the live headers."""
    response_row = {h: '' for h in LIVE_HEADERS}
    response_row.update({
        'Company Name *': 'Acme Corp',
        'Gift Item 1 - Product Name': 'Unisex Fleece Hoodie',
        'Gift 1 Quantity': 25,
        'Gift 1 Customization Notes': 'Navy, white logo',
        'Gift Item 10 - Product Name': 'Tote Bag',
        'Gift 10 Quantity': '50',
        'Will this order be drop-shipped to individual recipients? *': 'Yes',
        'Impact Cards Add-Ons': 'No',
    })
    parsed = parse_form_response(response_row)

    assert parsed['client_info']['company_name'] == 'Acme Corp'
    assert parsed['products'] == [
        {'name': 'Unisex Fleece Hoodie', 'quantity': 25, 'customization_notes': 'Navy, white logo'},
        {'name': 'Tote Bag', 'quantity': 50, 'customization_notes': ''},
    ]
    assert parsed['shipping_info']['drop_shipping'] == 'Yes'
    assert parsed['payment_info']['impact_cards'] == 'No'


def test_response_row_keeps_payment_preference_column_blank():
    """The Form Responses sheet still has the payment preference column; it is left blank."""
    from src.client_form import _build_response_row
    headers = ['Timestamp', 'Payment Preference *', 'Payment Method *']
    form_data = {'payment_info': {'payment_preference': '', 'payment_method': 'ACH'}}
    row, _, _ = _build_response_row(headers, form_data, None)
    assert row[1] == ''
    assert row[2] == 'ACH'


def test_accounting_contact_and_other_shipping_reach_form_responses():
    """The accounting email/platform and a typed "Other" shipping answer land in Form Responses and import back."""
    form = dict(SAMPLE_FORM,
                shipping_info=dict(SAMPLE_FORM['shipping_info'], drop_shipping='Other: Pick up at our warehouse'),
                payment_info=dict(SAMPLE_FORM['payment_info'], accounting_contact_type='Accounting platform',
                                  accounting_contact='BillPay.com'))
    client, response, _, _ = _mock_sheets(LIVE_HEADERS)
    _submit(client, 'PROP_1', 'sess1', form)

    cell = _response_rows(response)[0]
    accounting_header = 'Is there a specific platform or email address we need to send the invoice to (i.e. BillPay.com)?'
    assert cell[accounting_header] == 'Accounting platform: BillPay.com'
    assert cell['Will this order be drop-shipped to individual recipients? *'] == 'Other: Pick up at our warehouse'

    # Tab 3 import: the invoice answer has one home (bookkeeping note); "Other" shipping is kept as a team note
    order = form_response_to_order(parse_form_response(cell))
    assert order['order_notes']['internal_bookkeeping'] == 'Send invoice to: Accounting platform: BillPay.com'
    assert "Shipping (client's answer): Other: Pick up at our warehouse" in order['order_notes']['internal_pbp_team']
    assert order['client_info']['shipping_type'] == 'One Location'



def test_other_shipping_answer_starting_with_yes_or_no_is_kept():
    """An "Other" answer that starts with "No," or "Yes," is still kept as a note and is not drop-ship."""
    for answer in ['Other: No, we will pick up at the warehouse', 'Other: Yes, half to the office and half to homes']:
        response = {'shipping_info': {'drop_shipping': answer}}
        order = form_response_to_order(response)
        assert order['order_notes']['internal_pbp_team'] == f"Shipping (client's answer): {answer}"
        assert order['client_info']['shipping_type'] == 'One Location'


if __name__ == "__main__":
    test_other_shipping_answer_starting_with_yes_or_no_is_kept()
    test_generate_session_token_is_unique()
    test_accounting_contact_and_other_shipping_reach_form_responses()
    test_generate_session_token_is_url_safe()
    test_serialize_form_data_roundtrip()
    test_deserialize_form_data_handles_empty()
    test_find_response_column_matches_live_headers()
    test_submit_form_writes_items_to_live_headers()
    test_submit_form_sheets_down_client_still_sees_order_received()
    test_pending_order_syncs_on_next_app_run()
    test_background_sync_retries_until_it_succeeds()
    test_repeated_sync_does_not_duplicate_rows()
    test_stuck_order_is_reported_to_staff()
    test_save_progress_does_not_undo_a_received_order()
    test_submit_form_header_mismatch_keeps_order_pending()
    test_submit_form_fails_if_backup_never_saves()
    test_submit_form_backup_retries_after_sheets_error()
    test_submit_form_retries_backup_without_file()
    test_submit_form_too_big_file_keeps_stored_draft_file()
    test_transient_error_keeps_dropship_file()
    test_resubmit_after_synced_does_not_duplicate()
    test_submit_form_creates_drafts_tab_if_missing()
    test_submit_form_retries_after_quota_error()
    test_submit_form_does_not_reopen_sheets_every_time()
    test_parse_form_response_reads_live_headers()
    test_response_row_keeps_payment_preference_column_blank()
    print("All tests passed!")


NOTIFY_SETTINGS = {'ORDER_NOTIFY_EMAILS': 'team@example.com, ops@example.com', 'SMTP_HOST': 'smtp.example.com',
                   'SMTP_USER': 'sender@example.com', 'SMTP_PASSWORD': 'secret'}


class FakeSMTP:
    """Stands in for smtplib.SMTP; records every sent email in FakeSMTP.sent."""
    sent = []
    fail = None

    def __init__(self, host, port, timeout):
        if FakeSMTP.fail:
            raise FakeSMTP.fail
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        assert (user, password) == ('sender@example.com', 'secret')

    def send_message(self, message):
        FakeSMTP.sent.append(message)


def _submit_with_email(client, settings=NOTIFY_SETTINGS, fail=None):
    """Submit SAMPLE_FORM with fake email settings and a fake mail server."""
    FakeSMTP.sent, FakeSMTP.fail = [], fail
    with patch.dict(os.environ, settings), patch('src.client_form.smtplib.SMTP', FakeSMTP):
        return _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM)


def test_submitted_order_emails_the_team_once():
    """Once the order is in Form Responses, the team gets one email with company, contact, items and the app link."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    assert _submit_with_email(client) == (True, "Order received")

    assert len(FakeSMTP.sent) == 1
    email = FakeSMTP.sent[0]
    assert email['To'] == 'team@example.com, ops@example.com'
    assert email['From'] == 'sender@example.com'
    assert 'Acme Corp' in email['Subject']
    body = email.get_content()
    assert 'Jo Smith (jo@acme.com)' in body
    assert 'Items: 2' in body
    assert 'PROP_1' in body
    assert 'https://pbp-order-management-system.onrender.com/' in body

    # Later syncs (another submit click, the app's next-run retry) send nothing more
    with patch.dict(os.environ, NOTIFY_SETTINGS), patch('src.client_form.smtplib.SMTP', FakeSMTP), \
         patch('src.client_form.connect_to_sheets', return_value=client):
        sync_submission('PROP_1', 'sess1')
        retry_pending_syncs()
    assert len(FakeSMTP.sent) == 1


def test_pending_order_emails_only_when_it_reaches_form_responses():
    """No email while the order waits in the backup tab; one email when the retry copies it."""
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['update'] = [Exception("503 Service Unavailable")]
    _submit_with_email(client)
    assert FakeSMTP.sent == []

    with patch.dict(os.environ, NOTIFY_SETTINGS), patch('src.client_form.smtplib.SMTP', FakeSMTP), \
         patch('src.client_form.connect_to_sheets', return_value=client):
        retry_pending_syncs()
    assert len(FakeSMTP.sent) == 1


def test_stale_pending_row_sends_no_second_email():
    """Retry read the row as pending, then another sync copied and emailed it first: retry sends nothing more."""
    from src import client_form
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    response.fail['update'] = [Exception("503 Service Unavailable")]
    _submit_with_email(client)
    assert FakeSMTP.sent == []

    with patch.dict(os.environ, NOTIFY_SETTINGS), patch('src.client_form.smtplib.SMTP', FakeSMTP), \
         patch('src.client_form.connect_to_sheets', return_value=client):
        stale_rows = client_form._read_backup_rows(drafts)
        sync_submission('PROP_1', 'sess1')
        assert len(FakeSMTP.sent) == 1
        with patch('src.client_form._read_backup_rows', return_value=stale_rows):
            retry_pending_syncs()
    assert len(FakeSMTP.sent) == 1
    assert len(_response_rows(response)) == 1


def test_email_failure_never_fails_the_order():
    """Mail server down: client still sees 'Order received', the order is synced, and staff are warned."""
    from src.client_form import failed_notifications
    failed_notifications.clear()
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    assert _submit_with_email(client, fail=OSError("connection refused")) == (True, "Order received")

    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED
    assert [(f['proposal_id'], f['company_name']) for f in failed_notifications] == [('PROP_1', 'Acme Corp')]
    assert 'connection refused' in failed_notifications[0]['reason']
    failed_notifications.clear()


def test_bad_email_header_never_fails_the_sync():
    """A company name with a line break cannot go in an email subject: the order still syncs and staff are warned."""
    from src.client_form import failed_notifications
    failed_notifications.clear()
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
    form = json.loads(json.dumps(SAMPLE_FORM))
    form['client_info']['company_name'] = 'Acme\nCorp'
    FakeSMTP.sent, FakeSMTP.fail = [], None
    with patch.dict(os.environ, NOTIFY_SETTINGS), patch('src.client_form.smtplib.SMTP', FakeSMTP):
        assert _submit(client, 'PROP_1', 'sess1', form) == (True, "Order received")

    assert FakeSMTP.sent == []
    assert len(_response_rows(response)) == 1
    assert _backup(drafts)[1] == STATUS_SUBMITTED
    assert [f['proposal_id'] for f in failed_notifications] == ['PROP_1']
    failed_notifications.clear()


def test_no_email_when_not_set_up():
    """Without recipients or a mail server configured, submit works and no mail server is contacted."""
    for settings in ({}, {'ORDER_NOTIFY_EMAILS': 'team@example.com'}, {'SMTP_HOST': 'smtp.example.com'}):
        client, response, drafts, _ = _mock_sheets(LIVE_HEADERS)
        blank = {name: '' for name in NOTIFY_SETTINGS}
        assert _submit_with_email(client, dict(blank, **settings), fail=AssertionError("mail server contacted")) == (True, "Order received")
        assert FakeSMTP.sent == []
