"""
Demo mode (PBP_DEMO=1): the whole app runs against an in-memory copy of the
Google Sheets, seeded with sample partners, products, proposals, orders and a
client form submission. Nothing is read from or written to real Sheets or
Drive; edits live until the process stops.

Installed by pbp/web/app.py at import time when settings.DEMO is true.
"""

import json
import re
from datetime import date, datetime, timedelta

from pbp import settings
from pbp.core.forms_config import RESPONSE_COLUMNS
from pbp.sheets import catalog, client_form, gateway, templates

# ----------------------------------------------------------------------------
# A tiny gspread stand-in: just the calls the pbp package makes
# ----------------------------------------------------------------------------


def _col(letters):
    """'A' -> 1, 'Z' -> 26, 'AA' -> 27"""
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - ord("A") + 1)
    return number


def _cell(ref):
    """'C12' -> (row 12, col 3); 'C' -> (None, 3)"""
    match = re.fullmatch(r"([A-Z]+)(\d*)", ref)
    return (int(match.group(2)) if match.group(2) else None), _col(match.group(1))


class DemoWorksheet:
    def __init__(self, rows):
        self.rows = [list(r) for r in rows]

    def _pad(self, row_number, col_number):
        while len(self.rows) < row_number:
            self.rows.append([])
        row = self.rows[row_number - 1]
        if len(row) < col_number:
            row.extend([""] * (col_number - len(row)))
        return row

    def get_all_values(self):
        width = max((len(r) for r in self.rows), default=0)
        return [list(r) + [""] * (width - len(r)) for r in self.rows]

    def get_all_records(self):
        values = self.get_all_values()
        return [dict(zip(values[0], row)) for row in values[1:]] if values else []

    def row_values(self, number):
        return list(self.rows[number - 1]) if number <= len(self.rows) else []

    def append_row(self, row):
        self.rows.append([str(v) if v is not None else "" for v in row])

    def append_rows(self, rows):
        for row in rows:
            self.append_row(row)

    def update_cell(self, row_number, col_number, value):
        self._pad(row_number, col_number)[col_number - 1] = str(value) if value is not None else ""

    def update(self, range_name, values):
        first = range_name.split(":")[0]
        row_number, col_number = _cell(first)
        for r, row_values in enumerate(values):
            for c, value in enumerate(row_values):
                self.update_cell((row_number or 1) + r, col_number + c, value)

    def batch_update(self, updates):
        for item in updates:
            self.update(item["range"], item["values"])

    def batch_get(self, ranges):
        values = self.get_all_values()
        out = []
        for cell_range in ranges:
            start, end = cell_range.split(":")
            _, first = _cell(start)
            _, last = _cell(end)
            out.append([row[first - 1:last] for row in values])
        return out

    def delete_rows(self, index):
        del self.rows[index - 1]


class DemoSpreadsheet:
    def __init__(self, sheets):
        self.sheets = sheets

    def worksheet(self, name):
        if name not in self.sheets:
            import gspread
            raise gspread.exceptions.WorksheetNotFound(name)
        return self.sheets[name]

    def add_worksheet(self, title, rows=100, cols=10):
        self.sheets[title] = DemoWorksheet([])
        return self.sheets[title]


class DemoClient:
    def __init__(self, books):
        self.books = books

    def open_by_key(self, key):
        return self.books[key]

    def open_by_url(self, url):
        return self.books[url.rstrip("/").split("/")[-1]]


# ----------------------------------------------------------------------------
# Sample data
# ----------------------------------------------------------------------------

PRODUCT_COLUMNS = [
    "Partner", "Product/Service", "Marketing Description", "Billing Description (to Client)", "Purchase Description (to Partner)",
    "Country of Origin (Made In)", "Country of Origin (Ships From)", "Pricing Tiers (Y/N)", "Pricing Tiers Info",
    "PBP Cost (No Tiers/Tier 1)", "PBP Cost: Tier 2", "PBP Cost: Tier 3", "Units per Case", "Cost Basis (Per Item/Per Case)",
    "PBP Standard Markup", "Pricing Logic", "Vendor Published MSRP", "Client Price: Customization Setup Fee",
    "Client Price: Customization Cost per Unit", "PBP Cost: Customization Setup Fee", "PBP Cost: Customization Cost per Unit",
    "Customization Info", "MOQ (Partner)", "MOV (Partner)", "MOQ (PBP)", "MOV (PBP)", "Tariff Estimate (%)", "Tariff Estimate ($)",
    "PBP Cost: Shipping Cost per Unit", "Client Price: Shipping Price per Unit", "Has Variants (Y/N)", "Variant Type", "Pricing Notes",
]


