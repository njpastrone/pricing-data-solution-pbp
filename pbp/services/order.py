"""
Order building and pricing, independent of any UI.

An "order" is the same dict the Streamlit app saves to the saved_orders sheet
(order_items, shipping, discounts, client_info, order_notes ...), so orders
move freely between the two apps. The functions here reproduce the Tab 3 and
Tab 4 arithmetic of app.py line for line; the golden tests pin the numbers.
"""

import copy
from datetime import date, datetime

from pbp.core.helpers import (
    calculate_credit_card_fee,
    calculate_markup_from_price,
    calculate_moq,
    calculate_product_tariff,
    calculate_split_totals,
    clean_price,
    convert_proposal_to_order,
    get_column_value,
    get_shipping_costs,
    get_tariff_rate,
    round_to_nearest_fifty_cents,
    apply_marketing_rounding,
    format_product_with_variant,
)
from pbp.core.pricing_engine import calculate_pbp_msrp, get_unit_price_new_system

DISCOUNT_OPTIONS = ["None", "Non-profit (5%)", "Volume Order (5%)", "Custom"]
PAYMENT_TERMS = ["Net 30", "Net 15", "Net 60", "Due on Receipt", "50% Deposit", "Custom"]
PAYMENT_METHODS = ["Check", "ACH", "Credit Card", "Wire Transfer"]
SHIP_METHODS = ["Ground", "Air", "Freight", "Other"]
CONTACT_ROLES = ["Primary Contact", "Billing Contact", "Technical Contact", "Shipping Contact", "Other"]
NOTE_CATEGORIES = [
    ("internal_pbp_team", "Internal Notes (For PBP Team)"),
    ("internal_bookkeeping", "Internal Notes (For Bookkeeping)"),
    ("external_partners", "External Notes (For Partners/POs)"),
    ("external_clients", "External Notes (For Clients/Invoices)"),
]
MAX_PHOTOS_PER_PRODUCT = 5


# ----------------------------------------------------------------------------
# New order and defaults
# ----------------------------------------------------------------------------

def new_contact(role="Primary Contact"):
    return {"name": "", "email": "", "phone": "", "role": role}


def new_client_info():
    return {
        "is_new_client": True,
        "company_name": "",
        "contacts": [new_contact()],
        "client_po": "",
        "billing_address": "",
        "shipping_type": "One Location",
        "ship_method": "Ground",
        "shipping_address": "",
        "payment_timeline": "Net 30",
        "payment_preference": "Check",
        "client_in_hands_date": None,
        "pbp_in_hands_date": None,
        "order_submitted_by": "",
        "order_submitted_date": date.today(),
        "cost_submitted_by": "",
        "cost_submitted_date": None,
    }


def new_order():
    """An empty order with the same defaults the Streamlit app starts with."""
    return {
        "order_items": [],
        "order_shipping": 0.0,
        "partner_shipping": 0.0,
        "sales_tax": 0.0,
        "kitting_pbp_cost": 0.0,
        "kitting_client_price": 0.0,
        "order_discount_type": "none",
        "order_discount_preset": "Non-profit Discount (5%)",
        "order_discount_custom_desc": "",
        "order_discount_custom_value": 0.0,
        "order_use_marketing_rounding": False,
        "order_fifty_cent_rounding": True,
        "apply_cc_fee": False,
        "cc_fee_percent": 3.0,
        "client_info": new_client_info(),
        "order_notes": {key: "" for key, _ in NOTE_CATEGORIES},
        "order_confirmed": False,
        "product_photos": {},            # saved photo metadata {product: [{file_id, filename}]}
        "partner_contacts_editable": {},  # Tab 4 edits to partner POCs
    }


