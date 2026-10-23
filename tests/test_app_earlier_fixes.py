"""
The fixes from the client order form and order rounds (#33-#40), checked in the
REAL app (app.py) with Streamlit AppTest, the way a person uses it: the rep sends
a form link from Tab 2, the client fills in the form page and submits, staff open
the Submitted Order Forms tab, import, and finish the order in Tab 3 and Tab 4.

Google Sheets is the in-memory stand-in from tests/fake_sheets.py (see
tests/README.md). Helpers and the `app` fixture come from test_app_order_flow.py.

Run: pytest tests/test_app_earlier_fixes.py
"""

import io
import os
import sys
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from fake_sheets import FakeSheet
from test_app_order_flow import add_product, app, invoice_lines, open_client_form, start_app  # noqa: F401 (app is a fixture)
from test_client_form import LIVE_HEADERS
from src.data_loader import DATASET_CONFIGS, connect_to_sheets
from src.forms_config import GOOGLE_FORM_CONFIG
from src.order_manager import load_all_orders, load_order_data

DROP_SHIP_COLUMN = 'Will this order be drop-shipped to individual recipients? *'
INVOICE_COLUMN = 'Is there a specific platform or email address we need to send the invoice to (i.e. BillPay.com)?'


# ---------- helpers ----------

def response_row(**answers):
    """A Form Responses row (Google Form layout), e.g. response_row(**{'Company Name *': 'Acme'})."""
    return [answers.get(header, '') for header in LIVE_HEADERS]


def form_responses_sheet(earlier_rows=()):
    """Form Responses as in production: headers plus any earlier answers, and no spare grid rows."""
    rows = [LIVE_HEADERS, *earlier_rows]
    sheet = FakeSheet(rows, row_count=len(rows), title=GOOGLE_FORM_CONFIG['response_sheet_name'])

    def append_like_the_live_tab(row, **kwargs):
        """The live tab is a Sheets Table: Google put every appended row on row 8, over the last one."""
        sheet.rows.extend([] for _ in range(8 - len(sheet.rows)))
        sheet.rows[7] = list(row)

    sheet.append_row = append_like_the_live_tab
    connect_to_sheets().open_by_key(GOOGLE_FORM_CONFIG['response_sheet_id']).sheets[sheet.title] = sheet
    return sheet


def answers(sheet, row_number):
    """One Form Responses row as {header: value}."""
    return dict(zip(LIVE_HEADERS, sheet.rows[row_number - 1] + [''] * len(LIVE_HEADERS)))


def send_form_link(app, products):
    """Tab 2: the rep picks catalog products and generates a client form link."""
    app.multiselect(key='cf_staff_picks').set_value(products).run()
    app.button(key='gen_client_form_link_btn').click().run()
    return app.session_state['generated_client_form_link']


def fill_required(form, company, accounting='ap@acme.example'):
    """Client: type the answers the form requires (products come from the rep's picks)."""
    form.text_input(key='cf_company_name').input(company)
    form.text_input(key='cf_contact_name').input('Jo Smith')
    form.text_input(key='cf_contact_email').input('jo@acme.example')
    form.text_area(key='cf_shipping_address').input('1 Main St, Springfield')
    form.date_input(key='cf_in_hands_date').set_value(date(2026, 12, 1))
    form.text_input(key='cf_accounting_contact').input(accounting)
    form.run()


def submit(form):
    """Client clicks Submit Order. Returns the error shown, or '' when the order was received."""
    form.button(key='cf_submit_btn').click().run()
    assert not form.exception
    if any(s.value.startswith('Order received') for s in form.success):
        return ''
    return ' '.join(e.value for e in form.error)


def wait_for_rows(sheet, count):
    """The copy into Form Responses runs on a background thread."""
    for _ in range(100):
        if len(sheet.rows) >= count:
            break
        time.sleep(0.05)
    assert len(sheet.rows) == count


def load_submitted_forms(app):
    app.button(key='load_submitted_forms').click().run()
    assert not app.exception


