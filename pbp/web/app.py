"""
PBP web app (FastAPI + HTMX): the client order form (phase 1) and staff order screens (phase 2).

Routes (client form; staff screens live in staff.py):
  GET  /                        legacy link format ?client_form=ID&session=TOKEN -> redirect to /form/ID
  GET  /form/{proposal_id}      the order form (or "Order received" once submitted)
  POST /form/{proposal_id}      action=save | submit | add_item (works without JavaScript)
  POST /form/{proposal_id}/items  HTMX partial: the item rows with one more row
  GET  /internal/health         sync status and last Sheets contact

Run locally:
  uvicorn pbp.web.app:app --reload --port 8000
"""

import asyncio
import contextlib
import logging
import pathlib
import threading
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pbp import settings
from pbp.core.forms_config import MAX_PRODUCT_LINES
from pbp.sheets import client_form, gateway
from pbp.web import staff
from pbp.web.templating import templates

HERE = pathlib.Path(__file__).parent
log = logging.getLogger("pbp.web")

# Choices shown in the form (same as the Streamlit client form)
PAYMENT_METHODS = ["ACH", "Credit Card", "Check", "Other"]
ACCOUNTING_CONTACT_TYPES = ["Email", "Accounting platform"]

# Background sync state for /internal/health
sync_state = {"last_run_at": None, "stuck_orders": [], "runs": 0}
_sync_lock = threading.Lock()


def run_pending_syncs():
    """Copy received orders that are still waiting into Form Responses (safe to call any time)."""
    if not _sync_lock.acquire(blocking=False):
        return  # a run is already in progress
    try:
        sync_state["stuck_orders"] = client_form.retry_pending_syncs()
        sync_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
        sync_state["runs"] += 1
    except Exception as e:  # never let the loop die
        log.warning("pending-sync run failed: %s", e)
    finally:
        _sync_lock.release()


async def _sync_loop():
    # ponytail: single worker; move this to a Render cron job if a second instance is ever needed
    while True:
        await asyncio.to_thread(run_pending_syncs)
        await asyncio.sleep(settings.SYNC_LOOP_SECONDS)


@contextlib.asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(_sync_loop()) if settings.SYNC_LOOP_SECONDS > 0 else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Peace by Piece Order Form", lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
app.include_router(staff.router)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _page(request, template, status_code=200, **context):
    return templates.TemplateResponse(request, template, context, status_code=status_code)


def _error_page(request, message, status_code=404):
    return _page(request, "error.html", status_code=status_code, message=message)


def _load(proposal_id, session_id):
    """Proposal products and the saved draft for this link, or (None, None) when the proposal is gone."""
    proposal = client_form.load_proposal_for_client(proposal_id)
    if proposal is None:
        return None, None
    return proposal, client_form.load_draft(proposal_id, session_id)


def _item_rows_from_saved(saved_products):
    """Rows to show on first load: the saved items plus one empty row."""
    rows = [dict(product) for product in saved_products]
    rows.append({"name": "", "quantity": 100, "customization_notes": ""})
    return rows


def _item_rows_from_form(form):
    """Rows exactly as the client has them on screen (including empty ones)."""
    rows = []
    for index in range(MAX_PRODUCT_LINES):
        if f"product_{index}" not in form:
            break
        rows.append({
            "name": form.get(f"product_{index}", ""),
            "quantity": _int(form.get(f"quantity_{index}"), 100),
            "customization_notes": form.get(f"notes_{index}", ""),
        })
    return rows or _item_rows_from_saved([])


def _int(value, default):
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def _drop_shipping(form):
    """Saved as "Yes", "No", or "Other: <client's own words>" (same as the Streamlit form)."""
    choice = form.get("drop_shipping")
    if choice == "Other":
        return f"Other: {form.get('drop_shipping_other', '').strip()}"
    return "Yes" if choice == "Yes" else "No"


def _form_data(form, item_rows):
    """The dict stored as the draft / sent to Form Responses (same shape as the Streamlit form)."""
    return {
        "client_info": {
            "client_type": form.get("client_type", "New"),
            "company_name": form.get("company_name", "").strip(),
            "contact_name": form.get("contact_name", "").strip(),
            "contact_email": form.get("contact_email", "").strip(),
            "contact_phone": form.get("contact_phone", "").strip(),
        },
        "products": [row for row in item_rows if row["name"]],
        "shipping_info": {
            "shipping_address": form.get("shipping_address", "").strip(),
            "billing_address": form.get("billing_address", "").strip(),
            "drop_shipping": _drop_shipping(form),
            "drop_shipping_instructions": form.get("drop_shipping_instructions", "").strip(),
            "in_hands_date": form.get("in_hands_date", "").strip(),
        },
        "payment_info": {
            "impact_cards": form.get("impact_cards", "Yes"),
            "impact_card_selection": "",
            "payment_preference": "",  # Payment terms are set by PBP staff, not the client
            "payment_method": form.get("payment_method", "ACH"),
            "accounting_contact_type": form.get("accounting_contact_type", "Email"),
            "accounting_contact": form.get("accounting_contact", "").strip(),
        },
        "notes": form.get("notes", "").strip(),
    }