def _product(partner, name, made, ships, cost, msrp="", tiers=None, setup="", per_unit="", pbp_setup="", pbp_per_unit="",
             custom_info="", moq="", tariff_pct="", variants="", description=""):
    tiers = tiers or {}
    return {
        "Partner": partner, "Product/Service": name, "Marketing Description": description,
        "Billing Description (to Client)": description, "Purchase Description (to Partner)": name,
        "Country of Origin (Made In)": made, "Country of Origin (Ships From)": ships,
        "Pricing Tiers (Y/N)": "Y" if tiers else "N", "Pricing Tiers Info": tiers.get("info", ""),
        "PBP Cost (No Tiers/Tier 1)": cost, "PBP Cost: Tier 2": tiers.get("t2", ""), "PBP Cost: Tier 3": tiers.get("t3", ""),
        "Units per Case": "1", "Cost Basis (Per Item/Per Case)": "Per Item", "PBP Standard Markup": "2.0",
        "Pricing Logic": "Standard markup", "Vendor Published MSRP": msrp,
        "Client Price: Customization Setup Fee": setup, "Client Price: Customization Cost per Unit": per_unit,
        "PBP Cost: Customization Setup Fee": pbp_setup, "PBP Cost: Customization Cost per Unit": pbp_per_unit,
        "Customization Info": custom_info, "MOQ (Partner)": moq, "MOV (Partner)": "", "MOQ (PBP)": "", "MOV (PBP)": "",
        "Tariff Estimate (%)": tariff_pct, "Tariff Estimate ($)": "", "PBP Cost: Shipping Cost per Unit": "",
        "Client Price: Shipping Price per Unit": "", "Has Variants (Y/N)": "Y" if variants else "N", "Variant Type": variants,
        "Pricing Notes": "",
    }


PRODUCTS = [
    _product("GOEX", "Unisex Fleece Hoodie", "USA", "USA", "$25.00", msrp="$60.00", setup="$65", per_unit="$1.50", pbp_setup="$40", pbp_per_unit="$0.75",
             custom_info="Screen print or embroidery, one location", moq="50", variants="(S, M, L, XL)",
             description="Heavyweight fleece hoodie sewn in Kansas City by GOEX, a fair-wage apparel maker."),
    _product("GOEX", "Short Sleeve Tee", "USA", "USA", "$9.50", msrp="$24.00", setup="$50", per_unit="$1.00", pbp_setup="$30", pbp_per_unit="$0.50",
             custom_info="Screen print, one color", moq="48", variants="(S, M, L, XL, 2XL)", description="Soft 100% cotton tee, fair-wage made."),
    _product("1951 Coffee", "1951 Coffee", "USA", "USA", "$12.00", msrp="$22.00", setup="$75", per_unit="$2.00",
             custom_info="Custom label", moq="24", description="12 oz bag of specialty coffee roasted by refugee baristas in Berkeley."),
    _product("Bee Co", "9 oz Hot Honey", "USA", "USA", "$10.00", tiers={"info": "T1: 1-99, T2: 100-499, T3: 500+", "t2": "$9.00", "t3": "$8.00"},
             setup="$40", per_unit="$0.75", custom_info="Custom neck label", description="Chili-infused raw honey from a women-owned apiary."),
    _product("Amani Ya Juu", "Kitenge Tote Bag", "Kenya", "Kenya", "$14.00", msrp="$36.00", setup="$55", per_unit="$1.25", pbp_setup="$35", pbp_per_unit="$0.60",
             custom_info="Embroidered logo", moq="30", tariff_pct="10", description="Hand-sewn tote from upcycled kitenge fabric, made by refugee women in Nairobi."),
    _product("Amani Ya Juu", "Beaded Keychain", "Kenya", "Kenya", "$4.00", msrp="$10.00", tariff_pct="10",
             description="Hand-beaded keychain, a small gift with a big story."),
]

PARTNER_INFO = [
    {"Partner": "GOEX", "POC Name": "Pat Rivera", "POC Email": "pat@goex.org", "POC Phone": "(816) 555-0101"},
    {"Partner": "1951 Coffee", "POC Name": "Dana Lee", "POC Email": "orders@1951coffee.com", "POC Phone": "(510) 555-0199"},
    {"Partner": "Bee Co", "POC Name": "Sam Ortiz", "POC Email": "sam@beeco.com", "POC Phone": "(206) 555-0142"},
    {"Partner": "Amani Ya Juu", "POC Name": "Grace Wanjiru", "POC Email": "grace@amaniafrica.org", "POC Phone": "+254 700 555 013"},
]


