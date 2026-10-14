"""
Staff screens (phase 3): proposals (Tab 1), the PowerPoint match review and
generation, and the client form link (Tab 2).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from pbp import settings
from pbp.services import pptx_jobs
from pbp.services import proposal as svc
from pbp.sheets import catalog, client_form, match_memory, proposal_manager, templates
from pbp.web import auth, state
from pbp.web.staff import DATASET, _back, _is_htmx, _num, _safe
from pbp.web.templating import page

router = APIRouter()


def _catalog():
    df_template, _, _ = catalog.load_pricing_data(DATASET)
    return df_template


def _filters(request, sid):
    """Catalog filters from the query string, remembered per session."""
    q = request.query_params
    saved = state.meta(sid)["catalog_filters"]
    if any(key in q for key in ("search", "partners", "countries", "min_budget", "max_budget", "clear")):
        saved = {} if "clear" in q else {
            "search": q.get("search", "").strip(), "partners": q.getlist("partners"), "countries": q.getlist("countries"),
            "min_budget": _num(q, "min_budget", 0.0), "max_budget": _num(q, "max_budget", 0.0),
        }
        state.meta(sid)["catalog_filters"] = saved
    return {"search": "", "partners": [], "countries": [], "min_budget": 0.0, "max_budget": 0.0, **saved}


def _catalog_context(request, sid):
    filters = _filters(request, sid)
    try:
        df = _catalog()
        partners, countries = svc.filter_options(df)
        rows = svc.catalog_rows(df, filters["search"], filters["partners"], filters["countries"], filters["min_budget"], filters["max_budget"])
        error = ""
    except Exception as e:
        partners, countries, rows, error = [], [], [], str(e)
    in_proposal = {item["product_data"].get("Product/Service") for item in state.proposal(sid)["proposal_products"]}
    return {"filters": filters, "partners": partners, "countries": countries, "rows": rows, "catalog_error": error,
            "in_proposal": in_proposal, "new_count": sum(1 for r in rows if r["name"] not in in_proposal)}


def _editor_context(request, sid):
    proposal = state.proposal(sid)
    items = [{"item": item, "display": svc.item_display(item, proposal), "table": svc.moq_table(item, proposal)}
             for item in proposal["proposal_products"]]
    notes, warnings = svc.notes_and_warnings(proposal)
    pptx = state.meta(sid)["pptx"]
    return {"proposal": proposal, "items": items, "notes": notes, "warnings": warnings, "meta": state.meta(sid), "svc": svc,
            "flash": state.pop_flash(sid), "saved_proposals": _safe(proposal_manager.load_all_proposals, []),
            "templates": _safe(templates.list_templates, []), "selected_template": pptx.get("template"),
            "client_form_base_url": settings.CLIENT_FORM_BASE_URL, **_catalog_context(request, sid)}


# ----------------------------------------------------------------------------
# Proposals home and editor
# ----------------------------------------------------------------------------

@router.get("/proposals", response_class=HTMLResponse)
def proposals_home(request: Request, sid: str = Depends(auth.require_staff)):
    return page(request, "proposals_home.html", proposal=state.proposal(sid), meta=state.meta(sid), flash=state.pop_flash(sid),
                saved_proposals=_safe(proposal_manager.load_all_proposals, []))


@router.post("/proposals/new")
def new_proposal(sid: str = Depends(auth.require_staff)):
    state.replace_proposal(sid, svc.new_proposal())
    return RedirectResponse("/proposals/current", status_code=303)


@router.post("/proposals/load/{proposal_id}")
def load_proposal(proposal_id: str, sid: str = Depends(auth.require_staff)):
    ok, data, _ = proposal_manager.load_proposal_data(proposal_id)
    if not ok:
        state.flash(sid, "Failed to load proposal", "error")
        return RedirectResponse("/proposals", status_code=303)
    name = next((p["name"] for p in _safe(proposal_manager.load_all_proposals, []) if p["proposal_id"] == proposal_id), proposal_id)
    state.replace_proposal(sid, data, proposal_id=proposal_id, name=name)
    state.meta(sid)["proposal_products"] = state.proposal(sid)["proposal_products"]  # Tab 3 import uses the loaded proposal's markups
    state.flash(sid, f"Loaded proposal: {name}")
    return RedirectResponse("/proposals/current", status_code=303)


@router.post("/proposals/delete/{proposal_id}")
def delete_proposal(proposal_id: str, sid: str = Depends(auth.require_staff)):
    ok, message = proposal_manager.delete_proposal(proposal_id)
    state.flash(sid, message, "success" if ok else "error")
    return RedirectResponse("/proposals", status_code=303)


@router.get("/proposals/current", response_class=HTMLResponse)
def edit_proposal(request: Request, sid: str = Depends(auth.require_staff)):
    if _is_htmx(request):  # filter change: just the catalog
        return page(request, "_catalog.html", **_catalog_context(request, sid))
    return page(request, "proposal_edit.html", **_editor_context(request, sid))


@router.post("/proposals/current/items")
async def add_products(request: Request, sid: str = Depends(auth.require_staff)):
    """Add one product, every filtered product, or every product of the chosen partners."""
    form = await request.form()
    proposal = state.proposal(sid)
    try:
        df = _catalog()
        if form.get("action") == "all_filtered" or form.get("action") == "by_partner":
            f = _filters(request, sid)
            partners = form.getlist("bulk_partners") if form.get("action") == "by_partner" else f["partners"]
            rows = svc.catalog_rows(df, f["search"], partners, f["countries"], f["min_budget"], f["max_budget"])
            added, failed = svc.add_products(proposal, [r["product"] for r in rows])
        else:
            product = catalog.find_product(df, form.get("product", ""), form.get("partner") or None)
            added, failed = svc.add_products(proposal, [product] if product else [])
            if product is None:
                failed = [form.get("product", "?")]
        if added:
            state.flash(sid, f"Added {len(added)} product(s) to proposal" if len(added) > 1 else f"Added {added[0]} to proposal")
        elif not failed:
            state.flash(sid, "Those products are already in the proposal", "error")
        if failed:
            state.flash(sid, f"Skipped {len(failed)} product(s) with missing pricing data: {', '.join(failed)}", "error")
    except Exception as e:
        state.flash(sid, f"Could not add products: {e}", "error")
    return _back(request, "/proposals/current#products")


@router.post("/proposals/current/items/{index}")
async def update_item(request: Request, index: int, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    proposal = state.proposal(sid)
    items = proposal["proposal_products"]
    if index < len(items):
        item = items[index]
        action = form.get("action", "")
        if action == "remove":
            items.pop(index)
        else:
            item["manual_override"] = form.get("manual_override") == "on"
            if request.headers.get("HX-Trigger-Name") == "client_price" and _num(form, "client_price", 0.0) > 0:
                svc.set_item_price(item, _num(form, "client_price", 0.0), proposal)
            elif "markup_percent" in form:
                svc.set_item_markup(item, _num(form, "markup_percent", item["markup_percent"]), proposal)
    state.meta(sid)["pptx"].pop("results", None)  # product list changed: matches must be redone
    if not _is_htmx(request):
        return _back(request, "/proposals/current#products")
    return page(request, "_proposal_items.html", **_editor_context(request, sid))


@router.post("/proposals/current/settings")
async def update_settings(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    proposal = state.proposal(sid)
    svc.set_discount_option(proposal, form.get("discount_option", "None"), _num(form, "custom_discount", proposal.get("proposal_discount_percent", 0.0)))
    proposal["proposal_use_msrp"] = form.get("use_msrp") == "on"
    proposal["proposal_fifty_cent_rounding"] = form.get("fifty_cent_rounding") == "on"
    proposal["proposal_marketing_rounding"] = form.get("marketing_rounding") == "on"
    proposal["proposal_client_budget"] = _num(form, "client_budget", 0.0)
    if not _is_htmx(request):
        return _back(request, "/proposals/current#products")
    return page(request, "_proposal_items.html", **_editor_context(request, sid))


@router.get("/proposals/current/tables/{index}.csv")
def table_csv(index: int, sid: str = Depends(auth.require_staff)):
    proposal = state.proposal(sid)
    if index >= len(proposal["proposal_products"]):
        return Response(status_code=404)
    table = svc.moq_table(proposal["proposal_products"][index], proposal)
    if not table:
        return Response(status_code=404)
    name = table["name"].replace(" ", "_")
    return Response(svc.moq_table_csv(table), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="proposal_product_{index + 1}_{name}.csv"'})


@router.post("/proposals/current/save")
async def save_proposal(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    proposal = state.proposal(sid)
    name = (form.get("name") or "").strip()
    if not proposal["proposal_products"]:
        state.flash(sid, "Add products to your proposal to enable saving", "error")
    elif not name:
        state.flash(sid, "Please enter a proposal name", "error")
    else:
        ok, message, result = proposal_manager.save_proposal(name=name, created_by=(form.get("created_by") or "").strip(),
                                                            proposal_data=svc.saved_payload(proposal), dataset=DATASET,
                                                            overwrite=form.get("overwrite") == "on")
        if ok:
            state.meta(sid).update(loaded_proposal_id=result, loaded_proposal_name=name)
        state.flash(sid, message, "success" if ok else "error")
    return _back(request, "/proposals/current#save")


# ----------------------------------------------------------------------------
# Client form link (Tab 2)
# ----------------------------------------------------------------------------

@router.post("/proposals/current/form-link")
async def form_link(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    meta = state.meta(sid)
    if not meta.get("loaded_proposal_id"):
        state.flash(sid, "Save the proposal first: the client form loads its products from the saved proposal", "error")
        return _back(request, "/proposals/current#form-link")
    token = client_form.generate_session_token()
    client = {key: (form.get(key) or "").strip() for key in ("client_type", "company_name", "contact_name", "contact_email", "contact_phone")}
    client["client_type"] = client["client_type"] or "New"
    if any(client[k] for k in ("company_name", "contact_name", "contact_email", "contact_phone")):
        client_form.save_draft(meta["loaded_proposal_id"], token, {"client_info": client})
    meta["client_form_link"] = f"{settings.CLIENT_FORM_BASE_URL}?client_form={meta['loaded_proposal_id']}&session={token}"
    return _back(request, "/proposals/current#form-link")


# ----------------------------------------------------------------------------
# PowerPoint: template, match review, generation
# ----------------------------------------------------------------------------

def _pptx(sid):
    return state.meta(sid)["pptx"]


def _template(sid):
    """The selected template dict (newest by default), or None when Drive has none."""
    pptx = _pptx(sid)
    if not pptx.get("template"):
        available = _safe(templates.list_templates, [])
        if available:
            pptx["template"] = available[0]
    return pptx.get("template")


def _review_context(request, sid):
    proposal = state.proposal(sid)
    pptx = _pptx(sid)
    results, names = pptx.get("results", []), pptx.get("names", [])
    confirmations = pptx.setdefault("confirmations", {})
    rows = pptx_jobs.review_rows(results, confirmations)
    confirmed = pptx_jobs.confirmed_matches(results, confirmations)
    pending_names = pptx_jobs.pending(results, confirmations)
    groups_detail = []
    partners, resolved, all_impacts = [], {}, []
    if not pending_names and confirmed and pptx.get("path"):
        _, groups_detail = pptx_jobs.variant_groups(proposal, confirmed)
        partners, resolved, all_impacts = pptx_jobs.impact_slides(proposal, pptx["path"])
        selections = pptx.setdefault("impact", {})
        for partner in partners:
            selections.setdefault(partner, resolved.get(partner) or {"slide_title": None, "slide_index": None})
    job = pptx_jobs.job(pptx.get("job_id")) if pptx.get("job_id") else None
    return {"proposal": proposal, "rows": rows, "names": names, "confirmed": confirmed, "pending": pending_names,
            "ready": sum(1 for r in rows if r["status"] == "done"), "review": sum(1 for r in rows if r["status"] == "review"),
            "groups": groups_detail, "variant_prefs": pptx.setdefault("variant_prefs", {}), "partners": partners,
            "impact": pptx.get("impact", {}), "all_impacts": all_impacts, "job": job, "pptx_template": pptx.get("template"),
            "search": pptx.get("search", {}), "meta": state.meta(sid), "flash": state.pop_flash(sid),
            "summary": pptx_jobs.report_summary(job["reports"]) if job and job.get("reports") else None}


@router.post("/proposals/current/pptx/template")
async def choose_template(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    available = _safe(lambda: templates.list_templates(force=form.get("refresh") == "1"), [])
    chosen = next((t for t in available if t["file_id"] == form.get("file_id")), None)
    pptx = _pptx(sid)
    if chosen and (not pptx.get("template") or pptx["template"]["file_id"] != chosen["file_id"]):
        pptx.clear()
        pptx["template"] = chosen
    return _back(request, "/proposals/current#pptx")


@router.post("/proposals/current/pptx/match")
def run_matching(request: Request, sid: str = Depends(auth.require_staff)):
    """Download the template (once per process) and match every proposal product to a slide."""
    proposal = state.proposal(sid)
    template = _template(sid)
    if not proposal["proposal_products"]:
        state.flash(sid, "Add products to the proposal first", "error")
        return _back(request, "/proposals/current#pptx")
    if not template:
        state.flash(sid, "No product slide templates found in Google Drive", "error")
        return _back(request, "/proposals/current#pptx")
    try:
        path = templates.template_path(template)
        results, names, index = pptx_jobs.match_products(proposal, path, template["name"], DATASET)
    except Exception as e:
        state.flash(sid, f"Error loading PowerPoint template: {e}", "error")
        return _back(request, "/proposals/current#pptx")
    pptx = _pptx(sid)
    pptx.update(path=path, results=results, names=names, index=index, confirmations={}, impact={}, variant_prefs={}, job_id=None, search={})
    return RedirectResponse("/proposals/current/pptx", status_code=303)


@router.get("/proposals/current/pptx", response_class=HTMLResponse)
def review(request: Request, sid: str = Depends(auth.require_staff)):
    if not _pptx(sid).get("results"):
        return RedirectResponse("/proposals/current#pptx", status_code=303)
    return page(request, "pptx_review.html", **_review_context(request, sid))


@router.post("/proposals/current/pptx/decide")
async def decide(request: Request, sid: str = Depends(auth.require_staff)):
    """Confirm / change / use alternative / search / skip / cancel for one product."""
    form = await request.form()
    pptx = _pptx(sid)
    name, action, slide = form.get("gs_name", ""), form.get("action", ""), form.get("slide", "")
    confirmations = pptx.setdefault("confirmations", {})
    result = next((r for r in pptx.get("results", []) if r["gs_name"] == name), None)
    if result:
        if action == "confirm":
            confirmations[name] = {"confirmed": True, "pptx_name": slide or result["pptx_name"]}
            _remember(sid, result, confirmations[name]["pptx_name"], "fuzzy_confirmed" if result["kind"] == "fuzzy" else "poor_confirmed", result["confidence"])
        elif action == "use":
            confirmations[name] = {"confirmed": True, "pptx_name": slide}
            _remember(sid, result, slide, "alternative_selected" if slide in dict(result["alternatives"]) else "manual_search", 0)
        elif action == "skip":
            confirmations[name] = {"skipped": True}
        elif action == "change":
            confirmations[name] = {"changing": True}
        elif action == "search":
            confirmations[name] = {"changing": True}
            pptx.setdefault("search", {})[name] = form.get("query", "")
        else:  # cancel
            confirmations.pop(name, None)
            pptx.get("search", {}).pop(name, None)
        pptx["job_id"] = None
    if not _is_htmx(request):
        return RedirectResponse("/proposals/current/pptx", status_code=303)
    return page(request, "_pptx_review.html", **_review_context(request, sid))


def _remember(sid, result, slide, match_type, confidence):
    """Save the decision to the saved_matches sheet so the next session starts from it."""
    pptx = _pptx(sid)
    index = pptx.get("index", {})
    template = pptx.get("template") or {}
    if slide in index:
        try:
            match_memory.save_confirmed_match(product_name=result["gs_name"], slide_index=index[slide], slide_title=slide,
                                              dataset=DATASET, match_type=match_type, confidence=confidence,
                                              template_name=template.get("name", ""))
        except Exception as e:
            state.flash(sid, f"Match confirmed here but could not be saved to Google Sheets: {e}", "error")


@router.post("/proposals/current/pptx/options")
async def options(request: Request, sid: str = Depends(auth.require_staff)):
    """Variant display choices and impact slide selections."""
    form = await request.form()
    pptx = _pptx(sid)
    for key in form.keys():
        if key.startswith("variant__"):
            pptx.setdefault("variant_prefs", {})[key[len("variant__"):]] = form.get(key)
        elif key.startswith("impact__"):
            partner, title = key[len("impact__"):], form.get(key)
            slides = find_impacts(pptx)
            chosen = next((s for s in slides if s["slide_title"] == title), None)
            pptx.setdefault("impact", {})[partner] = {"slide_title": chosen["slide_title"], "slide_index": chosen["slide_index"]} if chosen \
                else {"slide_title": None, "slide_index": None}
    pptx["job_id"] = None
    if not _is_htmx(request):
        return RedirectResponse("/proposals/current/pptx", status_code=303)
    return page(request, "_pptx_review.html", **_review_context(request, sid))


def find_impacts(pptx):
    from pbp.core.slide_matcher import find_all_impact_slides
    return find_all_impact_slides(str(pptx["path"])) if pptx.get("path") else []


@router.post("/proposals/current/pptx/reset")
def reset(request: Request, sid: str = Depends(auth.require_staff)):
    pptx = _pptx(sid)
    pptx.update(confirmations={}, impact={}, variant_prefs={}, job_id=None, search={})
    return RedirectResponse("/proposals/current/pptx", status_code=303)


@router.post("/proposals/current/pptx/generate")
async def generate(request: Request, sid: str = Depends(auth.require_staff)):
    form = await request.form()
    proposal = state.proposal(sid)
    pptx = _pptx(sid)
    results, confirmations = pptx.get("results", []), pptx.get("confirmations", {})
    confirmed = pptx_jobs.confirmed_matches(results, confirmations)
    if pptx_jobs.pending(results, confirmations) or not confirmed:
        state.flash(sid, "Please review every pending match before generating", "error")
        return RedirectResponse("/proposals/current/pptx", status_code=303)
    overrides = {p: s for p, s in pptx.get("impact", {}).items() if s.get("slide_index") is not None}
    client_name = (form.get("client_name") or state.order(sid)["client_info"].get("company_name") or "Client").strip() or "Client"
    pptx["job_id"] = pptx_jobs.start_job(proposal, pptx["path"], confirmed, pptx.get("variant_prefs", {}), overrides, client_name)
    if not _is_htmx(request):
        return RedirectResponse("/proposals/current/pptx", status_code=303)
    return page(request, "_pptx_job.html", job=pptx_jobs.job(pptx["job_id"]), summary=None)


@router.get("/proposals/current/pptx/job", response_class=HTMLResponse)
def job_status(request: Request, sid: str = Depends(auth.require_staff)):
    job = pptx_jobs.job(_pptx(sid).get("job_id"))
    summary = pptx_jobs.report_summary(job["reports"]) if job and job.get("reports") else None
    return page(request, "_pptx_job.html", job=job, summary=summary)


@router.get("/proposals/current/pptx/download")
def download(sid: str = Depends(auth.require_staff)):
    job = pptx_jobs.job(_pptx(sid).get("job_id"))
    if not job or job["status"] != "done":
        return Response(status_code=404)
    return Response(job["data"], media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    headers={"Content-Disposition": f'attachment; filename="{job["filename"]}"'})
