"""Proposal arithmetic (pbp/services/proposal.py) and PowerPoint jobs on synthetic products and the committed deck."""

import os
import sys
import time
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from pbp.services import pptx_jobs
from pbp.services import proposal as svc
from pbp.sheets import templates
from test_order_service import HONEY, HOODIE

NO_PRICE = {"Partner": "Mystery", "Product/Service": "Priceless", "Pricing Tiers (Y/N)": "N", "PBP Cost (No Tiers)": ""}
DF = pd.DataFrame([HOODIE, HONEY, NO_PRICE])


def test_catalog_rows_filter_by_search_partner_and_price():
    rows = svc.catalog_rows(DF)
    assert [r["name"] for r in rows] == ["Unisex Fleece Hoodie", "9 oz Hot Honey", "Priceless"]
    hoodie = rows[0]
    assert hoodie["cost"] == 25.0 and hoodie["client_price"] == 50.0 and hoodie["msrp"] == 60.0
    assert [r["name"] for r in svc.catalog_rows(DF, search="honey")] == ["9 oz Hot Honey"]
    assert [r["name"] for r in svc.catalog_rows(DF, partners=["GOEX"])] == ["Unisex Fleece Hoodie"]
    # price filter uses the displayed client price and drops products without one
    assert [r["name"] for r in svc.catalog_rows(DF, min_budget=30)] == ["Unisex Fleece Hoodie"]
    assert [r["name"] for r in svc.catalog_rows(DF, max_budget=30)] == ["9 oz Hot Honey"]
    assert svc.filter_options(DF)[0] == ["Bee Co", "GOEX", "Mystery"]


def test_add_products_skips_duplicates_and_reports_failures():
    proposal = svc.new_proposal()
    added, failed = svc.add_products(proposal, [HOODIE, HONEY, NO_PRICE, HOODIE])
    assert added == ["Unisex Fleece Hoodie", "9 oz Hot Honey"] and failed == ["Priceless"]
    item = proposal["proposal_products"][0]
    assert item["markup_percent"] == 100.0 and item["pricing_method"] == "Standard markup"
    assert item["pricing_snapshot"]["moq"] == 50 and item["pricing_snapshot"]["client_price_per_unit"] == 50.0
    assert item["settings_snapshot"]["fifty_cent_rounding"] is True
    assert svc.add_products(proposal, [HOODIE]) == ([], [])


def test_item_display_price_markup_and_override():
    proposal = svc.new_proposal()
    svc.add_products(proposal, [HOODIE])
    item = proposal["proposal_products"][0]
    display = svc.item_display(item, proposal)
    assert display["base_cost"] == 25.0 and display["client_price"] == 50.0 and display["method"] == "Standard markup"

    svc.set_item_price(item, 55.0, proposal)
    assert item["markup_percent"] == 120.0
    item["manual_override"] = True
    display = svc.item_display(item, proposal)
    assert display["method"] == "Manual override" and display["client_price"] == 55.0

    proposal["proposal_marketing_rounding"] = True
    svc.set_item_markup(item, 140, proposal)  # 60.00 -> charm 59.00
    assert svc.item_display(item, proposal)["client_price"] == 59.0


def test_moq_table_with_discount_and_budget():
    proposal = svc.new_proposal()
    svc.add_products(proposal, [HONEY])
    item = proposal["proposal_products"][0]
    table = svc.moq_table(item, proposal)
    assert table["columns"][0] == "MOQ" and table["row"][0] == 56  # $1,000 MOV at the qty-100 estimate ($9 cost x2 = $18) -> 56 units
    assert table["row"][1] == "$20.00" and table["row"][2] == "$20.00"

    svc.set_discount_option(proposal, "Non-profit (5%)")
    proposal["proposal_client_budget"] = 10000  # affords 500 units: tier 3 at $8 cost -> $16
    table = svc.moq_table(item, proposal)
    assert "Price ea @ Qty 500" in table["columns"][2] and "5% Non-profit discount" in table["columns"][2]
    assert table["row"][2] == "$15.00"  # 16 * 0.95 = 15.20 -> $0.50 rounding
    assert svc.moq_table_csv(table).splitlines()[1].startswith("56,$20.00,$15.00")
    assert svc.moq_table({"product_data": NO_PRICE, "markup_percent": 100}, proposal) is None


def test_discount_options_round_trip():
    proposal = svc.new_proposal()
    for option in svc.DISCOUNT_OPTIONS:
        svc.set_discount_option(proposal, option, 12.5)
        assert svc.discount_option(proposal) == option
    assert proposal["proposal_discount_percent"] == 12.5
    svc.set_discount_option(proposal, "None")
    assert proposal["proposal_discount_type"] is None and proposal["proposal_discount_percent"] == 0.0


def test_slide_matching_review_and_generation_on_committed_deck():
    deck = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "November All Slides.pptx")
    names, index = pptx_jobs.slide_titles(deck)
    assert "1951 Coffee" in index and len(names) > 100

    proposal = svc.new_proposal()
    coffee = dict(HOODIE, **{"Product/Service": "1951 Coffee", "Partner": "1951 Coffee"})
    svc.add_products(proposal, [coffee, HONEY])
    with patch("pbp.sheets.match_memory.get_confirmed_match", return_value=None), \
         patch("pbp.sheets.match_memory._load_all_matches_data.clear"):
        results, _, _ = pptx_jobs.match_products(proposal, deck, "November All Slides.pptx")
    by_name = {r["gs_name"]: r for r in results}
    assert by_name["1951 Coffee"]["kind"] == "exact" and by_name["1951 Coffee"]["pptx_name"] == "1951 Coffee"
    honey = by_name["9 oz Hot Honey"]
    assert honey["kind"] in ("fuzzy", "poor")

    confirmations = {}
    rows = pptx_jobs.review_rows(results, confirmations)
    assert {r["gs_name"]: r["status"] for r in rows} == {"1951 Coffee": "done", "9 oz Hot Honey": "review" if honey["kind"] == "fuzzy" else "review"}
    confirmations["9 oz Hot Honey"] = {"skipped": True}
    assert pptx_jobs.pending(results, confirmations) == []
    assert pptx_jobs.confirmed_matches(results, confirmations) == {"1951 Coffee": "1951 Coffee"}
    assert pptx_jobs.search_slides(names, "coffee")[0].lower().find("coffee") >= 0

    with patch.object(templates, "impact_slide_mapping", return_value={}):
        job_id = pptx_jobs.start_job(proposal, deck, {"1951 Coffee": "1951 Coffee"}, {}, {}, "Acme")
        for _ in range(600):
            job = pptx_jobs.job(job_id)
            if job["status"] != "running":
                break
            time.sleep(0.1)
    assert job["status"] == "done", job.get("error")
    assert job["data"][:2] == b"PK" and job["filename"].startswith("Proposal_Acme_")
    assert job["product_count"] == 1 and isinstance(job["reports"], list)
    assert pptx_jobs.report_summary(job["reports"]).keys() >= {"auto_updated", "needs_review", "unchanged"}
