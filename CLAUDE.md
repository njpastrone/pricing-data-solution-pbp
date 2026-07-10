# CLAUDE.md

## 🚨 NON-NEGOTIABLE PROJECT RULES - READ FIRST 🚨

**These rules MUST be followed for ALL work on this project:**

1. **Always use Python for all development**
2. **Leverage Streamlit for the front-end**
3. **Write beginner-friendly code** - code must be readable and understandable by a beginner Python programmer
4. **Always take the simplest route to solving problems**
5. **The entire app should be "vibe-coder friendly"** - prioritize clarity over cleverness
6. **Make autonomous decisions** - avoid asking for user permissions unless making dangerous changes
7. **Minimize the size of the code base** - keep the project simple with fewer files when possible
8. **Avoid duplicating code**
9. **Refer to markdown files for context consistently**
10. **Do not be afraid to ask the user for questions or clarifications**
11. **NEVER use emojis in the app** - emojis make everything look AI-generated and unprofessional
12. **REMEMBER THAT IT IS 2026, NOT 2025**

---

## ACTIVE DEVELOPMENT STATUS - July 2026

**Current Focus:** Normal development - team-reported bug fixes
- **Last Major Update:** 2026-07-10 - Password gate first-click login and browser persistence (v8.5.2)
- **Current Version:** 8.5.2
- **Status:** Production-ready with 4-method pricing system (v8.1.0 schema, 45 columns)
- **Codebase:** ~19,500 lines of Python, clean and documented

**Recent Work (July 2026):**
- **Team Bug Fixes and Partner Shipping Field (v8.5.1):**
  - Per-partner "Shipping Instructions to PbP" field in Tab 4, printed on invoice/PO
  - Tab 3 to Tab 4 carry-over fixed (Tab 4 editors seed from client_info; removed contact clobber)
  - Stray $0.03 line-total fixed (full-precision markup conversion)
  - Save "always v2 / can't overwrite" fixed for orders and proposals (in-place Overwrite checkbox)
  - Proposal load no longer forces "Manual override" (clears stale per-row widget state)
  - Data note: blank Vendor MSRP with "MSRP + % of cost" logic falls back to 2x markup (spreadsheet fix, not code)
- **7 Team-Reported Bug Fixes (v8.5.0):** Rounded pricing in Order Summary, editable partner contacts, cost basis display, shipping type vs ship method separation, removed Cost Verified column, local password gate fix
- **Client Order Form as Shareable Link (v8.4.0):** New standalone form page accessible via direct URL
  - New `src/client_form.py` module (session tokens, proposal loading, draft save/load, form submission)
  - Query-param routing (`?client_form=<proposal_id>`) renders form instead of main app
  - Password gate for main app — clients bypass gate when accessing forms via link
  - Redesigned form UX with improved layout and usability
  - Dropshipping file download support in Tab 3 response preview
  - Generate Client Form Link section in Tab 2
  - Design spec: [docs/superpowers/specs/2026-05-24-client-order-form-design.md](docs/superpowers/specs/2026-05-24-client-order-form-design.md)
- Bug fixes: single-date picker for In-Hands Date, removed Impact Card Selection box, password gate width fix, query param routing across Streamlit versions
- v8.3.0: 16 bug fixes and feature requests from leadership meeting (see [docs/CHANGES_2026_05_23.md](docs/CHANGES_2026_05_23.md))
- See [CHANGELOG.md](CHANGELOG.md) for complete details

**Previous Work (Jan-Apr 2026):**
- Template-resilient PowerPoint generation (handles missing/changed slides gracefully)
- Volume Order Discount (5%) option in Tab 1 and Tab 3
- MOQ warnings for orders below minimum quantity
- Custom variant support and "Inquire about variants" handling
- Google Form generation without requiring a proposal first
- Per-product kitting as separate line items (Tab 3 and Tab 4)
- Tier parsing robustness (handles space-separated and multi-colon formats)
- Schema v8.1.0: Added "Other Add-On %" column, "Package" -> "Case" terminology

### Active Development Documents:
1. **[ACTIVE_DEVELOPMENT_TODO.md](ACTIVE_DEVELOPMENT_TODO.md)** - Current task list
2. **[CHANGELOG.md](CHANGELOG.md)** - Comprehensive project history (v8.4.0 is latest)
3. **[schema_update_jan_2026/MASTER_TRACKING.md](schema_update_jan_2026/MASTER_TRACKING.md)** - Schema transition reference (complete)
4. **[schema_reference.md](schema_reference.md)** - Complete 45-column schema definition (v8.1.0)
5. **[docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md)** - Pricing methodology (updated with 4 methods)

### Development Workflow:
1. Start with ACTIVE_DEVELOPMENT_TODO.md for current tasks
2. Reference CHANGELOG.md for recent changes and version history
3. Use clear git commit prefixes: `FIX:`, `FEAT:`, `TEST:`, `DOC:`
4. Update documentation when adding features

