"""
Submitted Order Forms tab: every submitted client order form is listed (newest
first, searchable) and opens with all of its answers readable.

All Google Sheets are fakes: nothing real is touched.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from streamlit.testing.v1 import AppTest

from src.client_form import load_received_orders
from pbp.core.forms_helper import build_submissions_list, load_form_responses, submission_matches_search
from test_client_form import FakeSheet, LIVE_HEADERS, SAMPLE_FORM, _mock_sheets, _submit
from test_form_to_order import FULL_FORM, _app_function_source


def _at(hour):
    """A datetime class whose now() is 2026-10-16 at the given hour, so submit times are known."""
    class FixedNow(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 16, hour, 0, 0)
    return FixedNow


def _records(response):
    """Form Responses rows as the dicts load_form_responses() gives (sheet order)."""
    headers = response.rows[0]
    return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in response.rows[1:]]


def _two_synced_and_one_stuck():
    """
    A Google Form answer (already imported), then two in-app orders: one copied into
    Form Responses, one whose copy failed (still pending in the backup tab).
    """
    google_form_row = {h: '' for h in LIVE_HEADERS}
    google_form_row.update({'Timestamp': '10/15/2026 08:30:00', 'Company Name *': 'Old Google Form Co',
                            'Gift Item 1 - Product Name': 'Candle', 'Gift 1 Quantity': '50',
                            'Imported?': 'TRUE', 'Order ID': 'IMPORTED-1'})
    response = FakeSheet([LIVE_HEADERS, [google_form_row[h] for h in LIVE_HEADERS]])
    client, response, drafts, _ = _mock_sheets(LIVE_HEADERS, response=response)

    with patch('src.client_form.datetime', _at(9)):
        assert _submit(client, 'PROP_1', 'sess1', SAMPLE_FORM, b'name,address', 'addresses.csv')[0]

    stuck_form = dict(FULL_FORM, client_info=dict(FULL_FORM['client_info'], company_name='Stuck Co'),
                      payment_info=dict(FULL_FORM['payment_info'], accounting_contact_type='Email',
                                        accounting_contact='ap@stuck.com'))
    response.fail['update'] = [Exception("Sheets is down")]
    with patch('src.client_form.datetime', _at(10)):
        assert _submit(client, 'PROP_2', 'sess2', stuck_form)[0]

    with patch('src.client_form.connect_to_sheets', return_value=client):
        received = load_received_orders()
    return build_submissions_list(_records(response), received)


def test_every_submitted_form_is_listed_newest_first():
    submissions = _two_synced_and_one_stuck()

    assert [s['data']['client_info']['company_name'] for s in submissions] == ['Stuck Co', 'Acme Corp', 'Old Google Form Co']

    stuck, acme, google_form = submissions
    assert stuck['pending'] and stuck['sheet_row'] is None and not stuck['imported']
    assert len(stuck['data']['products']) == 2

    # The synced in-app order is listed once, from Form Responses, and keeps its backup keys for the file
    assert not acme['pending'] and acme['sheet_row'] == 3 and not acme['imported']
    assert (acme['proposal_id'], acme['session_id']) == ('PROP_1', 'sess1')
    assert acme['data']['shipping_info']['dropshipping_file'] == 'addresses.csv'
    assert acme['data']['products'][0] == {'name': 'Unisex Fleece Hoodie', 'quantity': 25, 'customization_notes': 'Navy, white logo'}

    assert google_form['sheet_row'] == 2 and google_form['imported']
    assert google_form['data']['metadata']['order_id'] == 'IMPORTED-1'
    assert google_form['session_id'] == ''


def test_blank_sheet_rows_are_not_listed():
    records = [{h: '' for h in LIVE_HEADERS}, dict({h: '' for h in LIVE_HEADERS}, **{'Company Name *': 'Acme Corp'})]
    submissions = build_submissions_list(records, [])
    assert [s['sheet_row'] for s in submissions] == [3]


def test_submitted_backups_missing_from_form_responses_are_not_listed_as_pending():
    # Backups saved before submitted_at existed, or whose sheet row was edited, never match a row
    def backup(status, submitted_at=''):
        return {'proposal_id': 'P', 'session_id': status, 'file_name': '', 'status': status,
                'form_data': {'submitted_at': submitted_at, 'client_info': {'company_name': 'Acme Corp'}}}
    received = [backup('submitted'), backup('submitted'), backup('pending_sync', '10/16/2026 10:00:00')]
    records = [dict({h: '' for h in LIVE_HEADERS}, **{'Timestamp': '10/15/2026 08:30:00', 'Company Name *': 'Acme Corp'})]

    submissions = build_submissions_list(records, received)

    assert [(s['pending'], s['session_id']) for s in submissions] == [(True, 'pending_sync'), (False, '')]


def test_backup_tab_read_failure_raises_instead_of_hiding_pending_orders():
    client, _, drafts, _ = _mock_sheets(LIVE_HEADERS)
    drafts.fail['batch_get'] = [Exception("Sheets is down")]
    with patch('src.client_form.connect_to_sheets', return_value=client), pytest.raises(Exception, match="Sheets is down"):
        load_received_orders()


def test_search_finds_company_contact_email_date_and_product():
    acme = _two_synced_and_one_stuck()[1]
    for text in ['acme', 'JO SMITH', 'jo@acme.com', '10/16/2026', 'hot honey', '']:
        assert submission_matches_search(acme, text), text
    assert not submission_matches_search(acme, 'stuck co')


# The details view, rendered from app.py's own functions
DETAILS_SCRIPT = '\n\n'.join(_app_function_source(name) for name in
                             ['submission_status', 'show_answer', 'show_submission_details']) + '''

import pandas as pd
import streamlit as st
show_submission_details(st.session_state.submission)
'''


def test_details_show_every_answer():
    submission = _two_synced_and_one_stuck()[0]  # the full form, read from the backup tab
    submission['data']['notes'] = 'Budget is $500 to $600'
    app = AppTest.from_string(DETAILS_SCRIPT)
    app.session_state.submission = submission
    app.run()
    assert not app.exception

    texts = [t.value for t in app.text]
    for answer in ['Existing', 'Stuck Co', 'Jo Smith', 'jo@acme.com', '555-1234',
                   '123 Main St\nSpringfield', 'PO Box 9\nSpringfield', '2026-11-01', 'Yes',
                   'Split across 3 offices', 'Credit Card', 'ap@stuck.com', 'Budget is $500 to $600']:
        assert answer in texts, answer

    products = app.table[0].value
    assert list(products['Product']) == ['Unisex Fleece Hoodie', '9 oz Hot Honey']
    assert list(products['Quantity']) == [25, 100]
    assert list(products['Customization notes']) == ['Navy, white logo', '']
    assert 'Waiting to sync' in app.caption[0].value


def test_failed_form_responses_read_is_an_error_not_an_empty_list():
    """A Sheets error must reach the tab (shown as an error), never look like 'no submitted forms'."""
    worksheet = MagicMock()
    worksheet.get_all_records.side_effect = Exception("429 Quota exceeded")
    client = MagicMock()
    client.open_by_key.return_value.worksheet.return_value = worksheet
    with pytest.raises(Exception, match="Quota"):
        load_form_responses(client)


if __name__ == "__main__":
    test_every_submitted_form_is_listed_newest_first()
    test_blank_sheet_rows_are_not_listed()
    test_submitted_backups_missing_from_form_responses_are_not_listed_as_pending()
    test_search_finds_company_contact_email_date_and_product()
    test_details_show_every_answer()
    test_failed_form_responses_read_is_an_error_not_an_empty_list()
    print("All tests passed!")
