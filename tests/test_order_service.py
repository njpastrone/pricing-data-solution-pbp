"""Order arithmetic (pbp/services/order.py) and the invoice/PO builder, on synthetic products."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from pbp.services import invoice as inv
from pbp.services import order as svc

HOODIE = {"Partner": "GOEX", "Product/Service": "Unisex Fleece Hoodie", "Pricing Tiers (Y/N)": "N",
          "PBP Cost (No Tiers)": "$25.00", "MOQ (Partner)": 50, "Country of Origin (Made In)": "USA",
          "Country of Origin (Ships From)": "USA", "Vendor Published MSRP": "$60.00",
          "Client Price: Customization Setup Fee": "$65", "Client Price: Customization Cost per Unit": "$1.50"}
HONEY = {"Partner": "Bee Co", "Product/Service": "9 oz Hot Honey", "Pricing Tiers (Y/N)": "Y",
         "Pricing Tiers Info": "T1: 1-99, T2: 100-499, T3: 500+", "PBP Cost (No Tiers/Tier 1)": "$10.00",
         "PBP Cost: Tier 2": "$9.00", "PBP Cost: Tier 3": "$8.00", "Country of Origin (Made In)": "USA"}


def test_catalog_item_defaults_match_tab3_option_c():
    item = svc.catalog_item(HOODIE, quantity=1)
    assert item["markup_percent"] == 100.0 and item["pricing_method"] == "Standard markup"
    assert item["base_price"] == 25.0 and item["product_total"] == 50.0 and item["total_per_unit"] == 50.0
    assert item["customization_setup_fee"] == 65.0 and item["customization_per_unit"] == 1.5
    assert item["include_customization"] is False and item["tariff_amount"] == 0.0
    assert item["manual_override"] is False
    assert svc.catalog_item(HOODIE, use_msrp=False)["manual_override"] is True


def test_recalculate_customization_minimum_and_addons():
    item = svc.catalog_item(HOODIE, quantity=100)
    item.update(include_customization=True, customization_setup_fee=50, customization_per_unit=1.5,
                partner_customization_setup_fee=20, partner_customization_per_unit=0.5,
                apply_custom_minimum=True, customization_minimum_qty=120,
                customization_addons=[{"name": "Second Color", "client_setup_fee": 10, "client_per_unit_cost": 0.25,
                                       "partner_setup_fee": 5, "partner_per_unit_cost": 0.1},
                                      {"name": "", "client_setup_fee": 99}])  # unnamed add-ons are ignored
    svc.recalculate(item)
    assert item["customization_setup_total"] == 60.0            # 50 + 10
    assert item["customization_unit_total"] == (1.5 + 0.25) * 120  # minimum of 120 units applies
    assert item["customization_setup_cost"] == 25.0             # partner: 20 + 5
    assert item["customization_unit_cost"] == (0.5 + 0.1) * 120
    assert item["product_subtotal"] == 2500.0 and item["markup_amount"] == 2500.0
    assert item["product_total"] == 2500 + 2500 + 60 + 210
    # turning customization off clears it all, add-ons included
    item["include_customization"] = False
    svc.recalculate(item)
    assert item["customization_unit_total"] == 0 and item["customization_addons"] == []


def test_tiered_product_uses_tier_for_quantity():
    low = svc.catalog_item(HONEY, quantity=50)
    high = svc.catalog_item(HONEY, quantity=500)
    assert low["base_price"] == 10.0 and high["base_price"] == 8.0
    low["quantity"] = 150
    svc.recalculate(low)
    assert low["base_price"] == 9.0 and low["product_subtotal"] == 1350.0


def test_client_price_and_markup_are_two_views_of_one_number():
    item = svc.catalog_item(HOODIE, quantity=100)
    svc.set_client_price(item, 55.0)
    assert item["markup_percent"] == 120.0
    assert svc.client_price_per_unit(item, True) == (55.0, 55.0)
    item["markup_percent"] = 100
    svc.recalculate(item)
    rounded, raw = svc.client_price_per_unit(dict(item, markup_amount=2487.0), True)
    assert raw == 49.87 and rounded == 50.0


def test_totals_match_order_summary_formula():
    order = svc.new_order()
    item = svc.catalog_item(HOODIE, quantity=120)
    item.update(include_customization=True, customization_setup_fee=50, customization_per_unit=1.5,
                partner_customization_setup_fee=20, partner_customization_per_unit=0.5)
    svc.add_items(order, [svc.recalculate(item), svc.custom_line_item("Rush fee", 1, "Expedite", 50.0)])
    svc.set_discount_option(order, "Non-profit (5%)")
    order["apply_cc_fee"] = True
    t = svc.totals(order)
    # products 6000 + custom 50 = 6050 client; discount 5% of 6050 = 302.5; + customization 230 = 5977.5; cc 3% = 179.325; total 6156.825 -> $0.50 rounding
    assert t["split"]["products_only_client_price"] == 6050.0
    assert t["discount_amount"] == 302.5
    assert round(t["cc_fee_amount"], 3) == 179.325
    assert t["total_quote"] == 6157.0
    assert t["total_units"] == 121
    assert t["total_pbp_cost"] == 3000 + 50 + 80
    labels = [row[0] for row in t["rows"]]
    assert labels[0] == "Base Product: Unisex Fleece Hoodie" and "Products Subtotal" in labels
    assert "Unisex Fleece Hoodie - Setup" in labels and "Customization Subtotal" in labels
    assert labels[-1] == "TOTAL" and t["rows"][-1][-1] == "$6157.00"
    assert any(label.startswith("Discount (Non-profit") for label in labels)
    assert any(label.startswith("Credit Card Fee") for label in labels)


def test_marketing_rounding_and_custom_discount():
    order = svc.new_order()
    svc.add_items(order, [svc.catalog_item(HOODIE, quantity=10)])  # 500 client
    svc.set_discount_option(order, "Custom", 20)
    order["order_use_marketing_rounding"] = True
    t = svc.totals(order)
    assert t["discount_percent"] == 20.0 and t["discount_amount"] == 100.0
    assert t["total_quote"] == 399.0  # 400 -> charm pricing


def test_add_items_fills_partner_shipping_from_catalog():
    order = svc.new_order()
    product = dict(HOODIE, **{"PBP Cost: Shipping Cost per Unit": "$3.00"})
    svc.add_items(order, [svc.catalog_item(product, 10)])
    assert order["partner_shipping"] == 3.0


def test_import_form_response_sets_client_and_products():
    df = pd.DataFrame([HOODIE, HONEY])
    order = svc.new_order()
    response = {
        "client_info": {"client_type": "Existing", "company_name": "Acme", "contact_name": "Jo", "contact_email": "jo@acme.com", "contact_phone": "555"},
        "products": [{"name": "unisex fleece hoodie", "quantity": 25, "customization_notes": "Navy"}, {"name": "Unknown Thing", "quantity": 1, "customization_notes": ""}],
        "shipping_info": {"shipping_address": "1 Main St", "billing_address": "", "drop_shipping": "Yes", "in_hands_date": "2026-11-01"},
        "payment_info": {"payment_preference": "Net 60", "payment_method": "ACH", "invoice_platform": "Email: ap@acme.com"},
        "notes": "Rush please",
    }
    imported, skipped = svc.import_form_response(order, response, df, proposal_items=[{"product_data": HOODIE, "markup_percent": 150.0}])
    assert imported == ["Unisex Fleece Hoodie"] and skipped == ["Unknown Thing"]
    client = order["client_info"]
    assert client["is_new_client"] is False and client["shipping_type"] == "Drop Shipping"
    assert client["payment_timeline"] == "Net 60" and client["payment_preference"] == "ACH"
    assert str(client["client_in_hands_date"]) == "2026-11-01"
    item = order["order_items"][0]
    assert item["quantity"] == 25 and item["markup_percent"] == 150.0 and item["customization_description"] == "Navy"
    assert item["include_customization"] is False  # the client's notes add no customization pricing
    assert client["billing_address"] == "1 Main St"  # blank billing falls back to shipping
    assert "Client notes (order form): Rush please" in order["order_notes"]["internal_pbp_team"]
    assert order["order_notes"]["internal_bookkeeping"] == "Send invoice to: Email: ap@acme.com"


def test_normalize_migrates_old_orders():
    old = {"order_items": [{"product_name": "X", "product_data": HOODIE, "quantity": 2, "markup_percent": 100,
                            "customization_addons": [{"name": "A", "setup_fee": 5, "per_unit_cost": 1}]}],
           "client_info": {"contact_name": "Jo", "contact_email": "jo@x.com", "company_name": "X"},
           "order_notes": {"kitting": "old"}}
    order = svc.normalize(old)
    assert order["client_info"]["contacts"][0] == {"name": "Jo", "email": "jo@x.com", "phone": "", "role": "Primary Contact"}
    assert set(order["order_notes"]) == {key for key, _ in svc.NOTE_CATEGORIES}
    addon = order["order_items"][0]["customization_addons"][0]
    assert addon["client_setup_fee"] == 5 and addon["partner_setup_fee"] == 0.0
    assert order["order_items"][0]["kitting_quantity"] == 1
    assert "order_fifty_cent_rounding" in order


def test_invoice_lines_csv_and_html():
    order = svc.new_order()
    item = svc.catalog_item(HOODIE, quantity=100)
    item.update(include_customization=True, customization_setup_fee=65, customization_per_unit=1.5,
                partner_customization_setup_fee=30, partner_customization_per_unit=0.5, include_kitting=True,
                kitting_quantity=1, kitting_pbp_cost=10, kitting_client_price=20, kitting_description="Gift box",
                customization_description="Logo")
    svc.add_items(order, [svc.recalculate(item), svc.custom_line_item("Rush", 1, "Expedite", 50)])
    order["order_shipping"], order["partner_shipping"] = 40.0, 25.0
    order["client_info"].update(company_name="Acme", order_submitted_by="Nico", cost_submitted_by="Sam")
    order["client_info"]["contacts"][0].update(name="Jo", email="jo@acme.com")
    order["order_notes"]["external_partners"] = "Ship by 11/1"
    order["partner_contacts_editable"] = {"GOEX": {"poc_name": "Pat", "poc_email": "pat@goex.com", "poc_phone": "", "shipping_instructions": "Ground only"}}

    invoice = inv.build(order, pd.DataFrame([HOODIE]), {"GOEX": {"poc_name": "Spreadsheet", "poc_email": "s@goex.com", "poc_phone": ""}})
    descriptions = [line["DESCRIPTION (Invoice)"] for line in invoice["lines"]]
    assert descriptions[0] == "Unisex Fleece Hoodie (Customization: Logo)"  # printed whether or not customization is ticked
    assert "  └ Gift box" in descriptions and "  └ Setup Fee: Logo" in descriptions and "  └ Customization (per unit): Logo" in descriptions
    assert descriptions[-2:] == ["Expedite", "Shipping to Client"]
    base = invoice["lines"][0]
    assert base["COST/UNIT"] == "$25.00" and base["SELL PRICE/UNIT"] == "$50.00" and base["TOTAL SELL PRICE"] == "$5000.00"
    assert invoice["partner_rows"][0]["poc_name"] == "Pat" and invoice["partner_rows"][0]["shipping_instructions"] == "Ground only"
    assert invoice["totals_rows"][0] == ("Subtotal (Products + Customization)", "$5265.00")  # 5000 + 65 + 150 + 50
    assert invoice["totals_rows"][-1][0] == "TOTAL"
    assert "Client In-Hands Date is required" in invoice["warnings"]

    csv_text = inv.to_csv(invoice)
    lines = csv_text.splitlines()
    assert lines[0].startswith("PARTNER,DESCRIPTION (Invoice)")
    assert lines[1].startswith(",External Notes (For Partners/POs): Ship by 11/1")
    assert lines[-1].startswith(",TOTAL,") and lines[-1].endswith(invoice["totals_rows"][-1][1])

    html = inv.to_html(invoice, {"Unisex Fleece Hoodie": [{"filename": "a.png", "bytes": b"\x89PNG"}]}, {})
    assert "INVOICE AND PURCHASE ORDER REQUEST FORM" in html and "Pat &lt;pat@goex.com&gt;" in html
    assert "data:image/png;base64," in html and "Ship by 11/1" in html