### Quick Context Recovery:
**For normal development:**
1. Start with ACTIVE_DEVELOPMENT_TODO.md (current priorities)
2. Check CHANGELOG.md for recent changes
3. Read relevant code sections

**For schema/pricing questions:**
1. See [schema_update_jan_2026/MASTER_TRACKING.md](schema_update_jan_2026/MASTER_TRACKING.md) for complete transition context
2. See [docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md) for pricing logic details
3. See [schema_reference.md](schema_reference.md) for 45-column schema definition (v8.1.0)

---

## Important References

**Documentation is organized by topic. See [docs/README.md](docs/README.md) for complete index.**

**Core references (use before starting any work):**

- **[SCHEMA_UPDATE_PROCESS.md](SCHEMA_UPDATE_PROCESS.md)** - Systematic process for updating data model/schema
- **[docs/planning/PLANNING.md](docs/planning/PLANNING.md)** - Project requirements, architecture decisions, and implementation plans
- **[docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md)** - Pricing calculations, business rules, and partner-specific methodologies
- **[docs/planning/RESTRUCTURE_CONTEXT.md](docs/planning/RESTRUCTURE_CONTEXT.md)** - Current data structure from master_pricing_template_10_14
- **[docs/planning/INVOICE_AND_PROPOSAL_SPEC.md](docs/planning/INVOICE_AND_PROPOSAL_SPEC.md)** - Invoice format specifications and required information

**PowerPoint automation (latest feature):**

- **[SLIDE_MATCHING_NOTES.md](SLIDE_MATCHING_NOTES.md)** - Partner-specific notes on product-to-slide matching (active work)
- **[docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md](docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md)** - Phase 2 complete summary (production-ready)
- **[docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md](docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md)** - Phase 1 technical deep dive

---

## Project Overview

This is the pricing-data-solution-pbp project - a Python/Streamlit application focused on simplicity and beginner-friendly code.

## Development Guidelines

- Follow existing code patterns and conventions in the repository
- Ensure all changes are well-tested before committing
- Keep commits focused and atomic

## Schema Update Guidelines

**✅ MAJOR SCHEMA TRANSITION COMPLETE (January 2026 - v8.0.0)**

The schema transition is complete. For reference on the completed transition:
- **[schema_update_jan_2026/MASTER_TRACKING.md](schema_update_jan_2026/MASTER_TRACKING.md)** - Complete transition tracking and context
- **[schema_reference.md](schema_reference.md)** - Current 45-column schema definition (v8.1.0)
- **[CHANGELOG.md](CHANGELOG.md)** - Full release notes (v8.0.0 through v8.2.0)

When updating the data model/schema (renaming columns, adding fields, modifying data structure):

1. **ALWAYS follow the systematic process in [SCHEMA_UPDATE_PROCESS.md](SCHEMA_UPDATE_PROCESS.md)**
2. **ALWAYS update [docs/SCHEMA_TRANSITION_JAN2026.md](docs/SCHEMA_TRANSITION_JAN2026.md)** with progress
3. **Key principle:** Maintain backward compatibility via `get_column_value()` helper
4. **Required steps:**
   - Review core documentation for context
   - Search for ALL references to changed columns
   - Update `get_column_value()` mappings first
   - Update schema_reference.md
   - Test with both old and new spreadsheet formats
   - Document in CHANGELOG.md
   - Update SCHEMA_TRANSITION_JAN2026.md checklist

**Quick reference for column changes:**
- Rename: Add new canonical name to `get_column_value()`, keep old name as fallback
- Add: Include default value handling for spreadsheets without the column
- Remove: Keep in fallback list for old data, mark deprecated in docs
- Type change: Add parsing/conversion logic with format detection

See SCHEMA_UPDATE_PROCESS.md for complete walkthrough and examples.

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Sheets credentials:**
   - Credentials are stored in `.streamlit/secrets.toml`
   - Never commit this file to git (protected by .gitignore)

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Test connection:**
   ```bash
   streamlit run scripts/test_connection.py
   ```

## Architecture

- **Frontend:** Streamlit (Python-based web app) with 4-tab structure + standalone client form page
  - **Client Form Page** - Standalone form accessed via shareable link (`?client_form=<id>`), bypasses password gate
  - **Tab 1: Proposal Generator** - Product catalog, filtering, proposal generation (tables & PowerPoint)
  - **Tab 2: Client Order Form Generator** - Generate shareable client form links and legacy HTML forms
  - **Tab 3: Order & Client Info** - Order management, client data collection
  - **Tab 4: Execution & Accounting** - Invoice/PO generation, bookkeeping
