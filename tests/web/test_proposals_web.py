"""Proposal editor, PowerPoint review and client form link through the FastAPI test client (Sheets and Drive faked)."""

import json
import os
import time

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from pbp import settings
from pbp.sheets import catalog, client_form, match_memory, proposal_manager, templates
from pbp.web import app as web
from pbp.web import state
from test_order_service import HONEY, HOODIE

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DECK = os.path.join(REPO, "templates", "November All Slides.pptx")
COFFEE = dict(HOODIE, **{"Product/Service": "1951 Coffee", "Partner": "1951 Coffee", "Country of Origin (Ships From)": "Kenya"})
TEMPLATE = {"name": "November All Slides.pptx", "file_id": "local", "modified_time": "2026-10-01T00:00:00Z"}


class FakeProposals:
    def __init__(self):
        self.rows = {}
        self.drafts = []
        self.saved_matches = []

    def save_proposal(self, name, created_by, proposal_data, dataset, overwrite=False):
        if name in {v[0] for v in self.rows.values()} and not overwrite:
            return False, f"Proposal '{name}' already exists.", f"{name} (v2)"
        pid = next((k for k, v in self.rows.items() if v[0] == name), f"PROP_{len(self.rows) + 1}")
        self.rows[pid] = (name, json.loads(json.dumps(proposal_data, default=str)))
        return True, f"Proposal '{name}' saved successfully!", pid

    def load_all_proposals(self):
        return [{"proposal_id": k, "name": v[0], "created_by": "", "created_date": "2026-10-01 09:00:00", "dataset": "real"} for k, v in self.rows.items()]

    def load_proposal_data(self, pid):
        return (True, self.rows[pid][1], "real") if pid in self.rows else (False, None, None)

    def delete_proposal(self, pid):
        return (True, "Proposal deleted successfully") if self.rows.pop(pid, None) else (False, "Proposal not found")


@pytest.fixture
def fake(monkeypatch):
    store = FakeProposals()
    monkeypatch.setattr(catalog, "load_pricing_data", lambda dataset="real", force=False: (pd.DataFrame([COFFEE, HOODIE, HONEY]), pd.DataFrame(), pd.DataFrame()))
    for name in ("save_proposal", "load_all_proposals", "load_proposal_data", "delete_proposal"):
        monkeypatch.setattr(proposal_manager, name, getattr(store, name))
    monkeypatch.setattr(templates, "list_templates", lambda force=False: [TEMPLATE])
    monkeypatch.setattr(templates, "template_path", lambda template: DECK)
    monkeypatch.setattr(templates, "impact_slide_mapping", lambda force=False: {})
    monkeypatch.setattr(match_memory, "get_confirmed_match", lambda *a, **k: None)
    monkeypatch.setattr(match_memory._load_all_matches_data, "clear", lambda: None)
    monkeypatch.setattr(match_memory, "save_confirmed_match", lambda **kw: store.saved_matches.append(kw) or (True, "saved"))
    monkeypatch.setattr(client_form, "save_draft", lambda pid, token, data, *a, **k: store.drafts.append((pid, token, data)) or (True, "Draft saved"))
    monkeypatch.setattr(settings, "SYNC_LOOP_SECONDS", 0)
    monkeypatch.setattr(settings, "CLIENT_FORM_BASE_URL", "http://forms.test/")
    state._orders.clear(), state._proposals.clear(), state._photos.clear(), state._meta.clear()
    return store


@pytest.fixture
def http(fake):
    with TestClient(web.app, follow_redirects=False) as client:
        client.post("/login", data={"password": settings.APP_PASSWORD})
        yield client


def _proposal(http):
    from pbp.web import auth
    return state.proposal(auth._signer.unsign(http.cookies.get(auth.COOKIE)).decode())


def test_catalog_filters_and_add(http):
    page = http.get("/proposals/current")
    assert page.status_code == 200 and "1951 Coffee" in page.text and "9 oz Hot Honey" in page.text
    filtered = http.get("/proposals/current?search=honey", headers={"HX-Request": "true"})
    assert "<strong>9 oz Hot Honey</strong>" in filtered.text and "<strong>1951 Coffee</strong>" not in filtered.text and 'id="catalog"' in filtered.text
    assert "<strong>Unisex Fleece Hoodie</strong>" not in http.get("/proposals/current", headers={"HX-Request": "true"}).text  # filter remembered

    http.post("/proposals/current/items", data={"product": "9 oz Hot Honey", "partner": "Bee Co"})
    page = http.get("/proposals/current").text
    assert "Added 9 oz Hot Honey to proposal" in page and "1 product(s) in proposal" in page
    assert "Product 1: 9 oz Hot Honey" in page and "$20.00" in page  # MOQ table
    http.get("/proposals/current?clear=1")
    http.post("/proposals/current/items", data={"action": "all_filtered"})
    assert len(_proposal(http)["proposal_products"]) == 3
    assert "Added 2 product(s)" in http.get("/proposals/current").text


def test_bulk_by_partner_and_remove(http):
    http.post("/proposals/current/items", data={"action": "by_partner", "bulk_partners": ["GOEX", "Bee Co"]})
    names = [i["product_data"]["Product/Service"] for i in _proposal(http)["proposal_products"]]
    assert names == ["Unisex Fleece Hoodie", "9 oz Hot Honey"]
    response = http.post("/proposals/current/items/0", data={"action": "remove"}, headers={"HX-Request": "true"})
    assert response.status_code == 200 and 'id="products"' in response.text
    assert [i["product_data"]["Product/Service"] for i in _proposal(http)["proposal_products"]] == ["9 oz Hot Honey"]


