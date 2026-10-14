"""Demo mode (PBP_DEMO=1): every screen renders from the in-memory sample data, and nothing needs Google."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pbp import demo, settings
from pbp.sheets import client_form, gateway, templates
from pbp.web import app as web
from pbp.web import state


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(settings, "SYNC_LOOP_SECONDS", 0)
    real_connect, real_list, real_path = gateway.connect, templates.list_templates, templates.template_path
    real_notify = client_form.notify_team_of_order
    demo.install()
    state._orders.clear(), state._proposals.clear(), state._scenarios.clear(), state._photos.clear(), state._meta.clear()
    try:
        with TestClient(web.app, follow_redirects=False) as client:
            client.post("/login", data={"password": settings.APP_PASSWORD})
            yield client
    finally:
        gateway.connect, templates.list_templates, templates.template_path = real_connect, real_list, real_path
        client_form.notify_team_of_order = real_notify
        gateway.reset()


def test_demo_data_reaches_every_screen(http):
    assert "Riverbend Health - Holiday Gifts" in http.get("/proposals").text
    editor = http.get("/proposals/current").text
    assert "Unisex Fleece Hoodie" in editor
    assert "Kitenge Tote Bag" in editor
    http.post("/proposals/load/PROP_20260915_101500")
    assert "bundled demo copy" in http.get("/proposals/current").text  # template picker shows once the proposal has products
    assert "Riverbend Health - 120 hoodies" in http.get("/orders").text
    responses = http.get("/responses").text
    assert "Northwind Partners" in responses and "Imported" in responses and "Short Sleeve Tee (Qty: 60)" in responses
    assert "GOEX" in http.get("/exec").text

    http.post("/orders/load/ORDER_20260920_160000")
    accounting = http.get("/orders/current/accounting").text
    assert "Pat Rivera &lt;pat@goex.org&gt;" in accounting and "Riverbend Health" in accounting and "$3000.00" in accounting
    assert ",TOTAL," in http.get("/orders/current/invoice.csv").text

    # The seeded client form submission is readable from the client link too
    form = http.get("/form/PROP_20260928_143000?session=demo12345678").text
    assert "Order received" in form
    draft = http.get("/form/PROP_20260915_101500?session=demoabcdefgh").text
    assert 'value="Riverbend Health"' in draft and "Unisex Fleece Hoodie" in draft

    # Writes stay in memory: saving a proposal then loading it back works
    http.post("/proposals/load/PROP_20260928_143000")
    http.post("/proposals/current/save", data={"name": "Northwind Partners - Welcome Kits", "overwrite": "on"})
    assert "updated successfully" in http.get("/proposals/current").text


def test_demo_client_form_submit_lands_in_form_responses_without_email(http):
    data = {
        "client_type": "Existing", "company_name": "Riverbend Health", "contact_name": "Maria Chen",
        "contact_email": "maria.chen@riverbendhealth.org", "contact_phone": "",
        "product_0": "Unisex Fleece Hoodie", "quantity_0": "40", "notes_0": "",
        "shipping_address": "1 River Rd", "billing_address": "", "drop_shipping": "No",
        "drop_shipping_instructions": "", "in_hands_date": "2026-12-01", "impact_cards": "Yes",
        "payment_method": "ACH", "accounting_contact_type": "Email", "accounting_contact": "ap@riverbendhealth.org",
        "notes": "", "action": "submit",
    }
    smtp_settings = {"ORDER_NOTIFY_EMAILS": "team@example.com", "SMTP_HOST": "smtp.example.com"}
    with patch.dict(os.environ, smtp_settings), patch("pbp.sheets.client_form.smtplib.SMTP") as smtp, \
         patch("pbp.sheets.client_form._sync_in_background", side_effect=client_form.sync_submission):
        response = http.post("/form/PROP_20260915_101500?session=demoabcdefgh", data=data)
    assert "Order received" in response.text
    assert "Unisex Fleece Hoodie (Qty: 40)" in http.get("/responses").text
    smtp.assert_not_called()