- **Password Gate:** Main app requires password; client form links bypass the gate
- **Data Source:** Google Sheets with dataset selector (Demo or Real)
  - **Demo Dataset:** master_pricing_template_10_14 (19 products, 4 partners - testing/development data)
  - **Real Dataset:** master_pricing (133 products, 4 partners - production data READY)
  - **Required sheet structure:**
    - **Data**: Partner-product pricing data (header at row 6)
      - **Updated Schema (Jan 2026):** Now supports new canonical column names with backward compatibility
      - Core columns: Partner, Product/Service, MOQ, Pricing Tiers (Y/N), PBP Cost (No Tiers), PBP Cost: Tier 1-6
      - **Units per Case** (renamed from Units per Package): Normalizes case pricing to per-unit (default: 1)
      - **PBP Standard Markup** (new): Default markup multiplier (e.g., 2.0 = 100% markup)
      - **Vendor Published MSRP** (renamed from MSRP)
      - **Client Price: Customization Setup Fee** (renamed from Customization Setup Fee)
      - **Client Price: Customization Cost per Unit** (renamed from Customization Cost per Unit)
      - **PBP Cost: Shipping Cost per Unit** and **Client Price: Shipping Price per Unit** (renamed)
      - **Tariff Estimate ($)** and **Tariff Estimate (%)** (dual format support)
      - See [schema_reference.md](schema_reference.md) for complete details
    - **Metadata**: Deliverable field definitions (header at row 2)
    - **Partner-Specific Info**: Partner configuration reference (header at row 2)
- **Code Structure:** Modular with helper functions in `src/` directory
  - `src/data_loader.py` - Google Sheets data loading and caching
  - `src/helpers.py` - Utility functions, conversions, validation, HTML parsing
  - `src/pricing_engine.py` - Pricing calculations and quote generation
  - `src/client_form.py` - Client order form page (session tokens, proposal loading, draft save/load, submission)
- **Authentication:** Google Cloud service account + password gate for main app
- **Pricing Model:** Flexible tiered or flat-rate pricing per product
- **Recommended Workflow (Client Form Link):**
  1. **Tab 1 (Proposal Generator):** Browse & filter products → Configure proposal → Generate PowerPoint
  2. **Tab 2 (Client Order Form Generator):** Enter client info → Generate Client Form Link → Send link to client
  3. **Client completes form:** Standalone in-app form (no login required) → Saves to Google Sheets
  4. **Tab 3 (Order & Client Info):** Load & import form response → All data auto-populates → Configure order details
  5. **Tab 4 (Execution & Accounting):** Review/edit order → Generate invoice & PO → Download for bookkeeping
- **Alternative Workflows:**
  - **Google Form:** Tab 2 → Generate Google Form URL → Client completes → Tab 3 → Import response
  - **HTML Form:** Tab 2 → Generate HTML form → Client completes → Tab 3 → Import HTML file
  - **Proposal Direct:** Tab 1 → Create proposal → Tab 3 → Import from proposal (Option B)
  - **Manual Entry:** Tab 3 → Add products manually (Option C)

## Current Features

### Tab 1: Proposal Generator (for prospective clients)
- **Browse & Filter Products (Section 1):**
  - Collapsible product catalog (auto-collapses after adding products)
  - Filter by price range, partner, country of origin
  - View product details inline (country, tiered pricing, MOQ estimates, descriptions)
  - **Bulk Actions:** Add all products from one or more partners at once
    - **Quick Add All Products (Testing):** Add all filtered products with one click
    - Select multiple partners and add all their products with one click
    - Smart duplicate detection (skips products already in proposal)
    - Preview count before adding (shows new vs duplicate products)
    - Respects all active filters (price, partner, country)
    - Useful for quickly testing with complete product catalog
- **Proposal Configuration (Section 2):**
  - **Saved Proposals:** Save and load proposals across sessions
    - Name proposals for easy identification
    - Optional creator name tracking
    - Load previously saved proposals with all settings
    - Delete unwanted proposals
    - Dataset mismatch warnings when loading
    - Duplicate name detection with versioning (v2, v3, etc.)
    - Stored in Google Sheets (cloud-persistent)
  - **Use MSRP Pricing (Checkbox - Default: ON):** Automatically calculates markup to match MSRP
    - When enabled: Products added with MSRP will have markup auto-calculated to match MSRP
    - When disabled: All products use 100% markup (standard 2x pricing)
    - Applies to both individual and bulk product adds
    - Products without MSRP always use 100% markup
    - Handles edge cases: MSRP below cost set to 0% (break-even)
    - Markup still manually editable after products are added
  - Editable markup % per product in table
  - Client discount options (Non-profit 5%, Volume Order 5%, or custom)
  - Marketing rounding (charm pricing: $60 → $59)
  - Customization options and MSRP comparison display
  - Custom variant support ("Inquire about variants" handling)
