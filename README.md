# Peace by Piece International - Order Management System

A Python/Streamlit application for creating proposals, managing orders, and generating invoices for artisan products.

**Status:** IN PRODUCTION - https://pbp-order-management-system.onrender.com
**Version:** 8.4.0
**Last Updated:** 2026-05-27

---

## What's New (v8.4.0 - May 2026)

**Client Order Form as Shareable Link:**
- Standalone form page accessible via direct URL -- no app password or Google account needed
- New `src/client_form.py` module (session tokens, proposal loading, draft save/load, form submission)
- Query-param routing (`?client_form=<id>`) renders form instead of main app
- Password gate for main app; client form links bypass the gate
- Generate Client Form Link section in Tab 2

**v8.3.0 (May 2026):** 16 bug fixes and feature requests from leadership meeting. See [docs/CHANGES_2026_05_23.md](docs/CHANGES_2026_05_23.md).

**v8.0.0-8.2.0 (Jan-Apr 2026):** Major schema transition (33 to 45 columns), 4 pricing methods, per-product kitting, Google Forms integration, template-resilient PowerPoint generation. See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
- Credentials stored in `.streamlit/secrets.toml`
- Never commit this file (protected by `.gitignore`)

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Test Connection (Optional)
```bash
streamlit run scripts/test_connection.py
```

---

## Architecture

- **Frontend:** Streamlit (Python) with 4-tab structure + standalone client form page
- **Data Source:** Google Sheets (Demo and Real datasets, switchable in sidebar)
- **Authentication:** Google Cloud service account + password gate for main app
- **Codebase:** ~19,500 lines of Python (app.py + 14 src/ modules)

### Recommended Workflow
1. **Tab 1 (Proposal Generator):** Browse & filter products, configure proposal, generate PowerPoint
2. **Tab 2 (Client Order Form):** Generate shareable Client Form Link, send to client
3. **Client completes form:** Standalone in-app form (no login required), saves to Google Sheets
4. **Tab 3 (Order & Client Info):** Import form response, configure order details
5. **Tab 4 (Execution & Accounting):** Review order, generate invoice & PO, download exports

---

## Features

### Tab 1: Proposal Generator
- Product catalog with filtering (price range, partner, country)
- Bulk actions: add all products from selected partners
- MSRP pricing (auto-calculated markup to match vendor MSRP)
- Saved proposals (cloud-persistent via Google Sheets)
- MOQ-based pricing tables
- PowerPoint generation with automated slide matching

### Tab 2: Client Order Form Generator
- **Client Form Link (Recommended):** Shareable URL to standalone form page, no login needed
- **Google Form (Legacy):** Pre-filled Google Form URL generation
- **HTML Form (Legacy):** Professional HTML order forms with template customization

### Tab 3: Order & Client Info
- 4 entry points: Client Form import, HTML import, Proposal import, Manual selection
- Per-product markup, customization, kitting
- Tiered and flat-rate pricing
- Discount options (Non-profit 5%, Volume Order 5%, custom)
- Per-product photo uploads with cross-session persistence
- Detailed order summary with line-item breakdown

### Tab 4: Execution & Accounting
- 4-table Invoice/PO format (bookkeeper-standardized)
- Editable order information with validation
- Dual export: CSV (bookkeeper) and HTML (client-facing)
- Per-product photo display and download

### Pricing System (v8.1.0 Schema, 45 columns)
4 pricing methods:
1. **"MSRP + % of cost"** -- Vendor MSRP plus shipping recovery
2. **"MSRP capped -- ship absorbed"** -- Vendor MSRP exactly
3. **"Standard markup"** -- Traditional cost x markup
4. **"MSRP + Other Add-On %"** -- MSRP plus add-on percentage of cost

---

## Project Structure

```
pricing-data-solution-pbp/
├── app.py                      # Main application (~11,100 lines)
├── start.sh                    # Render deployment startup script
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Project rules & AI context
│
├── pbp/                        # Shared core package (Streamlit app + future web app)
│   ├── core/                  # helpers, pricing_engine, slide_matcher, pptx_generator,
│   │                          # match_manager, forms_config, forms_helper
│   └── sheets/                # drive_helper (photo storage via Google Sheets)
│
├── src/                        # Streamlit-coupled modules
│   ├── data_loader.py         # Google Sheets data loading
│   ├── client_form.py         # Client order form page (v8.4.0)
│   ├── template_loader.py     # Cloud-based template loading
│   ├── match_memory.py        # Confirmed match storage (Google Sheets)
│   ├── proposal_manager.py    # Save/load/delete proposals
│   └── order_manager.py       # Save/load/delete orders
│
├── tests/                      # Unit tests + golden parity tests (tests/golden/)
│
├── docs/                       # Documentation (organized by topic)
│   ├── planning/              # Requirements, pricing logic, data structure
│   ├── powerpoint/            # PowerPoint automation (Phase 1 & 2)
│   ├── meetings/              # Stakeholder meeting notes
│   ├── testing/               # Test plans and checklists
│   └── archive/               # Historical documentation
│
├── scripts/                    # Utility scripts (55+ files)
│   ├── core/                  # Essential: test_connection.py, investigate_data.py
│   ├── features/              # Feature-specific tests (43 files)
│   └── investigations/        # Technical debugging (16 files)
│
├── templates/                  # PowerPoint template, invoice reference
└── backups/                    # Pre-modular structure reference
```