def _pricing_book():
    header_row = 6  # header at row 7, data from row 8 (the real sheet's layout)
    data = [[""] * len(PRODUCT_COLUMNS) for _ in range(header_row)] + [PRODUCT_COLUMNS] + \
           [[p.get(col, "") for col in PRODUCT_COLUMNS] for p in PRODUCTS]
    metadata = [["Metadata"], ["Field", "Description"], ["Partner", "Maker organisation"]]
    partners = [["Partner-Specific Info"], ["Partner", "POC Name", "POC Email", "POC Phone"]] + \
               [[p["Partner"], p["POC Name"], p["POC Email"], p["POC Phone"]] for p in PARTNER_INFO]
    return DemoSpreadsheet({"Data": DemoWorksheet(data), "Metadata": DemoWorksheet(metadata), "Partner-Specific Info": DemoWorksheet(partners)})


def _proposals_book():
    from pbp.services import proposal as svc
    rows = [["Proposal_ID", "Proposal_Name", "Created_By", "Created_Date", "Dataset", "Proposal_Data_JSON"]]
    seeds = [
        ("PROP_20260915_101500", "Riverbend Health - Holiday Gifts", "Nico", "2026-09-15 10:15:00", PRODUCTS[0:1] + PRODUCTS[2:3] + PRODUCTS[4:5], "Non-profit (5%)"),
        ("PROP_20260928_143000", "Northwind Partners - Welcome Kits", "Alex", "2026-09-28 14:30:00", PRODUCTS[1:2] + PRODUCTS[3:4], "None"),
        ("PROP_20261006_091200", "Summit Advisors - Client Appreciation", "Nico", "2026-10-06 09:12:00", PRODUCTS[2:4] + PRODUCTS[5:6], "Volume Order (5%)"),
    ]
    for pid, name, by, when, products, discount in seeds:
        proposal = svc.new_proposal()
        svc.set_discount_option(proposal, discount)
        svc.add_products(proposal, products)
        rows.append([pid, name, by, when, "real", json.dumps(svc.saved_payload(proposal), default=str)])
    return DemoSpreadsheet({"Sheet1": DemoWorksheet(rows)})


