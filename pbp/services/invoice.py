"""
Invoice and Purchase Order request form (Tab 4 of the Streamlit app).

build() turns an order into the four bookkeeper tables plus line items and
totals; to_csv() and to_html() render them the same way the Streamlit app
downloads them.
"""

import base64
import csv
import io
import pathlib
from datetime import date, datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pbp.core.helpers import get_column_value, validate_invoice_completeness
from pbp.core.pricing_engine import calculate_pbp_msrp
from pbp.services import order as order_service

COLUMNS = ["PARTNER", "DESCRIPTION (Invoice)", "DESCRIPTION (PO)", "QTY", "IN-HANDS from Partner",
           "COST/UNIT", "TOTAL COST", "SELL PRICE/UNIT", "TOTAL SELL PRICE"]

# Printed at the top of every invoice/PO (parity with the Streamlit app's dropshipping instructions block)
DROPSHIPPING_NOTES = "For drop shipping orders, please provide: destination addresses, quantities per location, and any special delivery instructions"

_templates = Environment(loader=FileSystemLoader(str(pathlib.Path(__file__).parent.parent / "web" / "templates")),
                         autoescape=select_autoescape(["html"]))


def format_date(value):
    """MM/DD/YY, or the string itself, or 'Not specified'."""
    if not value:
        return "Not specified"
    if isinstance(value, str):
        return value
    try:
        return value.strftime("%m/%d/%y")
    except AttributeError:
        return str(value)


def _money(value):
    return f"${value:.2f}"


def _clean(text):
    text = str(text or "").strip()
    return text if text and text.lower() != "nan" else ""


def invoice_description(product_data, product_name):
    """Billing Description, else Marketing Description, else the product name."""
    return _clean(get_column_value(product_data, "billing_description", None)) or \
        _clean(get_column_value(product_data, "marketing_description", None)) or product_name


def po_description(product_data, product_name):
    """Purchase Description, else Billing Description, else the product name."""
    return _clean(get_column_value(product_data, "purchase_description", None)) or \
        _clean(get_column_value(product_data, "billing_description", None)) or product_name


def _line(partner, inv_desc, po_desc, qty, in_hands, cost_unit, cost_total, sell_unit, sell_total):
    return dict(zip(COLUMNS, [partner, inv_desc, po_desc, qty, in_hands, _money(cost_unit), _money(cost_total), _money(sell_unit), _money(sell_total)]))


