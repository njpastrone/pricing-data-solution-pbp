"""
Drive the REAL app (app.py) headless with Streamlit AppTest.

These tests click through Tab 3 and Tab 4 the way a person would: pick a
product, type a quantity, tick boxes, then read the Order Summary and the
Tab 4 invoice/PO. Google Sheets is replaced by the fixed snapshot in
tests/fixtures/sheets/ (see tests/fake_sheets.py), so no credentials are needed.

Snapshot prices used below (client price per unit). All but the Honey Stick
Case sit on a $0.50 step, so the default $0.50 rounding leaves them alone:
    Woven Market Tote   Standard markup, tiers $12.00 / $10.50 / $9.00 cost -> 2x cost
    9 oz Raw Honey      MSRP + % of cost: $14.10 MSRP + 15% of $6.00 cost = $15.00
    Stoneware Mug       MSRP + Other Add-On: $22.20 MSRP + 10% of $8.00 cost = $23.00
    Alpaca Beanie       MSRP capped - ship absorbed: $25.00 MSRP
    Honey Stick Case    Per Case: $40.00 per case of 50 -> $0.80 cost -> $1.60

Run: pytest tests/test_app_order_flow.py   (see tests/README.md)
"""

import os
import re

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')


@pytest.fixture
def app(monkeypatch):
    """The real app, logged in, reading the Sheets snapshot instead of Google."""
    monkeypatch.setenv('PBP_FAKE_SHEETS', '1')
    st.cache_data.clear()
    st.cache_resource.clear()  # fresh fake client = empty saved orders for every test
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.session_state['authenticated'] = True  # skip the password gate
    at.session_state['storage_init'] = {}  # browser localStorage; otherwise the component waits for a browser forever
    at.run()
    assert not at.exception
    yield at
    # Don't leave the cached fake client behind for other test files
    st.cache_data.clear()
    st.cache_resource.clear()


def add_product(at, partner, product, quantity):
    """Tab 3 Option C: pick partner + product, click Add to Order, type the quantity. Returns the item index."""
    at.selectbox(key='add_partner_select').select(partner).run()
    at.selectbox(key='add_product_select').select(product).run()
    next(b for b in at.button if b.label == 'Add to Order' and not b.key).click().run()
    idx = len(at.session_state['order_items']) - 1
    at.number_input(key=f'prod_qty_{idx}').set_value(quantity).run()
    assert not at.exception
    return idx


def total_quote(at):
    """The Tab 3 Order Summary total, from the 'Total Quote: $X' banner."""
    banner = next(s.value for s in at.success if s.value.startswith('Total Quote:'))
    return float(re.search(r'\$([\d.]+)', banner).group(1))


def item_client_total(at, idx):
    return round(at.session_state['order_items'][idx]['product_total'], 2)


def invoice_lines(at):
    """Tab 4 invoice/PO line items as {description: total sell price}."""
    df = next(d.value for d in at.dataframe if 'TOTAL SELL PRICE' in d.value.columns)
    return {row['DESCRIPTION (Invoice)']: row['TOTAL SELL PRICE'] for _, row in df.iterrows()}


def invoice_total(at):
    """The TOTAL row of the Tab 4 invoice/PO summary totals."""
    df = next(t.value for t in at.table if 'Amount' in t.value.columns)
    return df[df['Item'] == '**TOTAL**']['Amount'].iloc[0].strip('*')


def test_snapshot_catalog_and_partner_contacts_load(app):
    assert sorted(app.session_state['df_template']['Product/Service']) == [
        '9 oz Raw Honey', 'Alpaca Beanie', 'Honey Stick Case', 'Stoneware Mug', 'Woven Market Tote']
    assert app.session_state['partner_contacts']['Harbor Weavers']['poc_email'] == 'ana@harborweavers.example'


def test_each_pricing_method_gives_the_expected_client_price(app):
    honey = add_product(app, 'Sunrise Apiary', '9 oz Raw Honey', 24)
    mug = add_product(app, 'Mesa Ceramics', 'Stoneware Mug', 12)
    beanie = add_product(app, 'Highland Knits', 'Alpaca Beanie', 20)
    sticks = add_product(app, 'Sunrise Apiary', 'Honey Stick Case', 50)

    assert item_client_total(app, honey) == 15.00 * 24
    assert item_client_total(app, mug) == 23.00 * 12
    assert item_client_total(app, beanie) == 25.00 * 20
    assert item_client_total(app, sticks) == 1.60 * 50  # before $0.50 rounding
    assert total_quote(app) == 15.00 * 24 + 23.00 * 12 + 25.00 * 20 + 1.50 * 50  # $1.60 rounds to $1.50


def test_fifty_cent_and_marketing_rounding(app):
    add_product(app, 'Sunrise Apiary', 'Honey Stick Case', 100)  # $1.60 each
    assert app.session_state['order_fifty_cent_rounding'] is True  # on by default
    assert total_quote(app) == 150.00  # $1.60 rounds to $1.50

    app.checkbox(key='marketing_rounding_checkbox').check().run()
    assert total_quote(app) == 149.00  # $150 ends in 0 -> $149

    app.checkbox(key='order_fifty_cent_rounding_checkbox').uncheck().run()
    assert total_quote(app) == 159.00  # $160 unrounded, still charm-priced


def test_typed_client_price_overrides_the_pricing_method(app):
    beanie = add_product(app, 'Highland Knits', 'Alpaca Beanie', 20)  # $25.00 from MSRP
    app.checkbox(key=f'manual_override_tab3_{beanie}').check().run()
    app.number_input(key=f'prod_price_{beanie}').set_value(27.50).run()

    assert app.session_state['order_items'][beanie]['manual_override'] is True
    assert item_client_total(app, beanie) == 27.50 * 20
    assert total_quote(app) == 550.00


def test_per_product_kitting_is_added_to_the_total(app):
    mug = add_product(app, 'Mesa Ceramics', 'Stoneware Mug', 10)  # $230.00
    app.checkbox(key=f'prod_kitting_enabled_{mug}').check().run()
    app.number_input(key=f'prod_kitting_qty_{mug}').set_value(10).run()
    app.number_input(key=f'prod_kitting_pbp_{mug}').set_value(1.00).run()
    app.number_input(key=f'prod_kitting_client_{mug}').set_value(3.00).run()

    assert total_quote(app) == 230.00 + 10 * 3.00


def test_invoice_matches_the_order_summary(app):
    """Tab 4 invoice/PO: one line per product, and the same total as the Tab 3 Order Summary."""
    add_product(app, 'Highland Knits', 'Alpaca Beanie', 20)
    add_product(app, 'Sunrise Apiary', '9 oz Raw Honey', 24)
    assert total_quote(app) == 860.00

    lines = invoice_lines(app)
    assert lines['Alpaca Beanie'] == '$500.00'
    assert lines['9 oz Raw Honey'] == '$360.00'
    assert invoice_total(app) == '$860.00'


@pytest.mark.xfail(strict=True, reason="Known bug: after a quantity change the stale client price box "
                   "re-sets the markup, so the cheaper tier never reaches the client price")
def test_more_units_get_the_cheaper_tier_price(app):
    tote = add_product(app, 'Harbor Weavers', 'Woven Market Tote', 60)  # tier 2: $10.50 cost, 100% markup
    assert app.session_state['order_items'][tote]['base_price'] == 10.50
    assert item_client_total(app, tote) == 21.00 * 60
