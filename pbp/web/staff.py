"""
Staff screens (phase 2): login, orders (Tab 3) and accounting (Tab 4).

Pages are full HTML on first load; edits inside the order editor post small
HTMX requests that return just the changed card plus the refreshed summary.
Every POST also works as a plain form post (redirect back to the page).
"""

import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from pbp.core.forms_config import RESPONSE_COLUMNS
from pbp.core.forms_helper import load_form_responses, mark_response_imported, parse_form_response
from pbp.services import invoice as invoice_service
from pbp.services import order as svc
from pbp.sheets import catalog, gateway, order_manager, proposal_manager
from pbp.web import auth, state
from pbp.web.templating import page

router = APIRouter()
DATASET = "real"  # the Streamlit UI pins the real dataset too


# ----------------------------------------------------------------------------
# Form helpers
# ----------------------------------------------------------------------------

def _num(form, name, default=0.0, cast=float):
    value = form.get(name)
    if value is None or str(value).strip() == "":
        return default
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def _date(form, name):
    value = (form.get(name) or "").strip()
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _back(request, url="/orders/current"):
    return RedirectResponse(url, status_code=303)


def _catalog():
    df_template, _, _ = catalog.load_pricing_data(DATASET)
    return df_template


def _editor_context(request, sid):
    order = state.order(sid)
    try:
        df_template = _catalog()
        partners = sorted(df_template["Partner"].unique().tolist())
        catalog_error = ""
    except Exception as e:  # catalog unavailable: the editor still shows the order
        df_template, partners, catalog_error = None, [], str(e)
    return {
        "order": order, "totals": svc.totals(order), "meta": state.meta(sid), "flash": state.pop_flash(sid),
        "partners": partners, "catalog_error": catalog_error,
        "first_products": _products_for(df_template, partners[0]) if partners else [],
        "proposals": _safe(proposal_manager.load_all_proposals, []),
        "photos": state.photos(sid), "svc": svc,
    }


def _products_for(df_template, partner):
    if df_template is None or not partner:
        return []
    return df_template[df_template["Partner"] == partner]["Product/Service"].unique().tolist()


def _safe(func, default):
    try:
        return func()
    except Exception as e:
        print(f"{func.__name__} failed: {e}")
        return default


def _item_response(request, sid, index, status_code=200):
    """The edited item card plus the refreshed summary (out of band), or a redirect without HTMX."""
    if not _is_htmx(request):
        return _back(request)
    order = state.order(sid)
    body = page(request, "_item.html", order=order, item=order["order_items"][index], index=index, svc=svc).body.decode()
    body += page(request, "_summary.html", order=order, totals=svc.totals(order), oob=True, svc=svc).body.decode()
    return HTMLResponse(body, status_code=status_code)


# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/orders"):
    if auth.session_id(request):
        return RedirectResponse(next, status_code=303)
    return page(request, "login.html", next=next, error="")


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    form = await request.form()
    response = auth.login(form.get("password", ""), form.get("next") or "/orders")
    if response is None:
        return page(request, "login.html", next=form.get("next") or "/orders", error="Incorrect password.", status_code=401)
    return response


@router.post("/logout")
def logout():
    return auth.logout()


# ----------------------------------------------------------------------------
# Orders home: working order, saved orders
# ----------------------------------------------------------------------------

@router.get("/orders", response_class=HTMLResponse)
def orders_home(request: Request, sid: str = Depends(auth.require_staff)):
    order = state.order(sid)
    return page(request, "orders_home.html", order=order, totals=svc.totals(order), meta=state.meta(sid),
                flash=state.pop_flash(sid), saved_orders=_safe(order_manager.load_all_orders, []))


@router.post("/orders/new")
def new_order(sid: str = Depends(auth.require_staff)):
    state.clear_order(sid)
    return RedirectResponse("/orders/current", status_code=303)