- **Proposal Tables (Section 3):**
  - Collapsible MOQ-based pricing tables
  - Automatic minimum order quantity calculations
  - CSV downloads for proposal tables
- **PowerPoint Generation (Section 4):**
  - Automated slide matching and selection
  - Dynamic pricing table updates
  - Impact slides per partner
  - Intro/outro slides included
  - Manual match override (advanced)

### Tab 2: Client Order Form Generator
- **Section 1: Client Information** - Pre-fill client details (type, company, contact, email, phone)
- **Section 2: Generate Client Form Link (RECOMMENDED)** - Shareable link to in-app client form
  - Generates a unique URL with proposal data embedded via query params
  - Client accesses form without needing app password or Google account
  - Form pulls live product data from saved proposal
  - Supports file uploads (dropshipping address spreadsheets) without Google sign-in
  - Client can save draft and return later
  - Submissions saved to Google Sheets for import in Tab 3
- **Section 3: Generate Google Form (Legacy)** - Google Forms workflow (kept as fallback)
  - **Pre-filled URL Generation:**
    - Automatically populates form with proposal products and client info
    - Select which products to include (up to 10 product lines)
    - Adjust quantities before generating
    - One-click URL generation with copy button
    - "Open Form in New Tab" preview link
  - **Client Experience:**
    - Professional Google Form interface
    - Pre-filled with exec-provided info (client details + products)
    - Client completes: shipping, payment, in-hands date, special requests
    - Auto-saves to Google Sheets response sheet
  - **Benefits:**
    - 50-70% faster than HTML workflow (45-60s vs 2-3min)
    - Better client experience (familiar Google Forms UI)
    - Automatic cloud storage and tracking
    - Imports seamlessly into Tab 3 (Option A)
- **Section 3: HTML Order Form (Alternative)** - Legacy HTML form workflow
  - **Form Template Customization (Optional):** Customize template text
    - Dropdown selector to choose which field to edit (8 customizable fields)
    - Default selection: Dropshipping Instructions
    - Customizable fields: form instructions, dropshipping instructions/placeholder, shipping/billing placeholders, customization placeholder, impact card options, payment options
    - Changes apply to generated HTML form in real-time
  - **Client Order Form:** Professional, email-ready HTML order form
    - Styled table format (light/dark mode compatible)
    - Clear instructional prompts for clients
    - Pre-filled product names and quantities
    - Pre-filled client information from Section 1
    - Customizable template text throughout
    - Multiple choice delete-to-select format
    - Download as HTML, TXT, or CSV
    - "Update Order Form with This Info" button for confirmation

### Tab 3: Order & Client Info (main workflow)
- **Saved Orders:** Save and load orders across sessions
  - Name orders for easy identification
  - Optional creator name tracking
  - Load previously saved orders with all products, settings, and client info
  - Delete unwanted orders
  - Dataset mismatch warnings when loading
  - Duplicate name detection with versioning (v2, v3, etc.)
  - Stored in Google Sheets (cloud-persistent)
- **Workflow Guidance:** Clear instructions showing 4 pathways into Tab 3 with recommended workflow
- **Option A - Google Form Import (RECOMMENDED - NEW!):** Import completed Google Form responses
  - **Load Responses:** Click "Load Recent Form Responses" to fetch from Google Sheets
  - **Preview Before Import:** Expandable preview showing:
    - Client info (type, company, contact, email, phone)
    - Products with quantities and customization notes
    - Shipping details (address, drop-shipping, in-hands date)
    - Payment preferences (timeline, method)
    - Impact card selection
  - **One-Click Import:** Imports all data and adds products to order
  - **Automatic Product Matching:** Exact match, case-insensitive against catalog
  - **Default Settings:** Quantities from form, 100% markup (editable after import)
  - **Duplicate Prevention:** Tracking columns prevent re-importing same response
  - **Seamless Integration:** Works perfectly with Tab 2 Google Form generation
- **Option B - HTML Order Form Import (Alternative):** Upload completed client order forms (HTML format)
  - Supports both our generated HTML and Google Docs exported HTML
  - **Client Info Extraction:** Extracts 11 fields automatically (client type, company, contact info, shipping/billing addresses, drop shipping, in-hands date, impact cards, payment preference)
  - **Product Extraction:** Parses product names from Order Details table
    - Exact and partial matching against product catalog
    - Checkbox selection UI
    - Shows match type (Exact/Partial) and catalog name
    - Warns about unmatched products
    - Adds selected products with default settings (quantity 1, 100% markup)
  - Preview extracted data (client info + products) before applying
  - Smart defaults: shipping address field shows unless drop shipping is explicitly "Yes"
  - Handles user input errors gracefully