def line_items(order, df_template=None):
    """Table 4 rows: one per product plus indented kitting, customization, add-on and tariff lines."""
    lines = []
    for item in order["order_items"]:
        if item.get("is_custom"):
            desc = item.get("custom_description", "Custom line item")
            unit, total = item.get("total_per_unit", 0), item.get("product_total", 0)
            lines.append(_line("Custom", desc, desc, item["quantity"], "N/A", unit, total, unit, total))
            continue

        partner = item["partner"]
        name = order_service.display_name(item)
        product_data = None
        if df_template is not None:
            match = df_template[(df_template["Product/Service"] == item.get("product_ref", item["product_name"])) & (df_template["Partner"] == partner)]
            if match.empty:
                match = df_template[(df_template["Product/Service"] == item["product_name"]) & (df_template["Partner"] == partner)]
            if not match.empty:
                product_data = match.iloc[0].to_dict()
        inv_desc = invoice_description(product_data, name) if product_data is not None else name
        po_desc_text = po_description(product_data, name) if product_data is not None else name
        if item.get("edited_description"):
            inv_desc = po_desc_text = item["edited_description"]
        # A customization description prints on the product line whether or not customization is ticked
        customization_desc = item.get("customization_description", "")
        if customization_desc:
            inv_desc = f"{inv_desc} (Customization: {customization_desc})"
            po_desc_text = f"{po_desc_text} (Customization: {customization_desc})"

        qty = item["quantity"] or 1
        in_hands = str(item.get("partner_in_hands_date") or "TBD")

        cost_unit, sell_unit = None, None
        if product_data is not None:
            try:
                override = item.get("markup_percent") if item.get("manual_override") else None
                result = calculate_pbp_msrp(product_data, quantity=qty, user_markup_override=override)
                cost_unit, sell_unit = result["calculation_details"]["base_cost"], result["pbp_msrp"]
            except Exception:
                cost_unit = None
        if cost_unit is None:
            cost_unit = item.get("partner_cost_per_unit", item.get("base_price", 0))
            sell_unit = (item.get("product_subtotal", 0) + item.get("markup_amount", 0)) / qty
        lines.append(_line(partner, inv_desc, po_desc_text, qty, in_hands, cost_unit, cost_unit * qty, sell_unit, sell_unit * qty))

        if item.get("include_kitting"):
            kq = item.get("kitting_quantity", 1)
            kdesc = f"  └ {item.get('kitting_description') or 'Kitting'}"
            lines.append(_line(partner, kdesc, kdesc, kq, in_hands, item.get("kitting_pbp_cost", 0.0), item.get("kitting_pbp_cost", 0.0) * kq,
                               item.get("kitting_client_price", 0.0), item.get("kitting_client_price", 0.0) * kq))

        if item.get("include_customization"):
            cdesc = customization_desc or "Custom work"
            setup, unit_total = item.get("customization_setup_total", 0), item.get("customization_unit_total", 0)
            p_setup, p_unit_total = item.get("partner_customization_setup_total", 0), item.get("partner_customization_unit_total", 0)
            if setup > 0 or p_setup > 0:
                lines.append(_line(partner, f"  └ Setup Fee: {cdesc}", f"  └ Setup: {cdesc}", 1, in_hands, p_setup, p_setup, setup, setup))
            if unit_total > 0 or p_unit_total > 0:
                lines.append(_line(partner, f"  └ Customization (per unit): {cdesc}", f"  └ Per Unit Customization: {cdesc}", qty, in_hands,
                                   item.get("partner_customization_per_unit", 0), p_unit_total, item.get("customization_per_unit", 0), unit_total))
            for addon in item.get("customization_addons", []):
                if not addon.get("name"):
                    continue
                ps, cs = addon.get("partner_setup_fee", addon.get("setup_fee", 0.0)), addon.get("client_setup_fee", addon.get("setup_fee", 0.0))
                pu, cu = addon.get("partner_per_unit_cost", addon.get("per_unit_cost", 0.0)), addon.get("client_per_unit_cost", addon.get("per_unit_cost", 0.0))
                if ps > 0 or cs > 0:
                    lines.append(_line(partner, f"  └ Add-On Setup: {addon['name']}", f"  └ Add-On Setup: {addon['name']}", 1, in_hands, ps, ps, cs, cs))
                if pu > 0 or cu > 0:
                    lines.append(_line(partner, f"  └ Add-On (per unit): {addon['name']}", f"  └ Add-On: {addon['name']}", qty, in_hands, pu, pu * qty, cu, cu * qty))

        if item.get("tariff_amount", 0) > 0:
            rate, amount = item.get("tariff_rate_percent", 0), item["tariff_amount"]
            country = item.get("country_of_origin", "Unknown")
            lines.append(_line(partner, f"  └ Tariff ({country}, {rate:.1f}%)", f"  └ Tariff ({rate:.1f}%)", qty, "N/A", amount / qty, amount, amount / qty, amount))

    partner_shipping, client_shipping = order.get("partner_shipping", 0) or 0, order.get("order_shipping", 0) or 0
    if partner_shipping > 0 or client_shipping > 0:
        lines.append(_line("Shipping", "Shipping to Client", "Shipping from Partner", 1, "N/A", partner_shipping, partner_shipping, client_shipping, client_shipping))
    kp, kc = order.get("kitting_pbp_cost", 0) or 0, order.get("kitting_client_price", 0) or 0
    if kp > 0 or kc > 0:
        lines.append(_line("Kitting (Sale-wide)", "Gift Set Assembly & Packaging", "Kitting & Assembly Services", 1, "N/A", kp, kp, kc, kc))
    return lines


