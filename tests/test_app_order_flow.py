"""
Drive the REAL app (app.py) headless with Streamlit AppTest.

These tests click through Tab 3 and Tab 4 the way a person would: pick a
product, type a quantity, tick boxes, then read the Order Summary and the
Tab 4 invoice/PO. One test also follows a client order form with no proposal
from Tab 2 to the client's form page and back into Tab 3. Google Sheets is replaced by the fixed snapshot in
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
import time
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')


def start_app():
    """Open the app logged in, like a staff member in a new browser. Shares the test's fake sheets."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.session_state['authenticated'] = True  # skip the password gate
    at.session_state['storage_init'] = {}  # browser localStorage; otherwise the component waits for a browser forever
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def app(monkeypatch):
    """The real app, logged in, reading the Sheets snapshot instead of Google."""
    monkeypatch.setenv('PBP_FAKE_SHEETS', '1')
    st.cache_data.clear()
    st.cache_resource.clear()  # fresh fake client = empty saved orders for every test
    yield start_app()
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

    app.checkbox(key='tab4_fifty_cent_rounding_checkbox').check().run()  # same setting, from Tab 4
    assert total_quote(app) == 149.00


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


def test_more_units_get_the_cheaper_tier_price(app):
    tote = add_product(app, 'Harbor Weavers', 'Woven Market Tote', 60)  # tier 2: $10.50 cost, 100% markup
    assert app.session_state['order_items'][tote]['base_price'] == 10.50
    assert item_client_total(app, tote) == 21.00 * 60


def test_mistyped_cost_far_above_a_typed_price_does_not_crash(app):
    """Typed PbP MSRP $33, then PBP Cost mistyped as $235.70 (for $23.57): the page must keep working."""
    beanie = add_product(app, 'Highland Knits', 'Alpaca Beanie', 20)
    app.number_input(key=f'prod_price_{beanie}').set_value(33.00).run()
    app.number_input(key=f'prod_cost_{beanie}').set_value(235.70).run()
    assert not app.exception

    app.number_input(key=f'prod_cost_{beanie}').set_value(23.57).run()  # fixing the typo brings $33 back
    assert not app.exception
    assert item_client_total(app, beanie) == 33.00 * 20


def test_typed_price_below_half_the_cost_does_not_crash(app):
    """The markup field stops at -50%, so a typed price under half the cost is raised to half the cost everywhere."""
    tote = add_product(app, 'Harbor Weavers', 'Woven Market Tote', 60)  # $10.50 cost
    app.checkbox(key='order_fifty_cent_rounding_checkbox').uncheck().run()
    app.number_input(key=f'prod_price_{tote}').set_value(2.00).run()
    assert not app.exception
    assert app.session_state['order_items'][tote]['markup_percent'] == -50.0
    assert app.number_input(key=f'prod_price_{tote}').value == 5.25
    assert any('lowest allowed price' in c.value for c in app.caption)
    assert item_client_total(app, tote) == 5.25 * 60
    assert total_quote(app) == 5.25 * 60
    assert invoice_lines(app)['Woven Market Tote'] == '$315.00'


def open_client_form(link):
    """Open a client form link the way the client does: a fresh browser, never logged in."""
    params = parse_qs(urlparse(link).query)
    form = AppTest.from_file(APP_PATH, default_timeout=60)
    form.query_params['client_form'] = params['client_form'][0]
    form.query_params['session'] = params['session'][0]
    form.run()
    assert not form.exception
    return form