- **Option B - Import from Proposal (Tab 1):** Most commonly used workflow - import all or individual products from Tab 1 (preserves quantity & markup)
  - Full section (not hidden in expander) since this is the primary workflow
  - Shows proposal source info (saved name, creator, date)
  - Import All or select individual products
  - Shows helpful message when no proposal exists
- **Option C - Manual Product Selection:** One-click add from dropdown with MSRP pricing
  - **Use MSRP pricing checkbox (Default: ON):** Automatically calculates markup to match MSRP when adding products
  - Products with MSRP have markup auto-calculated, products without MSRP use 100% markup
  - Markup still manually editable after adding
  - Fallback for starting fresh without proposal or form
- **Inline Product Editing:** Always-visible settings for each product (no expand/collapse)
- **Real-time Pricing Updates:** Instant recalculation as you edit quantity, markup, or customization
- **Quantity Warning:** Visual alert when quantity=1 to prevent accidental single-unit orders
- **Flexible Pricing:** Both tiered and flat-rate products supported
- **Dynamic Tier Parsing:** Tier ranges defined in data (not hardcoded)
- **Universal Customization Options:** All products can add customization (setup fees + per-unit costs with optional minimum quantities)
  - If spreadsheet has customization data, defaults are pre-filled
  - If no spreadsheet data, defaults to $0 (user can still add custom values)
- **Smart Calculations:** Markup applies to product price only (not customization)
- **Discount Options:** Non-profit preset (5%), Volume Order (5%), or custom discounts
- **MOQ Warnings:** Visual alerts when order quantity is below minimum order quantity
- **Marketing Rounding:** Only applies when total is divisible by 10 (e.g., $60 → $59)
- **Custom Line Items:** Add unique services/customizations
- **Order Notes:** 5 categories (kitting, client requests, samples, artwork, general)
- **Detailed Order Summary:** Line-item breakdown showing:
  - Base product cost + markup (separate line per product)
  - Customization setup fee (if applicable, separate line item)
  - Customization per-unit cost (if applicable, separate line item)
  - Per-product kitting (if applicable, separate line item with "one-time" quantity)
  - Products subtotal
  - Customization subtotal (if applicable)
  - Per-product kitting subtotal (if applicable)
  - Discount (if applicable)
  - Shipping
  - Tariffs (per product with country & rate)
  - Credit card fee (if applicable)
  - Total quote
- **Section Flow:** Workflow Guidance → Options A/B/C (Add Products) → 2. Current Order → 3. Order Settings → 4. Order Summary → 5. Client & Order Information

### Tab 4: Execution & Accounting
- **Editable Order Information:** Review and complete any missing client/order information with inline editing
- **Order Validation:** Completeness check with warnings for missing fields
- **Comprehensive Order Settings:** Full editing access to all Tab 2 settings (shipping, tariffs, discounts, custom line items, notes)
- **4-Table Invoice/PO Format:** Structured to match bookkeeper template requirements:
  - **Table 1: Client/Company Information** - Company name, contact, billing/shipping addresses, PO number
  - **Table 2: Partners + Point of Contacts** - All partners with POC details auto-populated from Google Sheets
  - **Table 3: Order Details** - Client in-hands date, ship method, payment terms/method, submission details
  - **Table 4: Invoice and PO Item Details** - Line items with partner, specs, quantity, in-hands date, cost/unit, total cost, sell price/unit, total sell price
- **Detailed Line Items:** Each product shows:
  - Base product with cost per unit and total cost
  - Customization setup fee (separate line item with indentation)
  - Customization per-unit costs (separate line item with indentation)
  - Per-product kitting (separate line item with indentation, quantity = 1)
  - Tariffs with per-unit breakdown (separate line item showing rate and quantity)
- **Smart Pricing Display:** Sell price excludes customization to prevent double counting (customization shown separately)
- **Notes Section:** Displays all order notes (kitting specs, client requests, samples, artwork, general)
- **Dual Export Options:**
  - CSV download for spreadsheet import and bookkeeper submission
  - HTML download for professional, email-ready invoice/PO format

## Project Structure