@router.post("/orders/load/{order_id}")
def load_order(order_id: str, sid: str = Depends(auth.require_staff)):
    ok, data, dataset = order_manager.load_order_data(order_id)
    if not ok:
        state.flash(sid, "Failed to load order data", "error")
        return RedirectResponse("/orders", status_code=303)
    name = next((o["name"] for o in _safe(order_manager.load_all_orders, []) if o["order_id"] == order_id), order_id)
    state.replace_order(sid, data, order_id=order_id, name=name)
    state.flash(sid, f"Loaded order: {name}")
    return RedirectResponse("/orders/current", status_code=303)


@router.post("/orders/delete/{order_id}")
def delete_order(order_id: str, sid: str = Depends(auth.require_staff)):
    ok, message = order_manager.delete_order(order_id)
    state.flash(sid, message, "success" if ok else "error")
    return RedirectResponse("/orders", status_code=303)


# ----------------------------------------------------------------------------
# Order editor (Tab 3)
# ----------------------------------------------------------------------------

@router.get("/orders/current", response_class=HTMLResponse)
def edit_order(request: Request, sid: str = Depends(auth.require_staff)):
    return page(request, "order_edit.html", **_editor_context(request, sid))


@router.get("/catalog/products", response_class=HTMLResponse)
def catalog_products(request: Request, partner: str = "", sid: str = Depends(auth.require_staff)):
    """HTMX: the product <select> for a partner."""
    return page(request, "_product_options.html", products=_products_for(_safe(_catalog, None), partner))


