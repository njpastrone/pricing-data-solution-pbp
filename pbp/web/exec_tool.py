"""Staff screens (phase 4): the Executive Pricing Tool (Tab 5) and Reset session."""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from pbp.services import exec_pricing as svc
from pbp.sheets import catalog
from pbp.web import auth, state
from pbp.web.staff import DATASET, _back, _is_htmx, _num, _products_for, _safe
from pbp.web.templating import page

router = APIRouter()


def _context(request, sid):
    scenario = state.exec_scenario(sid)
    try:
        df, _, _ = catalog.load_pricing_data(DATASET)
        partners = sorted(df["Partner"].unique().tolist())
        error = ""
    except Exception as e:
        df, partners, error = None, [], str(e)
    return {"scenario": scenario, "views": [svc.view(p) for p in scenario["products"]], "summary": svc.summary(scenario),
            "partners": partners, "first_products": _products_for(df, partners[0]) if partners else [], "catalog_error": error,
            "flash": state.pop_flash(sid), "svc": svc}


def _product_response(request, sid, index):
    if not _is_htmx(request):
        return _back(request, "/exec")
    scenario = state.exec_scenario(sid)
    body = page(request, "_exec_product.html", product=scenario["products"][index], v=svc.view(scenario["products"][index]), index=index).body.decode()
    body += page(request, "_exec_summary.html", scenario=scenario, summary=svc.summary(scenario), oob=True).body.decode()
    return HTMLResponse(body)


@router.get("/exec", response_class=HTMLResponse)
def exec_tool(request: Request, sid: str = Depends(auth.require_staff)):
    return page(request, "exec.html", **_context(request, sid))


@router.post("/exec/products")
async def add_product(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    try:
        df, _, _ = catalog.load_pricing_data(DATASET)
        product = catalog.find_product(df, form.get("product", ""), form.get("partner") or None)
        if product is None:
            state.flash(sid, "Product not found in the catalog", "error")
        elif svc.add_product(state.exec_scenario(sid), product):
            state.flash(sid, f"Added {product['Product/Service']}")
        else:
            state.flash(sid, "Product already added", "error")
    except Exception as e:
        state.flash(sid, f"Could not add product: {e}", "error")
    return _back(request, "/exec#products")


@router.post("/exec/products/{index}")
async def update_product(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    scenario = state.exec_scenario(sid)
    if index >= len(scenario["products"]):
        return _back(request, "/exec")
    product = scenario["products"][index]
    product["quantity"] = min(10000, max(1, _num(form, "quantity", product["quantity"], int)))
    if request.headers.get("HX-Trigger-Name") == "client_price" and _num(form, "client_price", 0.0) > 0:
        svc.set_client_price(product, _num(form, "client_price", 0.0))
    else:
        product["markup_percent"] = _num(form, "markup_percent", product["markup_percent"])
    product["include_customization"] = form.get("include_customization") == "on"
    if product["include_customization"]:
        for key in ("custom_setup_fee", "custom_per_unit", "pbp_setup_fee", "pbp_per_unit_cost"):
            product[key] = _num(form, key, product.get(key, 0.0))
    product["include_tariffs"] = form.get("include_tariffs") == "on"
    if product["include_tariffs"]:
        product["tariff_input_method"] = form.get("tariff_input_method", product.get("tariff_input_method", "percentage"))
        trigger = request.headers.get("HX-Trigger-Name", "")
        if trigger == "tariff_input_method":
            product["tariff_rate"] = product["tariff_dollar"] = None  # back to the spreadsheet default for the new method
        elif product["tariff_input_method"] == "dollar":
            product["tariff_dollar"] = _num(form, "tariff_dollar", product.get("tariff_dollar"))
        else:
            product["tariff_rate"] = _num(form, "tariff_rate", product.get("tariff_rate"))
    return _product_response(request, sid, index)


@router.post("/exec/products/{index}/remove")
def remove_product(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    products = state.exec_scenario(sid)["products"]
    if index < len(products):
        products.pop(index)
    return _back(request, "/exec#products")


@router.post("/exec/settings")
async def update_settings(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    scenario = state.exec_scenario(sid)
    scenario["shipping"] = _num(form, "shipping", 0.0)
    scenario["cc_fee"] = form.get("cc_fee") == "on"
    scenario["cc_fee_percent"] = _num(form, "cc_fee_percent", scenario.get("cc_fee_percent", 3.0))
    if not _is_htmx(request):
        return _back(request, "/exec#summary")
    body = page(request, "_exec_settings.html", scenario=scenario).body.decode()
    body += page(request, "_exec_summary.html", scenario=scenario, summary=svc.summary(scenario), oob=True).body.decode()
    return HTMLResponse(body)


@router.get("/exec/summary.csv")
def summary_csv(sid: str = Depends(auth.require_staff)):
    return Response(svc.summary_csv(state.exec_scenario(sid)), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="exec_pricing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'})


@router.post("/exec/import/proposal")
def import_to_proposal(sid: str = Depends(auth.require_staff)):
    added = svc.to_proposal_items(state.exec_scenario(sid), state.proposal(sid))
    state.flash(sid, f"Added {added} product(s) to the proposal" if added else "All products already in the proposal", "success" if added else "error")
    return RedirectResponse("/proposals/current#products", status_code=303)


@router.post("/exec/import/order")
def import_to_order(sid: str = Depends(auth.require_staff)):
    added = svc.to_order_items(state.exec_scenario(sid), state.order(sid))
    state.flash(sid, f"Added {added} product(s) to the order" if added else "All products already in the order", "success" if added else "error")
    return RedirectResponse("/orders/current#items", status_code=303)


@router.post("/reset")
def reset_session(sid: str = Depends(auth.require_staff)):
    """Forget the working order, proposal and pricing scenario (the Streamlit 'Reset session')."""
    state.reset(sid)
    state.flash(sid, "Session reset: working order, proposal and pricing scenario cleared")
    return RedirectResponse("/orders", status_code=303)
