"""Tests for the order prices that reach the Tab 4 invoice/PO (rounding, kitting, PBP Cost override)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit.testing.v1 import AppTest

from src.helpers import get_item_client_unit_price, calculate_split_totals
from src.pricing_engine import get_item_unit_cost
from test_form_to_order import _app_function_source


def _item(unit_cost, client_unit_price, quantity=50):
    """An order item as Tab 3 stores it (cost + markup totals)."""
    return {
        'quantity': quantity,
        'base_price': unit_cost,
        'product_subtotal': unit_cost * quantity,
        'markup_amount': (client_unit_price - unit_cost) * quantity,
    }


def test_rounded_pbp_msrp_is_the_invoice_price():
    """Honey $7.06 shows as $7.00 and Tea Tin $16.35 as $16.50; the invoice must use the same numbers."""
    honey = _item(3.53, 7.06)
    tea = _item(8.175, 16.35)
    assert round(get_item_client_unit_price(honey, True), 2) == 7.00
    assert round(get_item_client_unit_price(tea, True), 2) == 16.50
    assert round(get_item_client_unit_price(honey, False), 2) == 7.06

    totals = calculate_split_totals([honey, tea], fifty_cent_rounding=True)
    assert round(totals['products_client_price'], 2) == round((7.00 + 16.50) * 50, 2)


# Tab 3 and Tab 4 order-settings fields bound to the same session values, like the real app
SETTINGS_SCRIPT = _app_function_source('synced_widget') + '''

import streamlit as st
if 'kitting_client_price' not in st.session_state:
    st.session_state.kitting_client_price = 0.0
    st.session_state.order_fifty_cent_rounding = False
synced_widget(st.checkbox, "Round (Tab 3)", st.session_state, 'order_fifty_cent_rounding', key="order_fifty_cent_rounding_checkbox")
synced_widget(st.number_input, "Kitting (Tab 3)", st.session_state, 'kitting_client_price', key="kitting_client_input", min_value=0.0)
synced_widget(st.checkbox, "Round (Tab 4)", st.session_state, 'order_fifty_cent_rounding', key="tab4_fifty_cent_rounding_checkbox")
synced_widget(st.number_input, "Kitting (Tab 4)", st.session_state, 'kitting_client_price', key="tab4_kitting_client_input", min_value=0.0)
# The invoice/PO is built after both tabs' widgets have run
st.session_state.invoice_kitting = st.session_state.kitting_client_price
st.session_state.invoice_rounding = st.session_state.order_fifty_cent_rounding
'''


def test_kitting_and_rounding_set_in_tab3_reach_the_invoice():
    """Tab 4's copies of the settings used to reset kitting to $0 and rounding to off before the invoice was built."""
    app = AppTest.from_string(SETTINGS_SCRIPT).run()
    app.number_input(key="kitting_client_input").set_value(575.0).run()
    app.checkbox(key="order_fifty_cent_rounding_checkbox").check().run()
    app.run()  # a later rerun must not lose them either
    assert app.session_state.invoice_kitting == 575.0
    assert app.session_state.invoice_rounding is True
    assert app.number_input(key="tab4_kitting_client_input").value == 575.0

    app.number_input(key="tab4_kitting_client_input").set_value(600.0).run()  # edit in Tab 4 shows in Tab 3
    assert app.number_input(key="kitting_client_input").value == 600.0
    assert app.session_state.invoice_kitting == 600.0
    assert not app.exception


def test_pbp_cost_override_replaces_the_spreadsheet_cost():
    """Leather sunglasses case: the typed PBP Cost ($23.57) is used instead of the spreadsheet cost."""
    item = {'product_data': {'Pricing Tiers (Y/N)': 'N', 'PBP Cost (No Tiers/Tier 1)': '$20.00'}}
    assert get_item_unit_cost(item, 10)[0] == 20.00

    item['pbp_cost_override'] = 23.57
    assert get_item_unit_cost(item, 10) == (23.57, "No Tiers", "PBP Cost (No Tiers/Tier 1)")

    # Totals and the PO read the stored cost (base_price / product_subtotal), so the override flows there
    stored = _item(23.57, 33.00, quantity=10)
    assert calculate_split_totals([stored])['products_pbp_cost'] == 235.70
    assert round(get_item_client_unit_price(stored, True), 2) == 33.00


if __name__ == "__main__":
    test_rounded_pbp_msrp_is_the_invoice_price()
    test_kitting_and_rounding_set_in_tab3_reach_the_invoice()
    test_pbp_cost_override_replaces_the_spreadsheet_cost()
    print("All order pricing tests passed")