---

## Data Source

**Datasets:** Switchable between Demo and Real data (sidebar selector)
- **Demo:** `master_pricing_template_10_14` (19 products, 4 partners)
- **Real:** `master_pricing` (302 products, 33 partners as of 2026-10-13)

**Schema:** v8.1.0, 45 columns. See [schema_reference.md](schema_reference.md) for complete definition.

**Structure:** 3-sheet Google Sheets workbook
- **Data** (header at row 6): Partner-product pricing data
- **Metadata** (header at row 2): Deliverable field definitions
- **Partner-Specific Info** (header at row 2): Partner configuration reference

---

## New web app (Streamlit migration, in progress)

The app is being rebuilt as a FastAPI + HTMX service in `pbp/web/`. It reads and writes the
same Google Sheets as the Streamlit app, so work moves freely between the two. Done so far:
the client order form (phase 1), the staff order editor plus invoice/PO accounting screens,
i.e. Tabs 3 and 4 (phase 2), and the proposal generator with PowerPoint match review and
generation plus the client form link, i.e. Tabs 1 and 2 (phase 3), and the Executive Pricing
Tool plus Reset session (phase 4). The legacy Google Form and HTML order form paths are not
ported (deprecated; the client form link replaces them). Staff log in at `/login` with the same
`APP_PASSWORD`.

Run it locally (needs Google credentials: `.streamlit/secrets.toml`, or the `GCP_*`
variables, or `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`):

```bash
pip install -r requirements.txt
uvicorn pbp.web.app:app --reload --port 8000
# staff:  http://localhost:8000/proposals/current and /orders   (log in with APP_PASSWORD)
# client form link from Tab 2 with the host swapped, e.g.
#   http://localhost:8000/?client_form=PROP_20260524_143022&session=abc123def456
# health: http://localhost:8000/internal/health
```

Set `APP_PASSWORD` for the staff login (without it the legacy local fallback applies). The
working order lives in server memory per browser session until you save it to the
saved_orders sheet, exactly like the Streamlit app. PowerPoint templates are downloaded from
Drive once per process into `PBP_TEMPLATE_CACHE_DIR` (default `/tmp/pbp-templates`).

To make Tab 2 generate links that point at the new app, run the Streamlit app with
`CLIENT_FORM_BASE_URL=http://localhost:8000/` (on Render this is the cutover switch).

Optional overrides so a local run never touches production tabs: `PBP_SAVED_ORDERS_SHEET_ID`
(drafts/backup tab lives here), `PBP_FORM_RESPONSES_SHEET_ID`, `PBP_SAVED_PROPOSALS_SHEET_ID`.
`PBP_SYNC_LOOP_SECONDS=0` disables the background Form Responses sync loop.

Tests: `python -m pytest tests -q` (all Google Sheets access is faked).

## Deployment

**Live URL:** https://pbp-order-management-system.onrender.com

- **Platform:** Render Standard tier (2GB RAM, $25/month)
- **Auto-deploy:** Connected to GitHub (deploys on push to main)
- **Environment:** GCP credentials set in Render dashboard
- **PowerPoint template:** 43MB file stored in Google Drive, downloaded on-demand

**Local Development:**
1. Clone repository
2. `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with GCP credentials
4. `streamlit run app.py`

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Project rules & development guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Complete version history (v6.0 through v8.4.0) |
| [ACTIVE_DEVELOPMENT_TODO.md](ACTIVE_DEVELOPMENT_TODO.md) | Current task list and priorities |
| [schema_reference.md](schema_reference.md) | 45-column schema definition (v8.1.0) |
| [docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md) | Pricing calculations & business rules |
| [docs/planning/PLANNING.md](docs/planning/PLANNING.md) | Project requirements & goals |
| [docs/planning/INVOICE_AND_PROPOSAL_SPEC.md](docs/planning/INVOICE_AND_PROPOSAL_SPEC.md) | Invoice/PO format specs |
| [SCHEMA_UPDATE_PROCESS.md](SCHEMA_UPDATE_PROCESS.md) | Process for updating data model |

---

## Development Guidelines

See [CLAUDE.md](CLAUDE.md) for complete rules:
- Always use Python & Streamlit
- Write beginner-friendly code
- Take the simplest route
- Minimize codebase size, avoid duplication
- No emojis in the app
- Commit prefixes: `FEAT:`, `FIX:`, `TEST:`, `DOC:`

---

Peace by Piece International - Internal Tool
