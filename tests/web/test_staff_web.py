"""
Staff screens (login, order editor, accounting, responses) through the FastAPI
test client. Google Sheets is replaced by in-memory fakes.
"""

import json
import re

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from pbp import settings
from pbp.services import order as svc
from pbp.sheets import catalog, order_manager, proposal_manager
from pbp.web import app as web
from pbp.web import staff, state
from test_order_service import HONEY, HOODIE

PARTNER_INFO = pd.DataFrame([{"Partner": "GOEX", "POC Name": "Pat", "POC Email": "pat@goex.com", "POC Phone": "555"}])


class FakeStore:
    """Stand-in for the saved_orders / saved_proposals sheets."""

    def __init__(self):
        self.orders = {}
        self.proposals = {"PROP_1": ("Spring", {"proposal_products": [{"product_data": HONEY, "quantity": 200, "markup_percent": 80.0}]})}

    def save_order(self, name, created_by, order_data, dataset, photos_by_product=None, overwrite=False):
        if name in {v[0] for v in self.orders.values()} and not overwrite:
            return False, f"Order '{name}' already exists.", f"{name} (v2)"
        order_id = next((k for k, v in self.orders.items() if v[0] == name), f"ORDER_{len(self.orders) + 1}")
        if photos_by_product:
            order_data["product_photos"] = {p: [{"file_id": f"id{i}", "filename": f["filename"]} for i, f in enumerate(files)] for p, files in photos_by_product.items()}
        self.orders[order_id] = (name, json.loads(json.dumps(order_data, default=str)))
        return True, f"Order '{name}' saved successfully!", order_id

    def load_all_orders(self):
        return [{"order_id": k, "name": v[0], "created_by": "", "created_date": "2026-10-13 10:00:00", "dataset": "real"} for k, v in self.orders.items()]

    def load_order_data(self, order_id):
        return (True, self.orders[order_id][1], "real") if order_id in self.orders else (False, None, None)

    def delete_order(self, order_id):
        return (True, "Order deleted successfully") if self.orders.pop(order_id, None) else (False, "Order not found")

    def load_all_proposals(self):
        return [{"proposal_id": k, "name": v[0], "created_by": "", "created_date": "2026-10-01 09:00:00", "dataset": "real"} for k, v in self.proposals.items()]

    def load_proposal_data(self, proposal_id):
        return (True, self.proposals[proposal_id][1], "real") if proposal_id in self.proposals else (False, None, None)