def submitted_forms_table(app):
    return next(d.value for d in app.dataframe if 'Company' in d.value.columns)


def select_submitted_form(app, company, search='', status='All'):
    """Click the table row of this company's form (AppTest can't click a table row, so set the selection)."""
    row = list(submitted_forms_table(app)['Company']).index(company)
    key = f"submitted_forms_table_{app.session_state['submitted_forms_loads']}_{search}_{status}"
    selection = {'selection': {'rows': [row], 'columns': [], 'cells': []}}
    app.session_state[key] = selection
    app.run()
    app.session_state[key] = selection  # keep it selected for the next click too


def import_selected_form(app):
    app.button(key='import_submitted_form').click().run()
    assert not app.exception


def png(color):
    """A small real PNG image."""
    buffer = io.BytesIO()
    Image.new('RGB', (4, 4), color).save(buffer, format='PNG')
    return buffer.getvalue()


def stored_photo_ids():
    """Photo IDs in the Photos tab of the saved orders spreadsheet."""
    photos = connect_to_sheets().open_by_key(DATASET_CONFIGS['saved_orders']['spreadsheet_id']).worksheet('Photos')
    return {row[0] for row in photos.rows[1:]}


def saved_order_photos(name):
    order_id = next(o['order_id'] for o in load_all_orders() if o['name'] == name)
    _, order_data, _ = load_order_data(order_id)
    return {product: [p['filename'] for p in photos] for product, photos in order_data['product_photos'].items()}


def save_and_finalize(app, name, overwrite=False):
    app.text_input(key='save_order_name_bottom').input(name)
    if overwrite:
        app.checkbox(key='save_order_overwrite_bottom').check()
    app.button(key='save_order_btn_bottom').click().run()
    assert not app.exception
    assert not app.error, [e.value for e in app.error]


# ---------- #34: every submit gets its own Form Responses row ----------

def test_two_client_submits_get_their_own_rows_and_import_marks_the_right_row(app):
    earlier = response_row(**{'Timestamp': '10/01/2026 09:00:00', 'Company Name *': 'Old Client Co',
                              'Gift Item 1 - Product Name': 'Alpaca Beanie', 'Gift 1 Quantity': '10'})
    responses = form_responses_sheet([earlier])

    acme = open_client_form(send_form_link(app, ['Stoneware Mug']))
    birch = open_client_form(send_form_link(app, ['Woven Market Tote']))
    fill_required(acme, 'Acme Corp')
    fill_required(birch, 'Birch Bakery')
    assert submit(acme) == ''
    assert submit(birch) == ''
    wait_for_rows(responses, 4)

    # The earlier answer is untouched and each client has a row of their own
    assert responses.rows[1] == earlier
    assert [(answers(responses, n)['Company Name *'], answers(responses, n)['Gift Item 1 - Product Name'])
            for n in (2, 3, 4)] == [
        ('Old Client Co', 'Alpaca Beanie'), ('Acme Corp', 'Stoneware Mug'), ('Birch Bakery', 'Woven Market Tote')]

    # Importing Acme marks Acme's row (tracking columns are past column Z), nobody else's
    load_submitted_forms(app)
    select_submitted_form(app, 'Acme Corp')
    import_selected_form(app)
    marked = [n for n in (2, 3, 4) if answers(responses, n)['Imported?'] == 'TRUE']
    assert marked == [3]
    assert answers(responses, 3)['Order ID'].startswith('IMPORTED-')
    assert answers(responses, 3)['Import Date']
    assert 'could not be marked' not in ' '.join(s.value for s in app.success)
    statuses = dict(zip(submitted_forms_table(app)['Company'], submitted_forms_table(app)['Status']))
    assert statuses == {'Acme Corp': 'Imported', 'Birch Bakery': 'Not imported', 'Old Client Co': 'Not imported'}


# ---------- #35: drop-ship acknowledgement, "Other" shipping, required accounting contact ----------