def test_form_without_a_proposal_carries_products_prices_and_notes_into_the_order(app):
    """
    No proposal: the rep picks products in Tab 2 and sends the link, the client changes
    a quantity, adds a product and submits, then staff import it from Submitted Order Forms.
    """
    from src.data_loader import connect_to_sheets
    from src.forms_config import GOOGLE_FORM_CONFIG
    from fake_sheets import FakeSheet
    from test_client_form import LIVE_HEADERS
    # The Google Form's response sheet always exists (with its headers) in production
    responses = FakeSheet([LIVE_HEADERS], title=GOOGLE_FORM_CONFIG['response_sheet_name'])
    connect_to_sheets().open_by_key(GOOGLE_FORM_CONFIG['response_sheet_id']).sheets[responses.title] = responses

    # Tab 2, rep side: client info, then products from the catalog with quantity and notes
    assert not app.session_state['loaded_proposal_id']
    app.text_input(key='order_detail_company_name').input('Acme Corp')
    app.text_input(key='order_detail_contact_name').input('Jo Smith')
    app.text_input(key='order_detail_contact_email').input('jo@acme.example').run()
    app.multiselect(key='cf_staff_picks').select('Stoneware Mug').select('Woven Market Tote').run()
    app.number_input(key='cf_staff_qty_Woven Market Tote').set_value(60).run()  # tier 2: $10.50 cost
    app.text_input(key='cf_staff_notes_Stoneware Mug').input('Blue glaze, logo on base').run()
    rep_prices = [c.value for c in app.caption if 'per unit' in c.value]
    assert rep_prices == ['\\$23.00 per unit, \\$2,300.00 total', '\\$21.00 per unit, \\$1,260.00 total']
    app.button(key='gen_client_form_link_btn').click().run()
    link = app.session_state['generated_client_form_link']
    assert 'client_form=catalog_real_' in link

    # Client side: the rep's picks are filled in, with prices
    form = open_client_form(link)
    assert form.text_input(key='cf_company_name').value == 'Acme Corp'
    assert [form.selectbox(key=f'cf_product_{i}').value for i in range(2)] == ['Stoneware Mug', 'Woven Market Tote']
    assert [form.number_input(key=f'cf_qty_{i}').value for i in range(2)] == [100, 60]
    assert form.text_input(key='cf_notes_0').value == 'Blue glaze, logo on base'

    form.number_input(key='cf_qty_0').set_value(40).run()
    form.button(key='cf_add_item').click().run()
    form.selectbox(key='cf_product_2').select('9 oz Raw Honey').run()
    form.number_input(key='cf_qty_2').set_value(24).run()
    form.text_input(key='cf_notes_2').input('Gift tag').run()
    assert [c.value for c in form.caption if c.value.startswith('Price:')] == [
        f'Price: \\${unit} per unit, \\${total} for {qty} (before customization, shipping and taxes)'
        for unit, total, qty in [('23.00', '920.00', 40), ('21.00', '1,260.00', 60), ('15.00', '360.00', 24)]]

    form.text_area(key='cf_shipping_address').input('1 Main St, Springfield')
    form.date_input(key='cf_in_hands_date').set_value(date(2026, 12, 1))
    form.text_input(key='cf_accounting_contact').input('ap@acme.example').run()
    form.button(key='cf_submit_btn').click().run()
    assert any(s.value.startswith('Order received') for s in form.success)

    # The copy into Form Responses runs on a background thread
    for _ in range(100):
        if len(responses.rows) > 1:
            break
        time.sleep(0.05)
    assert len(responses.rows) == 2

    # Staff side: load the submitted forms, select the order and import it into Tab 3
    app.button(key='load_submitted_forms').click().run()
    first_row = {'selection': {'rows': [0], 'columns': [], 'cells': []}}  # AppTest can't click a table row
    app.session_state['submitted_forms_table_1__All'] = first_row
    app.run()
    app.session_state['submitted_forms_table_1__All'] = first_row
    app.button(key='import_submitted_form').click().run()
    assert not app.exception
    assert any(s.value.startswith('Imported 3 product(s) from Acme Corp.') and 'could not' not in s.value
               for s in app.success)

    items = {item['product_name']: item for item in app.session_state['order_items']}
    assert {name: (item['quantity'], item['customization_description']) for name, item in items.items()} == {
        'Stoneware Mug': (40, 'Blue glaze, logo on base'),
        'Woven Market Tote': (60, ''),
        '9 oz Raw Honey': (24, 'Gift tag'),
    }
    # The order prices each product the same as the form showed the client
    assert {name: item_client_total(app, i) for i, (name, item) in enumerate(items.items())} == {
        'Stoneware Mug': 920.00, 'Woven Market Tote': 1260.00, '9 oz Raw Honey': 360.00}
    assert total_quote(app) == 2540.00
    assert app.session_state['client_info']['company_name'] == 'Acme Corp'
    assert app.session_state['client_info']['contacts'][0]['email'] == 'jo@acme.example'


def test_a_guessed_catalog_link_shows_no_catalog(app):
    form = open_client_form('https://example.com/?client_form=catalog_real_000000000000&session=abcdefabcdef')
    assert [e.value for e in form.error] == ["This form is no longer available. Please contact your PBP representative."]
    assert not form.selectbox
