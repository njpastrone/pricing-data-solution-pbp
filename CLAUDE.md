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

---

## Important References

**Documentation is organized by topic. See [docs/README.md](docs/README.md) for complete index.**

**Core references (use before starting any work):**

- **[docs/planning/PLANNING.md](docs/planning/PLANNING.md)** - Project requirements, architecture decisions, and implementation plans
- **[docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md)** - Pricing calculations, business rules, and partner-specific methodologies
- **[docs/planning/RESTRUCTURE_CONTEXT.md](docs/planning/RESTRUCTURE_CONTEXT.md)** - Current data structure from master_pricing_template_10_14
- **[docs/planning/INVOICE_AND_PROPOSAL_SPEC.md](docs/planning/INVOICE_AND_PROPOSAL_SPEC.md)** - Invoice format specifications and required information

**PowerPoint automation (latest feature):**

- **[docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md](docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md)** - Phase 2 complete summary (production-ready)
- **[docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md](docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md)** - Phase 1 technical deep dive

---

## Project Overview

This is the pricing-data-solution-pbp project - a Python/Streamlit application focused on simplicity and beginner-friendly code.

## Development Guidelines

- Follow existing code patterns and conventions in the repository
- Ensure all changes are well-tested before committing
- Keep commits focused and atomic

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

- **Frontend:** Streamlit (Python-based web app) with 4-tab structure
  - **Tab 1: Proposal Generator** - Product catalog, filtering, proposal generation (tables & PowerPoint)
  - **Tab 2: Client Order Form Generator** - Create professional HTML order forms to send to clients
  - **Tab 3: Order & Client Info** - Order management, client data collection
  - **Tab 4: Execution & Accounting** - Invoice/PO generation, bookkeeping
- **Data Source:** Google Sheets with dataset selector (Demo or Real)
  - **Demo Dataset:** master_pricing_template_10_14 (19 products, 4 partners - testing/development data)
  - **Real Dataset:** master_pricing (133 products, 4 partners - production data READY)
  - **Required sheet structure:**
    - **Data**: Partner-product pricing data (header at row 6)
    - **Metadata**: Deliverable field definitions (header at row 2)
    - **Partner-Specific Info**: Partner configuration reference (header at row 2)
- **Code Structure:** Modular with helper functions in `src/` directory
  - `src/data_loader.py` - Google Sheets data loading and caching
  - `src/helpers.py` - Utility functions, conversions, validation, HTML parsing
  - `src/pricing_engine.py` - Pricing calculations and quote generation
- **Authentication:** Google Cloud service account
- **Pricing Model:** Flexible tiered or flat-rate pricing per product
- **Recommended Workflow:**
  1. **Tab 1 (Proposal Generator):** Browse & filter products → Configure proposal → Generate tables & PowerPoint (optional: send to client)
  2. **Tab 2 (Client Order Form Generator):** Enter client info → Generate HTML order form → Send to client
  3. **Tab 3 (Order & Client Info):** Import completed HTML form (recommended) OR import from proposal OR add products manually → Configure order → Collect client details
  4. **Tab 4 (Execution & Accounting):** Review/edit order → Generate invoice & PO → Download for bookkeeping
- **Workflow Notes:**
  - Tab 3 has 3 entry points with clear guidance at the top
  - HTML form import (Option A) is the recommended workflow when available
  - Proposal import (Option B) is an alternative if you have a proposal but no completed form
  - Manual selection (Option C) is a fallback for starting from scratch

## Current Features

### Tab 1: Proposal Generator (for prospective clients)
- **Browse & Filter Products (Section 1):**
  - Collapsible product catalog (auto-collapses after adding products)
  - Filter by price range, partner, country of origin
  - View product details inline (country, tiered pricing, MOQ estimates, descriptions)
  - **Bulk Actions:** Add all products from one or more partners at once
    - Select multiple partners and add all their products with one click
    - Smart duplicate detection (skips products already in proposal)
    - Preview count before adding (shows new vs duplicate products)
    - Respects all active filters (price, partner, country)