def test_client_form_drop_ship_other_shipping_and_required_accounting_contact(app):
    responses = form_responses_sheet()
    form = open_client_form(send_form_link(app, ['Stoneware Mug']))
    fill_required(form, 'Acme Corp', accounting='')

    # Drop-shipping asks for no file, just tells the client a spreadsheet comes later
    form.selectbox(key='cf_drop_shipping').select('Yes, dropshipped to multiple addresses').run()
    assert not form.get('file_uploader')
    assert any('do not need a recipient spreadsheet right now' in i.value for i in form.info)
    assert form.text_area(key='cf_drop_instructions').label == 'Additional Dropshipping Instructions'

    # "Other" needs the client's own words, and an accounting email or platform is required
    form.selectbox(key='cf_drop_shipping').select('Other').run()
    error = submit(form)
    assert 'Shipping description (Other)' in error
    assert 'Accounting Email or Platform' in error

    form.text_input(key='cf_drop_shipping_other').input('Half to the NYC office, half held for pickup')
    form.text_input(key='cf_accounting_contact').input('accounts at acme').run()
    assert submit(form) == 'Please fill in required fields: a valid Accounting Email Address'

    form.radio(key='cf_accounting_type').set_value('Accounting platform').run()
    form.text_input(key='cf_accounting_contact').input('BillPay.com, account 4417').run()
    assert submit(form) == ''

    wait_for_rows(responses, 2)
    row = answers(responses, 2)
    assert row[DROP_SHIP_COLUMN] == 'Other: Half to the NYC office, half held for pickup'
    assert row[INVOICE_COLUMN] == 'Accounting platform: BillPay.com, account 4417'


# ---------- #36: every answer reaches the order, Tab 3 and Tab 4 agree ----------

def test_every_form_answer_reaches_tab_3_and_tab_4_shows_the_same(app):
    responses = form_responses_sheet()
    form = open_client_form(send_form_link(app, ['Stoneware Mug', 'Woven Market Tote']))
    form.selectbox(key='cf_client_type').select('Existing')
    form.text_input(key='cf_contact_phone').input('555-0100')
    form.text_input(key='cf_notes_0').input('Blue glaze, logo on base')
    form.number_input(key='cf_qty_1').set_value(60)
    form.selectbox(key='cf_drop_shipping').select('Yes, dropshipped to multiple addresses').run()
    form.text_area(key='cf_drop_instructions').input('40 home addresses, list to follow')
    form.selectbox(key='cf_impact_cards').select('No')
    form.selectbox(key='cf_payment_method').select('Check')
    form.text_area(key='cf_special_requests').input('Please gift wrap')
    fill_required(form, 'Acme Corp')  # billing address left blank: same as shipping
    assert submit(form) == ''
    wait_for_rows(responses, 2)

    load_submitted_forms(app)
    select_submitted_form(app, 'Acme Corp')
    import_selected_form(app)

    # Products, with the client's customization notes on the order and the invoice
    items = app.session_state['order_items']
    assert [(i['product_name'], i['quantity'], i['customization_description']) for i in items] == [
        ('Stoneware Mug', 100, 'Blue glaze, logo on base'), ('Woven Market Tote', 60, '')]
    assert app.text_input(key='prod_custom_desc_0').value == 'Blue glaze, logo on base'
    assert 'Stoneware Mug (Customization: Blue glaze, logo on base)' in invoice_lines(app)

    # Client details: Tab 3 and Tab 4 show the same imported values
    expected = {
        'is_new_client': False,
        'company_name': 'Acme Corp',
        'billing_address': '1 Main St, Springfield',  # blank on the form -> shipping address
        'shipping_address': '1 Main St, Springfield',
        'shipping_type': 'Drop Shipping',
        'drop_shipping_instructions': '40 home addresses, list to follow',
        'payment_method': 'Check',
        'client_in_hands_date': date(2026, 12, 1),
        'contact_name_0': 'Jo Smith',
        'contact_email_0': 'jo@acme.example',
        'contact_phone_0': '555-0100',
    }
    for tab in ('t3', 't4'):
        shown = {field: app.get_by_key(f'{tab}_{field}').value for field in expected}
        assert shown == expected, tab
    table_1 = next(t.value for t in app.table if 'Field' in t.value.columns).set_index('Field')['Value']
    assert table_1['Company Billing Address + Email'] == '1 Main St, Springfield | jo@acme.example'

    # Answers with no field of their own land in the notes, the same in both tabs
    team_note = 'Client notes (order form): Please gift wrap\nImpact cards: No'
    bookkeeping_note = 'Send invoice to: Email: ap@acme.example'
    for tab in ('t3', 't4'):
        assert app.text_area(key=f'{tab}_note_internal_pbp_team').value == team_note
        assert app.text_area(key=f'{tab}_note_internal_bookkeeping').value == bookkeeping_note

    # Tab 4 edits carry back to Tab 3
    app.text_area(key='t4_note_external_partners').input('Kitting: gift box with ribbon').run()
    app.text_area(key='t4_billing_address').input('PO Box 9, Springfield').run()
    assert app.text_area(key='t3_note_external_partners').value == 'Kitting: gift box with ribbon'
    assert app.text_area(key='t3_billing_address').value == 'PO Box 9, Springfield'
    assert app.text_area(key='t4_note_internal_pbp_team').value == team_note

    # And Tab 3 edits show in Tab 4
    app.text_area(key='t3_note_external_clients').input('Thank-you card in each box').run()
    assert app.text_area(key='t4_note_external_clients').value == 'Thank-you card in each box'