@pytest.fixture
def store(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(catalog, "load_pricing_data", lambda dataset="real", force=False: (pd.DataFrame([HOODIE, HONEY]), pd.DataFrame(), PARTNER_INFO))
    for name in ("save_order", "load_all_orders", "load_order_data", "delete_order"):
        monkeypatch.setattr(order_manager, name, getattr(fake, name))
    for name in ("load_all_proposals", "load_proposal_data"):
        monkeypatch.setattr(proposal_manager, name, getattr(fake, name))
    monkeypatch.setattr(settings, "SYNC_LOOP_SECONDS", 0)
    state._orders.clear(), state._photos.clear(), state._meta.clear()
    return fake


@pytest.fixture
def http(store):
    with TestClient(web.app, follow_redirects=False) as client:
        client.post("/login", data={"password": settings.APP_PASSWORD}, follow_redirects=False)
        yield client


def _current(http):
    """The working order of the test client's session."""
    from pbp.web import auth
    sid = auth._signer.unsign(http.cookies.get(auth.COOKIE)).decode()
    return state.order(sid)


def test_login_gate_and_wrong_password(store):
    with TestClient(web.app, follow_redirects=False) as anon:
        response = anon.get("/orders", follow_redirects=False)
        assert response.status_code == 303 and response.headers["location"].startswith("/login")
        bad = anon.post("/login", data={"password": "nope"})
        assert bad.status_code == 401 and "Incorrect password" in bad.text
        good = anon.post("/login", data={"password": settings.APP_PASSWORD, "next": "/orders/current"}, follow_redirects=False)
        assert good.status_code == 303 and good.headers["location"] == "/orders/current"
        assert anon.get("/orders").status_code == 200


def test_editor_lists_catalog_and_adds_product(http):
    page = http.get("/orders/current")
    assert page.status_code == 200
    assert "GOEX" in page.text and "No products in order yet" in page.text

    response = http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie", "use_msrp": "on", "variant": "Large"})
    assert response.status_code == 303
    page = http.get("/orders/current").text
    assert "Added Unisex Fleece Hoodie - Large to order" in page
    assert 'id="item-0"' in page and "Base Product: Unisex Fleece Hoodie" in page
    order = _current(http)
    assert order["order_items"][0]["selected_variant"] == "Large" and order["order_items"][0]["quantity"] == 1
    assert "WARNING: Qty = 1" in page

    options = http.get("/catalog/products?partner=Bee Co").text
    assert "9 oz Hot Honey" in options and "Hoodie" not in options


def test_item_update_via_htmx_returns_card_and_summary(http):
    http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie", "use_msrp": "on"})
    form = {"quantity": "120", "markup_percent": "100.0", "client_price": "50.00", "include_customization": "on",
            "customization_description": "Logo", "customization_setup_fee": "50", "customization_per_unit": "1.5",
            "partner_customization_setup_fee": "20", "partner_customization_per_unit": "0.5"}
    response = http.post("/orders/current/items/0", data=form, headers={"HX-Request": "true", "HX-Trigger-Name": "quantity"})
    assert response.status_code == 200
    assert 'id="item-0"' in response.text and 'hx-swap-oob="true"' in response.text
    item = _current(http)["order_items"][0]
    assert item["quantity"] == 120 and item["customization_unit_total"] == 180.0
    assert "$6230.00" in response.text  # product_total in the pricing breakdown totals

    # Typing a client price sets the markup instead
    response = http.post("/orders/current/items/0", data=dict(form, client_price="55.00"), headers={"HX-Request": "true", "HX-Trigger-Name": "client_price"})
    assert _current(http)["order_items"][0]["markup_percent"] == 120.0
    assert 'value="120.0"' in response.text

    # Add-on round trip
    response = http.post("/orders/current/items/0/addons", data=form, headers={"HX-Request": "true"})
    assert 'name="addon_0_name"' in response.text
    http.post("/orders/current/items/0", data=dict(form, addon_0_name="Second Color", addon_0_client_perunit="0.25"), headers={"HX-Request": "true", "HX-Trigger-Name": "addon_0_name"})
    assert _current(http)["order_items"][0]["customization_unit_total"] == (1.5 + 0.25) * 120
    http.post("/orders/current/items/0/addons/0/remove", headers={"HX-Request": "true"})
    assert _current(http)["order_items"][0]["customization_addons"] == []

    # Without HTMX the same post redirects back to the editor
    assert http.post("/orders/current/items/0", data=form, follow_redirects=False).status_code == 303


def test_settings_discount_and_summary(http):
    http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    http.post("/orders/current/items/0", data={"quantity": "100", "markup_percent": "100"}, headers={"HX-Request": "true"})
    response = http.post("/orders/current/settings", data={"discount_option": "Non-profit (5%)", "fifty_cent_rounding": "on", "apply_cc_fee": "on", "cc_fee_percent": "3.0",
                                                           "order_shipping": "40", "internal_pbp_team": "Rush"}, headers={"HX-Request": "true"})
    assert response.status_code == 200
    order = _current(http)
    assert order["order_discount_type"] == "preset" and order["order_shipping"] == 40.0 and order["order_notes"]["internal_pbp_team"] == "Rush"
    t = svc.totals(order)
    assert t["discount_amount"] == 250.0
    assert f"${t['total_quote']:.2f}" in response.text and "Discount (Non-profit Discount (5%))" in response.text


def test_custom_items_and_remove_and_clear(http):
    http.post("/orders/current/items", data={"action": "custom_product", "name": "Engraving", "partner": "Custom/Other", "base_cost": "4"})
    http.post("/orders/current/items", data={"action": "custom_line", "name": "Rush", "quantity": "1", "description": "Expedite", "total_price": "50"})
    bad = http.post("/orders/current/items", data={"action": "custom_line", "name": "", "total_price": "0"})
    assert bad.status_code == 303
    page = http.get("/orders/current").text
    assert "Custom product" in page and "Custom line item: Expedite" in page and "Please fill in Product/Service Name" in page
    assert len(_current(http)["order_items"]) == 2
    http.post("/orders/current/items/1/remove")
    assert len(_current(http)["order_items"]) == 1
    http.post("/orders/current/clear")
    assert _current(http)["order_items"] == []


def test_client_info_contacts_and_confirm(http):
    http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    data = {"company_name": "Acme", "is_new_client": "on", "shipping_type": "One Location", "shipping_address": "1 Main St",
            "payment_timeline": "Custom", "custom_payment_terms": "Net 45", "payment_preference": "ACH", "ship_method": "Air",
            "contact_name_0": "Jo", "contact_email_0": "jo@acme.com", "contact_phone_0": "", "contact_role_0": "Primary Contact",
            "client_in_hands_date": "2026-11-01", "order_submitted_by": "Nico", "action": "add_contact"}
    response = http.post("/orders/current/client", data=data, headers={"HX-Request": "true"})
    assert response.status_code == 200
    client = _current(http)["client_info"]
    assert client["company_name"] == "Acme" and client["payment_timeline"] == "Net 45" and client["ship_method"] == "Air"
    assert len(client["contacts"]) == 2 and client["contacts"][0]["email"] == "jo@acme.com"
    assert str(client["client_in_hands_date"]) == "2026-11-01"
    http.post("/orders/current/client", data=dict(data, action="confirm"), headers={"HX-Request": "true"})
    assert _current(http)["order_confirmed"] is True


def test_save_load_delete_round_trip(http, store):
    http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    http.post("/orders/current/items/0", data={"quantity": "40", "markup_percent": "100"}, headers={"HX-Request": "true"})
    http.post("/orders/current/photos", files=[("photos", ("mock.png", b"\x89PNG", "image/png"))], data={"product": "Unisex Fleece Hoodie"})
    assert http.get("/orders/current/photos/Unisex%20Fleece%20Hoodie/0").status_code == 200

    response = http.post("/orders/current/save", data={"name": "Acme Q4", "created_by": "Nico"})
    assert response.status_code == 303
    assert list(store.orders.values())[0][0] == "Acme Q4"
    saved = list(store.orders.values())[0][1]
    assert saved["order_items"][0]["quantity"] == 40 and saved["product_photos"]["Unisex Fleece Hoodie"][0]["filename"] == "mock.png"
    assert "order_fifty_cent_rounding" in saved
    home = http.get("/orders").text
    assert "Acme Q4" in home and "saved successfully" in home

    # Duplicate name without overwrite is refused; with overwrite it updates in place
    http.post("/orders/current/save", data={"name": "Acme Q4"})
    assert "already exists" in http.get("/orders/current").text
    http.post("/orders/current/save", data={"name": "Acme Q4", "overwrite": "on"})
    assert len(store.orders) == 1

    # New order, then load the saved one back
    http.post("/orders/new")
    assert _current(http)["order_items"] == []
    http.post("/orders/load/ORDER_1")
    assert _current(http)["order_items"][0]["quantity"] == 40
    assert "Loaded order: Acme Q4" in http.get("/orders/current").text
    http.post("/orders/delete/ORDER_1")
    assert store.orders == {}


def test_import_proposal(http):
    response = http.post("/orders/current/import-proposal/PROP_1", follow_redirects=False)
    assert response.status_code == 303
    item = _current(http)["order_items"][0]
    assert item["product_name"] == "9 oz Hot Honey" and item["quantity"] == 200 and item["markup_percent"] == 80.0
    assert item["source"] == "proposal" and item["base_price"] == 9.0
    assert "Imported 1 product(s) from the proposal" in http.get("/orders/current").text


def test_accounting_page_and_downloads(http):
    http.post("/orders/current/items", data={"action": "catalog", "partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    http.post("/orders/current/items/0", data={"quantity": "100", "markup_percent": "100", "include_kitting": "on", "kitting_quantity": "1", "kitting_pbp_cost": "10", "kitting_client_price": "20", "kitting_description": "Gift box"}, headers={"HX-Request": "true"})
    page = http.get("/orders/current/accounting")
    assert page.status_code == 200
    assert "field(s) need attention" in page.text
    assert "Pat &lt;pat@goex.com&gt;" in page.text  # partner POC from the catalog's Partner-Specific Info
    assert "Gift box" in page.text and "$5000.00" in page.text

    http.post("/orders/current/accounting", data={"description_0": "Hoodies for the team", "partner_in_hands_0": "2026-10-20",
                                                  "poc_name__GOEX": "Sam", "poc_email__GOEX": "sam@goex.com", "poc_phone__GOEX": "", "ship__GOEX": "Ground only"})
    page = http.get("/orders/current/accounting").text
    assert "Hoodies for the team" in page and "Sam &lt;sam@goex.com&gt;" in page and "Ground only" in page

    csv_response = http.get("/orders/current/invoice.csv")
    assert csv_response.status_code == 200 and "attachment" in csv_response.headers["content-disposition"]
    assert "Hoodies for the team" in csv_response.text and ",TOTAL," in csv_response.text
    html_response = http.get("/orders/current/invoice.html")
    assert "INVOICE AND PURCHASE ORDER REQUEST FORM" in html_response.text and "2026-10-20" in html_response.text
    assert http.get("/orders/current/summary.csv").text.splitlines()[0].startswith("Item,Qty")


def test_responses_list_and_import(http, monkeypatch):
    from test_client_form import LIVE_HEADERS
    row = {h: "" for h in LIVE_HEADERS}
    row.update({"Timestamp": "10/13/2026 10:00:00", "Company Name *": "Acme Corp", "Contact Name *": "Jo", "Contact Email *": "jo@acme.com",
                "Gift Item 1 - Product Name": "Unisex Fleece Hoodie", "Gift 1 Quantity": "25", "Gift 1 Customization Notes": "Navy",
                "Gift Item 2 - Product Name": "Mystery Item", "Gift 2 Quantity": "3",
                "Shipping Address *": "1 Main St", "In-Hands Date (When do you need this order?) *": "2026-11-01",
                "Payment Preference *": "Net 30", "Payment Method *": "ACH", "Imported?": ""})
    marked = []
    monkeypatch.setattr(staff, "load_form_responses", lambda gc: pd.DataFrame([row]))
    monkeypatch.setattr(staff, "mark_response_imported", lambda gc, row_number, order_id, imported_by="": marked.append((row_number, order_id)) or True)
    monkeypatch.setattr(staff.gateway, "connect", lambda: object())

    page = http.get("/responses?show=new")
    assert page.status_code == 200 and "Acme Corp" in page.text and "Unisex Fleece Hoodie (Qty: 25)" in page.text
    response = http.post("/responses/import", data={"row_number": "2"}, follow_redirects=False)
    assert response.status_code == 303
    order = _current(http)
    assert order["client_info"]["company_name"] == "Acme Corp" and order["order_items"][0]["quantity"] == 25
    assert marked and marked[0][0] == 2
    editor = http.get("/orders/current").text
    assert "Imported 1 product(s) from Acme Corp" in editor and "Could not match: Mystery Item" in editor