- **Proposal Configuration (Section 2):** Quantity, markup %, customization options, MSRP comparison
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
- **Order Details (Section 1):** Pre-fill client information (type, company, contact, email)
- **Client Order Form (Section 2):** Professional, email-ready HTML order form with:
  - Styled table format (light/dark mode compatible)
  - Clear instructional prompts for clients
  - Pre-filled product names and quantities
  - Multiple choice delete-to-select format
  - Download as HTML, TXT, or CSV
  - "Update Order Form with This Info" button for confirmation

### Tab 3: Order & Client Info (main workflow)
- **Workflow Guidance:** Clear instructions showing 3 pathways into Tab 3 with recommended workflow
- **Option A - HTML Order Form Import (RECOMMENDED):** Upload completed client order forms (HTML format)
  - Supports both our generated HTML and Google Docs exported HTML
  - Extracts 11 fields automatically: client type, company, contact info, shipping/billing addresses, drop shipping, in-hands date, impact cards, payment preference
  - Preview extracted data before applying
  - Smart defaults: shipping address field shows unless drop shipping is explicitly "Yes"
  - Handles user input errors gracefully
  - Prominently placed at top (no longer hidden in Section 5)
- **Option B - Proposal-to-Order Import:** Import all or individual products from Tab 1 (preserves quantity & markup only)
  - Only shows if proposal products exist
  - Alternative workflow when you have a proposal but no completed form