# ---------- #38: one Save & Finalize button, at the bottom of Tab 3 ----------

def test_tab_3_has_one_save_and_finalize_button_at_the_bottom(app):
    """The bottom of Tab 3 had Confirm Order and Save Order; now one button. The quick save at the top stays."""
    add_product(app, 'Mesa Ceramics', 'Stoneware Mug', 12)
    all_labels = [b.label for b in app.button]
    assert all_labels.count('Save & Finalize Order') == 1
    assert not [label for label in all_labels if label in ('Confirm Order', 'Edit Order')]
    tab_3_labels = [b.label for b in app.tabs[2].button]
    assert tab_3_labels[-1] == 'Save & Finalize Order'
    assert tab_3_labels.count('Save Order') == 1  # the quick save at the top of Tab 3 (keeps the order unfinalized)

    save_and_finalize(app, 'Acme Q4')
    assert app.session_state['order_confirmed'] is True
    assert any(s.value.startswith('This order is finalized') for s in app.success)
    assert [o['name'] for o in load_all_orders()] == ['Acme Q4']


# ---------- #39: Submitted Order Forms tab ----------

def test_submitted_order_forms_list_search_details_and_import(app, monkeypatch):
    responses = form_responses_sheet([
        response_row(**{'Timestamp': '10/02/2026 10:00:00', 'Company Name *': 'Birch Bakery',
                        'Contact Name *': 'Bo Lee', 'Gift Item 1 - Product Name': 'Alpaca Beanie',
                        'Gift 1 Quantity': '20'}),
        response_row(**{'Timestamp': '10/10/2026 10:00:00', 'Company Name *': 'Cedar Clinic',
                        'Contact Name *': 'Cy Park', 'Gift Item 1 - Product Name': '9 oz Raw Honey',
                        'Gift 1 Quantity': '24', 'Imported?': 'TRUE', 'Order ID': 'IMPORTED-1'}),
    ])
    form = open_client_form(send_form_link(app, ['Stoneware Mug']))
    form.text_input(key='cf_notes_0').input('Logo on base')
    fill_required(form, 'Acme Corp')
    assert submit(form) == ''
    wait_for_rows(responses, 4)

    # A later order whose copy into Form Responses has not happened yet (only in the backup tab)
    time.sleep(1)  # a later submit time
    monkeypatch.setattr('src.client_form._sync_in_background', lambda *args: None)
    stuck = open_client_form(send_form_link(app, ['Alpaca Beanie']))
    fill_required(stuck, 'Dune Deli')
    assert submit(stuck) == ''
    assert len(responses.rows) == 4

    # List: newest first, with status
    load_submitted_forms(app)
    table = submitted_forms_table(app)
    assert list(table['Company']) == ['Dune Deli', 'Acme Corp', 'Cedar Clinic', 'Birch Bakery']
    assert list(table['Status']) == ['Waiting to sync', 'Not imported', 'Imported', 'Not imported']

    # Search and filter
    app.text_input(key='submitted_forms_search').input('bo lee').run()
    assert list(submitted_forms_table(app)['Company']) == ['Birch Bakery']
    assert any(c.value == 'Showing 1 of 4 submitted order forms' for c in app.caption)
    app.text_input(key='submitted_forms_search').input('').run()
    app.selectbox(key='submitted_forms_filter').select('Imported').run()
    assert list(submitted_forms_table(app)['Company']) == ['Cedar Clinic']
    app.selectbox(key='submitted_forms_filter').select('All').run()

    # The waiting order can be read but not imported yet
    select_submitted_form(app, 'Dune Deli')
    assert any(h.value == 'Dune Deli' for h in app.subheader)
    assert any(i.value.startswith('This order is still being copied into Form Responses') for i in app.info)
    assert not [b for b in app.button if b.key == 'import_submitted_form']

    # Details of the selected form
    select_submitted_form(app, 'Acme Corp')
    assert any(h.value == 'Acme Corp' for h in app.subheader)
    products = next(t.value for t in app.table if 'Customization notes' in t.value.columns)
    assert products.to_dict('records') == [
        {'Product': 'Stoneware Mug', 'Quantity': 100, 'Customization notes': 'Logo on base'}]
    shown = [t.value for t in app.text]
    assert '1 Main St, Springfield' in shown
    assert 'Same as shipping' in shown
    assert 'Email: ap@acme.example' in shown

    # Import into Tab 3
    import_selected_form(app)
    assert any(s.value.startswith('Imported 1 product(s) from Acme Corp.') for s in app.success)
    assert [i['product_name'] for i in app.session_state['order_items']] == ['Stoneware Mug']
    assert app.session_state['client_info']['company_name'] == 'Acme Corp'
    assert list(submitted_forms_table(app)['Status']) == ['Waiting to sync', 'Imported', 'Imported', 'Not imported']


