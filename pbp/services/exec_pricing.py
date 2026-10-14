"""
Executive Pricing Tool (Tab 5 of the Streamlit app): quick what-if pricing
scenarios with margins, customization and pass-through tariffs.
"""

import csv
import io

from pbp.core.helpers import calculate_markup_from_price, clean_price, get_column_value
from pbp.core.pricing_engine import get_unit_price_new_system
from pbp.services import order as order_service

USA = {"USA", "UNITED STATES", "US", "U.S.", "AMERICA", "UNITED STATES OF AMERICA"}


def new_scenario():
    return {"products": [], "shipping": 70.0, "cc_fee": False, "cc_fee_percent": 3.0}


def _price(product_data, *names):
    return clean_price(get_column_value(product_data, names[0], names[1], 0)) or 0.0


def add_product(scenario, product_data):
    """Add a catalog product with the Tab 5 defaults (100 units, 100% markup, tariffs on for non-USA). False if already there."""
    name = product_data.get("Product/Service", "")
    if any(p["product_name"] == name for p in scenario["products"]):
        return False
    product_data = dict(product_data)
    country = str(product_data.get("Country of Origin (Ships From)", "Unknown") or "Unknown")
    scenario["products"].append({
        "product_name": name, "partner": product_data.get("Partner", ""), "product_data": product_data,
        "quantity": 100, "markup_percent": 100.0, "include_customization": False,
        "custom_setup_fee": _price(product_data, "Client Price: Customization Setup Fee", "Customization Setup Fee"),
        "custom_per_unit": _price(product_data, "Client Price: Customization Cost per Unit", "Customization Cost per Unit"),
        "pbp_setup_fee": _price(product_data, "PBP Cost: Customization Setup Fee", "Customization Setup Fee"),
        "pbp_per_unit_cost": _price(product_data, "PBP Cost: Customization Cost per Unit", "Customization Cost per Unit"),
        "include_tariffs": country.upper() not in USA,
        "tariff_input_method": "dollar" if _price(product_data, "Tariff Estimate ($)", "Tariff Estimate ($)") > 0 else "percentage",
        "tariff_rate": None, "tariff_dollar": None,
    })
    return True


def set_client_price(product, client_price):
    base_cost, _, _ = get_unit_price_new_system(product["product_data"], product["quantity"])
    if base_cost:
        product["markup_percent"] = calculate_markup_from_price(base_cost, float(client_price))