```
pricing-data-solution-pbp/
├── app.py                      # Main application (PRODUCTION)
├── start.sh                    # Render deployment startup script
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # This file - project rules & context
├── README.md                   # Project overview & quick start
├── SCHEMA_UPDATE_PROCESS.md    # Systematic process for schema updates
│
├── .streamlit/
│   └── secrets.toml           # Google credentials (SECRET - never commit locally)
│
├── docs/                       # Documentation (organized by topic)
│   ├── README.md              # Documentation index
│   ├── CHANGES_2026_05_23.md  # May 23, 2026 changes & bug fixes (16 items)
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   ├── SCROLL_PRESERVATION_PATTERN.md # Scroll preservation implementation
│   ├── SESSION_STATE_AUDIT.md # Session state management
│   ├── CODE_SIMPLIFICATION_AGENT.md # Code cleanup process documentation
│   ├── planning/              # Core project documentation
│   │   ├── PLANNING.md        # Project requirements & goals
│   │   ├── METHODOLOGY_LOGIC.md # Pricing calculations & business rules
│   │   ├── RESTRUCTURE_CONTEXT.md # Data structure reference
│   │   ├── INVOICE_AND_PROPOSAL_SPEC.md # Invoice/PO format
│   │   ├── GOOGLE_FORMS_IMPLEMENTATION_COMPLETE.md # Google Forms integration guide (v7.6)
│   │   ├── GOOGLE_FORM_CREATION_GUIDE.md # Step-by-step form creation (v7.6)
│   │   └── GOOGLE_FORMS_PREFILLED_WORKFLOW.md # Workflow analysis (v7.6)
│   ├── powerpoint/            # PowerPoint automation (Phase 1 & 2)
│   │   ├── PHASE_2_COMPLETION_SUMMARY.md # Phase 2 final summary
│   │   └── PHASE_1_COMPLETION_SUMMARY.md # Phase 1 technical deep dive
│   ├── meetings/              # Stakeholder meetings and notes
│   │   ├── STAKEHOLDER_MEETING_NOTES.md # Organized requirements
│   │   ├── RAW_MEETING_NOTES_113024.md # Original Nov 30 notes
│   │   └── PBP_MEETING_042125.md # Apr 21, 2025 leadership meeting notes
│   ├── testing/               # Testing documentation
│   │   └── TAB3_TAB4_TESTING_CHECKLIST.md # Tab 3→4 test plan
│   ├── investigations/        # Technical investigations
│   │   └── PARTNER_POC_INVESTIGATION.md # Partner contact debugging
│   └── archive/               # Historical/deprecated documentation
│       ├── powerpoint-planning/ # PowerPoint planning docs (14 files)
│       ├── tab2-improvements/   # Tab 2 UI redesign docs (9 files)
│       └── [Other archived documents]
│
├── src/                        # Modular code (extracted from app.py)
│   ├── data_loader.py         # Google Sheets data loading
│   ├── helpers.py             # Utility functions, conversions, validation
│   ├── pricing_engine.py      # Pricing calculations and quote generation
│   ├── client_form.py         # Client order form page (v8.4.0)
│   ├── slide_matcher.py       # PowerPoint slide matching (Phase 1)
│   ├── pptx_generator.py      # PowerPoint generation (Phase 2)
│   ├── template_loader.py     # Cloud-based PowerPoint template loading (v6.16)
│   ├── match_manager.py       # Manual match storage (JSON-based)
│   ├── match_memory.py        # Confirmed match storage (Google Sheets, v6.9)
│   ├── proposal_manager.py    # Save/load/delete proposals (v6.6)
│   ├── order_manager.py       # Save/load/delete orders (v6.7)
│   ├── drive_helper.py        # Photo storage via Google Sheets (base64 chunked)
│   ├── forms_config.py        # Google Forms configuration (v7.6)
│   └── forms_helper.py        # Google Forms URL generation & response import (v7.6)
│
├── tests/                      # Unit tests
│   └── test_client_form.py    # Client form module tests
│
├── templates/                  # Templates and reference files
│   ├── November All Slides.pptx # PowerPoint template (339 slides, 43MB)
│   ├── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md
│   └── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf
│
├── scripts/                    # Utility scripts (organized, 75+ files)
│   ├── core/                  # Essential core functionality (2 files)
│   │   ├── test_connection.py # Test Google Sheets API (ESSENTIAL)
│   │   └── investigate_data.py # Data structure debugging
│   ├── features/              # Feature-specific tests (43 files)
│   │   ├── test_saved_proposals.py # Save/load proposals
│   │   ├── test_saved_orders.py # Save/load orders
│   │   ├── test_volume_order_discount.py # Volume discount testing
│   │   ├── test_per_product_kitting.py # Kitting separation
│   │   ├── test_new_pricing_logic.py # v8.0 pricing methods
│   │   └── [38 more feature tests...]
│   └── investigations/        # Technical debugging (16 files)
│       ├── investigate_tier_overlaps.py # Tier overlap debugging
│       └── [15 more investigation scripts...]
│
└── backups/                    # Reference backup
    └── app_before_modular_refactor_20251027.py  # Pre-modular structure reference
```

## Common Tasks

- **Refresh pricing data:** Click "Refresh Data" button in sidebar (fetches fresh data from Google Sheets)
  - 30-second cooldown between refreshes to protect against API rate limits
  - Alternative: Click menu → "Rerun" to restart app (uses cached data if < 5 minutes old)
  - Data auto-refreshes every 5 minutes via TTL cache