@router.post("/orders/current/items")
async def add_item(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    action = form.get("action", "catalog")
    try:
        if action == "catalog":
            product = catalog.find_product(_catalog(), form.get("product", ""), form.get("partner") or None)
            if product is None:
                state.flash(sid, "Product not found in the catalog", "error")
            else:
                item = svc.catalog_item(product, quantity=1, use_msrp=form.get("use_msrp") == "on", variant=(form.get("variant") or "").strip() or None)
                if item is None:
                    state.flash(sid, "Could not determine pricing for this product", "error")
                else:
                    svc.add_items(order, [item])
                    state.flash(sid, f"Added {svc.display_name(item)} to order")
        elif action == "custom_product":
            name, cost = (form.get("name") or "").strip(), _num(form, "base_cost", 0.0)
            if len(name) < 3 or cost <= 0:
                state.flash(sid, "Product name (3+ characters) and a base cost above $0 are required", "error")
            else:
                svc.add_items(order, [svc.custom_product_item(name, form.get("partner") or "Custom/Other", cost)])
                state.flash(sid, f"Added {name} to order")
        elif action == "custom_line":
            name, price = (form.get("name") or "").strip(), _num(form, "total_price", 0.0)
            if not name or price <= 0:
                state.flash(sid, "Please fill in Product/Service Name and set Total Price greater than $0", "error")
            else:
                svc.add_items(order, [svc.custom_line_item(name, _num(form, "quantity", 1, int), form.get("description", ""), price)])
                state.flash(sid, f"Added custom item: {name}")
    except Exception as e:
        state.flash(sid, f"Could not add product: {e}", "error")
    return _back(request)


@router.post("/orders/current/import-proposal/{proposal_id}")
def import_proposal(proposal_id: str, sid: str = Depends(auth.require_staff)):
    ok, data, _ = proposal_manager.load_proposal_data(proposal_id)
    if not ok:
        state.flash(sid, "Failed to load proposal", "error")
        return RedirectResponse("/orders/current", status_code=303)
    order = state.order(sid)
    items = svc.items_from_proposal(data.get("proposal_products", []))
    svc.add_items(order, items)
    state.meta(sid)["proposal_products"] = data.get("proposal_products", [])
    state.flash(sid, f"Imported {len(items)} product(s) from the proposal. Order now has {len(order['order_items'])} product(s).")
    return RedirectResponse("/orders/current#items", status_code=303)


@router.post("/orders/current/items/{index}")
async def update_item(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    if index >= len(order["order_items"]):
        return _back(request)
    item = order["order_items"][index]
    if item.get("is_custom"):
        return _item_response(request, sid, index)

    item["quantity"] = max(1, _num(form, "quantity", item.get("quantity", 1), int))
    item["manual_override"] = form.get("manual_override") == "on"
    item["include_customization"] = form.get("include_customization") == "on"
    if item["include_customization"]:
        item["customization_description"] = form.get("customization_description", "")
        item["customization_setup_fee"] = _num(form, "customization_setup_fee", 0.0)
        item["customization_per_unit"] = _num(form, "customization_per_unit", 0.0)
        item["partner_customization_setup_fee"] = _num(form, "partner_customization_setup_fee", 0.0)
        item["partner_customization_per_unit"] = _num(form, "partner_customization_per_unit", 0.0)
        item["apply_custom_minimum"] = form.get("apply_custom_minimum") == "on"
        item["customization_minimum_qty"] = _num(form, "customization_minimum_qty", 0, int) if item["apply_custom_minimum"] else 0
        for j, addon in enumerate(item.get("customization_addons", [])):
            if f"addon_{j}_name" in form:
                addon.update(name=form.get(f"addon_{j}_name", ""),
                             client_setup_fee=_num(form, f"addon_{j}_client_setup", 0.0),
                             client_per_unit_cost=_num(form, f"addon_{j}_client_perunit", 0.0),
                             partner_setup_fee=_num(form, f"addon_{j}_partner_setup", 0.0),
                             partner_per_unit_cost=_num(form, f"addon_{j}_partner_perunit", 0.0))
    item["include_kitting"] = form.get("include_kitting") == "on"
    if item["include_kitting"]:
        item["kitting_quantity"] = max(1, _num(form, "kitting_quantity", 1, int))
        item["kitting_pbp_cost"] = _num(form, "kitting_pbp_cost", 0.0)
        item["kitting_client_price"] = _num(form, "kitting_client_price", 0.0)
        item["kitting_description"] = form.get("kitting_description", "")
    if item.get("is_custom_product"):
        made, ships = form.get("country_made_in", ""), form.get("country_ships_from", "")
        item["country_of_origin_made_in"] = made
        item["country_of_origin_ships_from"] = ships or made
        item["product_data"]["Country of Origin (Made In)"] = made
        item["product_data"]["Country of Origin (Ships From)"] = ships or made
        item["tariff_rate_percent"] = _num(form, "tariff_rate_percent", 0.0)
    item["partner_in_hands_date"] = form.get("partner_in_hands_date", "")
    item["edited_description"] = form.get("edited_description", "")

    # Price and markup are two views of one number: whichever the user touched wins
    if request.headers.get("HX-Trigger-Name") == "client_price" and _num(form, "client_price", 0.0) > 0:
        svc.recalculate(item)  # base price for the new quantity first
        svc.set_client_price(item, _num(form, "client_price", 0.0))
    else:
        item["markup_percent"] = _num(form, "markup_percent", item.get("markup_percent", 100.0))
        svc.recalculate(item)
    return _item_response(request, sid, index)


@router.post("/orders/current/items/{index}/remove")
def remove_item(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    order = state.order(sid)
    if index < len(order["order_items"]):
        removed = order["order_items"].pop(index)
        state.flash(sid, f"Removed {removed.get('product_name', 'item')}")
    return _back(request)


@router.post("/orders/current/items/{index}/addons")
def add_addon(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    item = state.order(sid)["order_items"][index]
    item.setdefault("customization_addons", []).append(
        {"name": "", "client_setup_fee": 0.0, "client_per_unit_cost": 0.0, "partner_setup_fee": 0.0, "partner_per_unit_cost": 0.0})
    item["include_customization"] = True
    return _item_response(request, sid, index)


@router.post("/orders/current/items/{index}/addons/{addon_index}/remove")
def remove_addon(request: Request, index: int, addon_index: int, sid: str = Depends(auth.require_staff)):
    item = state.order(sid)["order_items"][index]
    addons = item.get("customization_addons", [])
    if addon_index < len(addons):
        addons.pop(addon_index)
    svc.recalculate(item)
    return _item_response(request, sid, index)


@router.post("/orders/current/clear")
def clear_items(request: Request, sid: str = Depends(auth.require_staff)):
    state.order(sid)["order_items"] = []
    return _back(request)


@router.post("/orders/current/settings")
async def update_settings(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    svc.set_discount_option(order, form.get("discount_option", "None"), _num(form, "custom_discount", order.get("order_discount_custom_value", 0.0)))
    order["order_fifty_cent_rounding"] = form.get("fifty_cent_rounding") == "on"
    order["order_use_marketing_rounding"] = form.get("marketing_rounding") == "on"
    order["apply_cc_fee"] = form.get("apply_cc_fee") == "on"
    order["cc_fee_percent"] = _num(form, "cc_fee_percent", order.get("cc_fee_percent", 3.0))
    order["order_shipping"] = _num(form, "order_shipping", 0.0)
    order["partner_shipping"] = _num(form, "partner_shipping", 0.0)
    order["sales_tax"] = _num(form, "sales_tax", 0.0)
    order["kitting_pbp_cost"] = _num(form, "kitting_pbp_cost", 0.0)
    order["kitting_client_price"] = _num(form, "kitting_client_price", 0.0)
    for key, _ in svc.NOTE_CATEGORIES:
        if key in form:
            order["order_notes"][key] = form.get(key, "")
    for i, item in enumerate(order["order_items"]):
        if f"tariff_rate_{i}" in form and not item.get("is_custom"):
            item["tariff_rate_percent"] = _num(form, f"tariff_rate_{i}", 0.0)
            svc.recalculate(item)
    if not _is_htmx(request):
        return _back(request)
    body = page(request, "_settings.html", order=order, totals=svc.totals(order), svc=svc).body.decode()
    body += page(request, "_summary.html", order=order, totals=svc.totals(order), oob=True, svc=svc).body.decode()
    return HTMLResponse(body)


@router.post("/orders/current/client")
async def update_client(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    client = order["client_info"]
    action = form.get("action", "save")

    client["is_new_client"] = form.get("is_new_client") == "on"
    for key in ("company_name", "client_po", "billing_address", "shipping_type", "ship_method", "payment_preference",
                "order_submitted_by", "cost_submitted_by"):
        if key in form:
            client[key] = form.get(key, "")
    client["shipping_address"] = form.get("shipping_address", "") if client.get("shipping_type") == "One Location" else ""
    terms = form.get("payment_timeline", client.get("payment_timeline", "Net 30"))
    client["payment_timeline"] = (form.get("custom_payment_terms") or "Custom") if terms == "Custom" else terms
    for key in ("client_in_hands_date", "pbp_in_hands_date", "cost_submitted_date"):
        if key in form:
            client[key] = _date(form, key)

    contacts = []
    i = 0
    while f"contact_name_{i}" in form:
        contacts.append({"name": form.get(f"contact_name_{i}", ""), "email": form.get(f"contact_email_{i}", ""),
                         "phone": form.get(f"contact_phone_{i}", ""), "role": form.get(f"contact_role_{i}", "")})
        i += 1
    if contacts:
        client["contacts"] = contacts
    if action == "add_contact":
        client["contacts"].append(svc.new_contact(""))
    elif action.startswith("remove_contact_"):
        idx = int(action.rsplit("_", 1)[1])
        if len(client["contacts"]) > 1 and idx < len(client["contacts"]):
            client["contacts"].pop(idx)
    if action == "confirm":
        order["order_confirmed"] = True
    elif action == "edit":
        order["order_confirmed"] = False

    if not _is_htmx(request):
        return _back(request, form.get("return_to") or "/orders/current#client")
    return page(request, "_client.html", order=order, svc=svc)


@router.post("/orders/current/save")
async def save_order(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    name = (form.get("name") or "").strip()
    if not order["order_items"]:
        state.flash(sid, "Add products to your order to enable saving", "error")
    elif not name:
        state.flash(sid, "Please enter an order name", "error")
    else:
        photos = {product: list(files) for product, files in state.photos(sid).items() if files} or None
        payload = svc.saved_payload(order)  # save_order adds the uploaded photo metadata to this copy
        ok, message, result = order_manager.save_order(name=name, created_by=(form.get("created_by") or "").strip(),
                                                        order_data=payload, dataset=DATASET,
                                                        photos_by_product=photos, overwrite=form.get("overwrite") == "on")
        if ok:
            state.meta(sid).update(loaded_order_id=result, loaded_order_name=name)
            if photos:
                order["product_photos"] = payload.get("product_photos", {})
                state.photos(sid).clear()  # now stored in the sheet; shown from there
        state.flash(sid, message, "success" if ok else "error")
    return _back(request, "/orders/current#save")


# ----------------------------------------------------------------------------
# Product photos (kept in memory until the order is saved)
# ----------------------------------------------------------------------------

@router.post("/orders/current/photos")
async def upload_photos(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    product = form.get("product", "")
    store = state.photos(sid).setdefault(product, [])
    added = 0
    for upload in form.getlist("photos"):
        if not getattr(upload, "filename", ""):
            continue
        if len(store) >= svc.MAX_PHOTOS_PER_PRODUCT:
            state.flash(sid, f"Maximum {svc.MAX_PHOTOS_PER_PRODUCT} photos per product reached.", "error")
            break
        store.append({"filename": upload.filename, "bytes": await upload.read()})
        added += 1
    if added:
        state.flash(sid, f"Added {added} photo(s) for {product}")
    return _back(request, "/orders/current#photos")


@router.get("/orders/current/photos/{product}/{index}")
def photo(product: str, index: int, sid: str = Depends(auth.require_staff)):
    files = state.photos(sid).get(product, [])
    if index >= len(files):
        return Response(status_code=404)
    return Response(files[index]["bytes"], media_type="image/*")


@router.post("/orders/current/photos/{product}/{index}/remove")
def remove_photo(request: Request, product: str, index: int, sid: str = Depends(auth.require_staff)):
    files = state.photos(sid).get(product, [])
    if index < len(files):
        files.pop(index)
    return _back(request, "/orders/current#photos")


# ----------------------------------------------------------------------------
# Client form responses (Tab 3 Option A)
# ----------------------------------------------------------------------------

def _responses():
    df = load_form_responses(gateway.connect())
    rows = []
    for position, (_, row) in enumerate(df.iterrows()):
        parsed = parse_form_response(row)
        parsed["row_number"] = position + 2  # header + 1-indexed
        parsed["imported"] = str(parsed["metadata"].get("imported", "")).upper() == "TRUE"
        parsed["file_name"] = row.get(RESPONSE_COLUMNS["dropshipping_file"], "") if hasattr(row, "get") else ""
        rows.append(parsed)
    rows.sort(key=lambda r: r["metadata"].get("timestamp", ""), reverse=True)
    has_tracking = RESPONSE_COLUMNS["imported"] in df.columns
    return rows, has_tracking


@router.get("/responses", response_class=HTMLResponse)
def responses(request: Request, show: str = "all", sid: str = Depends(auth.require_staff)):
    try:
        rows, has_tracking = _responses()
        error = ""
    except Exception as e:
        rows, has_tracking, error = [], False, str(e)
    if show == "new":
        rows = [r for r in rows if not r["imported"]]
    elif show == "imported":
        rows = [r for r in rows if r["imported"]]
    return page(request, "responses.html", rows=rows, has_tracking=has_tracking, show=show, error=error,
                flash=state.pop_flash(sid), order=state.order(sid))


@router.post("/responses/import")
async def import_response(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    row_number = _num(form, "row_number", 0, int)
    try:
        rows, has_tracking = _responses()
        response = next(r for r in rows if r["row_number"] == row_number)
        order = state.order(sid)
        imported, skipped = svc.import_form_response(order, response, _catalog(), state.meta(sid).get("proposal_products", []))
        if has_tracking:
            mark_response_imported(gateway.connect(), row_number, f"IMPORTED-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        message = f"Imported {len(imported)} product(s) from {response['client_info'].get('company_name') or 'the response'}"
        if skipped:
            message += f". Could not match: {', '.join(skipped)}"
        state.flash(sid, message, "success" if imported else "error")
    except StopIteration:
        state.flash(sid, "Response not found (the sheet may have changed); reload and try again", "error")
    except Exception as e:
        state.flash(sid, f"Import failed: {e}", "error")
    return RedirectResponse("/orders/current#items", status_code=303)


# ----------------------------------------------------------------------------
# Accounting (Tab 4)
# ----------------------------------------------------------------------------

def _invoice(sid):
    order = state.order(sid)
    df_template = _safe(_catalog, None)
    contacts = _safe(lambda: catalog.partner_contacts(DATASET), {})
    return order, invoice_service.build(order, df_template, contacts), contacts


@router.get("/orders/current/accounting", response_class=HTMLResponse)
def accounting(request: Request, sid: str = Depends(auth.require_staff)):
    order, invoice, contacts = _invoice(sid)
    partners = sorted({item["partner"] for item in order["order_items"] if not item.get("is_custom")})
    editable = order.setdefault("partner_contacts_editable", {})
    for partner in partners:
        editable.setdefault(partner, {**{"poc_name": "", "poc_email": "", "poc_phone": ""}, **contacts.get(partner, {}), "shipping_instructions": ""})
        editable[partner].setdefault("shipping_instructions", "")
    return page(request, "accounting.html", order=order, invoice=invoice, partners=partners, svc=svc, totals=invoice["totals"],
                flash=state.pop_flash(sid), meta=state.meta(sid))


@router.post("/orders/current/accounting")
async def update_accounting(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    order = state.order(sid)
    for i, item in enumerate(order["order_items"]):
        if f"description_{i}" in form:
            item["edited_description"] = form.get(f"description_{i}", "")
        if f"partner_in_hands_{i}" in form:
            item["partner_in_hands_date"] = form.get(f"partner_in_hands_{i}", "")
    editable = order.setdefault("partner_contacts_editable", {})
    for key in list(form.keys()):
        if key.startswith("poc_name__"):
            partner = key[len("poc_name__"):]
            editable[partner] = {"poc_name": form.get(f"poc_name__{partner}", ""), "poc_email": form.get(f"poc_email__{partner}", ""),
                                 "poc_phone": form.get(f"poc_phone__{partner}", ""), "shipping_instructions": form.get(f"ship__{partner}", "")}
    state.flash(sid, "Order information updated")
    return RedirectResponse("/orders/current/accounting", status_code=303)


@router.get("/orders/current/invoice.csv")
def invoice_csv(sid: str = Depends(auth.require_staff)):
    _, invoice, _ = _invoice(sid)
    return Response(invoice_service.to_csv(invoice), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{invoice_service.filename("csv")}"'})


@router.get("/orders/current/invoice.html")
def invoice_html(sid: str = Depends(auth.require_staff)):
    order, invoice, _ = _invoice(sid)
    html = invoice_service.to_html(invoice, state.photos(sid), order.get("product_photos", {}))
    return Response(html, media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="{invoice_service.filename("html")}"'})


@router.get("/orders/current/summary.csv")
def summary_csv(sid: str = Depends(auth.require_staff)):
    import csv
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Item", "Qty", "PBP Cost (Per Unit)", "PBP Cost", "Client Price (Per Unit)", "Client Price"])
    writer.writerows(svc.totals(state.order(sid))["rows"])
    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="order_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'})
