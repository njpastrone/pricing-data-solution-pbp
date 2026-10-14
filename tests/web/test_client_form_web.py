"""
End-to-end tests for the FastAPI client order form, against an in-memory
Google Sheets fake (nothing touches a real spreadsheet).

Covers the phase 1 checklist: legacy link redirect, draft save and resume,
add item (HTMX partial and no-JS fallback), submit, duplicate submit, "Other"
shipping and accounting contact answers, header mismatch, health endpoint.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pbp import settings
from pbp.sheets import gateway
from pbp.sheets.client_form import STATUS_PENDING, STATUS_SUBMITTED
from pbp.web import app as web
from test_client_form import DRAFT_HEADERS, LIVE_HEADERS, FakeSheet

PROPOSAL_ID = "PROP_20260524_143022"
SESSION = "abc123def456"
PROPOSAL_ROW = [PROPOSAL_ID, "Spring Gifts", "Nico", "2026-05-24 14:30:22", "real", json.dumps({
    "proposal_products": [
        {"product_data": {"Product/Service": "Unisex Fleece Hoodie", "Partner": "GOEX"}},
        {"product_data": {"Product/Service": "9 oz Hot Honey", "Partner": "Bee Co"}},
        {"product_data": {"Product/Service": "Tote Bag", "Partner": "Weavers"}},
    ]
})]

FILLED = {
    "client_type": "New", "company_name": "Acme Corp", "contact_name": "Jo Smith",
    "contact_email": "jo@acme.com", "contact_phone": "555-1234",
    "product_0": "Unisex Fleece Hoodie", "quantity_0": "25", "notes_0": "Navy, white logo",
    "product_1": "", "quantity_1": "100", "notes_1": "",
    "shipping_address": "123 Main St", "billing_address": "", "drop_shipping": "No",
    "drop_shipping_instructions": "", "in_hands_date": "2026-11-01",
    "impact_cards": "Yes", "payment_method": "ACH", "accounting_contact_type": "Email",
    "accounting_contact": "ap@acme.com", "notes": "Rush please",
}


@pytest.fixture
def sheets():
    """Fake proposals, drafts and Form Responses sheets wired into the gateway; no sleeping."""
    gateway.reset()
    proposals = FakeSheet([["Proposal_ID", "Proposal_Name", "Created_By", "Created_Date", "Dataset", "Proposal_Data_JSON"], PROPOSAL_ROW])
    drafts = FakeSheet([DRAFT_HEADERS])
    responses = FakeSheet([LIVE_HEADERS])

    books = {
        settings.SAVED_PROPOSALS_SHEET_ID: MagicMock(**{"worksheet.return_value": proposals}),
        settings.SAVED_ORDERS_SHEET_ID: MagicMock(**{"worksheet.return_value": drafts}),
        settings.FORM_RESPONSES_SHEET_ID: MagicMock(**{"worksheet.return_value": responses}),
    }
    client = MagicMock()
    client.open_by_key.side_effect = books.__getitem__

    with patch("pbp.sheets.gateway.connect", return_value=client), \
         patch("pbp.sheets.gateway.time.sleep"), \
         patch("pbp.sheets.client_form.time.sleep"), \
         patch("pbp.sheets.client_form._sync_in_background", side_effect=web.client_form.sync_submission):
        yield {"proposals": proposals, "drafts": drafts, "responses": responses}
    gateway.reset()


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(settings, "SYNC_LOOP_SECONDS", 0)  # no background loop inside tests
    with TestClient(web.app) as client:
        yield client


FORM_URL = f"/form/{PROPOSAL_ID}?session={SESSION}"


def _response_rows(responses):
    return [dict(zip(LIVE_HEADERS, row)) for row in responses.rows[1:]]


def _draft(drafts):
    assert len(drafts.rows) == 2, drafts.rows
    return json.loads(drafts.rows[1][2]), drafts.rows[1][7]


def test_legacy_link_redirects_to_form(http, sheets):
    response = http.get(f"/?client_form={PROPOSAL_ID}&session={SESSION}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == FORM_URL


def test_form_shows_proposal_products_and_one_empty_item(http, sheets):
    response = http.get(FORM_URL)
    assert response.status_code == 200
    assert "Spring Gifts" in response.text
    assert "Unisex Fleece Hoodie" in response.text and "Tote Bag" in response.text
    assert response.text.count("<legend>Item") == 1
    assert "Add Another Item" in response.text


def test_missing_session_or_unknown_proposal_show_an_error(http, sheets):
    assert http.get(f"/form/{PROPOSAL_ID}").status_code == 400
    response = http.get(f"/form/PROP_NOPE?session={SESSION}")
    assert response.status_code == 404
    assert "no longer available" in response.text


def test_save_progress_persists_and_reload_shows_values(http, sheets):
    response = http.post(FORM_URL, data=FILLED)
    assert response.status_code == 200
    assert "Progress saved" in response.text

    form, status = _draft(sheets["drafts"])
    assert status == "draft"
    assert form["client_info"]["company_name"] == "Acme Corp"
    assert form["products"] == [{"name": "Unisex Fleece Hoodie", "quantity": 25, "customization_notes": "Navy, white logo"}]
    assert _response_rows(sheets["responses"]) == []  # a draft is not an order

    reloaded = http.get(FORM_URL).text
    assert 'value="Acme Corp"' in reloaded
    assert 'value="Navy, white logo"' in reloaded
    assert reloaded.count("<legend>Item") == 2  # saved item + one empty row


def test_add_item_partial_keeps_typed_values(http, sheets):
    response = http.post(f"/form/{PROPOSAL_ID}/items?session={SESSION}", data=FILLED)
    assert response.status_code == 200
    assert response.text.count("<legend>Item") == 3
    assert 'value="Navy, white logo"' in response.text
    assert len(sheets["drafts"].rows) == 1  # nothing saved by adding a row


def test_add_item_without_javascript_rerenders_full_page(http, sheets):
    response = http.post(FORM_URL, data=dict(FILLED, action="add_item"))
    assert response.text.count("<legend>Item") == 3
    assert "Peace by Piece International Order Form" in response.text
    assert len(sheets["drafts"].rows) == 1


def test_add_item_stops_at_number_of_proposal_products(http, sheets):
    three_rows = dict(FILLED, product_2="", quantity_2="1", notes_2="")
    response = http.post(f"/form/{PROPOSAL_ID}/items?session={SESSION}", data=three_rows)
    assert response.text.count("<legend>Item") == 3
    assert "Add Another Item" not in response.text


def test_submit_requires_fields_and_keeps_input(http, sheets):
    response = http.post(FORM_URL, data=dict(FILLED, action="submit", company_name="", product_0=""))
    assert response.status_code == 200
    assert "Please fill in required fields: At least one product, Company Name" in response.text
    assert 'value="Jo Smith"' in response.text  # typed values kept
    assert _response_rows(sheets["responses"]) == []


def test_submit_writes_form_responses_and_shows_received(http, sheets):
    response = http.post(FORM_URL, data=dict(FILLED, action="submit"))
    assert "Order received" in response.text

    rows = _response_rows(sheets["responses"])
    assert len(rows) == 1
    assert rows[0]["Company Name *"] == "Acme Corp"
    assert rows[0]["Gift Item 1 - Product Name"] == "Unisex Fleece Hoodie"
    assert rows[0]["Gift 1 Quantity"] == "25"
    assert rows[0]["In-Hands Date (When do you need this order?) *"] == "2026-11-01"
    assert _draft(sheets["drafts"])[1] == STATUS_SUBMITTED

    # The link now shows the receipt and a second submit changes nothing
    assert "Order received" in http.get(FORM_URL).text
    http.post(FORM_URL, data=dict(FILLED, action="submit", notes="Changed my mind"))
    assert len(_response_rows(sheets["responses"])) == 1


def test_other_shipping_and_accounting_contact_reach_form_responses(http, sheets):
    data = dict(FILLED, drop_shipping="Other", drop_shipping_other="Half to Boston, half to Denver",
                accounting_contact_type="Accounting platform", accounting_contact="BillPay.com, account 42")
    response = http.post(FORM_URL, data=data)
    assert "Progress saved" in response.text
    page = http.get(FORM_URL).text
    assert '<option value="Other" selected>' in page
    assert 'value="Half to Boston, half to Denver"' in page

    http.post(FORM_URL, data=dict(data, action="submit"))
    row = _response_rows(sheets["responses"])[0]
    assert row["Will this order be drop-shipped to individual recipients? *"] == "Other: Half to Boston, half to Denver"
    invoice_column = [h for h in LIVE_HEADERS if h.startswith("Is there a specific platform or email")][0]
    assert row[invoice_column] == "Accounting platform: BillPay.com, account 42"


def test_submit_requires_accounting_contact_and_other_description(http, sheets):
    response = http.post(FORM_URL, data=dict(FILLED, action="submit", accounting_contact="not-an-email",
                                             drop_shipping="Other", drop_shipping_other=""))
    assert "Shipping description (Other)" in response.text
    assert "a valid Accounting Email Address" in response.text
    response = http.post(FORM_URL, data=dict(FILLED, action="submit", accounting_contact=""))
    assert "Accounting Email or Platform" in response.text
    assert len(sheets["responses"].rows) == 1  # nothing submitted


def test_header_mismatch_keeps_order_pending_and_health_reports_it(http, sheets):
    sheets["responses"].rows = [[h for h in LIVE_HEADERS if "Gift" not in h]]
    response = http.post(FORM_URL, data=dict(FILLED, action="submit"))
    assert "Order received" in response.text  # the client never sees a Sheets problem
    assert _draft(sheets["drafts"])[1] == STATUS_PENDING
    assert len(sheets["responses"].rows) == 1

    # Still pending after the 10-minute grace period: the sync loop flags it
    backup = json.loads(sheets["drafts"].rows[1][2])
    backup["submitted_at"] = "01/01/2026 09:00:00"
    sheets["drafts"].rows[1][2] = json.dumps(backup)
    web.run_pending_syncs()
    health = http.get("/internal/health")
    assert health.status_code == 503
    body = health.json()
    assert body["status"] == "degraded"
    assert body["sync"]["stuck_orders"][0]["proposal_id"] == PROPOSAL_ID


def test_health_ok_when_nothing_is_pending(http, sheets):
    web.run_pending_syncs()
    health = http.get("/internal/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["sync"]["runs"] >= 1