def normalize(order):
    """Fill in keys older saved orders lack (same migrations the Streamlit app applies on load)."""
    base = new_order()
    for key, value in base.items():
        order.setdefault(key, value)
    if "internal_pbp_team" not in order.get("order_notes", {}):
        order["order_notes"] = {key: "" for key, _ in NOTE_CATEGORIES}
    client = order["client_info"]
    for key, value in new_client_info().items():
        client.setdefault(key, value)
    if "contact_name" in client:  # pre-contacts structure
        client["contacts"] = [{"name": client.pop("contact_name", ""), "email": client.pop("contact_email", ""), "phone": "", "role": "Primary Contact"}]
    if not client.get("contacts"):
        client["contacts"] = [new_contact()]
    for item in order["order_items"]:
        normalize_item(item)
    return order


def normalize_item(item):
    item.setdefault("edited_description", "")
    item.setdefault("pricing_method", "Standard markup")
    item.setdefault("pricing_notes", "")
    item.setdefault("manual_override", False)
    item.setdefault("validation_warning", None)
    item.setdefault("include_kitting", False)
    item.setdefault("kitting_pbp_cost", 0.0)
    item.setdefault("kitting_client_price", 0.0)
    item.setdefault("kitting_description", "")
    item.setdefault("kitting_quantity", 1)
    item.setdefault("customization_addons", [])
    for key in ("base_price", "product_subtotal", "markup_amount", "product_total", "total_per_unit", "tariff_base",
                "customization_setup_total", "customization_unit_total", "partner_customization_setup_total",
                "partner_customization_unit_total", "customization_setup_cost", "customization_unit_cost",
                "customization_setup_fee", "customization_per_unit", "partner_customization_setup_fee",
                "partner_customization_per_unit", "tariff_rate_percent", "tariff_amount"):
        item.setdefault(key, 0.0)
    item.setdefault("customization_minimum_qty", 0)
    item.setdefault("apply_custom_minimum", False)
    item.setdefault("include_customization", False)
    for addon in item["customization_addons"]:
        if "setup_fee" in addon and "client_setup_fee" not in addon:
            addon["client_setup_fee"] = addon.get("setup_fee", 0.0)
            addon["partner_setup_fee"] = 0.0
        if "per_unit_cost" in addon and "client_per_unit_cost" not in addon:
            addon["client_per_unit_cost"] = addon.get("per_unit_cost", 0.0)
            addon["partner_per_unit_cost"] = 0.0
    return item


def display_name(item):
    return format_product_with_variant(item.get("product_name", ""), item.get("selected_variant"))


# ----------------------------------------------------------------------------
# Adding products
# ----------------------------------------------------------------------------

def _markup_from_pricing(pricing_result):
    """Markup % implied by the spreadsheet pricing method (Tab 3 Option A/B/C logic)."""
    if pricing_result["method_used"] == "Standard markup":
        return pricing_result["calculation_details"].get("markup_percent", 100.0)
    base_cost = pricing_result["calculation_details"]["per_item_cost"]
    if base_cost > 0:
        return ((pricing_result["pbp_msrp"] / base_cost) - 1) * 100
    return 100.0


def default_markup(product_data):
    """PBP Standard Markup from the spreadsheet (2.0 = 100%), else 100%."""
    multiplier = get_column_value(product_data, "PBP Standard Markup", None, None)
    try:
        multiplier = float(multiplier)
        if multiplier > 0:
            return (multiplier - 1) * 100
    except (TypeError, ValueError):
        pass
    return 100.0