- **Update credentials:** Edit `.streamlit/secrets.toml`
- **Test API connection:** `streamlit run scripts/test_connection.py`
- **Investigate data structure:** `streamlit run scripts/investigate_jaggery_demo.py` or `python scripts/check_jaggery_demo.py`
- **Deploy to Render:** Automatic deployment on git push (environment variables set in Render dashboard)
- **Local development:** Use `.streamlit/secrets.toml` for credentials (never commit)

---

## Current Status

**Version:** 8.5.2

**Last Updated:** 2026-07-10

**Deployment:** IN PRODUCTION at https://pbp-order-management-system.onrender.com
- Render Standard tier (2GB RAM, $25/month)
- Cloud-based PowerPoint template loading
- Password gate for main app (client form links bypass)

**Codebase Status:**
- ~19,500 lines of Python code (app.py + 14 src/ modules)
- 55+ test scripts organized in scripts/ (core, features, investigations)
- 4-method pricing system (v8.1.0 schema, 45 columns)
- Fully deployed and operational on Render

**Recent Improvements (2026-07-10 - v8.5.2):**
- Password gate now logs in on the first click (was requiring multiple clicks)
- Login is remembered per browser via `streamlit-local-storage` (previous iframe-redirect approach was blocked by browser sandbox and never persisted)

**Recent Improvements (2026-07-10 - v8.5.1):**
- Per-partner "Shipping Instructions to PbP" field (Tab 4 + invoice/PO export)
- Tab 3 to Tab 4 carry-over fixed (Tab 4 editors seed from client_info; contact clobber removed)
- Stray $0.03 line-total fixed (full-precision markup conversion in `calculate_markup_from_price`)
- Overwrite-on-save for orders and proposals (in-place update, keeps original ID); fixed version increment
- Proposal load no longer forces "Manual override" (clears stale per-row widget state)

**Recent Improvements (2026-07-02 - v8.5.0):**
- 7 team-reported bug fixes: rounded pricing in Order Summary, editable partner contacts, cost basis display, shipping type vs ship method separation, removed Cost Verified column, local password gate fix

**Recent Improvements (2026-05-27 - v8.4.0):**
- Client Order Form as shareable link (standalone page, no login required)
- New `src/client_form.py` module with session tokens, proposal loading, draft save/load, form submission
- Query-param routing in app.py (`?client_form=<id>` renders form instead of main app)
- Password gate for main app (client forms bypass gate)
- Redesigned client order form UX
- Dropshipping file download in Tab 3 response preview
- Generate Client Form Link section in Tab 2
- Bug fixes: single-date picker for In-Hands Date, removed Impact Card Selection box, password gate width, query param routing across Streamlit versions

**Recent Improvements (2026-05-23 - v8.3.0):**
- 16 bug fixes and feature requests from leadership meeting
- Full details: [docs/CHANGES_2026_05_23.md](docs/CHANGES_2026_05_23.md)

**Recent Improvements (2026-02 to 2026-04 - v8.2.0):**
- Template-resilient PowerPoint generation (handles missing/changed template slides gracefully)
- Tab 2 Google Form generation works without requiring a proposal first
- Custom variant support and "Inquire about variants" handling in Tab 3
- MOQ warnings for orders below minimum quantity
- Volume order discount reminder for orders over $10,000
- Tier parsing robustness (space-separated formats, multi-colon edge cases)

**Recent Improvements (2026-01-28 to 2026-01-29 - v8.1.0):**
- Schema v8.1.0: Added "Other Add-On % (of Cost)" column (45 total columns)
- "Package" -> "Case" terminology (Units per Case, Cost Basis Per Case)
- Fourth pricing method: "MSRP + Other Add-On % (of Cost)"
- Volume Order Discount (5%) option in Tab 1 and Tab 3
- Per-product kitting shown as separate line items in Tab 3 and Tab 4
- Kitting quantity field for flexible kitting charges
- Fixed Refresh Data button (was returning cached data)
- Fixed PowerPoint discount labels and pricing (3 related fixes)
- Fixed "MSRP + Other Add-On %" pricing logic
- Fixed double normalization bug for Per Case products
- Google Form bug fixes and UI cleanup
- Removed Workflow Progress section from sidebar
- Removed variant functionality from Tab 1 (moved to Tab 3 custom variants)
- All emojis removed from app UI
- Enforced PBP $1,000 baseline MOV per-product in MOQ calculations

**Previous Versions:** See [CHANGELOG.md](CHANGELOG.md) for complete history (v6.0 through v8.3.0)