- **Option C - Manual Product Selection:** One-click add from dropdown (defaults: qty=1, markup=100%)
  - Becomes "Option B" when no proposal exists
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
- **Discount Options:** NGO preset (5%) + custom discounts
- **Marketing Rounding:** Only applies when total is divisible by 10 (e.g., $60 → $59)
- **Custom Line Items:** Add unique services/customizations
- **Order Notes:** 5 categories (kitting, client requests, samples, artwork, general)
- **Detailed Order Summary:** Line-item breakdown showing:
  - Base product cost + markup (separate line per product)
  - Customization setup fee (if applicable)
  - Customization per-unit cost (if applicable)
  - Products subtotal
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
  - Customization setup fee (separate line item)
  - Customization per-unit costs (separate line item)
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
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # This file - project rules & context
├── README.md                   # Project overview & quick start
│
├── .streamlit/
│   └── secrets.toml           # Google credentials (SECRET - never commit)
│
├── docs/                       # Documentation (organized by topic)
│   ├── README.md              # Documentation index
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   ├── planning/              # Core project documentation
│   │   ├── PLANNING.md        # Project requirements & goals
│   │   ├── METHODOLOGY_LOGIC.md # Pricing calculations & business rules
│   │   ├── RESTRUCTURE_CONTEXT.md # Data structure reference
│   │   └── INVOICE_AND_PROPOSAL_SPEC.md # Invoice/PO format
│   ├── powerpoint/            # PowerPoint automation (Phase 1 & 2)
│   │   ├── PHASE_2_COMPLETION_SUMMARY.md # Phase 2 final summary
│   │   ├── PHASE_1_COMPLETION_SUMMARY.md # Phase 1 technical deep dive
│   │   ├── PPTX_AUTOMATION_IMPLEMENTATION_ROADMAP.md # Full roadmap
│   │   └── [13 other PowerPoint docs]
│   ├── tab2-improvements/     # Historical Tab 2 redesign docs
│   │   └── [9 UI redesign documents]
│   └── archive/               # Deprecated/historical docs
│       └── [5 archived documents]
│
├── src/                        # Modular code (extracted from app.py)
│   ├── data_loader.py         # Google Sheets data loading
│   ├── helpers.py             # Utility functions, conversions, validation
│   ├── pricing_engine.py      # Pricing calculations and quote generation
│   ├── slide_matcher.py       # PowerPoint slide matching (Phase 1)
│   └── pptx_generator.py      # PowerPoint generation (Phase 2)
│
├── templates/                  # Templates and reference files
│   ├── November All Slides.pptx # PowerPoint template (339 slides, 43MB)
│   ├── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md
│   └── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf
│
├── scripts/                    # Utility scripts
│   ├── test_connection.py     # Test Google Sheets connection
│   ├── check_jaggery_demo.py  # Investigate jaggery_demo (Python)
│   ├── investigate_jaggery_demo.py  # Investigate tool (Streamlit)
│   ├── test_improved_matching.py    # Test Phase 1 matching improvements
│   ├── test_edge_cases.py     # Test Phase 1 edge cases
│   └── test_integration.py    # Test Phase 1 complete workflow
│
├── backups/                    # Backup files
│   └── app_mvp_backup.py      # Original MVP
│
└── archive/                    # Deprecated files (old scripts & data)
```

## Common Tasks

- **Refresh pricing data:** Click menu → "Rerun" in the Streamlit app
- **Update credentials:** Edit `.streamlit/secrets.toml`
- **Test API connection:** `streamlit run scripts/test_connection.py`
- **Investigate data structure:** `streamlit run scripts/investigate_jaggery_demo.py` or `python scripts/check_jaggery_demo.py`
- **Deploy to cloud:** Follow Streamlit Cloud deployment guide (add secrets in app settings)

---

## Current Status

**Version:** 6.3 - Bulk Add Partners to Proposal

**Last Updated:** 2025-11-10

**Recent Improvements (2025-11-10 - v6.3):**
- ✅ **Bulk Add Products from Partner(s) (New Feature):**
  - Added "Bulk Actions" section in Tab 1 for quickly adding all products from selected partners
  - Multi-select partner dropdown to choose one or more partners
  - Smart duplicate detection: automatically skips products already in proposal
  - Preview count shows new vs duplicate products before adding
  - Respects all active filters (client budget, partner, country filters)
  - Success message shows count and partner names
  - Scroll position preserved after bulk add
  - Uses 100% markup default (same as individual product adds)

**Recent Improvements (2025-11-10 - v6.2):**
- ✅ **Dataset Selector (New Feature - Production Ready):**
  - Added sidebar option to switch between Demo and Real pricing datasets
  - Demo dataset: master_pricing_template_10_14 (19 products, 4 partners - testing data)
  - Real dataset: master_pricing (133 products, 4 partners - production data READY)
  - Automatic data reload when switching datasets
  - Prevents data mismatch by clearing proposals/orders when switching datasets
  - Sheet structure updated: 'Data' sheet (renamed from 'Template') for pricing data
- ✅ **Scroll Preservation System:**
  - Implemented JavaScript-based scroll position preservation (95-98% effective)
  - Global CSS fix to prevent automatic scrolling on widget interactions
  - sessionStorage-based capture and restore on page reruns
  - Button-specific scroll capture in Tab 1 (product catalog, PowerPoint section, fuzzy matching)
  - MutationObserver for dynamically rendered buttons
  - Added keep_catalog_expanded flag to prevent catalog collapse after adding products
  - Documentation: [docs/SCROLL_PRESERVATION_PATTERN.md](docs/SCROLL_PRESERVATION_PATTERN.md) and [docs/SESSION_STATE_AUDIT.md](docs/SESSION_STATE_AUDIT.md)

**Previous Improvements (2025-11-05 - v6.1):**
- ✅ **Tab 3 Workflow Clarity (Major UX Improvement):**
  - Added "Getting Started - Choose Your Workflow" guidance section at top of Tab 3
  - Restructured Tab 3 to prioritize recommended workflow (HTML import first)
  - Moved HTML order form import from Section 5 to Option A (prominently placed)
  - Renamed sections: Option A (HTML import - recommended), Option B (Proposal import), Option C (Manual selection)
  - Added conditional display: Option C becomes "Option B" when no proposal exists
  - Updated all section numbers to be sequential (2. Current Order, 3. Order Settings, 4. Order Summary, 5. Client & Order Information)
  - Clear "Use this if..." guidance for each workflow option
- ✅ **Tab 1 Filter Improvements:**
  - Renamed "Max Price" filter → "Client Budget" (more accurate description)
  - Filter now based on client price (cost × 2 for 100% markup) instead of PBP cost
  - Renamed "Price/Unit" column → "Cost/Unit" (what PBP pays partner)
  - Added "Price/Unit (100% markup)" column showing client price with default markup
  - Updated MOQ estimate caption to show both cost and client price

**Previous Improvements (2025-11-05 - v6.0):**
- ✅ **4-Tab Structure Reorganization:**
  - Split Tab 1 into two focused tabs: "Proposal Generator" and "Client Order Form Generator"
  - Moved Order Details and Client Order Form sections from Tab 1 to new Tab 2
  - Old Tab 2 became Tab 3 (Order & Client Info)
  - Old Tab 3 became Tab 4 (Execution & Accounting)
  - Clean separation of concerns: proposals → client forms → orders → execution
- ✅ **UI Improvements:**
  - Combined "Filter Products" and "Product Catalog" into single "Browse & Filter Products" section
  - Added collapsible expanders for Product Catalog (auto-collapses after adding products)
  - Added collapsible expander for Proposal Tables section
  - Product details now show inline instead of nested expanders
  - Improved filter result messaging
- ✅ **Bug Fixes:**
  - Fixed Manual Match Override section to use correct session state variable (`df_template`)
  - Restored "Update Order Form with This Info" button in Tab 2
  - Fixed PowerPoint repair warning with user notice
- ✅ **Navigation Updates:**
  - Updated all tab references and navigation buttons throughout app
  - Updated sidebar progress tracker for 4-tab structure
  - Updated "How to Use" instructions

**Previous Improvements (2025-11-04):**
- ✅ **PowerPoint Proposal Automation - Phase 1 & 2 COMPLETE:**
  - **Phase 1 - Matching System:**
    - Intelligent product name matching with 78.9% accuracy (15 of 19 products)
    - Multi-scorer fuzzy matching (3 algorithms: token_sort, token_set, partial_ratio)
    - Keyword category boosting (+15% confidence for same-category products)
    - Variant name normalization (strips (Noir), -MOF, - Large, - Set of 3, etc.)
    - Manual product mappings for guaranteed exact matches
    - User confirmation UI for all fuzzy matches
    - Alternative selection interface (top 3 alternatives per product)
  - **Phase 2 - PowerPoint Generation:**
    - Automated slide selection and removal (keeps only confirmed products)
    - Dynamic pricing table updates for all 3 table formats (2×3, 2×4, 3×4)
    - Calculates MOQ, base price, and discounted client price
    - Updates table headers dynamically based on MOQ and discount
    - Preserves original font formatting (15pt template font maintained)
    - Professional cover slide with client name and date
    - Progress indicators during generation (4 steps)
    - Generation time tracking and success metrics
    - Improved error handling with detailed debugging info
    - One-click download of customized presentation
  - **Section 10 in Tab 1:** "Generate PowerPoint Proposal (BETA)" - Full workflow from matching to download

**Previous Improvements (2025-11-03):**
- ✅ **HTML Client Order Form Import (Issue #27):** Major feature allowing import of completed forms
  - Parses both our generated HTML and Google Docs exported HTML
  - Extracts 11 fields: client type, company name, contact info, shipping/billing, drop shipping, in-hands date, impact cards, payment
  - Preview UI showing extracted data before applying
  - Smart defaults: shipping address shows unless drop shipping is explicitly "Yes"
  - Handles user input errors gracefully (typos, unclear answers)
- ✅ **UI/UX Polish (Issues #20, #22, #26, #28):**
  - Fixed success message showing after adding info to order form
  - Added tab navigation buttons at bottom of Tab 1 and Tab 2
  - Removed all emojis from app (replaced [X]/[ ] checkboxes, removed page icon)
  - Fixed progress tracker to update when order is confirmed
- ✅ **Pricing Transparency (Issues #21, #23, #24, #25):**
  - Restructured dropshipping instructions in HTML form (single row layout)
  - Enhanced price change warnings showing old/new values and reasons (tier change, markup change)
  - Added Partner Customization Costs section showing what PBP pays partners
  - Always show "Discount Quoted to Client" warning in order adjustments
- ✅ **Critical Bug Fix (Issue #19):**
  - Fixed CSV download mismatch - completely rewrote to match UI display logic
  - Both CSV and UI now use same MOQ calculation, pricing, discounts, marketing rounding
  - Ensures data consistency across all exports

**Features Implemented:**
- ✅ **3-Tab Workflow:** Proposals → Order & Client Info → Execution & Accounting
- ✅ **Proposal System:** Product filtering, catalog browser, MOQ-based pricing tables
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
- ✅ Discount options (NGO preset 5% + custom discounts)
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
- ✅ Discount application tested (5% NGO discount)

**Production Status:** ✅ Ready for production use - Phase 1 & 2 complete

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