def catalog_item(product_data, quantity=1, use_msrp=True, variant=None, markup_override=None, with_tariff=False):
    """
    A new order line for a catalog product (Tab 3 Option C, also used by the
    Option A import with with_tariff=True and the client's quantity).

    Returns None when the product has no usable price.
    """
    product_data = dict(product_data)
    pricing_result = calculate_pbp_msrp(product_data, quantity, user_markup_override=markup_override)
    validation_warning = None
    if pricing_result["validation_status"] == "mismatch":
        validation_warning = (f"Price mismatch: Spreadsheet=${pricing_result['spreadsheet_msrp']:.2f} | "
                              f"Calculated=${pricing_result['pbp_msrp']:.2f}")
    markup = _markup_from_pricing(pricing_result) if use_msrp else default_markup(product_data)

    base_price, tier_range, tier_column = get_unit_price_new_system(product_data, quantity)
    if not base_price:
        return None

    item = {
        "product_name": product_data.get("Product/Service", "Unknown Product"),
        "partner": product_data.get("Partner", "Unknown Partner"),
        "product_data": product_data,
        "product_data_row": product_data,
        "quantity": quantity,
        "markup_percent": markup,
        "selected_variant": variant or None,
        "pricing_method": pricing_result["method_used"],
        "pricing_notes": get_column_value(product_data, "Pricing Notes", "", ""),
        "validation_warning": validation_warning,
        "manual_override": not use_msrp,
        "include_customization": False,
        "customization_description": product_data.get("Customization Info", ""),
        "customization_setup_fee": float(clean_price(get_column_value(product_data, "Client Price: Customization Setup Fee", "Customization Setup Fee", "")) or 0.0),
        "customization_per_unit": float(clean_price(get_column_value(product_data, "Client Price: Customization Cost per Unit", "Customization Cost per Unit", "")) or 0.0),
        "customization_minimum_qty": 0,
        "apply_custom_minimum": False,
        "include_tariff": with_tariff,
        "is_custom": False,
        "include_kitting": False,
        "kitting_pbp_cost": 0.0,
        "kitting_client_price": 0.0,
        "kitting_description": "",
        "kitting_quantity": 1,
        "customization_addons": [],
        "base_price": base_price,
        "tier_range": tier_range,
        "tier_column": tier_column,
        "product_ref": product_data.get("Partner Product SKU/REF", "N/A"),
        "country_of_origin_made_in": product_data.get("Country of Origin (Made In)", "N/A"),
        "country_of_origin_ships_from": product_data.get("Country of Origin (Ships From)", "N/A"),
        "tariff_rate_percent": 0.0,
        "tariff_amount": 0.0,
        "edited_description": "",
    }
    if with_tariff:
        subtotal = base_price * quantity
        item["tariff_rate_percent"] = get_tariff_rate(product_data, subtotal)
        item["tariff_info"] = f"{product_data.get('Country', 'N/A')} - {item['tariff_rate_percent']}%" if item["tariff_rate_percent"] > 0 else ""
        item["proposal_markup_percent"] = markup
    if markup_override is not None:
        item["proposal_markup_percent"] = markup_override
    return recalculate(item)


def custom_product_item(name, partner, base_cost):
    """Tab 3 'Create Custom Product': a one-off product priced like a flat-rate catalog row."""
    product_data = {
        "Product/Service": name.strip(), "Partner": partner, "Pricing Tiers (Y/N)": "N",
        "PBP Cost (No Tiers/Tier 1)": base_cost, "PBP Standard Markup": 100.0,
        "Country of Origin (Made In)": "", "Country of Origin (Ships From)": "", "Vendor Published MSRP": 0,
        "Customization Setup Fee": 0, "Customization Cost per Unit": 0, "Customization Info": "",
        "Marketing Description": "", "Tariff Estimate (%)": 0, "MOQ (PBP)": "", "MOV (PBP)": "",
        "MOQ (Partner)": "", "MOV (Partner)": "", "Tariff Info": "", "Purchase Description": "", "Units per Case": 1,
    }
    item = {
        "product_name": name.strip(), "partner": partner, "product_data": product_data, "quantity": 1,
        "markup_percent": 100.0, "selected_variant": None, "pricing_method": "Standard markup", "pricing_notes": "",
        "validation_warning": None, "manual_override": False, "include_customization": False,
        "customization_setup_fee": 0.0, "customization_per_unit": 0.0, "customization_minimum_qty": 0,
        "apply_custom_minimum": False, "include_tariff": False, "is_custom_product": True, "source": "custom",
        "include_kitting": False, "kitting_pbp_cost": 0.0, "kitting_client_price": 0.0, "kitting_description": "",
        "kitting_quantity": 1, "customization_addons": [], "base_price": float(base_cost), "tier_range": "No Tiers",
        "tier_column": "PBP Cost (No Tiers/Tier 1)", "product_ref": "CUSTOM", "country_of_origin_made_in": "",
        "country_of_origin_ships_from": "", "customization_description": "", "tariff_rate_percent": 0.0,
        "tariff_amount": 0.0, "edited_description": "",
    }
    return recalculate(item)