def _orders_book():
    from pbp.services import order as svc
    rows = [["Order_ID", "Order_Name", "Created_By", "Created_Date", "Dataset", "Order_Data_JSON"]]
    seeds = [
        ("ORDER_20260920_160000", "Riverbend Health - 120 hoodies", "Nico", "2026-09-20 16:00:00",
         [(PRODUCTS[0], 120, True), (PRODUCTS[2], 120, False)],
         {"company_name": "Riverbend Health", "contact": ("Maria Chen", "maria.chen@riverbendhealth.org", "(312) 555-0147"),
          "billing_address": "400 Lakeshore Dr\nChicago, IL 60611", "shipping_address": "400 Lakeshore Dr\nChicago, IL 60611",
          "client_po": "RH-2026-0912", "payment_timeline": "Net 30", "payment_preference": "ACH", "in_hands": 45,
          "order_submitted_by": "Nico", "cost_submitted_by": "Alex", "notes": {"external_partners": "Please ship in two cartons, labelled by size."}}, True),
        ("ORDER_20261003_113000", "Northwind Partners - welcome kits", "Alex", "2026-10-03 11:30:00",
         [(PRODUCTS[1], 60, True), (PRODUCTS[3], 60, False), (PRODUCTS[5], 60, False)],
         {"company_name": "Northwind Partners", "contact": ("Jordan Blake", "jblake@northwind.co", "(503) 555-0188"),
          "billing_address": "1200 SW Morrison St, Portland, OR 97205", "shipping_address": "", "client_po": "",
          "payment_timeline": "Net 15", "payment_preference": "Credit Card", "in_hands": 30, "order_submitted_by": "Alex",
          "cost_submitted_by": "", "notes": {"internal_pbp_team": "Drop ship to 60 remote employees; address file in the client form response."}}, False),
    ]
    for oid, name, by, when, lines, info, confirmed in seeds:
        order = svc.new_order()
        items = []
        for product, qty, custom in lines:
            item = svc.catalog_item(product, quantity=qty)
            if custom:
                item.update(include_customization=True, customization_description=product["Customization Info"],
                            partner_customization_setup_fee=float(str(product["PBP Cost: Customization Setup Fee"]).replace("$", "") or 0),
                            partner_customization_per_unit=float(str(product["PBP Cost: Customization Cost per Unit"]).replace("$", "") or 0))
                svc.recalculate(item)
            items.append(item)
        svc.add_items(order, items)
        client = order["client_info"]
        name_, email, phone = info["contact"]
        client.update(company_name=info["company_name"], contacts=[{"name": name_, "email": email, "phone": phone, "role": "Primary Contact"}],
                      billing_address=info["billing_address"], shipping_address=info["shipping_address"],
                      shipping_type="One Location" if info["shipping_address"] else "Drop Shipping", client_po=info["client_po"],
                      payment_timeline=info["payment_timeline"], payment_preference=info["payment_preference"],
                      client_in_hands_date=date.today() + timedelta(days=info["in_hands"]), pbp_in_hands_date=date.today() + timedelta(days=info["in_hands"] - 10),
                      order_submitted_by=info["order_submitted_by"], cost_submitted_by=info["cost_submitted_by"], order_submitted_date=date.fromisoformat(when[:10]))
        order["order_notes"].update(info["notes"])
        order["order_confirmed"] = confirmed
        if info["payment_preference"] == "Credit Card":
            order["apply_cc_fee"] = True
        rows.append([oid, name, by, when, "real", json.dumps(svc.saved_payload(order), default=str)])

    submission = {
        "client_info": {"client_type": "New", "company_name": "Northwind Partners", "contact_name": "Jordan Blake", "contact_email": "jblake@northwind.co", "contact_phone": "(503) 555-0188"},
        "products": [{"name": "Short Sleeve Tee", "quantity": 60, "customization_notes": "Navy with white Northwind logo, left chest"},
                     {"name": "9 oz Hot Honey", "quantity": 60, "customization_notes": ""}],
        "shipping_info": {"shipping_address": "1200 SW Morrison St, Portland, OR 97205", "billing_address": "", "drop_shipping": "Yes",
                          "drop_shipping_instructions": "One kit per remote employee; addresses in the attached file.", "in_hands_date": (date.today() + timedelta(days=30)).isoformat()},
        "payment_info": {"impact_cards": "Yes", "impact_card_selection": "", "payment_preference": "Net 15", "payment_method": "Credit Card"},
        "notes": "Please include a handwritten welcome note if possible.", "submitted_at": "10/02/2026 09:41:12",
    }
    drafts = [["Proposal_ID", "Session_ID", "Draft_Data_JSON", "File_Data_Base64", "File_Name", "Created_Date", "Updated_Date", "Status"],
              ["PROP_20260928_143000", "demo12345678", json.dumps(submission), "", "northwind_addresses.csv", "2026-10-01 17:20:00", "2026-10-02 09:41:12", "submitted"],
              ["PROP_20260915_101500", "demoabcdefgh", json.dumps({"client_info": {"client_type": "Existing", "company_name": "Riverbend Health", "contact_name": "Maria Chen", "contact_email": "maria.chen@riverbendhealth.org", "contact_phone": ""}}), "", "", "2026-10-10 08:00:00", "2026-10-10 08:00:00", "draft"]]
    photos = [["Photo_ID", "Order_ID", "Product_Name", "Photo_Index", "Filename", "Chunk_Index", "Base64_Chunk"]]
    return DemoSpreadsheet({"Sheet1": DemoWorksheet(rows), "client_form_drafts": DemoWorksheet(drafts), "Photos": DemoWorksheet(photos)}), submission


