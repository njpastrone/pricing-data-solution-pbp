"""
Golden parity snapshots for saved orders and saved proposals.

Why this exists: the pricing engine and PowerPoint generator are being moved
out of the Streamlit app (pbp/core). A snapshot of what they produce today for
every saved order and proposal lets any later change prove it did not alter a
single number or slide.

Two modes:

1. GENERATE (needs Google credentials, READ-ONLY against the live Sheets):

       python tests/golden/golden.py

   Reads every row of the saved_orders and saved_proposals sheets and writes
   one JSON file per order/proposal under tests/golden/snapshots/. Each file
   holds the pricing inputs (client details stripped) plus the expected
   outputs. Snapshots hold internal cost data, so they are generated locally
   and kept out of git (tests/golden/snapshots/ is in .gitignore). Nothing is ever written to Google Sheets: the client is built with
   read-only scopes, so a write would be rejected by Google itself.

   Credentials come from the same GCP_* environment variables the app uses on
   Render, or from GOLDEN_SERVICE_ACCOUNT_JSON=/path/to/service-account.json.

2. COMPARE (offline, on the machine that holds the snapshots):

       python -m pytest tests/golden -q

   tests/golden/test_golden.py recomputes every snapshot from its stored
   inputs and fails if anything differs. Without snapshots (e.g. in CI) the
   snapshot tests are skipped and only the synthetic self-check runs.

What is covered: unit prices, tiers, quotes, MOQ and tariff per order line;
split totals per order; proposal pricing and PBP MSRP per proposal line; the
PowerPoint deck (slide titles and every table cell) generated for each
proposal from the committed template with automatic slide matching.

What is NOT covered yet: the invoice/PO HTML and CSV. That code still lives
inline in app.py (Tab 4) and cannot be called without running the Streamlit
app; phase 2 of the migration moves it into pbp/ and extends these snapshots.
"""

import json
import os
import sys
from datetime import date, datetime
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

SNAPSHOT_DIR = os.path.join(REPO_ROOT, "tests", "golden", "snapshots")
PRODUCT_TEMPLATE = os.path.join(REPO_ROOT, "templates", "November All Slides.pptx")
INTRO_OUTRO_TEMPLATE = os.path.join(REPO_ROOT, "templates", "Intro_Outro_Slides_PbP_Proposals.pptx")

NO_CREDENTIALS_HELP = """
No Google credentials found, so no snapshots were generated.

To generate the golden baselines (one-time, before phase 1 of the migration starts):

  1. Get the read-only service-account key for the PBP Google Cloud project
     (the same service account the app uses on Render). Either:
       export GOLDEN_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
     or export the GCP_* variables exactly as they are set on Render
     (GCP_TYPE, GCP_PROJECT_ID, GCP_PRIVATE_KEY_ID, GCP_PRIVATE_KEY, GCP_CLIENT_EMAIL,
      GCP_CLIENT_ID, GCP_AUTH_URI, GCP_TOKEN_URI, GCP_AUTH_PROVIDER_X509_CERT_URL,
      GCP_CLIENT_X509_CERT_URL, GCP_UNIVERSE_DOMAIN).
  2. From the repository root, on the main branch:
       pip install -r requirements.txt
       python tests/golden/golden.py
     This reads the saved_orders and saved_proposals sheets (read-only scope, no
     writes possible) and writes tests/golden/snapshots/orders/*.json and
     tests/golden/snapshots/proposals/*.json. Expect a few minutes: one PowerPoint
     deck is generated per proposal.
  3. Keep the snapshots local: tests/golden/snapshots/ is in .gitignore and must
     never be committed (client_info, order_notes, partner_shipping and
     product_photos are stripped, but internal costs and markups remain).
  4. From then on `python -m pytest tests/golden -q` on that machine fails on any
     pricing or PowerPoint change. Re-run it on each later phase's branch.
"""