def build(order, df_template=None, partner_contacts=None):
    """Everything the invoice/PO page, CSV and HTML need."""
    client = order["client_info"]
    contacts = client.get("contacts") or []
    if len(contacts) == 1:
        contact_display = f"{contacts[0].get('name') or 'Not specified'} <{contacts[0].get('email') or 'Not specified'}>"
    elif contacts:
        contact_display = " | ".join(
            f"{c.get('name') or 'Not specified'} <{c.get('email') or 'Not specified'}>" + (f" ({c['role']})" if c.get("role") else "")
            for c in contacts)
    else:
        contact_display = "Not specified <Not specified>"
    billing_email = contacts[0].get("email") or "Not specified" if contacts else "Not specified"

    client_rows = [
        ("Company/Client Name", client.get("company_name") or "Not specified"),
        ("New Client?", "[X] Yes  [ ] No" if client.get("is_new_client") else "[ ] Yes  [X] No"),
        ("Contact + Email", contact_display),
        ("Company Billing Address + Email", f"{(client.get('billing_address') or 'Not specified')} | {billing_email}"),
        ("Company Shipping Address", f"{(client.get('shipping_address') or 'Not specified')} ({client.get('shipping_type') or 'Not specified'})"),
        ("Client PO #", client.get("client_po") or "N/A"),
    ]

    partners = sorted({item["partner"] for item in order["order_items"] if not item.get("is_custom")})
    editable = order.get("partner_contacts_editable", {})
    partner_contacts = partner_contacts or {}
    partner_rows = []
    for partner in partners:
        edited = editable.get(partner, {})
        source = edited if (edited.get("poc_name") or edited.get("poc_email")) else partner_contacts.get(partner, {})
        partner_rows.append({
            "partner": partner,
            "poc_name": source.get("poc_name") or "Not specified",
            "poc_email": source.get("poc_email") or "Not specified",
            "poc_phone": source.get("poc_phone") or "",
            "shipping_instructions": (edited.get("shipping_instructions") or "").strip() or "Not specified",
        })

    submitted_date = client.get("order_submitted_date") or date.today()
    cost_date = client.get("cost_submitted_date")
    detail_rows = [
        ("Client In-Hands Date", format_date(client.get("client_in_hands_date"))),
        ("PBP In-Hands Date", format_date(client.get("pbp_in_hands_date"))),
        ("Ship Method", client.get("ship_method") or "Not specified"),
        ("Payment Terms", client.get("payment_timeline") or "Not specified"),
        ("Payment Method", client.get("payment_preference") or "Not specified"),
        ("Order Submitted By", f"{client.get('order_submitted_by') or 'Not specified'} (Date: {format_date(submitted_date)})"),
        ("Cost Submitted By", f"{client.get('cost_submitted_by') or 'Not specified'} (Date: {format_date(cost_date) if cost_date else 'Not specified'})"),
    ]

    t = order_service.totals(order)
    totals_rows = [("Subtotal (Products + Customization)", _money(t["products_subtotal"]))]
    if t["discount_percent"] > 0:
        totals_rows.append((f"Discount ({t['discount_description']}) - on products only", f"-{_money(t['discount_amount'])}"))
    totals_rows.append(("Shipping", _money(t["shipping"])))
    if t["tariff"] > 0:
        totals_rows.append(("Tariff", _money(t["tariff"])))
    if order.get("apply_cc_fee") and t["cc_fee_amount"] > 0:
        totals_rows.append((f"Credit Card Fee ({order.get('cc_fee_percent', 3.0)}%)", _money(t["cc_fee_amount"])))
    totals_rows.append(("TOTAL", _money(t["total_quote"])))

    notes = [(label, order["order_notes"].get(key, "")) for key, label in order_service.NOTE_CATEGORIES if order["order_notes"].get(key)]

    return {
        "client_rows": client_rows, "partner_rows": partner_rows, "detail_rows": detail_rows,
        "lines": line_items(order, df_template), "totals_rows": totals_rows, "notes": notes,
        "dropshipping_notes": DROPSHIPPING_NOTES,
        "warnings": validate_invoice_completeness(client, order["order_items"]),
        "totals": t,
    }


def to_csv(invoice):
    """Same layout as the Streamlit download: notes first, line items, blank row, totals in the sell-price column."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    if invoice["notes"]:
        for label, body in invoice["notes"]:
            writer.writerow(["", f"{label}: {body}".replace("\n", " ")] + [""] * 7)
        writer.writerow([""] * 9)
    for line in invoice["lines"]:
        writer.writerow([line[col] for col in COLUMNS])
    writer.writerow([""] * 9)
    for label, amount in invoice["totals_rows"]:
        writer.writerow(["", label, "", "", "", "", "", "", amount])
    return out.getvalue()


def _photo_blocks(photos_in_memory, photo_metadata):
    """[(product, [(filename, data_uri)])] for every product with photos, uploads first, then saved ones."""
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
    blocks = []
    products = sorted({k for k, v in photos_in_memory.items() if v} | {k for k, v in photo_metadata.items() if v})
    for product in products:
        images = []
        if photos_in_memory.get(product):
            for photo in photos_in_memory[product]:
                ext = photo["filename"].rsplit(".", 1)[-1].lower()
                images.append((photo["filename"], f"data:{mime.get(ext, 'image/png')};base64,{base64.b64encode(photo['bytes']).decode()}"))
        elif photo_metadata.get(product):
            from pbp.sheets.drive_helper import download_photo
            for meta in photo_metadata[product]:
                data = download_photo(meta["file_id"])
                if data:
                    ext = meta["filename"].rsplit(".", 1)[-1].lower()
                    images.append((meta["filename"], f"data:{mime.get(ext, 'image/png')};base64,{base64.b64encode(data).decode()}"))
        if images:
            blocks.append((product, images))
    return blocks


def to_html(invoice, photos_in_memory=None, photo_metadata=None):
    """Standalone, email-ready HTML (the Streamlit 'Download as HTML')."""
    template = _templates.get_template("invoice.html")
    return template.render(invoice=invoice, photo_blocks=_photo_blocks(photos_in_memory or {}, photo_metadata or {}))


def filename(extension):
    return f"invoice_po_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
