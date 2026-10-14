"""
PowerPoint proposal generation: slide matching, review state, and a small
background job runner so the browser can poll instead of waiting 5 to 30 s.
"""

import threading
import uuid
from datetime import datetime

from pptx import Presentation

from pbp.core.pptx_generator import (
    calculate_proposal_pricing,
    check_pricing_consistency,
    create_complete_proposal_presentation,
    detect_variant_groups,
    download_presentation,
    get_slide_title,
)
from pbp.core.pricing_engine import get_unit_price_new_system
from pbp.core.slide_matcher import SlideMatcher, extract_unique_partners, find_all_impact_slides, resolve_impact_slides
from pbp.sheets import match_memory, templates

CONFIDENCE_OK = 70
SKIP_IMPACT = "None - Skip impact slide"


# ----------------------------------------------------------------------------
# Matching
# ----------------------------------------------------------------------------

def slide_titles(template_path):
    """(ordered unique product-slide titles, {title: slide index}) of a deck."""
    names, index = [], {}
    for i, slide in enumerate(Presentation(str(template_path)).slides):
        title = get_slide_title(slide)
        if title and title not in index:
            names.append(title)
            index[title] = i
    return names, index


def match_products(proposal, template_path, template_name, dataset="real"):
    """Match every proposal product to a slide. Returns (results as dicts, slide titles, title->index)."""
    names, index = slide_titles(template_path)
    match_memory._load_all_matches_data.clear()  # confirmations from other sessions apply right away
    matcher = SlideMatcher(names)
    gs_names = [item["product_data"]["Product/Service"] for item in proposal["proposal_products"]]
    results = []
    for r in matcher.batch_match(gs_names, dataset=dataset, template_name=template_name):
        kind = "exact" if r.match_type == "exact" else ("fuzzy" if r.match_type == "fuzzy" and r.confidence >= CONFIDENCE_OK else "poor")
        source = {"confirmed": "Previously Confirmed", "manual": "Manual Override"}.get(r.match_source, "Exact Match") if kind == "exact" \
            else ("Auto-match" if kind == "fuzzy" else "No match found")
        results.append({
            "gs_name": r.gs_product_name, "pptx_name": r.pptx_product_name if kind != "poor" else None,
            "kind": kind, "confidence": r.confidence, "alternatives": list(r.alternatives[:3]), "source": source,
        })
    # Items needing review first, lowest confidence first
    results.sort(key=lambda x: (x["kind"] == "exact", x["confidence"] if x["kind"] != "exact" else 999, x["gs_name"]))
    return results, names, index


def review_rows(results, confirmations):
    """Results merged with the staff decisions: confirmed/skipped/pending plus the slide that will be used."""
    rows = []
    for r in results:
        decision = confirmations.get(r["gs_name"], {})
        if r["kind"] == "exact" and not decision:
            status, slide = "done", r["pptx_name"]
        elif decision.get("confirmed"):
            status, slide = "done", decision["pptx_name"]
        elif decision.get("skipped"):
            status, slide = "skipped", None
        else:
            status, slide = "review", (r["pptx_name"] if r["kind"] == "fuzzy" else None)
        rows.append({**r, "status": status, "slide": slide, "changing": decision.get("changing", False)})
    return rows


def pending(results, confirmations):
    return [row["gs_name"] for row in review_rows(results, confirmations) if row["status"] == "review" and row["kind"] == "fuzzy"]


def confirmed_matches(results, confirmations):
    return {row["gs_name"]: row["slide"] for row in review_rows(results, confirmations) if row["status"] == "done" and row["slide"]}


def search_slides(names, query, limit=15):
    query = query.lower().strip()
    return [n for n in names if query and query in n.lower()][:limit]


# ----------------------------------------------------------------------------
# Variants and impact slides
# ----------------------------------------------------------------------------

def variant_groups(proposal, confirmed):
    """Products sharing one slide, with their pricing and the display options offered."""
    groups, _ = detect_variant_groups(confirmed)
    out = []
    items = {item["product_data"]["Product/Service"]: item for item in proposal["proposal_products"]}
    for slide_name, products in groups.items():
        pricing = [calculate_proposal_pricing(items[p], get_unit_price_new_system, proposal.get("proposal_marketing_rounding", False),
                                              proposal.get("proposal_discount_percent", 0.0)) for p in products if p in items]
        pricing = [p for p in pricing if p]
        consistent = check_pricing_consistency(pricing)
        partners = {items[p]["product_data"].get("Partner", "") for p in products if p in items} - {""}
        if consistent:
            options = ["Display single row (all variants have same pricing)", "Display all variants (show each variant in separate row)",
                       "Create separate slides (duplicate slide for each variant)", "Skip these products"]
            default = options[0]
        else:
            options = ["Display together (recommended - fills multiple table rows)", "Create separate slides (duplicate slide for each variant)", "Skip these products"]
            default = options[0] if len(partners) <= 1 else options[1]
        out.append({"slide": slide_name, "products": products, "pricing": pricing, "consistent": consistent,
                    "partners": sorted(partners), "options": options, "default": default})
    return groups, out


def impact_slides(proposal, template_path):
    """(unique partners, auto-resolved {partner: slide}, every impact slide in the deck)."""
    partners = extract_unique_partners(proposal["proposal_products"])
    all_slides = find_all_impact_slides(str(template_path))
    resolved = resolve_impact_slides(partners, templates.impact_slide_mapping(), all_slides)
    return partners, resolved, all_slides


# ----------------------------------------------------------------------------
# Generation job
# ----------------------------------------------------------------------------

_jobs = {}
_lock = threading.Lock()


def start_job(proposal, template_path, confirmed, variant_prefs, impact_overrides, client_name="Client"):
    """Generate in a background thread; returns the job id to poll."""
    job_id = uuid.uuid4().hex[:12]
    job = {"id": job_id, "status": "running", "step": "Loading templates", "started": datetime.now(), "error": None,
           "data": None, "filename": None, "reports": [], "seconds": None, "product_count": len(confirmed)}
    with _lock:
        _jobs[job_id] = job

    def run():
        try:
            job["step"] = f"Selecting and updating {len(confirmed)} product slide(s)"
            groups, _ = detect_variant_groups(confirmed)
            partners, resolved, _ = impact_slides(proposal, template_path)
            prs, reports = create_complete_proposal_presentation(
                str(template_path), str(templates.intro_outro_path()), confirmed, proposal["proposal_products"],
                get_unit_price_new_system, proposal.get("proposal_marketing_rounding", False),
                proposal.get("proposal_discount_percent", 0.0), impact_overrides or None, groups or None,
                variant_prefs or None, proposal.get("proposal_fifty_cent_rounding", False),
                proposal.get("proposal_discount_type"), resolved,
            )
            job["step"] = "Preparing download"
            job["data"] = download_presentation(prs, client_name).getvalue()
            job["filename"] = f"Proposal_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pptx"
            job["reports"] = reports
            job["seconds"] = (datetime.now() - job["started"]).total_seconds()
            job["status"] = "done"
        except Exception as e:  # shown to the user on the review page
            job["error"] = str(e)
            job["status"] = "failed"

    threading.Thread(target=run, daemon=True).start()
    return job_id


def job(job_id):
    return _jobs.get(job_id)


def report_summary(reports):
    counts = {"auto_updated": 0, "needs_review": 0, "unchanged": 0}
    for r in reports:
        counts[r.get("status", "unchanged")] = counts.get(r.get("status", "unchanged"), 0) + 1
    return counts
