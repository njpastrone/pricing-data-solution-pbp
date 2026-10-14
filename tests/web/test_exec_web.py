"""Executive Pricing Tool screen and Reset session through the FastAPI test client."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from pbp import settings
from pbp.sheets import catalog
from pbp.web import app as web
from pbp.web import auth, state
from test_order_service import HONEY, HOODIE


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(catalog, "load_pricing_data", lambda dataset="real", force=False: (pd.DataFrame([HOODIE, HONEY]), pd.DataFrame(), pd.DataFrame()))
    monkeypatch.setattr(settings, "SYNC_LOOP_SECONDS", 0)
    state._orders.clear(), state._proposals.clear(), state._scenarios.clear(), state._photos.clear(), state._meta.clear()
    with TestClient(web.app, follow_redirects=False) as client:
        client.post("/login", data={"password": settings.APP_PASSWORD})
        yield client


def _sid(http):
    return auth._signer.unsign(http.cookies.get(auth.COOKIE)).decode()


def test_exec_tool_add_update_summary_and_imports(http):
    page = http.get("/exec")
    assert page.status_code == 200 and "No products added yet" in page.text and "GOEX" in page.text

    http.post("/exec/products", data={"partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    page = http.get("/exec").text
    assert "Added Unisex Fleece Hoodie" in page and 'id="exec-0"' in page and "$5000.00" in page
    http.post("/exec/products", data={"partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    assert "Product already added" in http.get("/exec").text

    response = http.post("/exec/products/0", data={"quantity": "200", "markup_percent": "100", "client_price": "50.00", "include_tariffs": "on",
                                                   "tariff_input_method": "percentage", "tariff_rate": "4"}, headers={"HX-Request": "true", "HX-Trigger-Name": "quantity"})
    assert response.status_code == 200 and 'hx-swap-oob="true"' in response.text
    product = state.exec_scenario(_sid(http))["products"][0]
    assert product["quantity"] == 200 and product["include_tariffs"] and product["tariff_rate"] == 4.0
    assert "Tariff (4.0% - USA)" in response.text

    http.post("/exec/products/0", data={"quantity": "200", "markup_percent": "100", "client_price": "60.00"}, headers={"HX-Request": "true", "HX-Trigger-Name": "client_price"})
    assert product["markup_percent"] == 140.0

    response = http.post("/exec/settings", data={"shipping": "100", "cc_fee": "on", "cc_fee_percent": "3.0"}, headers={"HX-Request": "true"})
    scenario = state.exec_scenario(_sid(http))
    assert scenario["shipping"] == 100.0 and scenario["cc_fee"] is True and "Credit Card Fee (3.0%)" in response.text
    assert http.get("/exec/summary.csv").text.splitlines()[-1].startswith("TOTAL,200 units")

    http.post("/exec/import/proposal")
    assert state.proposal(_sid(http))["proposal_products"][0]["markup_percent"] == 140.0
    http.post("/exec/import/order")
    assert state.order(_sid(http))["order_items"][0]["quantity"] == 200
    http.post("/exec/products/0/remove")
    assert state.exec_scenario(_sid(http))["products"] == []


def test_reset_session_clears_everything(http):
    http.post("/exec/products", data={"partner": "GOEX", "product": "Unisex Fleece Hoodie"})
    http.post("/exec/import/order")
    assert state.order(_sid(http))["order_items"]
    response = http.post("/reset")
    assert response.status_code == 303 and response.headers["location"] == "/orders"
    assert state.order(_sid(http))["order_items"] == [] and state.exec_scenario(_sid(http))["products"] == []
    assert "Session reset" in http.get("/orders").text
