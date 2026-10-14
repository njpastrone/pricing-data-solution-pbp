"""
Proposal building and pricing (Tab 1 of the Streamlit app), independent of any UI.

A "proposal" is the dict the Streamlit app saves to the saved_proposals sheet
(proposal_products plus the proposal-wide settings).
"""

import copy
import csv
import io

import pandas as pd

from pbp.core.helpers import (
    apply_marketing_rounding,
    calculate_markup_from_price,
    calculate_moq,
    calculate_pricing_snapshot,
    clean_price,
    format_shipping_display,
    get_column_value,
    round_to_nearest_fifty_cents,
)
from pbp.core.pricing_engine import calculate_catalog_client_price, calculate_pbp_msrp, get_unit_price_new_system

DISCOUNT_OPTIONS = ["None", "Non-profit (5%)", "Volume Order (5%)", "Custom"]
REFERENCE_QUANTITY = 100  # Tab 1 prices every product at quantity 100 for display


def new_proposal():
    return {
        "proposal_products": [],
        "proposal_marketing_rounding": False,
        "proposal_fifty_cent_rounding": True,
        "proposal_use_msrp": True,
        "proposal_discount_type": None,
        "proposal_discount_percent": 0.0,
        "proposal_client_budget": 0.0,
    }


def normalize(proposal):
    base = new_proposal()
    for key, value in base.items():
        proposal.setdefault(key, value)
    return proposal


def saved_payload(proposal):
    """The dict written to the saved_proposals sheet (same keys as the Streamlit app plus the $0.50 rounding flag)."""
    return copy.deepcopy({key: proposal.get(key) for key in new_proposal()})


# ----------------------------------------------------------------------------
# Catalog
# ----------------------------------------------------------------------------

def catalog_rows(df_template, search="", partners=(), countries=(), min_budget=0.0, max_budget=0.0):
    """
    Catalog rows after the Tab 1 filters, each with the pricing shown in the catalog.

    The price filter uses the same client price that is displayed (calculate_catalog_client_price).
    """
    df = df_template
    if partners:
        df = df[df["Partner"].isin(partners)]
    if countries and "Country of Origin (Ships From)" in df.columns:
        df = df[df["Country of Origin (Ships From)"].isin(countries)]
    if search:
        df = df[df["Product/Service"].str.lower().str.contains(search.lower(), na=False)]
    price_filter = (min_budget > 0 or max_budget > 0) and not (min_budget > 0 and max_budget > 0 and min_budget > max_budget)

    rows = []
    for _, row in df.iterrows():
        pricing = calculate_catalog_client_price(row)
        price = pricing["client_price"]
        if price_filter:
            if not price or (min_budget > 0 and price < min_budget) or (max_budget > 0 and price > max_budget):
                continue
        product = row.to_dict()
        msrp = clean_price(get_column_value(product, "Vendor Published MSRP", "MSRP", ""))
        rows.append({
            "product": product,
            "name": product.get("Product/Service", ""),
            "partner": product.get("Partner", ""),
            "ships_from": product.get("Country of Origin (Ships From)", "N/A"),
            "made_in": product.get("Country of Origin (Made In)", "N/A"),
            "tiered": product.get("Pricing Tiers (Y/N)", "N/A"),
            "cost": pricing["moq_cost"],
            "client_price": price,
            "moq_text": pricing["moq_display_text"],
            "markup": pricing["actual_markup"],
            "method": pricing["method_used"] if pricing["estimated_moq"] else (get_column_value(product, "Pricing Logic", None) or "Standard markup"),
            "cost_basis": get_column_value(product, "Cost Basis (Per Item/Per Case)", "Per Item"),
            "msrp": msrp if msrp and msrp > 0 else None,
            "shipping": format_shipping_display(product),
            "description": str(product.get("Marketing Description", "") or "").strip(),
        })
    return rows


def filter_options(df_template):
    partners = sorted(df_template["Partner"].dropna().unique().tolist())
    countries = []
    if "Country of Origin (Ships From)" in df_template.columns:
        countries = sorted(c for c in df_template["Country of Origin (Ships From)"].dropna().unique().tolist() if str(c).strip())
    return partners, countries


# ----------------------------------------------------------------------------
# Proposal items
# ----------------------------------------------------------------------------