# ---------- #33 / #40: product photos attach once and survive a reload + re-save ----------

def test_a_photo_attaches_once_and_survives_reloading_and_resaving_the_order(app):
    add_product(app, 'Mesa Ceramics', 'Stoneware Mug', 12)
    app.file_uploader(key='photo_uploader_Stoneware Mug').set_value(('mug.png', png('blue'), 'image/png')).run()
    for qty in (13, 14, 15):  # more clicks: the uploader hands the same file back each time
        app.number_input(key='prod_qty_0').set_value(qty).run()
    assert [p.name for p in app.session_state['product_photos']['Stoneware Mug']] == ['mug.png']
    assert any(c.value == '- Stoneware Mug: 1 photo(s)' for c in app.caption)

    save_and_finalize(app, 'Mug order')
    assert saved_order_photos('Mug order') == {'Stoneware Mug': ['mug.png']}
    assert len(stored_photo_ids()) == 1

    # Saving again in the same session does not upload the photo twice
    app.number_input(key='prod_qty_0').set_value(20).run()
    save_and_finalize(app, 'Mug order', overwrite=True)
    assert saved_order_photos('Mug order') == {'Stoneware Mug': ['mug.png']}
    assert len(stored_photo_ids()) == 1

    # Later, in a new browser: load the order, change it, save it again
    later = start_app()
    order_id = load_all_orders()[0]['order_id']
    later.button(key=f'load_ord_{order_id}').click().run()
    assert not later.exception
    assert [img.captions for img in later.get('image')] == [['mug.png']]  # Tab 4 shows the saved photo
    assert any(c.value == '- Stoneware Mug: 1 photo(s)' for c in later.caption)
    later.number_input(key='prod_qty_0').set_value(30).run()
    save_and_finalize(later, 'Mug order', overwrite=True)
    assert saved_order_photos('Mug order') == {'Stoneware Mug': ['mug.png']}
    assert len(stored_photo_ids()) == 1

    # Same with Tab 3's own Load button and the quick Save Order at the top of Tab 3
    tab_3 = start_app()
    tab_3.button(key='load_order_btn').click().run()
    tab_3.text_input(key='save_order_name').input('Mug order')
    tab_3.checkbox(key='save_order_overwrite').check()
    tab_3.button(key='save_order_btn').click().run()
    assert not tab_3.exception and not tab_3.error
    assert saved_order_photos('Mug order') == {'Stoneware Mug': ['mug.png']}
    assert len(stored_photo_ids()) == 1


