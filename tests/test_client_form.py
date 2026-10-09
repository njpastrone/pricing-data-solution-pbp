"""Tests for src/client_form.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from unittest.mock import MagicMock, patch

import gspread

from src.client_form import generate_session_token, load_proposal_for_client, _serialize_form_data, _deserialize_form_data, submit_form, DRAFTS_SHEET_NAME, _open_worksheet, _open_drafts_sheet
from src.forms_config import GOOGLE_FORM_CONFIG, find_response_column
from src.forms_helper import parse_form_response


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


def _mock_sheets(response_headers, drafts_exists=True):
    """Build a fake gspread client with a response sheet and a drafts sheet."""
    # Forget worksheets cached by an earlier test
    _open_worksheet.clear()
    _open_drafts_sheet.clear()

    response_ws = MagicMock()
    response_ws.row_values.return_value = list(response_headers)

    drafts_ws = MagicMock()
    drafts_ws.get.return_value = [['Proposal_ID', 'Session_ID']]  # ID columns A:B

    response_book = MagicMock()
    response_book.worksheet.return_value = response_ws

    drafts_book = MagicMock()
    if drafts_exists:
        drafts_book.worksheet.return_value = drafts_ws
    else:
        drafts_book.worksheet.side_effect = gspread.exceptions.WorksheetNotFound(DRAFTS_SHEET_NAME)
        drafts_book.add_worksheet.return_value = drafts_ws

    client = MagicMock()
    client.open_by_key.side_effect = lambda key: (
        response_book if key == GOOGLE_FORM_CONFIG['response_sheet_id'] else drafts_book
    )
    return client, response_ws, drafts_ws, drafts_book


def _backup_json(drafts_ws):
    """Return the form JSON saved in the drafts sheet backup row."""
    saved_row = drafts_ws.append_row.call_args[0][0]
    return json.loads(saved_row[2])


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
    """Items land in the 'Gift ...' columns; a full backup is saved first."""
    client, response_ws, drafts_ws, _ = _mock_sheets(LIVE_HEADERS)
    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert success, msg
    row = response_ws.append_row.call_args[0][0]
    cell = dict(zip(LIVE_HEADERS, row))
    assert cell['Gift Item 1 - Product Name'] == 'Unisex Fleece Hoodie'
    assert cell['Gift 1 Quantity'] == '25'
    assert cell['Gift 1 Customization Notes'] == 'Navy, white logo'
    assert cell['Gift Item 2 - Product Name'] == '9 oz Hot Honey'
    assert cell['Gift 2 Quantity'] == '100'
    assert cell['Will this order be drop-shipped to individual recipients? *'] == 'No'
    assert cell['Impact Cards Add-Ons'] == 'Yes'
    assert cell['Company Name *'] == 'Acme Corp'

    # Backup holds the complete form
    assert _backup_json(drafts_ws) == SAMPLE_FORM


def test_submit_form_fails_loudly_on_header_mismatch():
    """If item columns are missing, nothing is written and the client sees an error."""
    headers_without_items = [h for h in LIVE_HEADERS if 'Gift' not in h]
    client, response_ws, drafts_ws, _ = _mock_sheets(headers_without_items)
    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert not success
    assert 'Product Line 1 - Product Name' in msg
    response_ws.append_row.assert_not_called()
    # The client's input is still preserved in the backup
    assert _backup_json(drafts_ws)['products'] == SAMPLE_FORM['products']


def test_submit_form_stops_if_backup_fails():
    """No backup, no submission: the response sheet is not touched."""
    client, response_ws, _, _ = _mock_sheets(LIVE_HEADERS)
    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form._get_drafts_sheet', return_value=None):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert not success
    response_ws.append_row.assert_not_called()


def test_submit_form_retries_backup_without_file():
    """A file too big for a sheet cell must not block the order."""
    client, response_ws, drafts_ws, _ = _mock_sheets(LIVE_HEADERS)
    drafts_ws.append_row.side_effect = [Exception("cell over 50000 characters"), None]
    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM, b'x' * 60000, 'addresses.xlsx')

    assert success, msg
    response_ws.append_row.assert_called_once()
    retry_row = drafts_ws.append_row.call_args[0][0]
    assert json.loads(retry_row[2]) == SAMPLE_FORM
    assert retry_row[3] == ''
    assert retry_row[4] == 'addresses.xlsx'


def test_submit_form_retry_keeps_stored_draft_file():
    """A form-only retry must not wipe a file already saved in the draft."""
    client, response_ws, drafts_ws, _ = _mock_sheets(LIVE_HEADERS)
    drafts_ws.get.return_value = [
        ['Proposal_ID', 'Session_ID'],
        ['PROP_1', 'sess1'],
    ]
    drafts_ws.update.side_effect = [Exception("429 rate limit"), None, None]
    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM, b'stored', 'addresses.xlsx')

    assert success, msg
    response_ws.append_row.assert_called_once()
    retry_range, retry_values = drafts_ws.update.call_args_list[1][0]
    assert retry_range == 'C2'
    assert json.loads(retry_values[0][0]) == SAMPLE_FORM


def test_submit_form_creates_drafts_tab_if_missing():
    """The backup tab is created when it doesn't exist yet."""
    client, response_ws, drafts_ws, drafts_book = _mock_sheets(LIVE_HEADERS, drafts_exists=False)
    with patch('src.client_form.connect_to_sheets', return_value=client):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert success, msg
    drafts_book.add_worksheet.assert_any_call(title=DRAFTS_SHEET_NAME, rows=100, cols=8)
    assert _backup_json(drafts_ws) == SAMPLE_FORM