def settings_snapshot(proposal):
    return {
        "fifty_cent_rounding": proposal.get("proposal_fifty_cent_rounding", False),
        "marketing_rounding": proposal.get("proposal_marketing_rounding", False),
        "discount_percent": proposal.get("proposal_discount_percent", 0.0),
    }


def proposal_item(product_data, proposal):
    """A proposal line for a catalog product (Tab 1 'Add to Proposal'). Raises on missing pricing data."""
    product_data = dict(product_data)
    pricing_result = calculate_pbp_msrp(product_data, quantity=REFERENCE_QUANTITY)
    if proposal.get("proposal_use_msrp", True):
        per_item_cost = pricing_result["calculation_details"]["per_item_cost"]
        markup = ((pricing_result["pbp_msrp"] / per_item_cost) - 1) * 100 if per_item_cost and per_item_cost > 0 else 100.0
    else:
        markup = 100.0
    snapshot = calculate_pricing_snapshot(
        product_data, markup, quantity=REFERENCE_QUANTITY,
        discount_percent=proposal.get("proposal_discount_percent", 0.0),
        marketing_rounding=proposal.get("proposal_marketing_rounding", False),
        fifty_cent_rounding=proposal.get("proposal_fifty_cent_rounding", True),
    )
    return {
        "product_data": product_data,
        "markup_percent": markup,
        "pricing_snapshot": snapshot,
        "pricing_method": pricing_result["method_used"],
        "pricing_notes": pricing_result.get("pricing_notes", ""),
        "manual_override": False,
        "validation_warning": pricing_result.get("validation_warning"),
        "settings_snapshot": settings_snapshot(proposal),
    }


def add_products(proposal, products):
    """Add catalog rows, skipping ones already in the proposal. Returns (added names, failed names)."""
    existing = {item["product_data"].get("Product/Service") for item in proposal["proposal_products"]}
    added, failed = [], []
    for product in products:
        name = product.get("Product/Service", "Unknown Product")
        if name in existing:
            continue
        try:
            proposal["proposal_products"].append(proposal_item(product, proposal))
            existing.add(name)
            added.append(name)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            failed.append(name)
    return added, failed


def item_display(item, proposal):
    """Numbers for one row of the 'Products in Proposal' table."""
    product = item["product_data"]
    base_cost, _, _ = get_unit_price_new_system(product, REFERENCE_QUANTITY)
    if item.get("manual_override"):
        price = base_cost * (1 + item["markup_percent"] / 100) if base_cost else None
    else:
        result = calculate_pbp_msrp(product, REFERENCE_QUANTITY)
        price = result["pbp_msrp"] if result else None
    unrounded = price
    if price:
        price = round_to_nearest_fifty_cents(price, proposal.get("proposal_fifty_cent_rounding", True))
        price = apply_marketing_rounding(price, proposal.get("proposal_marketing_rounding", False))
    msrp = clean_price(get_column_value(product, "Vendor Published MSRP", "MSRP", ""))
    return {
        "name": product.get("Product/Service", ""), "partner": product.get("Partner", ""),
        "base_cost": base_cost, "msrp": msrp if msrp and msrp > 0 else None,
        "method": "Manual override" if item.get("manual_override") else (item.get("pricing_method") or "Standard markup"),
        "client_price": price, "unrounded": unrounded,
        "rounded_note": unrounded is not None and price is not None and abs(price - unrounded) > 0.01,
    }


def set_item_markup(item, markup, proposal):
    item["markup_percent"] = float(markup)
    item["settings_snapshot"] = settings_snapshot(proposal)


def set_item_price(item, price, proposal):
    """Entering a client price sets the markup that produces it (at the reference quantity)."""
    base_cost, _, _ = get_unit_price_new_system(item["product_data"], REFERENCE_QUANTITY)
    if base_cost:
        item["markup_percent"] = calculate_markup_from_price(base_cost, float(price))
        item["settings_snapshot"] = settings_snapshot(proposal)


def discount_option(proposal):
    kind = proposal.get("proposal_discount_type")
    return {"Non-profit": "Non-profit (5%)", "Volume Order": "Volume Order (5%)", "Custom": "Custom"}.get(kind, "None")