def custom_line_item(name, quantity, description, total_price):
    """Tab 3 'Add Custom Line Item': a fixed-price service line (no markup, cost = price)."""
    quantity = max(1, int(quantity))
    return {
        "product_name": name, "product_ref": "CUSTOM", "partner": "Custom", "quantity": quantity,
        "markup_percent": 0.0, "include_labels": False, "base_price": total_price / quantity,
        "tier_range": "N/A", "tier_column": "N/A", "additional_costs": {}, "product_subtotal": total_price,
        "art_setup_total": 0, "label_cost_total": 0, "subtotal_before_markup": total_price, "markup_amount": 0,
        "product_total": total_price, "total_per_unit": total_price / quantity, "is_custom": True,
        "custom_description": description or "Custom line item", "country_of_origin": "",
        "tariff_rate_percent": 0.0, "tariff_info": "", "tariff_base": 0.0, "tariff_amount": 0.0,
        "edited_description": "", "include_kitting": False, "kitting_pbp_cost": 0.0, "kitting_client_price": 0.0,
        "kitting_description": "", "kitting_quantity": 1,
    }


def add_items(order, items):
    """Append items and auto-fill partner shipping from the most expensive product shipping (Tab 3 behaviour)."""
    max_shipping = 0.0
    for item in items:
        order["order_items"].append(normalize_item(item))
        if not item.get("is_custom"):
            pbp_shipping, _ = get_shipping_costs(item.get("product_data", {}))
            max_shipping = max(max_shipping, pbp_shipping)
    if max_shipping > 0 and not order.get("partner_shipping"):
        order["partner_shipping"] = max_shipping
    return order


def items_from_proposal(proposal_items):
    """Order lines for proposal products (Tab 3 Option B), quantity and markup preserved."""
    return [recalculate(convert_proposal_to_order(item, get_unit_price_new_system, calculate_product_tariff))
            for item in proposal_items]


