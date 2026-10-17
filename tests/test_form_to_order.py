"""
Client order form -> Form Responses -> Tab 3 import -> saved order -> Tab 4.

A fully filled form is pushed through the whole chain and every answer is
checked where it lands. All Google Sheets are fakes: nothing real is touched.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ast
from datetime import date
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.forms_helper import parse_form_response, form_response_to_order, html_form_to_order, add_order_notes
from src.order_manager import save_order, load_order_data
from src.helpers import convert_proposal_to_order
from test_client_form import FakeSheet, LIVE_HEADERS, _mock_sheets, _submit

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')

FULL_FORM = {
    'client_info': {'client_type': 'Existing', 'company_name': 'Acme Corp', 'contact_name': 'Jo Smith',
                    'contact_email': 'jo@acme.com', 'contact_phone': '555-1234'},
    'products': [
        {'name': 'Unisex Fleece Hoodie', 'quantity': 25, 'customization_notes': 'Navy, white logo'},
        {'name': '9 oz Hot Honey', 'quantity': 100, 'customization_notes': ''},
    ],
    'shipping_info': {'shipping_address': '123 Main St\nSpringfield', 'billing_address': 'PO Box 9\nSpringfield',
                      'drop_shipping': 'Yes', 'drop_shipping_instructions': 'Split across 3 offices',
                      'in_hands_date': '2026-11-01'},
    'payment_info': {'impact_cards': 'Yes', 'impact_card_selection': '', 'payment_preference': '',
                     'payment_method': 'Credit Card'},
    'notes': 'Please gift wrap',
}


def _form_to_imported_order(form, file_name=None):
    """Submit the form into a fake Form Responses sheet and import it the way Tab 3 does."""
    client, response, _, _ = _mock_sheets(LIVE_HEADERS)
    success, _ = _submit(client, 'PROP_1', 'sess1', form, b'name,address' if file_name else None, file_name)
    assert success
    headers = response.rows[0]
    record = dict(zip(headers, response.rows[1] + [''] * (len(headers) - len(response.rows[1]))))
    return form_response_to_order(parse_form_response(record))


def test_full_form_reaches_the_order():
    """Every client form answer lands in the right order field."""
    order = _form_to_imported_order(FULL_FORM, 'addresses.csv')
    client_info = order['client_info']

    assert client_info['is_new_client'] is False
    assert client_info['company_name'] == 'Acme Corp'
    assert client_info['contacts'] == [{'name': 'Jo Smith', 'email': 'jo@acme.com', 'phone': '555-1234',
                                        'role': 'Primary Contact'}]
    assert client_info['billing_address'] == 'PO Box 9\nSpringfield'
    assert client_info['shipping_address'] == '123 Main St\nSpringfield'
    assert client_info['shipping_type'] == 'Drop Shipping'
    assert client_info['drop_shipping_instructions'] == 'Split across 3 offices\nAddress file: addresses.csv'
    assert client_info['client_in_hands_date'] == date(2026, 11, 1)
    assert client_info['payment_preference'] == 'Credit Card'
    assert client_info['payment_timeline'] == 'Net 30'  # set by PBP staff, not the client

    # Customization notes stay with their own product
    assert order['products'] == [
        {'name': 'Unisex Fleece Hoodie', 'quantity': 25, 'customization_description': 'Navy, white logo'},
        {'name': '9 oz Hot Honey', 'quantity': 100, 'customization_description': ''},
    ]

    # Additional notes and impact cards go into the team notes
    assert order['order_notes'] == {'internal_pbp_team': 'Client notes (order form): Please gift wrap\nImpact cards: Yes'}


def test_blank_billing_address_means_same_as_shipping():
    """The form asks for billing only 'if different from shipping'."""
    form = dict(FULL_FORM, shipping_info=dict(FULL_FORM['shipping_info'], billing_address=''))
    order = _form_to_imported_order(form)
    assert order['client_info']['billing_address'] == '123 Main St\nSpringfield'


def test_html_order_form_lands_like_a_form_response():
    """The legacy HTML form import writes contacts, billing fallback and drop-ship notes too."""
    order = html_form_to_order({
        'client_type': 'New', 'company_name': 'Acme Corp',
        'contact_name': 'Jane Doe', 'contact_email': 'jane@acme.com',
        'drop_shipping': 'Yes', 'shipping_address': '123 Main St',
        'dropshipping_info': 'Split across 3 offices', 'billing_address': '',
        'client_in_hands_date': '11/1/2026', 'impact_card_preference': 'Yes',
        'payment_preference': 'ACH', 'products': ['Hoodie'], 'parse_errors': [],
    })
    client_info = order['client_info']
    assert client_info['contacts'] == [{'name': 'Jane Doe', 'email': 'jane@acme.com', 'phone': '', 'role': 'Primary Contact'}]
    assert client_info['billing_address'] == '123 Main St'
    assert client_info['shipping_type'] == 'Drop Shipping'
    assert client_info['drop_shipping_instructions'] == 'Split across 3 offices'
    assert client_info['client_in_hands_date'] == date(2026, 11, 1)
    assert client_info['payment_preference'] == 'ACH'
    assert order['order_notes'] == {'internal_pbp_team': 'Impact cards: Yes'}
    assert order['products'] == []


def test_proposal_import_leaves_customization_description_blank():
    """Catalog 'Customization Info' is availability text, not ordered customization: it must not reach invoice lines."""
    proposal_item = {
        'product_data': {'Product/Service': 'Hoodie', 'Partner': 'Acme', 'Customization Info': 'Laser engraving available, MOQ 50'},
        'quantity': 10, 'markup_percent': 100.0,
    }
    order_item = convert_proposal_to_order(proposal_item, lambda data, qty: (5.0, '1-49', 1), lambda base, rate: 0.0)
    assert order_item['customization_description'] == ''
    assert order_item['include_customization'] is False


def test_imported_order_survives_save_and_load():
    """What Tab 3 imports is what a saved order (and Tab 4) gets back."""
    order = _form_to_imported_order(FULL_FORM)
    notes = add_order_notes({'internal_pbp_team': '', 'internal_bookkeeping': '',
                             'external_partners': '', 'external_clients': ''}, order['order_notes'])
    order_data = {'client_info': order['client_info'], 'order_notes': notes, 'order_items': order['products']}

    sheet = FakeSheet([['Order_ID', 'Order_Name', 'Created_By', 'Created_Date', 'Dataset', 'Order_Data_JSON']])
    with patch('src.order_manager.initialize_orders_sheet', return_value=sheet):
        saved, _, order_id = save_order('Acme order', 'staff', order_data, 'demo')
        loaded_ok, loaded, _ = load_order_data(order_id)

    assert saved and loaded_ok
    assert loaded['client_info'] == order['client_info']
    assert loaded['order_notes'] == notes
    assert loaded['order_items'] == order['products']


def test_google_form_answers_are_understood():
    """Answers in the Google Form's own wording map to the order's options."""
    record = {h: '' for h in LIVE_HEADERS}
    record.update({
        'Company Name *': 'Acme Corp',
        'Shipping Address *': '1 Elm St',
        'Will this order be drop-shipped to individual recipients? *': 'Yes - Ship directly to my customer(s)',
        'In-Hands Date (When do you need this order?) *': '2/27/2026',
        'Payment Method *': 'ACH / Bank Transfer',
        'Impact Cards Add-Ons': 'Yes - Include impact cards for each artisan',
        'Is there a specific platform or email address we need to send the invoice to (i.e. BillPay.com)?': 'ap@acme.com',
    })
    order = form_response_to_order(parse_form_response(record))

    assert order['client_info']['shipping_type'] == 'Drop Shipping'
    assert order['client_info']['client_in_hands_date'] == date(2026, 2, 27)
    assert order['client_info']['payment_preference'] == 'ACH'
    assert order['client_info']['billing_address'] == '1 Elm St'
    assert order['order_notes']['internal_bookkeeping'] == 'Send invoice to: ap@acme.com'
    assert 'Impact cards: Yes - Include impact cards' in order['order_notes']['internal_pbp_team']


def test_add_order_notes_keeps_staff_notes_and_skips_repeats():
    """Importing never wipes notes staff typed, and re-importing does not add the text twice."""
    existing = {'internal_pbp_team': 'Call client Monday', 'external_clients': ''}
    new = {'internal_pbp_team': 'Client notes (order form): Rush'}
    merged = add_order_notes(existing, new)
    assert merged['internal_pbp_team'] == 'Call client Monday\nClient notes (order form): Rush'
    assert add_order_notes(merged, new) == merged
    assert existing['internal_pbp_team'] == 'Call client Monday'  # input not changed


def _app_function_source(name):
    """Source of one top-level function in app.py (app.py itself cannot be imported: it runs the app)."""
    source = open(APP_PATH).read()
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"{name} not found in app.py")


# A Tab 3 field and a Tab 4 field bound to the same order data, like the real app
TWO_TABS_SCRIPT = _app_function_source('synced_widget') + '''

import streamlit as st
if 'client_info' not in st.session_state:
    st.session_state.client_info = {'company_name': 'Old Co', 'client_in_hands_date': None}
if st.button("Import"):
    st.session_state.client_info = {'company_name': 'Imported Co', 'client_in_hands_date': __import__('datetime').date(2026, 11, 1)}
ci = st.session_state.client_info
synced_widget(st.text_input, "Company (Tab 3)", ci, 'company_name', key="t3_company_name")
synced_widget(st.date_input, "In-Hands (Tab 3)", ci, 'client_in_hands_date', key="t3_date", default=None)
synced_widget(st.text_input, "Company (Tab 4)", ci, 'company_name', key="t4_company_name")
synced_widget(st.date_input, "In-Hands (Tab 4)", ci, 'client_in_hands_date', key="t4_date", default=None)
'''


def test_tab3_and_tab4_show_the_same_current_order_data():
    """After an import both tabs show the imported values, and an edit in either tab shows in the other."""
    app = AppTest.from_string(TWO_TABS_SCRIPT).run()
    assert [w.value for w in app.text_input] == ['Old Co', 'Old Co']

    app.button[0].click().run()  # import replaces the order data
    assert [w.value for w in app.text_input] == ['Imported Co', 'Imported Co']
    assert [w.value for w in app.date_input] == [date(2026, 11, 1), date(2026, 11, 1)]

    app.text_input(key="t4_company_name").input("Edited in Tab 4").run()
    assert [w.value for w in app.text_input] == ['Edited in Tab 4', 'Edited in Tab 4']
    assert app.session_state.client_info['company_name'] == 'Edited in Tab 4'

    app.text_input(key="t3_company_name").input("Edited in Tab 3").run()
    assert [w.value for w in app.text_input] == ['Edited in Tab 3', 'Edited in Tab 3']
    assert not app.exception


if __name__ == "__main__":
    test_full_form_reaches_the_order()
    test_blank_billing_address_means_same_as_shipping()
    test_html_order_form_lands_like_a_form_response()
    test_proposal_import_leaves_customization_description_blank()
    test_imported_order_survives_save_and_load()
    test_google_form_answers_are_understood()
    test_add_order_notes_keeps_staff_notes_and_skips_repeats()
    test_tab3_and_tab4_show_the_same_current_order_data()
    print("All tests passed!")