def test_settings_price_and_markup(http):
    http.post("/proposals/current/items", data={"product": "Unisex Fleece Hoodie", "partner": "GOEX"})
    response = http.post("/proposals/current/settings", data={"discount_option": "Non-profit (5%)", "fifty_cent_rounding": "on", "use_msrp": "on", "client_budget": "0"}, headers={"HX-Request": "true"})
    assert response.status_code == 200
    proposal = _proposal(http)
    assert proposal["proposal_discount_type"] == "Non-profit" and proposal["proposal_marketing_rounding"] is False
    assert "5% Non-profit discount" in response.text

    http.post("/proposals/current/items/0", data={"client_price": "55.00", "markup_percent": "100"}, headers={"HX-Request": "true", "HX-Trigger-Name": "client_price"})
    assert proposal["proposal_products"][0]["markup_percent"] == 120.0
    http.post("/proposals/current/items/0", data={"client_price": "55.00", "markup_percent": "150", "manual_override": "on"}, headers={"HX-Request": "true", "HX-Trigger-Name": "markup_percent"})
    item = proposal["proposal_products"][0]
    assert item["markup_percent"] == 150.0 and item["manual_override"] is True
    assert "Manual override" in http.get("/proposals/current").text
    csv_text = http.get("/proposals/current/tables/0.csv").text
    assert csv_text.startswith("MOQ,Price Ea (@ Qty 50),Client Price")


def test_save_load_and_form_link(http, fake):
    http.post("/proposals/current/items", data={"product": "9 oz Hot Honey", "partner": "Bee Co"})
    assert "Save the proposal first" in http.get("/proposals/current").text
    http.post("/proposals/current/form-link", data={"company_name": "Acme"})
    assert "Save the proposal first" in http.get("/proposals/current").text

    http.post("/proposals/current/save", data={"name": "Spring Gifts", "created_by": "Nico"})
    assert list(fake.rows.values())[0][0] == "Spring Gifts"
    saved = list(fake.rows.values())[0][1]
    assert saved["proposal_products"][0]["product_data"]["Product/Service"] == "9 oz Hot Honey" and "proposal_use_msrp" in saved

    http.post("/proposals/current/form-link", data={"company_name": "Acme", "contact_email": "jo@acme.com"})
    page = http.get("/proposals/current").text
    assert "http://forms.test/?client_form=PROP_1&amp;session=" in page
    assert fake.drafts[0][0] == "PROP_1" and fake.drafts[0][2]["client_info"]["company_name"] == "Acme"

    http.post("/proposals/new")
    assert _proposal(http)["proposal_products"] == []
    http.post("/proposals/load/PROP_1")
    assert _proposal(http)["proposal_products"][0]["product_data"]["Product/Service"] == "9 oz Hot Honey"
    assert "Spring Gifts" in http.get("/proposals").text
    http.post("/proposals/delete/PROP_1")
    assert fake.rows == {}


def test_pptx_match_review_and_generate(http, fake):
    http.post("/proposals/current/items", data={"product": "1951 Coffee", "partner": "1951 Coffee"})
    http.post("/proposals/current/items", data={"product": "9 oz Hot Honey", "partner": "Bee Co"})
    assert http.get("/proposals/current/pptx").status_code == 303  # nothing matched yet

    response = http.post("/proposals/current/pptx/match")
    assert response.status_code == 303 and response.headers["location"] == "/proposals/current/pptx"
    review = http.get("/proposals/current/pptx").text
    assert "1951 Coffee" in review and "Exact Match" in review and "9 oz Hot Honey" in review

    # Search for a slide for the honey, use it, and confirm it is remembered in the matches sheet
    response = http.post("/proposals/current/pptx/decide", data={"gs_name": "9 oz Hot Honey", "action": "search", "query": "coffee"}, headers={"HX-Request": "true"})
    assert "Use" in response.text and "SPECIALTY COFFEE" in response.text
    http.post("/proposals/current/pptx/decide", data={"gs_name": "9 oz Hot Honey", "action": "use", "slide": "SPECIALTY COFFEE"}, headers={"HX-Request": "true"})
    assert fake.saved_matches[-1]["product_name"] == "9 oz Hot Honey" and fake.saved_matches[-1]["slide_title"] == "SPECIALTY COFFEE"
    review = http.get("/proposals/current/pptx").text
    assert "Ready to generate PowerPoint with 2 product(s)" in review and "Step 2. Impact slides" in review

    # Skip the honey instead, then generate and poll the job
    http.post("/proposals/current/pptx/decide", data={"gs_name": "9 oz Hot Honey", "action": "skip"})
    response = http.post("/proposals/current/pptx/generate", data={"client_name": "Acme"}, headers={"HX-Request": "true"})
    assert response.status_code == 200 and 'id="pptx-job"' in response.text
    for _ in range(600):
        status = http.get("/proposals/current/pptx/job").text
        if "Generating" not in status:
            break
        time.sleep(0.1)
    assert "PowerPoint generated in" in status and "Download PowerPoint presentation" in status, status
    download = http.get("/proposals/current/pptx/download")
    assert download.status_code == 200 and download.content[:2] == b"PK"
    assert "Proposal_Acme_" in download.headers["content-disposition"]

    http.post("/proposals/current/pptx/reset")
    assert "pending match" in http.get("/proposals/current/pptx").text or "Ready to generate" in http.get("/proposals/current/pptx").text