def _responses_book(submission):
    headers = list(RESPONSE_COLUMNS.values())
    row = {h: "" for h in headers}
    client, ship, pay = submission["client_info"], submission["shipping_info"], submission["payment_info"]
    row.update({
        RESPONSE_COLUMNS["timestamp"]: submission["submitted_at"], RESPONSE_COLUMNS["client_type"]: client["client_type"],
        RESPONSE_COLUMNS["company_name"]: client["company_name"], RESPONSE_COLUMNS["contact_name"]: client["contact_name"],
        RESPONSE_COLUMNS["contact_email"]: client["contact_email"], RESPONSE_COLUMNS["contact_phone"]: client["contact_phone"],
        RESPONSE_COLUMNS["shipping_address"]: ship["shipping_address"], RESPONSE_COLUMNS["drop_shipping"]: ship["drop_shipping"],
        RESPONSE_COLUMNS["drop_shipping_instructions"]: ship["drop_shipping_instructions"], RESPONSE_COLUMNS["in_hands_date"]: ship["in_hands_date"],
        RESPONSE_COLUMNS["impact_cards"]: pay["impact_cards"], RESPONSE_COLUMNS["payment_preference"]: pay["payment_preference"],
        RESPONSE_COLUMNS["payment_method"]: pay["payment_method"], RESPONSE_COLUMNS["special_requests"]: submission["notes"],
        RESPONSE_COLUMNS["dropshipping_file"]: "northwind_addresses.csv",
    })
    for i, product in enumerate(submission["products"], start=1):
        row[RESPONSE_COLUMNS[f"line_{i}_name"]] = product["name"]
        row[RESPONSE_COLUMNS[f"line_{i}_qty"]] = str(product["quantity"])
        row[RESPONSE_COLUMNS[f"line_{i}_notes"]] = product["customization_notes"]
    older = dict(row, **{RESPONSE_COLUMNS["timestamp"]: "09/18/2026 14:05:33", RESPONSE_COLUMNS["company_name"]: "Riverbend Health",
                         RESPONSE_COLUMNS["contact_name"]: "Maria Chen", RESPONSE_COLUMNS["contact_email"]: "maria.chen@riverbendhealth.org",
                         RESPONSE_COLUMNS["contact_phone"]: "(312) 555-0147", RESPONSE_COLUMNS["drop_shipping"]: "No",
                         RESPONSE_COLUMNS["drop_shipping_instructions"]: "", RESPONSE_COLUMNS["dropshipping_file"]: "",
                         RESPONSE_COLUMNS["line_1_name"]: "Unisex Fleece Hoodie", RESPONSE_COLUMNS["line_1_qty"]: "120",
                         RESPONSE_COLUMNS["line_1_notes"]: "Charcoal, embroidered logo", RESPONSE_COLUMNS["line_2_name"]: "1951 Coffee",
                         RESPONSE_COLUMNS["line_2_qty"]: "120", RESPONSE_COLUMNS["line_2_notes"]: "", RESPONSE_COLUMNS["special_requests"]: "",
                         RESPONSE_COLUMNS["imported"]: "TRUE", RESPONSE_COLUMNS["order_id"]: "IMPORTED-20260920-160000",
                         RESPONSE_COLUMNS["imported_by"]: "Nico", RESPONSE_COLUMNS["import_date"]: "2026-09-20 16:00:00"})
    return DemoSpreadsheet({settings.FORM_RESPONSES_SHEET_NAME: DemoWorksheet([headers, [row[h] for h in headers], [older[h] for h in headers]])})


def build_client():
    """A DemoClient holding every spreadsheet the app knows about."""
    orders_book, submission = _orders_book()
    impact = [["Partner", "Slide Title"], ["GOEX", "Apparel - Your Impact"], ["1951 Coffee", "Coffee - Your Impact"],
              ["Amani Ya Juu", "Bags - Your Impact"], ["Bee Co", "Honey Products - Your Impact"]]
    books = {
        catalog.DATASETS["real"]["spreadsheet_id"]: _pricing_book(),
        catalog.DATASETS["demo"]["spreadsheet_id"]: _pricing_book(),
        settings.SAVED_PROPOSALS_SHEET_ID: _proposals_book(),
        settings.SAVED_ORDERS_SHEET_ID: orders_book,
        settings.FORM_RESPONSES_SHEET_ID: _responses_book(submission),
        settings.SAVED_MATCHES_SHEET_ID: DemoSpreadsheet({"Sheet1": DemoWorksheet([["Match_ID", "Product_Name", "Original_Product_Name", "Slide_Index", "Slide_Title", "Dataset", "Match_Type", "Confidence", "Created_Date", "Template_Name"]])}),
        settings.IMPACT_SLIDE_MAPPING_SHEET_ID: DemoSpreadsheet({"Sheet1": DemoWorksheet(impact)}),
    }
    return DemoClient(books)


DEMO_TEMPLATE = {"name": "November All Slides.pptx (bundled demo copy)", "file_id": "demo-bundled", "modified_time": ""}


def install():
    """Point the gateway and Drive helpers at the in-memory demo data."""
    client = build_client()
    gateway.connect = lambda: client
    gateway.reset()
    templates.list_templates = lambda force=False: [DEMO_TEMPLATE]
    templates.template_path = lambda template: settings.REPO_ROOT / "templates" / "November All Slides.pptx"
    client_form.notify_team_of_order = lambda proposal_id, form_data: None  # demo orders never email the team
    print(f"PBP demo mode: in-memory sample data, {len(PRODUCTS)} products, no Google Sheets or Drive access. Login password: {settings.APP_PASSWORD}")
