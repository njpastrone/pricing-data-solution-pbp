"""Executive Pricing Tool arithmetic (pbp/services/exec_pricing.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pbp.services import exec_pricing as svc
from pbp.services import order as order_service
from pbp.services import proposal as proposal_service
from test_order_service import HONEY, HOODIE

IMPORTED = dict(HOODIE, **{"Product/Service": "Alpaca Scarf", "Country of Origin (Ships From)": "Peru",
                          "Tariff Estimate ($)": "$250", "PBP Cost: Customization Setup Fee": "$30"})


def test_add_product_defaults_and_tariff_autocheck():
    scenario = svc.new_scenario()
    assert svc.add_product(scenario, HOODIE) and not svc.add_product(scenario, HOODIE)
    assert svc.add_product(scenario, IMPORTED)
    usa, peru = scenario["products"]
    assert usa["quantity"] == 100 and usa["markup_percent"] == 100.0 and usa["include_tariffs"] is False
    assert usa["custom_setup_fee"] == 65.0 and usa["pbp_setup_fee"] == 0.0
    assert peru["include_tariffs"] is True and peru["tariff_input_method"] == "dollar" and peru["pbp_setup_fee"] == 30.0


def test_view_margins_customization_and_tariff_methods():
    scenario = svc.new_scenario()
    svc.add_product(scenario, IMPORTED)
    product = scenario["products"][0]
    v = svc.view(product)
    assert v["base_cost"] == 25.0 and v["client_price"] == 50.0 and v["margin_per_unit"] == 25.0 and v["margin_percent"] == 50.0
    # $250 per 100 units -> $2.50 per unit, 5% of the $50 commercial value
    assert v["tariff_per_unit"] == 2.5 and v["tariff_rate"] == 5.0 and v["tariff_total"] == 250.0
    assert v["rows"][-1][0].startswith("Alpaca Scarf - Tariff (5.0% - Peru)")
    assert v["pbp_subtotal"] == 2500 + 250 and v["client_subtotal"] == 5000 + 250 and v["product_margin"] == 2500.0

    product["tariff_input_method"], product["tariff_rate"] = "percentage", 10.0
    assert svc.view(product)["tariff_per_unit"] == 5.0
    product["include_customization"] = True
    product.update(custom_setup_fee=65, custom_per_unit=1.5, pbp_setup_fee=30, pbp_per_unit_cost=0.5)
    v = svc.view(product)
    assert [r[0] for r in v["rows"]][1:3] == ["Alpaca Scarf - Setup", "Alpaca Scarf - Per Unit"]
    assert v["product_margin"] == 2500 + (65 - 30) + (1.5 - 0.5) * 100
    assert round(v["product_margin_percent"], 2) == round(v["product_margin"] / (5000 + 65 + 150) * 100, 2)

    svc.set_client_price(product, 60.0)
    assert product["markup_percent"] == 140.0


def test_summary_totals_and_csv():
    scenario = svc.new_scenario()
    svc.add_product(scenario, HOODIE)
    svc.add_product(scenario, IMPORTED)
    scenario["products"][1]["include_customization"] = True
    scenario["cc_fee"] = True
    s = svc.summary(scenario)
    # products 5000 + 5000 client, 2500 + 2500 cost; customization 65 + 150 client vs 30 + 0 cost; shipping 70; tariff 250
    assert s["units"] == 200 and s["tariff_total"] == 250.0 and s["shipping"] == 70.0
    before_cc = 10000 + 215 + 70 + 250
    assert round(s["cc_fee"], 2) == round(before_cc * 0.03, 2) and round(s["total"], 2) == round(before_cc * 1.03, 2)
    assert s["total_pbp"] == 5000 + 30 + 70 + 250
    assert s["true_margin"] == 5000 + 185 and round(s["margin_percent"], 2) == round(5185 / 10215 * 100, 2)
    labels = [r[0] for r in s["rows"]]
    assert labels[0] == "Base Product: Unisex Fleece Hoodie" and "Customization Subtotal" in labels and labels[-1] == "TOTAL"
    assert any(l.startswith("Tariff: Alpaca Scarf") for l in labels) and any(l.startswith("Credit Card Fee") for l in labels)
    assert svc.summary_csv(scenario).splitlines()[0].startswith("Item,Qty")


def test_import_into_proposal_and_order():
    scenario = svc.new_scenario()
    svc.add_product(scenario, HOODIE)
    scenario["products"][0].update(markup_percent=150.0, quantity=40, include_customization=True)
    proposal = proposal_service.new_proposal()
    assert svc.to_proposal_items(scenario, proposal) == 1 and svc.to_proposal_items(scenario, proposal) == 0
    assert proposal["proposal_products"][0]["markup_percent"] == 150.0 and proposal["proposal_products"][0]["manual_override"] is True
    order = order_service.new_order()
    assert svc.to_order_items(scenario, order) == 1 and svc.to_order_items(scenario, order) == 0
    item = order["order_items"][0]
    assert item["quantity"] == 40 and item["markup_percent"] == 150.0 and item["include_customization"] is True
    assert item["customization_setup_total"] == 65.0 and item["product_total"] == 1000 + 1500 + 65 + 60