# Order keys that hold client details rather than pricing inputs. Stripped
# before a snapshot is written so no personal data lands in the snapshot.
ORDER_KEYS_TO_STRIP = ("client_info", "order_notes", "partner_shipping", "product_photos")


def plain(value):
    """Round-trip through JSON so numpy numbers, dates and tuples compare as plain Python values."""
    return json.loads(json.dumps(value, default=_json_default))


def _json_default(value):
    if hasattr(value, "item"):  # numpy scalar
        return value.item()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, set):
        return sorted(value)
    return str(value)


# ----------------------------------------------------------------------------
# Snapshot builders (pure functions of the saved JSON blobs)
# ----------------------------------------------------------------------------

def order_snapshot(order_data):
    """Pricing outputs for one saved order (Tab 3 / Tab 4 numbers that come from pbp.core)."""
    from pbp.core.helpers import calculate_moq, calculate_split_totals, get_tariff_rate
    from pbp.core.pricing_engine import calculate_product_quote, get_unit_price_new_system

    items = order_data.get("order_items", [])
    snapshot = {
        "items": [],
        "split_totals": calculate_split_totals(items, fifty_cent_rounding=False),
        "split_totals_fifty_cent": calculate_split_totals(items, fifty_cent_rounding=True),
    }

    for item in items:
        line = {"product_name": item.get("product_name"), "quantity": item.get("quantity")}
        if item.get("is_custom") or item.get("is_custom_product"):
            line["custom"] = True
            snapshot["items"].append(line)
            continue

        product = item.get("product_data", {})
        quantity = item.get("quantity", 1)
        markup = item.get("markup_percent", 100)
        unit_price, tier_range, price_column = get_unit_price_new_system(product, quantity)

        line["unit_price"] = unit_price
        line["tier_range"] = tier_range
        line["price_column"] = price_column
        line["quote"] = calculate_product_quote(
            product, quantity, markup,
            include_customization=item.get("include_customization", False),
            customization_minimum=item.get("customization_minimum"),
        )
        if unit_price is not None:
            line["tariff_rate"] = get_tariff_rate(product, unit_price)
            line["moq"] = calculate_moq(unit_price * (1 + markup / 100), product)["moq"]
        snapshot["items"].append(line)

    return plain(snapshot)


def proposal_pricing_snapshot(proposal_data):
    """Pricing outputs for one saved proposal (Tab 1 tables and PowerPoint prices)."""
    from pbp.core.pptx_generator import calculate_proposal_pricing
    from pbp.core.pricing_engine import calculate_pbp_msrp, get_unit_price_new_system

    marketing_rounding = proposal_data.get("proposal_marketing_rounding", False)
    discount_percent = proposal_data.get("proposal_discount_percent") or 0.0

    lines = []
    for item in proposal_data.get("proposal_products", []):
        product = item["product_data"]
        lines.append({
            "product_name": product.get("Product/Service"),
            "quantity": item.get("quantity"),
            "markup_percent": item.get("markup_percent"),
            "proposal_pricing": calculate_proposal_pricing(
                item, get_unit_price_new_system, marketing_rounding, discount_percent
            ),
            "pbp_msrp": calculate_pbp_msrp(product, item.get("quantity") or 100),
        })
    return plain({"items": lines})