def view(product):
    """Everything one product card shows: cost, price, margin, tariff defaults and the breakdown rows."""
    row, qty = product["product_data"], product["quantity"]
    base_cost, tier_range, _ = get_unit_price_new_system(row, qty)
    base_cost = base_cost or 0.0
    client_price = base_cost * (1 + product["markup_percent"] / 100)
    country = str(row.get("Country of Origin (Ships From)", "Unknown") or "Unknown")

    # Tariffs: % of commercial value (client price) or $ per unit; spreadsheet defaults are per 100 units ($) or a %
    sheet_dollar = _price(row, "Tariff Estimate ($)", "Tariff Estimate ($)")
    sheet_percent = _price(row, "Tariff Estimate (%)", "Tariff Estimate (%)")
    default_rate = (sheet_dollar / (client_price * 100)) * 100 if sheet_dollar > 0 and client_price > 0 else sheet_percent
    default_dollar = sheet_dollar / 100 if sheet_dollar > 0 else client_price * sheet_percent / 100
    tariff_per_unit, tariff_rate = 0.0, 0.0
    if product.get("include_tariffs"):
        if product.get("tariff_input_method") == "dollar":
            tariff_per_unit = float(product["tariff_dollar"]) if product.get("tariff_dollar") is not None else default_dollar
            tariff_rate = tariff_per_unit / client_price * 100 if client_price > 0 else 0.0
        else:
            tariff_rate = float(product["tariff_rate"]) if product.get("tariff_rate") is not None else default_rate
            tariff_per_unit = client_price * tariff_rate / 100
    tariff_total = tariff_per_unit * qty

    custom = product.get("include_customization", False)
    setup, per_unit = (product["custom_setup_fee"], product["custom_per_unit"]) if custom else (0.0, 0.0)
    pbp_setup, pbp_per_unit = (product["pbp_setup_fee"], product["pbp_per_unit_cost"]) if custom else (0.0, 0.0)

    rows = [["Base Product: " + product["product_name"], qty, base_cost, base_cost * qty, client_price, client_price * qty]]
    if custom and setup > 0:
        rows.append([product["product_name"] + " - Setup", "one-time", pbp_setup, pbp_setup, setup, setup])
    if custom and per_unit > 0:
        rows.append([product["product_name"] + " - Per Unit", qty, pbp_per_unit, pbp_per_unit * qty, per_unit, per_unit * qty])
    if tariff_per_unit > 0:
        rows.append([f"{product['product_name']} - Tariff ({tariff_rate:.1f}% - {country})", qty, tariff_per_unit, tariff_total, tariff_per_unit, tariff_total])

    pbp_subtotal = base_cost * qty + pbp_setup + pbp_per_unit * qty + tariff_total
    client_subtotal = client_price * qty + setup + per_unit * qty + tariff_total
    margin = (client_price - base_cost) * qty + (setup - pbp_setup) + (per_unit - pbp_per_unit) * qty
    revenue = client_price * qty + setup + per_unit * qty
    return {
        "base_cost": base_cost, "tier_range": tier_range or "", "client_price": client_price, "country": country,
        "margin_per_unit": client_price - base_cost, "margin_total": (client_price - base_cost) * qty,
        "margin_percent": (client_price - base_cost) / client_price * 100 if client_price > 0 else 0.0,
        "sheet_dollar": sheet_dollar, "sheet_percent": sheet_percent, "default_rate": default_rate, "default_dollar": default_dollar,
        "tariff_per_unit": tariff_per_unit, "tariff_rate": tariff_rate, "tariff_total": tariff_total,
        "pbp_setup": pbp_setup, "pbp_per_unit": pbp_per_unit, "setup": setup, "per_unit": per_unit,
        "rows": rows, "pbp_subtotal": pbp_subtotal, "client_subtotal": client_subtotal,
        "product_margin": margin, "product_margin_percent": margin / revenue * 100 if revenue > 0 else 0.0,
    }


def _money(value):
    return f"${value:.2f}"