# ---------- Client form: the rep's products are fixed lines the client can remove ----------

def test_proposal_form_shows_fixed_lines_the_client_can_remove_and_add_back(app):
    """A form from a saved proposal: every proposal product is a fixed line (no dropdown);
    "Add Another Item" offers only that proposal's products; a saved draft keeps fixed vs added."""
    from src.proposal_manager import save_proposal
    responses = form_responses_sheet()
    products = [('Mesa Ceramics', 'Stoneware Mug'), ('Harbor Weavers', 'Woven Market Tote'),
                ('Highland Knits', 'Alpaca Beanie')]
    proposal = {'proposal_products': [{'product_data': {'Partner': partner, 'Product/Service': name}}
                                      for partner, name in products]}
    saved, _, proposal_id = save_proposal('Acme gifts', '', proposal, 'real')
    assert saved
    link = f'https://example.com/?client_form={proposal_id}&session=abcdefabcdef'

    form = open_client_form(link)
    assert not [s for s in form.selectbox if s.key.startswith('cf_product_')]
    assert [form.number_input(key=f'cf_qty_{i}').value for i in range(3)] == [100, 100, 100]
    assert not [b for b in form.button if b.key == 'cf_add_item']  # every proposal product is already on

    # Remove the tote: the beanie after it keeps its answers
    form.number_input(key='cf_qty_2').set_value(30)
    form.text_input(key='cf_notes_2').input('Navy').run()
    form.button(key='cf_remove_1').click().run()
    assert not form.exception
    assert form.number_input(key='cf_qty_2').value == 30
    assert form.text_input(key='cf_notes_2').value == 'Navy'

    # Add it back from the proposal's products only
    form.button(key='cf_add_item').click().run()
    assert form.selectbox(key='cf_product_3').options == ['-- Select a product --', 'Woven Market Tote']
    form.selectbox(key='cf_product_3').select('Woven Market Tote').run()
    form.number_input(key='cf_qty_3').set_value(60).run()
    form.button(key='cf_save_btn').click().run()
    assert any(s.value.startswith('Progress saved') for s in form.success)

    # The client comes back later: same lines, the added one still has its picker
    later = open_client_form(link)
    assert [s.key for s in later.selectbox if s.key.startswith('cf_product_')] == ['cf_product_2']
    assert later.selectbox(key='cf_product_2').value == 'Woven Market Tote'
    assert [later.number_input(key=f'cf_qty_{i}').value for i in range(3)] == [100, 30, 60]
    fill_required(later, 'Acme Corp')
    assert submit(later) == ''

    wait_for_rows(responses, 2)
    row = answers(responses, 2)
    assert [(row[f'Gift Item {i} - Product Name'], row[f'Gift {i} Quantity']) for i in (1, 2, 3)] == [
        ('Stoneware Mug', '100'), ('Alpaca Beanie', '30'), ('Woven Market Tote', '60')]
    assert row['Gift 2 Customization Notes'] == 'Navy'