def import_form_response(order, response, df_template, proposal_items=()):
    """
    Tab 3 Option A: client info and products from a parsed client form response.

    Returns (imported_names, skipped_names).
    """
    client = response["client_info"]
    shipping = response["shipping_info"]
    payment = response["payment_info"]
    in_hands = None
    if shipping.get("in_hands_date"):
        try:
            in_hands = datetime.strptime(shipping["in_hands_date"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            in_hands = None
    order["client_info"] = {
        **new_client_info(),
        "is_new_client": client.get("client_type", "New") == "New",
        "company_name": client.get("company_name", ""),
        "contacts": [{"name": client.get("contact_name", ""), "email": client.get("contact_email", ""),
                      "phone": client.get("contact_phone", ""), "role": "Primary Contact"}],
        "billing_address": shipping.get("billing_address", ""),
        "shipping_type": "Drop Shipping" if shipping.get("drop_shipping") == "Yes" else "One Location",
        "shipping_address": shipping.get("shipping_address", ""),
        "payment_timeline": payment.get("payment_preference") or "Net 30",
        "payment_preference": payment.get("payment_method") or "Check",
        "client_in_hands_date": in_hands,
    }

    from pbp.sheets.catalog import find_product
    imported, skipped, items = [], [], []
    for product in response["products"]:
        product_data = find_product(df_template, product["name"])
        if product_data is None:
            skipped.append(product["name"])
            continue
        proposal_markup = next((p["markup_percent"] for p in proposal_items
                                if p["product_data"].get("Product/Service", "").lower() == product["name"].lower()), None)
        item = catalog_item(product_data, product["quantity"], markup_override=proposal_markup, with_tariff=True)
        if item is None:
            skipped.append(product["name"])
            continue
        item["client_customization_notes"] = product.get("customization_notes", "")
        items.append(item)
        imported.append(item["product_name"])
    add_items(order, items)
    return imported, skipped


# ----------------------------------------------------------------------------
# Editing a line
# ----------------------------------------------------------------------------

def recalculate(item):
    """Recompute every derived number on a line (the Tab 3 'RECALCULATE PRICING' block)."""
    if item.get("is_custom"):
        return item
    normalize_item(item)
    quantity = max(1, int(item.get("quantity", 1)))
    item["quantity"] = quantity
    product_data = item["product_data"]
    base_price, tier_range, tier_column = get_unit_price_new_system(product_data, quantity)
    if not base_price:
        base_price = item.get("base_price", 0.0) or 0.0
        tier_range, tier_column = item.get("tier_range", ""), item.get("tier_column", "")

    include_custom = bool(item.get("include_customization"))
    custom_qty = quantity
    if include_custom and item.get("apply_custom_minimum") and item.get("customization_minimum_qty", 0) > quantity:
        custom_qty = int(item["customization_minimum_qty"])
    named_addons = [a for a in item.get("customization_addons", []) if a.get("name")]

    if include_custom:
        setup_total = float(item.get("customization_setup_fee", 0.0)) + sum(a.get("client_setup_fee", 0.0) for a in named_addons)
        unit_total = (float(item.get("customization_per_unit", 0.0)) + sum(a.get("client_per_unit_cost", 0.0) for a in named_addons)) * custom_qty
        partner_setup_total = float(item.get("partner_customization_setup_fee", 0.0)) + sum(a.get("partner_setup_fee", 0.0) for a in named_addons)
        partner_unit_total = (float(item.get("partner_customization_per_unit", 0.0)) + sum(a.get("partner_per_unit_cost", 0.0) for a in named_addons)) * custom_qty
    else:
        setup_total = unit_total = partner_setup_total = partner_unit_total = 0.0
        item["customization_addons"] = []

    product_subtotal = base_price * quantity
    markup_amount = product_subtotal * (float(item.get("markup_percent", 100.0)) / 100)
    subtotal_before_markup = product_subtotal + setup_total + unit_total
    product_total = subtotal_before_markup + markup_amount

    item.update({
        "base_price": base_price, "tier_range": tier_range, "tier_column": tier_column,
        "product_subtotal": product_subtotal, "subtotal_before_markup": subtotal_before_markup,
        "markup_amount": markup_amount, "product_total": product_total, "total_per_unit": product_total / quantity,
        "customization_setup_total": setup_total, "customization_unit_total": unit_total,
        "partner_customization_setup_total": partner_setup_total, "partner_customization_unit_total": partner_unit_total,
        "customization_setup_cost": partner_setup_total, "customization_unit_cost": partner_unit_total,
        "tariff_base": product_subtotal,
    })
    if not include_custom:
        item["customization_description"] = item.get("customization_description", "")
    if not item.get("include_kitting"):
        item.update({"kitting_quantity": 1, "kitting_pbp_cost": 0.0, "kitting_client_price": 0.0, "kitting_description": ""})
    item["tariff_amount"] = calculate_product_tariff(product_subtotal, item.get("tariff_rate_percent", 0.0) or 0.0) if item.get("tariff_rate_percent", 0) else 0.0
    return item


def client_price_per_unit(item, fifty_cent_rounding):
    """Product price per unit shown to the client (base + markup, optionally rounded to $0.50)."""
    quantity = item.get("quantity", 1) or 1
    raw = (item.get("product_subtotal", 0.0) + item.get("markup_amount", 0.0)) / quantity
    return round_to_nearest_fifty_cents(raw, fifty_cent_rounding), raw


def set_client_price(item, client_price):
    """Bidirectional pricing: entering a client price sets the markup that produces it."""
    item["markup_percent"] = calculate_markup_from_price(item.get("base_price", 0.0), float(client_price))
    return recalculate(item)


def moq_warning(item):
    """'Below MOQ' note for a line, or None."""
    if item.get("is_custom") or item.get("is_custom_product"):
        return None
    base_price = item.get("base_price")
    if not base_price:
        return None
    estimate = base_price * (1 + item.get("markup_percent", 100) / 100)
    result = calculate_moq(estimate, item.get("product_data", {}))
    if result and result.get("moq") and item.get("quantity", 1) < result["moq"]:
        return f"Below MOQ of {result['moq']} ({result['breakdown']['source']})"
    return None


def price_change_from_proposal(item, fifty_cent_rounding):
    """(quoted, current, reasons) when a proposal product's price moved, else None."""
    quoted = item.get("quoted_price_per_unit", 0.0) or 0.0
    if quoted <= 0:
        return None
    current, _ = client_price_per_unit(item, fifty_cent_rounding)
    if abs(current - quoted) <= 0.01:
        return (quoted, current, [])
    reasons = []
    if item.get("proposal_tier_column") and item.get("tier_column") and item["proposal_tier_column"] != item["tier_column"]:
        reasons.append(f"Tier change: {item['proposal_tier_column']} ({item.get('proposal_tier_range', '')}) to {item['tier_column']} ({item.get('tier_range', '')})")
    if abs(item.get("proposal_markup_percent", 0) - item.get("markup_percent", 0)) > 0.01:
        reasons.append(f"Markup change: {item.get('proposal_markup_percent', 0):.0f}% to {item.get('markup_percent', 0):.0f}%")
    return (quoted, current, reasons)


# ----------------------------------------------------------------------------
# Order-level numbers (Tab 3 "4. Order Summary")
# ----------------------------------------------------------------------------

def discount(order):
    """(percent, description) for the order's discount setting."""
    kind = order.get("order_discount_type", "none")
    if kind == "preset":
        preset = order.get("order_discount_preset", "")
        percent = 0.0
        if "(" in preset and "%" in preset:
            percent = float(preset.split("(")[1].split("%")[0])
        return percent, preset
    if kind == "custom":
        percent = float(order.get("order_discount_custom_value", 0.0) or 0.0)
        return percent, order.get("order_discount_custom_desc") or f"Custom Discount ({percent}%)"
    return 0.0, ""


def discount_option(order):
    kind = order.get("order_discount_type", "none")
    if kind == "preset":
        return "Volume Order (5%)" if "Volume Order" in order.get("order_discount_preset", "") else "Non-profit (5%)"
    if kind == "custom":
        return "Custom"
    return "None"


def set_discount_option(order, option, custom_value=None):
    if option == "Non-profit (5%)":
        order.update(order_discount_type="preset", order_discount_preset="Non-profit Discount (5%)", order_discount_custom_value=0.0, order_discount_custom_desc="")
    elif option == "Volume Order (5%)":
        order.update(order_discount_type="preset", order_discount_preset="Volume Order Discount (5%)", order_discount_custom_value=0.0, order_discount_custom_desc="")
    elif option == "Custom":
        order["order_discount_type"] = "custom"
        if custom_value is not None:
            order["order_discount_custom_value"] = float(custom_value)
    else:
        order.update(order_discount_type="none", order_discount_custom_value=0.0, order_discount_custom_desc="")


def totals(order):
    """Every number on the Order Summary, plus the summary table rows."""
    items = order.get("order_items", [])
    rounding = order.get("order_fifty_cent_rounding", True)
    split = calculate_split_totals(items, fifty_cent_rounding=rounding)
    discount_percent, discount_description = discount(order)
    discount_amount = split["products_only_client_price"] * (discount_percent / 100)
    subtotal_after_discount = split["products_only_client_price"] - discount_amount + split["customization_client_price"]

    shipping = float(order.get("order_shipping", 0.0) or 0.0)
    sales_tax = float(order.get("sales_tax", 0.0) or 0.0)
    tariff = sum(item.get("tariff_amount", 0.0) or 0.0 for item in items)
    global_kitting_pbp = float(order.get("kitting_pbp_cost", 0.0) or 0.0)
    global_kitting_client = float(order.get("kitting_client_price", 0.0) or 0.0)
    per_kitting_pbp = sum(item.get("kitting_pbp_cost", 0.0) * item.get("kitting_quantity", 1) for item in items if item.get("include_kitting"))
    per_kitting_client = sum(item.get("kitting_client_price", 0.0) * item.get("kitting_quantity", 1) for item in items if item.get("include_kitting"))
    kitting_pbp = global_kitting_pbp + per_kitting_pbp
    kitting_client = global_kitting_client + per_kitting_client

    total_before_cc = subtotal_after_discount + shipping + sales_tax + kitting_client + tariff
    cc_fee_amount = calculate_credit_card_fee(total_before_cc, order.get("apply_cc_fee", False), order.get("cc_fee_percent", 3.0))
    total_quote = total_before_cc + cc_fee_amount
    total_quote = round_to_nearest_fifty_cents(total_quote, rounding)
    total_quote = apply_marketing_rounding(total_quote, order.get("order_use_marketing_rounding", False))
    total_units = sum(item.get("quantity", 0) for item in items)
    total_pbp_cost = split["total_pbp_cost"] + shipping + kitting_pbp + tariff

    result = {
        "split": split, "discount_percent": discount_percent, "discount_description": discount_description,
        "discount_amount": discount_amount, "subtotal_after_discount": subtotal_after_discount,
        "shipping": shipping, "sales_tax": sales_tax, "tariff": tariff,
        "global_kitting_pbp": global_kitting_pbp, "global_kitting_client": global_kitting_client,
        "per_product_kitting_pbp": per_kitting_pbp, "per_product_kitting_client": per_kitting_client,
        "kitting_pbp": kitting_pbp, "kitting_client": kitting_client, "total_before_cc": total_before_cc,
        "cc_fee_amount": cc_fee_amount, "total_quote": total_quote, "total_units": total_units,
        "total_pbp_cost": total_pbp_cost, "avg_per_unit": total_quote / total_units if total_units else 0.0,
        "products_subtotal": sum(item.get("product_total", 0.0) for item in items),
    }
    result["rows"] = _summary_rows(order, result)
    return result


def _money(value):
    return f"${value:.2f}"


def _summary_rows(order, t):
    """The 6-column Order Summary table: Item, Qty, PBP/unit, PBP, Client/unit, Client."""
    items = order["order_items"]
    rounding = order.get("order_fifty_cent_rounding", True)
    rows = []
    for item in items:
        if item.get("is_custom"):
            rows.append([item["product_name"], item["quantity"], _money(item["total_per_unit"]), _money(item["product_total"]),
                         _money(item["total_per_unit"]), _money(item["product_total"])])
            continue
        pbp_cost = item.get("product_subtotal", 0)
        qty = item["quantity"] or 1
        client_unit, _ = client_price_per_unit(item, rounding)
        rows.append([f"Base Product: {item['product_name']}", qty, _money(pbp_cost / qty), _money(pbp_cost),
                     _money(client_unit), _money(client_unit * qty)])
    split = t["split"]
    rows.append(["Products Subtotal", "", "", _money(split["products_pbp_cost"]), "", _money(split["products_client_price"])])

    if split["customization_client_price"] > 0:
        rows.append(["", "", "", "", "", ""])
        for item in items:
            if item.get("is_custom"):
                continue
            setup_pbp, setup_client = item.get("customization_setup_cost", 0), item.get("customization_setup_total", 0)
            unit_pbp, unit_client = item.get("customization_unit_cost", 0), item.get("customization_unit_total", 0)
            if setup_client > 0:
                rows.append([f"{item['product_name']} - Setup", "one-time", _money(setup_pbp), _money(setup_pbp), _money(setup_client), _money(setup_client)])
            if unit_client > 0:
                custom_qty = item.get("customization_minimum_qty", item["quantity"]) if item.get("apply_custom_minimum") else item["quantity"]
                custom_qty = custom_qty or 1
                rows.append([f"{item['product_name']} - Per Unit", custom_qty, _money(unit_pbp / custom_qty), _money(unit_pbp),
                             _money(unit_client / custom_qty), _money(unit_client)])
        rows.append(["Customization Subtotal", "", "", _money(split["customization_pbp_cost"]), "", _money(split["customization_client_price"])])

    if t["per_product_kitting_client"] > 0:
        rows.append(["", "", "", "", "", ""])
        for item in items:
            if item.get("is_custom") or not item.get("include_kitting") or item.get("kitting_client_price", 0) <= 0:
                continue
            qty = item.get("kitting_quantity", 1)
            rows.append([f"{item['product_name']} - {item.get('kitting_description') or 'Kitting'}", str(qty),
                         _money(item["kitting_pbp_cost"]), _money(item["kitting_pbp_cost"] * qty),
                         _money(item["kitting_client_price"]), _money(item["kitting_client_price"] * qty)])
        rows.append(["Per-Product Kitting Subtotal", "", "", _money(t["per_product_kitting_pbp"]), "", _money(t["per_product_kitting_client"])])

    rows.append(["", "", "", "", "", ""])
    if t["discount_percent"] > 0:
        rows.append([f"Discount ({t['discount_description']})", "", "", "", f"-{_money(t['discount_amount'])}", ""])
    rows.append(["Shipping", "", "", _money(t["shipping"]), "", _money(t["shipping"])])
    if t["sales_tax"] > 0:
        rows.append(["Sales Tax (Estimated)", "", "", "", "", _money(t["sales_tax"])])
    if t["global_kitting_pbp"] > 0 or t["global_kitting_client"] > 0:
        rows.append(["Kitting/Gift Set Assembly (Sale-wide)", "", "", _money(t["global_kitting_pbp"]), "", _money(t["global_kitting_client"])])
    for item in items:
        if item.get("tariff_amount", 0) > 0:
            rows.append([f"Tariff: {item['product_name']} ({item.get('tariff_rate_percent', 0)}% - {item.get('country_of_origin', 'Unknown')})",
                         "", "", _money(item["tariff_amount"]), "", _money(item["tariff_amount"])])
    if order.get("apply_cc_fee") and t["cc_fee_amount"] > 0:
        rows.append([f"Credit Card Fee ({order.get('cc_fee_percent', 3.0)}%)", "", "", "", "", _money(t["cc_fee_amount"])])
    rows.append(["TOTAL", f"{t['total_units']} units", "", _money(t["total_pbp_cost"]), "", _money(t["total_quote"])])
    return rows


# ----------------------------------------------------------------------------
# Saving
# ----------------------------------------------------------------------------

SAVED_KEYS = [
    "order_items", "order_shipping", "partner_shipping", "sales_tax", "kitting_pbp_cost", "kitting_client_price",
    "order_discount_type", "order_discount_preset", "order_discount_custom_desc", "order_discount_custom_value",
    "order_use_marketing_rounding", "order_fifty_cent_rounding", "apply_cc_fee", "cc_fee_percent", "client_info",
    "order_notes", "order_confirmed", "product_photos", "partner_contacts_editable",
]


def saved_payload(order):
    """The dict written to the saved_orders sheet (same keys as the Streamlit app, plus the two web-only ones)."""
    return copy.deepcopy({key: order.get(key) for key in SAVED_KEYS if key in order})