**Features Implemented:**
- ✅ **Client Order Form Link (v8.4.0):** Shareable URL to standalone form page, no login/Google account needed
- ✅ **Password Gate (v8.4.0):** Main app password-protected, client form links bypass gate
- ✅ **4-Tab Workflow:** Proposals → Client Order Forms → Order & Client Info → Execution & Accounting
- ✅ **Proposal System:** Product filtering, catalog browser, MOQ-based pricing tables, saved proposals
- ✅ **HTML Client Order Form Generation:** Professional table format with clear instructions
- ✅ **HTML Order Form Import:** Parse completed forms (both our HTML and Google Docs formats)
- ✅ **PowerPoint Proposal Automation (Phase 1 & 2 - COMPLETE):** End-to-end automated PowerPoint generation
- ✅ **Copy Buttons:** Easy copy for Kitting Pricing & Terms sections
- ✅ **Proposal-to-Order Connection:** Import all products or select individually
- ✅ **Next Steps Guidance:** Dynamic messaging in Tab 1 guiding to Tab 2
- ✅ **Success Banners:** Visual feedback on available proposal products
- ✅ **CSV Downloads:** Export proposals and client order forms
- ✅ **Tab Navigation Buttons:** Quick navigation between tabs with helpful prompts
- ✅ **Enhanced Price Warnings:** Show old/new values and reasons for price changes
- ✅ **Partner Cost Visibility:** Display what PBP pays partners for customization
- ✅ Multi-partner support (Partner X and future partners)
- ✅ Flexible pricing: tiered AND flat-rate products
- ✅ Dynamic tier parsing from Google Sheets data
- ✅ 3-sheet data architecture (Template, Metadata, Partner-Specific Info)
- ✅ Customization system (setup fee + per-unit costs)
- ✅ Multi-product ordering with add-to-cart pattern
- ✅ Per-product markup configuration
- ✅ Smart markup calculation (product only)
- ✅ Discount options (Non-profit 5%, Volume Order 5%, custom)
- ✅ Marketing rounding (charm pricing: $60 → $59)
- ✅ Custom line items for unique services/customizations
- ✅ Per-product proposal tables (4-column MOQ format)
- ✅ Bookkeeper-standardized Invoice & PO template (4-table format)
- ✅ Editable order information in Tab 3 (complete all missing fields before generation)
- ✅ Comprehensive order settings access in Tab 3 (mirrors Tab 2 functionality)
- ✅ Detailed per-unit and total pricing columns (cost/unit, total cost, sell price/unit, total sell price)
- ✅ Smart sell price calculation (excludes customization to prevent double counting)
- ✅ Tariff per-unit breakdown (shows rate and quantity-based calculation)
- ✅ HTML invoice/PO export (professional, email-ready format)
- ✅ Dual export options (CSV for bookkeeper, HTML for client communication)
- ✅ Partner contact auto-extraction from Google Sheets
- ✅ Comprehensive order notes system (5 categories)
- ✅ Field validation with user warnings
- ✅ Standardized payment/shipping dropdowns
- ✅ Date tracking for order/cost submission

**Testing Status:**
- ✅ Data loads from master_pricing_template_10_14
- ✅ Tier parsing logic verified (T1-T6 ranges)
- ✅ Tier selection working correctly for various quantities
- ✅ New column structure compatible with app
- ✅ Partner filtering functional
- ✅ HTML import tested with both our HTML and Google Docs formats (11/11 fields)
- ✅ CSV download matches UI display (pricing, MOQ, discounts)
- ✅ All Phase 1-4 fixes tested and verified
- ✅ PowerPoint matching system tested (78.9% match rate achieved)
- ✅ Edge cases validated (all exact, all fuzzy, no matches, mixed, empty)
- ✅ Integration testing complete (5/5 checks passed)
- ✅ User confirmation UI tested and validated
- ✅ PowerPoint generation tested with multiple products
- ✅ Font formatting preservation verified (15pt maintained)
- ✅ Table updates verified across all 3 formats (2×3, 2×4, 3×4)
- ✅ MOQ calculation corrected (math.ceil vs int)
- ✅ Discount application tested (5% Non-profit discount)
- ✅ Volume Order Discount tested (5%)
- ✅ Per-product kitting separation tested (5 tests passing)
- ✅ Schema v8.1.0 compatibility tested (45 columns)
- ✅ Tier parsing edge cases tested (overlaps, spaces, multi-colon)
- ✅ Template-resilient PowerPoint generation tested
- ✅ Client form module unit tests (tests/test_client_form.py)
- ✅ Query param routing tested across Streamlit versions
- ✅ Password gate tested (main app gated, client forms bypass)

**Production Status:** Ready for production use

---

## Future Enhancements

### Phase 3: PowerPoint Enhancements (Optional)
- **Slide reordering:** Allow users to reorder products before generation
- **Custom cover design:** Template selection and custom branding
- **Slide preview:** Preview matched slides before generation
- **Batch operations:** Generate multiple presentations at once
- **Status:** Phase 1 & 2 complete, future enhancements optional

### Other Enhancements
- Multi-partner support (different tier structures per partner)
- Partner-specific configuration file
- Auto-detect tier ranges from column headers
- Remove debug expanders (optional)
- Admin UI for managing partner configurations