def _quota_error():
    """A gspread APIError like the real 'Quota exceeded ... Read requests per minute' (HTTP 429)."""
    response = MagicMock()
    response.json.return_value = {'error': {'code': 429, 'message': 'Quota exceeded', 'status': 'RESOURCE_EXHAUSTED'}}
    return gspread.exceptions.APIError(response)


def test_submit_form_retries_after_quota_error():
    """A 429 on the response write waits and retries; exactly one row lands."""
    client, response_ws, drafts_ws, _ = _mock_sheets(LIVE_HEADERS)
    response_ws.row_values.side_effect = [_quota_error(), list(LIVE_HEADERS)]
    response_ws.append_row.side_effect = [_quota_error(), None]  # 429 = rejected, nothing written
    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form.time.sleep') as fake_sleep:
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert success, msg
    assert response_ws.append_row.call_count == 2  # first try rejected, second accepted
    assert fake_sleep.call_count == 2
    assert _backup_json(drafts_ws) == SAMPLE_FORM


def test_submit_form_fails_loudly_when_quota_never_clears():
    """If every retry hits the quota, submit reports failure but the backup is kept."""
    client, response_ws, drafts_ws, _ = _mock_sheets(LIVE_HEADERS)
    response_ws.append_row.side_effect = _quota_error()
    with patch('src.client_form.connect_to_sheets', return_value=client), \
         patch('src.client_form.time.sleep'):
        success, msg = submit_form('PROP_1', 'sess1', SAMPLE_FORM)

    assert not success
    assert 'Quota exceeded' in msg
    assert _backup_json(drafts_ws) == SAMPLE_FORM
    drafts_ws.update_cell.assert_not_called()  # draft is NOT marked submitted


def test_submit_form_does_not_reopen_sheets_every_time():
    """Spreadsheets are opened once and reused, saving read quota on later submits."""
    client, response_ws, _, _ = _mock_sheets(LIVE_HEADERS)
    with patch('src.client_form.connect_to_sheets', return_value=client):
        submit_form('PROP_1', 'sess1', SAMPLE_FORM)
        submit_form('PROP_2', 'sess2', SAMPLE_FORM)

    assert client.open_by_key.call_count == 2  # response sheet + drafts sheet, once each
    assert response_ws.append_row.call_count == 2


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


if __name__ == "__main__":
    test_generate_session_token_is_unique()
    test_generate_session_token_is_url_safe()
    test_serialize_form_data_roundtrip()
    test_deserialize_form_data_handles_empty()
    test_find_response_column_matches_live_headers()
    test_submit_form_writes_items_to_live_headers()
    test_submit_form_fails_loudly_on_header_mismatch()
    test_submit_form_stops_if_backup_fails()
    test_submit_form_retries_backup_without_file()
    test_submit_form_retry_keeps_stored_draft_file()
    test_submit_form_creates_drafts_tab_if_missing()
    test_submit_form_retries_after_quota_error()
    test_submit_form_fails_loudly_when_quota_never_clears()
    test_submit_form_does_not_reopen_sheets_every_time()
    test_parse_form_response_reads_live_headers()
    print("All tests passed!")