def set_discount_option(proposal, option, custom_percent=None):
    if option == "Non-profit (5%)":
        proposal.update(proposal_discount_type="Non-profit", proposal_discount_percent=5.0)
    elif option == "Volume Order (5%)":
        proposal.update(proposal_discount_type="Volume Order", proposal_discount_percent=5.0)
    elif option == "Custom":
        proposal["proposal_discount_type"] = "Custom"
        if custom_percent is not None:
            proposal["proposal_discount_percent"] = float(custom_percent)
    else:
        proposal.update(proposal_discount_type=None, proposal_discount_percent=0.0)


# ----------------------------------------------------------------------------
# Proposal (MOQ) tables
# ----------------------------------------------------------------------------

def _price_at(item, product, quantity, proposal):
    """Client price per unit at a quantity (manual override uses the stored markup, else the spreadsheet method)."""
    base, _, _ = get_unit_price_new_system(product, quantity)
    if base is None:
        return None
    if item.get("manual_override"):
        price = (base * quantity * (1 + item["markup_percent"] / 100)) / quantity
    else:
        price = calculate_pbp_msrp(product, quantity=quantity, user_markup_override=None)["pbp_msrp"]
    price = round_to_nearest_fifty_cents(price, proposal.get("proposal_fifty_cent_rounding", True))
    return apply_marketing_rounding(price, proposal.get("proposal_marketing_rounding", False))


def moq_table(item, proposal):
    """The one-row proposal table for a product (MOQ, price at MOQ, client price, delivery), or None."""
    product = item["product_data"]
    preliminary, _, _ = get_unit_price_new_system(product, REFERENCE_QUANTITY)
    if preliminary is None:
        return None
    moq_result = calculate_moq(preliminary * (1 + item["markup_percent"] / 100), product)
    moq = (moq_result or {}).get("moq") or 5
    moq_price = _price_at(item, product, moq, proposal)
    if moq_price is None:
        return None

    client_price, notes = moq_price, []
    budget = float(proposal.get("proposal_client_budget", 0.0) or 0.0)
    if budget > 0 and budget > moq * moq_price:
        quantity = int(budget / moq_price)
        better = _price_at(item, product, quantity, proposal)
        if better is not None and better < moq_price:
            client_price = better
            notes.append(f"Price ea @ Qty {quantity}")
    discount = float(proposal.get("proposal_discount_percent", 0.0) or 0.0)
    if discount > 0:
        client_price = client_price * (1 - discount / 100)
        client_price = round_to_nearest_fifty_cents(client_price, proposal.get("proposal_fifty_cent_rounding", True))
        client_price = apply_marketing_rounding(client_price, proposal.get("proposal_marketing_rounding", False))
        kind = proposal.get("proposal_discount_type")
        notes.append({"Non-profit": "5% Non-profit discount", "Volume Order": "5% Volume Order discount"}.get(kind, f"{discount:.1f}% discount"))

    setup_fee = clean_price(get_column_value(product, "Client Price: Customization Setup Fee", "Customization Setup Fee", "")) or 0.0
    per_unit = clean_price(get_column_value(product, "Client Price: Customization Cost per Unit", "Customization Cost per Unit", "")) or 0.0
    return {
        "name": product.get("Product/Service", ""),
        "columns": ["MOQ", f"Price Ea (@ Qty {moq})", "Client Price" + (f" ({', '.join(notes)})" if notes else ""), "Delivery"],
        "row": [moq, f"${moq_price:.2f}", f"${client_price:.2f}", ""],
        "moq_text": (moq_result or {}).get("display_text", ""),
        "customization": (f"Artwork set-up: ${setup_fee:.2f} / Branding per piece: ${per_unit:.2f}"
                          if setup_fee > 0 or per_unit > 0 else "Contact for pricing"),
    }


def moq_table_csv(table):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(table["columns"])
    writer.writerow(table["row"])
    return out.getvalue()


def notes_and_warnings(proposal):
    items = proposal["proposal_products"]
    notes = [(i["product_data"].get("Product/Service", ""), i["pricing_notes"]) for i in items if i.get("pricing_notes") and not i.get("manual_override")]
    warnings = [(i["product_data"].get("Product/Service", ""), i["validation_warning"]) for i in items if i.get("validation_warning") and not i.get("manual_override")]
    return notes, warnings