def _missing_required(data):
    missing = []
    if not data["products"]:
        missing.append("At least one product")
    if not data["client_info"]["company_name"]:
        missing.append("Company Name")
    if not data["client_info"]["contact_name"]:
        missing.append("Contact Name")
    if not data["client_info"]["contact_email"]:
        missing.append("Contact Email")
    if not data["shipping_info"]["shipping_address"]:
        missing.append("Shipping Address")
    if not data["shipping_info"]["in_hands_date"]:
        missing.append("In-Hands Date")
    if data["shipping_info"]["drop_shipping"] == "Other: ":
        missing.append("Shipping description (Other)")
    payment = data["payment_info"]
    if not payment["accounting_contact"]:
        missing.append("Accounting Email or Platform")
    elif payment["accounting_contact_type"] == "Email" and "@" not in payment["accounting_contact"]:
        missing.append("a valid Accounting Email Address")
    return missing


def _render_form(request, proposal_id, session_id, proposal, draft, data, item_rows, errors=(), message=""):
    return _page(
        request, "form.html",
        proposal_id=proposal_id, session_id=session_id, proposal=proposal,
        data=data, item_rows=item_rows, errors=list(errors), message=message,
        draft=draft, max_items=min(len(proposal["products"]), MAX_PRODUCT_LINES),
        payment_methods=PAYMENT_METHODS, accounting_contact_types=ACCOUNTING_CONTACT_TYPES,
    )


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, client_form: str = "", session: str = ""):
    """Links generated by the Streamlit app look like /?client_form=ID&session=TOKEN."""
    if client_form:
        return RedirectResponse(f"/form/{client_form}?session={session}", status_code=307)
    return _page(request, "index.html")


@app.get("/form/{proposal_id}", response_class=HTMLResponse)
def show_form(request: Request, proposal_id: str, session: str = ""):
    if not session:
        return _error_page(request, "Invalid form link (missing session). Please contact your PBP representative.", 400)
    proposal, draft = _load(proposal_id, session)
    if proposal is None:
        return _error_page(request, "This form is no longer available. Please contact your PBP representative.")
    if draft and draft.get("status") in (client_form.STATUS_PENDING, client_form.STATUS_SUBMITTED):
        return _page(request, "received.html")

    saved = draft["form_data"] if draft else {}
    item_rows = _item_rows_from_saved(saved.get("products", []))
    return _render_form(request, proposal_id, session, proposal, draft, saved, item_rows)


@app.post("/form/{proposal_id}", response_class=HTMLResponse)
async def post_form(request: Request, proposal_id: str, session: str = ""):
    """Save Progress, Submit Order, or (without JavaScript) Add Another Item."""
    if not session:
        return _error_page(request, "Invalid form link (missing session). Please contact your PBP representative.", 400)
    proposal, draft = _load(proposal_id, session)
    if proposal is None:
        return _error_page(request, "This form is no longer available. Please contact your PBP representative.")
    if draft and draft.get("status") in (client_form.STATUS_PENDING, client_form.STATUS_SUBMITTED):
        return _page(request, "received.html")

    form = await request.form()
    action = form.get("action", "save")
    item_rows = _item_rows_from_form(form)
    data = _form_data(form, item_rows)

    if action == "add_item":
        if len(item_rows) < min(len(proposal["products"]), MAX_PRODUCT_LINES):
            item_rows.append({"name": "", "quantity": 100, "customization_notes": ""})
        return _render_form(request, proposal_id, session, proposal, draft, data, item_rows)

    # No file upload on the form; a file saved with an older draft is kept as it is
    if action == "submit":
        missing = _missing_required(data)
        if missing:
            return _render_form(request, proposal_id, session, proposal, draft, data, item_rows,
                                errors=["Please fill in required fields: " + ", ".join(missing)])
        ok, msg = await asyncio.to_thread(client_form.submit_form, proposal_id, session, data)
        if ok:
            return _page(request, "received.html")
        return _render_form(request, proposal_id, session, proposal, draft, data, item_rows, errors=[msg])

    ok, msg = await asyncio.to_thread(client_form.save_draft, proposal_id, session, data)
    if ok:
        draft = {"form_data": data, "updated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": client_form.STATUS_DRAFT}
        return _render_form(request, proposal_id, session, proposal, draft, data, item_rows,
                            message="Progress saved. You can close this page and return later using the same link.")
    return _render_form(request, proposal_id, session, proposal, draft, data, item_rows, errors=[f"Could not save: {msg}"])


@app.post("/form/{proposal_id}/items", response_class=HTMLResponse)
async def add_item(request: Request, proposal_id: str, session: str = ""):
    """HTMX: return the item rows with one more empty row, keeping what the client typed."""
    proposal = client_form.load_proposal_for_client(proposal_id)
    if proposal is None:
        return HTMLResponse("", status_code=404)
    form = await request.form()
    item_rows = _item_rows_from_form(form)
    max_items = min(len(proposal["products"]), MAX_PRODUCT_LINES)
    if len(item_rows) < max_items:
        item_rows.append({"name": "", "quantity": 100, "customization_notes": ""})
    return _page(request, "_items.html", proposal=proposal, item_rows=item_rows, max_items=max_items,
                 proposal_id=proposal_id, session_id=session)


@app.get("/internal/health")
def health():
    """Sync status for Render health checks and staff."""
    pending = len(sync_state["stuck_orders"])
    return JSONResponse({
        "status": "degraded" if pending else "ok",
        "sync": {**sync_state, "loop_seconds": settings.SYNC_LOOP_SECONDS},
        "sheets": gateway.state,
    }, status_code=503 if pending else 200)