def proposal_pptx_snapshot(proposal_data, dataset="real"):
    """
    Slide titles and table cells of the deck generated for one saved proposal.

    Matching is forced to the automatic fuzzy matcher (no confirmed-match
    lookup in Sheets, no local manual_matches.json) so the result depends only
    on the code and the committed template.
    """
    from pptx import Presentation

    from pbp.core.pptx_generator import (
        create_complete_proposal_presentation,
        detect_variant_groups,
        get_slide_title,
    )
    from pbp.core.pricing_engine import get_unit_price_new_system
    from pbp.core.slide_matcher import SlideMatcher

    items = proposal_data.get("proposal_products", [])
    gs_names = [item["product_data"]["Product/Service"] for item in items]

    template_titles = []
    for slide in Presentation(PRODUCT_TEMPLATE).slides:
        title = get_slide_title(slide)
        if title and title not in template_titles:
            template_titles.append(title)

    with patch("pbp.sheets.match_memory.get_confirmed_match", return_value=None), \
         patch("pbp.core.slide_matcher.get_manual_match", return_value=None):
        results = SlideMatcher(template_titles).batch_match(gs_names, dataset=dataset)

    confirmed = {r.gs_product_name: r.pptx_product_name for r in results if r.is_usable()}
    variant_groups, _ = detect_variant_groups(confirmed)

    prs, table_reports = create_complete_proposal_presentation(
        PRODUCT_TEMPLATE,
        INTRO_OUTRO_TEMPLATE,
        confirmed,
        items,
        get_unit_price_new_system,
        marketing_rounding=proposal_data.get("proposal_marketing_rounding", False),
        discount_percent=proposal_data.get("proposal_discount_percent") or 0.0,
        variant_groups=variant_groups or None,
        variant_grouping_prefs={},
        discount_type=proposal_data.get("proposal_discount_type"),
    )

    slides = []
    for slide in prs.slides:
        tables = [
            [[cell.text for cell in row.cells] for row in shape.table.rows]
            for shape in slide.shapes if shape.has_table
        ]
        slides.append({"title": get_slide_title(slide), "tables": tables})

    return plain({"matches": confirmed, "slides": slides, "table_reports": table_reports})


# ----------------------------------------------------------------------------
# Generation against the live Sheets (read-only)
# ----------------------------------------------------------------------------

def _readonly_sheets_client():
    """gspread client that can only read. Google rejects any write made with these scopes."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    json_path = os.getenv("GOLDEN_SERVICE_ACCOUNT_JSON")
    if json_path:
        creds = Credentials.from_service_account_file(json_path, scopes=scopes)
    elif os.getenv("GCP_PROJECT_ID"):
        keys = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id",
                "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"]
        info = {key: os.getenv("GCP_" + key.upper()) for key in keys}
        info["private_key"] = (info["private_key"] or "").replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        sys.exit(NO_CREDENTIALS_HELP)
    return gspread.authorize(creds)


def _read_saved_rows(client, config_key):
    """Yield (id, dataset, data_dict) for every saved row in a saved_* spreadsheet."""
    from src.data_loader import DATASET_CONFIGS

    sheet = client.open_by_key(DATASET_CONFIGS[config_key]["spreadsheet_id"]).worksheet("Sheet1")
    for row in sheet.get_all_values()[1:]:
        if len(row) >= 6 and row[0] and row[5]:
            yield row[0], row[4], json.loads(row[5])


def _write(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True, default=_json_default)
        handle.write("\n")


def generate():
    client = _readonly_sheets_client()

    count = 0
    for order_id, dataset, order_data in _read_saved_rows(client, "saved_orders"):
        for key in ORDER_KEYS_TO_STRIP:
            order_data.pop(key, None)
        _write(os.path.join(SNAPSHOT_DIR, "orders", f"{order_id}.json"), {
            "id": order_id, "dataset": dataset, "input": order_data,
            "expected": order_snapshot(order_data),
        })
        count += 1
    print(f"wrote {count} order snapshots")

    count = 0
    for proposal_id, dataset, proposal_data in _read_saved_rows(client, "saved_proposals"):
        _write(os.path.join(SNAPSHOT_DIR, "proposals", f"{proposal_id}.json"), {
            "id": proposal_id, "dataset": dataset, "input": proposal_data,
            "expected": {
                "pricing": proposal_pricing_snapshot(proposal_data),
                "pptx": proposal_pptx_snapshot(proposal_data, dataset or "real"),
            },
        })
        count += 1
        print(f"  {proposal_id} done")
    print(f"wrote {count} proposal snapshots")


if __name__ == "__main__":
    generate()