def summary(scenario):
    """The order summary table (same six columns as Tab 3) and the totals."""
    rows, units, products_pbp, products_client, custom_pbp, custom_client, tariff_total = [], 0, 0.0, 0.0, 0.0, 0.0, 0.0
    tariff_rows = []
    for product in scenario["products"]:
        v = view(product)
        if v["base_cost"] <= 0:
            continue
        qty = product["quantity"]
        units += qty
        products_pbp += v["base_cost"] * qty
        products_client += v["client_price"] * qty
        rows.append([f"Base Product: {product['product_name']}", str(qty), _money(v["base_cost"]), _money(v["base_cost"] * qty), _money(v["client_price"]), _money(v["client_price"] * qty)])
        if v["setup"] > 0:
            rows.append([f"{product['product_name']} - Setup", "one-time", _money(v["pbp_setup"]), _money(v["pbp_setup"]), _money(v["setup"]), _money(v["setup"])])
            custom_pbp += v["pbp_setup"]
            custom_client += v["setup"]
        if v["per_unit"] > 0:
            rows.append([f"{product['product_name']} - Per Unit", str(qty), _money(v["pbp_per_unit"]), _money(v["pbp_per_unit"] * qty), _money(v["per_unit"]), _money(v["per_unit"] * qty)])
            custom_pbp += v["pbp_per_unit"] * qty
            custom_client += v["per_unit"] * qty
        if v["tariff_per_unit"] > 0:
            tariff_rows.append([f"Tariff: {product['product_name']} ({v['tariff_rate']:.1f}% - {v['country']})", str(qty), _money(v["tariff_per_unit"]), _money(v["tariff_total"]), _money(v["tariff_per_unit"]), _money(v["tariff_total"])])
            tariff_total += v["tariff_total"]

    rows.append(["Products Subtotal", "", "", _money(products_pbp), "", _money(products_client)])
    if custom_client > 0:
        rows.append(["", "", "", "", "", ""])
        rows.append(["Customization Subtotal", "", "", _money(custom_pbp), "", _money(custom_client)])
    rows.append(["", "", "", "", "", ""])
    shipping = float(scenario.get("shipping", 0.0) or 0.0)
    if shipping > 0:
        rows.append(["Shipping", "", "", _money(shipping), "", _money(shipping)])
    rows.extend(tariff_rows)
    total_pbp = products_pbp + custom_pbp + shipping + tariff_total
    before_cc = products_client + custom_client + shipping + tariff_total
    cc_fee = before_cc * float(scenario.get("cc_fee_percent", 3.0)) / 100 if scenario.get("cc_fee") else 0.0
    if cc_fee:
        rows.append([f"Credit Card Fee ({scenario.get('cc_fee_percent', 3.0)}%)", "", "", "", "", _money(cc_fee)])
    total = before_cc + cc_fee
    rows.append(["TOTAL", f"{units} units", "", _money(total_pbp), "", _money(total)])
    margin = (products_client - products_pbp) + (custom_client - custom_pbp)
    revenue = products_client + custom_client
    return {
        "rows": rows, "units": units, "total_pbp": total_pbp, "total": total, "avg_per_unit": total / units if units else 0.0,
        "true_margin": margin, "margin_percent": margin / revenue * 100 if revenue > 0 else 0.0,
        "shipping": shipping, "tariff_total": tariff_total, "cc_fee": cc_fee,
    }


def summary_csv(scenario):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Item", "Qty", "PBP Cost (Per Unit)", "PBP Cost", "Client Price (Per Unit)", "Client Price"])
    writer.writerows(summary(scenario)["rows"])
    return out.getvalue()


def to_proposal_items(scenario, proposal):
    """Proposal lines carrying the scenario's markups (duplicates skipped). Returns the count added."""
    from pbp.services import proposal as proposal_service
    existing = {i["product_data"].get("Product/Service") for i in proposal["proposal_products"]}
    added = 0
    for product in scenario["products"]:
        if product["product_name"] in existing:
            continue
        try:
            item = proposal_service.proposal_item(product["product_data"], proposal)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        proposal_service.set_item_markup(item, product["markup_percent"], proposal)
        item["manual_override"] = True
        proposal["proposal_products"].append(item)
        added += 1
    return added


def to_order_items(scenario, order):
    """Order lines with the scenario's quantity, markup and customization (duplicates skipped). Returns the count added."""
    existing = {i["product_name"] for i in order["order_items"] if not i.get("is_custom")}
    items = []
    for product in scenario["products"]:
        if product["product_name"] in existing:
            continue
        item = order_service.catalog_item(product["product_data"], quantity=product["quantity"], use_msrp=False)
        if item is None:
            continue
        item["markup_percent"] = product["markup_percent"]
        item["include_customization"] = product.get("include_customization", False)
        item["customization_setup_fee"] = product.get("custom_setup_fee", 0.0)
        item["customization_per_unit"] = product.get("custom_per_unit", 0.0)
        item["partner_customization_setup_fee"] = product.get("pbp_setup_fee", 0.0)
        item["partner_customization_per_unit"] = product.get("pbp_per_unit_cost", 0.0)
        items.append(order_service.recalculate(item))
    order_service.add_items(order, items)
    return len(items)
