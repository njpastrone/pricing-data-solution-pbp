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
12. **REMEMBER THAT IT IS 2025, NOT 2024**

---

## 🔥 ACTIVE DEVELOPMENT STATUS - December 2025 🔥

**Current Focus:** Week 2 Sprint - New Feature Implementation
- **Meeting Date:** November 30, 2025
- **Status:** 16 of 19 features complete (84%)
- **Priority:** Completing Week 2 Sprint features (3 of 6 done)

### Active Development Documents (READ THESE FIRST):
1. **[ACTIVE_DEVELOPMENT_TODO.md](ACTIVE_DEVELOPMENT_TODO.md)** - Current task list with implementation details
2. **[CHANGELOG.md](CHANGELOG.md)** - Comprehensive project history and version tracking
3. **[STAKEHOLDER_MEETING_NOTES.md](docs/meetings/STAKEHOLDER_MEETING_NOTES.md)** - Organized requirements from Nov 30 meeting
4. **[RAW_MEETING_NOTES_113024.md](docs/meetings/RAW_MEETING_NOTES_113024.md)** - Original meeting notes (do not edit)

### Development Workflow:
1. Start with ACTIVE_DEVELOPMENT_TODO.md for current tasks
2. Reference STAKEHOLDER_MEETING_NOTES.md for requirement details
3. Update this file (CLAUDE.md) after completing major phases
4. Use clear git commit prefixes: `FIX:`, `FEAT:`, `TEST:`

### Quick Context Recovery:
**If you lose context, read these files in order:**
1. This section of CLAUDE.md (current status)
2. ACTIVE_DEVELOPMENT_TODO.md (what to work on)
3. STAKEHOLDER_MEETING_NOTES.md (why we're doing it)
4. The relevant code sections mentioned in the TODO

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

When updating the data model/schema (renaming columns, adding fields, modifying data structure):

1. **ALWAYS follow the systematic process in [SCHEMA_UPDATE_PROCESS.md](SCHEMA_UPDATE_PROCESS.md)**
2. **Key principle:** Maintain backward compatibility via `get_column_value()` helper
3. **Required steps:**
   - Review core documentation for context
   - Search for ALL references to changed columns
   - Update `get_column_value()` mappings first
   - Update schema_reference.md
   - Test with both old and new spreadsheet formats
   - Document in CHANGELOG.md

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
      - **Updated Schema (Jan 2026):** Now supports new canonical column names with backward compatibility
      - Core columns: Partner, Product/Service, MOQ, Pricing Tiers (Y/N), PBP Cost (No Tiers), PBP Cost: Tier 1-6
      - **Units per Package**: Normalizes package pricing to per-unit (default: 1)
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
  - Client discount options (Non-profit 5% preset or custom)
  - Marketing rounding (charm pricing: $60 → $59)
  - Customization options and MSRP comparison display
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
- **Form Template Customization (Optional):** Customize any template text in the order form
  - Dropdown selector to choose which field to edit (8 customizable fields)
  - Default selection: Dropshipping Instructions
  - Customizable fields: form instructions, dropshipping instructions/placeholder, shipping/billing placeholders, customization placeholder, impact card options, payment options
  - Changes apply to generated HTML form in real-time
  - Positioned before "Update Order Form" button for better workflow
- **Client Order Form (Section 2):** Professional, email-ready HTML order form with:
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
- **Workflow Guidance:** Clear instructions showing 3 pathways into Tab 3 with recommended workflow
- **Option A - HTML Order Form Import (RECOMMENDED):** Upload completed client order forms (HTML format)
  - Supports both our generated HTML and Google Docs exported HTML
  - **Client Info Extraction:** Extracts 11 fields automatically (client type, company, contact info, shipping/billing addresses, drop shipping, in-hands date, impact cards, payment preference)
  - **Product Extraction (NEW):** Parses product names from Order Details table
    - Exact and partial matching against product catalog
    - Checkbox selection UI (similar to Option B)
    - Shows match type (Exact/Partial) and catalog name
    - Warns about unmatched products
    - Adds selected products with default settings (quantity 1, 100% markup)
  - Preview extracted data (client info + products) before applying
  - Smart defaults: shipping address field shows unless drop shipping is explicitly "Yes"
  - Handles user input errors gracefully
  - Prominently placed at top (no longer hidden in Section 5)
- **Option B - Proposal-to-Order Import:** Import all or individual products from Tab 1 (preserves quantity & markup only)
  - Only shows if proposal products exist
  - Alternative workflow when you have a proposal but no completed form
- **Option C - Manual Product Selection:** One-click add from dropdown with MSRP pricing
  - **Use MSRP pricing checkbox (Default: ON):** Automatically calculates markup to match MSRP when adding products
  - Products with MSRP have markup auto-calculated, products without MSRP use 100% markup
  - Markup still manually editable after adding
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
- **Discount Options:** Non-profit preset (5%) + custom discounts
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
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   ├── SCROLL_PRESERVATION_PATTERN.md # Scroll preservation implementation
│   ├── SESSION_STATE_AUDIT.md # Session state management
│   ├── CODE_SIMPLIFICATION_AGENT.md # Code cleanup process documentation
│   ├── planning/              # Core project documentation
│   │   ├── PLANNING.md        # Project requirements & goals
│   │   ├── METHODOLOGY_LOGIC.md # Pricing calculations & business rules
│   │   ├── RESTRUCTURE_CONTEXT.md # Data structure reference
│   │   └── INVOICE_AND_PROPOSAL_SPEC.md # Invoice/PO format
│   ├── powerpoint/            # PowerPoint automation (Phase 1 & 2)
│   │   ├── PHASE_2_COMPLETION_SUMMARY.md # Phase 2 final summary
│   │   └── PHASE_1_COMPLETION_SUMMARY.md # Phase 1 technical deep dive
│   ├── meetings/              # Stakeholder meetings and notes
│   │   ├── STAKEHOLDER_MEETING_NOTES.md # Organized requirements
│   │   └── RAW_MEETING_NOTES_113024.md # Original Nov 30 notes
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
│   ├── slide_matcher.py       # PowerPoint slide matching (Phase 1)
│   ├── pptx_generator.py      # PowerPoint generation (Phase 2)
│   ├── template_loader.py     # Cloud-based PowerPoint template loading (v6.16)
│   ├── match_manager.py       # Manual match storage (JSON-based)
│   ├── match_memory.py        # Confirmed match storage (Google Sheets, v6.9)
│   ├── proposal_manager.py    # Save/load/delete proposals (v6.6)
│   └── order_manager.py       # Save/load/delete orders (v6.7)
│
├── templates/                  # Templates and reference files
│   ├── November All Slides.pptx # PowerPoint template (339 slides, 43MB)
│   ├── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md
│   └── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf
│
├── scripts/                    # Utility scripts (organized, 26 files)
│   ├── core/                  # Essential core functionality (2 files)
│   │   ├── test_connection.py # Test Google Sheets API (ESSENTIAL)
│   │   └── investigate_data.py # Data structure debugging
│   ├── features/              # Feature-specific tests (19 files)
│   │   ├── test_saved_proposals.py # Save/load proposals
│   │   ├── test_saved_orders.py # Save/load orders
│   │   ├── test_units_per_package.py # Package pricing normalization
│   │   ├── test_match_memory.py # PowerPoint match memory
│   │   ├── test_bidirectional_pricing.py # Tab 1 & 3 price editing
│   │   └── [14 more feature tests...]
│   └── investigations/        # Technical debugging (7 files)
│       ├── investigate_partner_poc.py # Partner contact debugging
│       └── [6 more investigation scripts...]
│
└── backups/                    # Reference backup
    └── app_before_modular_refactor_20251027.py  # Pre-modular structure reference
```

## Common Tasks

- **Refresh pricing data:** Click menu → "Rerun" in the Streamlit app
- **Update credentials:** Edit `.streamlit/secrets.toml`
- **Test API connection:** `streamlit run scripts/test_connection.py`
- **Investigate data structure:** `streamlit run scripts/investigate_jaggery_demo.py` or `python scripts/check_jaggery_demo.py`
- **Deploy to Render:** Automatic deployment on git push (environment variables set in Render dashboard)
- **Local development:** Use `.streamlit/secrets.toml` for credentials (never commit)

---

## Current Status

**Version:** 7.4.0 - Schema Update & Bug Fixes

**Last Updated:** 2026-01-08

**Deployment:** ✅ **IN PRODUCTION** at https://pricing-data-solution-pbp.onrender.com
- Render Standard tier (2GB RAM, $25/month)
- Active partner data: Partial (collecting remaining partner data)
- Cloud-based PowerPoint template loading

**Current Sprint:** Week 2 - New Feature Implementation
- **Focus:** 16 of 19 features complete (84%)
- **Week 2 Progress:** 3 of 6 features done (Tab 3 pricing, terminology, directory cleanup)
- **Active Tasks:** See [ACTIVE_DEVELOPMENT_TODO.md](ACTIVE_DEVELOPMENT_TODO.md)
- **Requirements:** See [docs/meetings/STAKEHOLDER_MEETING_NOTES.md](docs/meetings/STAKEHOLDER_MEETING_NOTES.md)
- **Issues Count:** 0 critical (ALL FIXED), 3 remaining Week 2 features

**Codebase Status:**
- ~14,138 lines of Python code (49% reduction from cleanup)
- 26 test scripts organized in scripts/ (core, features, investigations)
- Clean documentation structure (organized in docs/ subdirectories)
- Fully deployed and operational on Render
- CHANGELOG.md added for comprehensive version history

**Recent Improvements (2026-01-08 - v7.4.0):**
- ✅ **Schema Update with Full Backward Compatibility:**
  - Implemented new canonical pricing data schema (30 columns)
  - Added `get_column_value()` helper for seamless old→new column name transitions
  - Updated all column references throughout the codebase
  - App works with both old spreadsheets and new schema
- ✅ **New Field Support:**
  - **MOQ from Spreadsheet:** Uses partner MOQ when available, calculates otherwise
  - **PBP Standard Markup:** Partner-specific default markups (replaces hardcoded 100%)
  - **Dual Tariff Format:** Supports both percentage and dollar amount estimates
- ✅ **Critical Bug Fixes:**
  - Fixed Streamlit `query_params` compatibility (works with all versions)
  - Fixed pandas Series boolean evaluation error in `calculate_moq`
  - Both errors were blocking app functionality - now resolved
- ✅ **Documentation Updates:**
  - Added comprehensive schema_reference.md
  - Updated README.md and CLAUDE.md with new schema details
  - Created testing guide for schema validation

**Recent Improvements (2025-12-20 - v7.3.0):**
- ✅ **Bidirectional Price Editing in Tab 3:**
  - Users can now edit client price per unit directly, not just markup %
  - Markup % automatically recalculates when price is changed
  - Matches Tab 1 pricing behavior for consistency
  - Fixed critical undefined `new_markup` variable error
- ✅ **NGO → Non-profit Terminology:**
  - Updated all references throughout app for better inclusivity
  - Changed discount label, form fields, and UI text
  - Maintains 5% preset for non-profit organizations
- ✅ **Directory Reorganization:**
  - Organized docs/ into subdirectories (meetings, testing, investigations)
  - Organized scripts/ into core, features, investigations
  - Created comprehensive CHANGELOG.md
  - Cleaner, more maintainable project structure

**Recent Improvements (2025-12-04 - v7.2):**
- ✅ **Critical Fixes Complete - All Data Loss Issues Resolved:**
  - Fixed client info persistence bug in Tab 4 (3 critical fixes total)
  - Client data now properly persists when editing confirmed orders
  - Added callback functions to all 12 input fields in "Edit Order Information"
  - Save UX improvements with unsaved changes indicators
  - All critical data loss issues from stakeholder meeting now resolved

**Recent Improvements (2025-11-20 - v7.0):**
- ✅ **Production Milestone:**
  - Application fully deployed and operational on Render
  - Added [docs/CODE_SIMPLIFICATION_AGENT.md](docs/CODE_SIMPLIFICATION_AGENT.md) documenting cleanup process
  - Documents autonomous code maintenance workflow
  - Serves as reference for future AI-assisted improvements
  - Production-ready codebase with clean architecture

**Recent Improvements (2025-11-20 - v6.18):**
- ✅ **Codebase Simplification & Cleanup:**
  - Deleted archive/ directory (22.5MB, deprecated jaggery_demo code)
  - Consolidated backups (3 of 4 deleted, kept modular refactor reference)
  - Removed 13 obsolete test scripts (~1,249 lines)
  - Archived 23 completed planning docs to docs/archive/ (preserved for reference)
  - Total reduction: ~13,649 lines of code deleted, 22MB saved
- ✅ **Code Clarity Improvement:**
  - Renamed `normalize_product_name()` → `normalize_for_storage()` in match_manager.py
  - Fixed confusing duplicate function names (uppercase vs lowercase)
  - Removed unused imports in slide_matcher.py
  - Updated function docstrings for clarity
  - Now beginner-friendly and self-documenting

**Recent Improvements (2025-11-20 - v6.17):**
- ✅ **Render Deployment Optimizations:**
  - Successfully deployed to Render at https://pricing-data-solution-pbp.onrender.com
  - Upgraded from Starter tier (512MB) to Standard tier (2GB RAM)
  - Moved 43MB PowerPoint template to Google Drive for on-demand loading
  - Added `template_loader.py` module with cloud-based template management
  - Updated `data_loader.py` to support environment variables for Render deployment
  - Created `start.sh` for Render deployment configuration
- ✅ **Memory Optimization Infrastructure (v6.16):**
  - Added `USE_MEMORY_OPTIMIZATION` toggle in app.py (currently disabled)
  - Lazy loading support in `template_loader.py` with `use_cache` parameter
  - Garbage collection in `pptx_generator.py` after heavy operations
  - Memory optimization disabled after tier upgrade (better UX with caching)
  - Template downloads once and caches for session (no duplicate downloads)
- ✅ **Branding Improvements:**
  - Added peace dove icon (🕊️) to replace Streamlit crown logo
  - Fits "Peace by Piece International" brand identity
  - Visible in browser tab and bookmarks

**Recent Improvements (2025-11-19 - v6.15):**
- ✅ **HTML Order Form Product Extraction:**
  - Enhanced `parse_client_order_form_html()` to extract product names from Order Details table
  - Parses products from 3-column table (Product Name, Quantity, Customization)
  - Filters out placeholder text and empty rows
  - **Product Matching System:**
    - Exact match first (case-insensitive)
    - Fallback to partial match if no exact match found
    - Shows match type and catalog name for transparency
    - Warns about products not found in catalog
  - **Selection UI:**
    - Checkbox interface (similar to Option B)
    - Products pre-selected by default
    - Shows partner for each product
    - "Add X Selected Product(s) to Order" button
  - **Order Item Creation:**
    - Default settings: quantity 1, 100% markup
    - Full order item structure with pricing, tariff, customization fields
    - Ready for user editing in Section 2
  - Toast notification on successful import
  - Updated function docstring with products list

**Recent Improvements (2025-11-19 - v6.14):**
- ✅ **Toast Notifications for Product Actions:**
  - Replaced `st.success()` with `st.toast()` for all product addition messages
  - Toast notifications appear in bottom-right corner of screen
  - Visible regardless of scroll position (major UX improvement)
  - Auto-dismiss after 4 seconds (non-intrusive)
  - Applied to 5 locations:
    - Individual product addition to proposal (Tab 1)
    - Bulk product addition to proposal (Tab 1)
    - Proposal-to-order import (Tab 3)
    - Custom line items in Tab 3
    - Custom line items in Tab 4
  - Removed all emoji icons from toast notifications and UI elements for professional appearance

**Recent Improvements (2025-11-19 - v6.13):**
- ✅ **Multi-Variant Product Consolidation:**
  - Automatic detection when multiple products match to same PowerPoint slide
  - User confirmation UI with conditional options based on pricing consistency
  - Multi-row pricing table population (fills all variant rows automatically)
  - Smart variant identifier extraction (size, flavor, numeric units, parentheses, fallback to "Option N")
  - Customization row detection and preservation
  - Partner validation (warns if variants are from different partners)
  - Handles table formats: 2×3, 2×4, 3×4, and multi-row
  - Example: "Strawberry Jam - 4oz" and "Strawberry Jam - 8oz" both populate same slide
  - New functions: `detect_variant_groups()`, `extract_variant_identifier()`, `check_pricing_consistency()`
  - Updated `update_pricing_table()` to support variant_mode parameter
  - Backward compatible: single-product slides work exactly as before

- ✅ **Smart Pricing Consistency Detection:**
  - Automatically detects if all variants have identical MOQ and price
  - Shows pricing indicator in UI: "✅ Consistent Pricing" or "⚠️ Variable Pricing"
  - Displays MOQ and price next to each product name for transparency
  - **Conditional display options:**
    - **Consistent pricing (4 options):**
      1. "Display single row (all variants have same pricing)" [recommended]
      2. "Display all variants (show each variant in separate row)"
      3. "Create separate slides (duplicate slide for each variant)"
      4. "Skip these products"
    - **Variable pricing (3 options):**
      1. "Display together (recommended - fills multiple table rows)" [default]
      2. "Create separate slides (duplicate slide for each variant)"
      3. "Skip these products"
  - Prevents unnecessary multi-row tables when all variants have identical pricing

- ✅ **Smart 4-Column Table Layout:**
  - Added "Price @ Qty 100" calculation to `calculate_proposal_pricing()`
  - Returns both `price_at_100` and `client_price_at_100` for proper table population
  - **Simplified variant layout** when prices are identical:
    - `Variant | MOQ | Price Ea @ MOQ | Delivery`
    - Shows variant name, MOQ value, single price, and delivery time
  - **Full variant layout** when prices differ (tiered pricing OR discount):
    - `Variant | Price @ MOQ | Price @ Qty 100 | Delivery`
    - Shows variant name, price at MOQ quantity, price at 100 units, and delivery time
  - **Single product mode** maintains original format:
    - `MOQ | Price @ MOQ | Price @ Qty 100 | Delivery`
  - Automatic detection compares `client_price` vs `client_price_at_100` (epsilon 0.01)
  - Debug output shows simplification decision and pricing consistency for troubleshooting

- ✅ **Delivery Time Preservation:**
  - Always reads delivery time from PowerPoint template (preserves original template value)
  - Works correctly for all modes: multi-row variants, single-row variants, and single products
  - Fallback to Google Sheets data only if template value is missing/empty
  - Fixed bug where single-row variant tables showed hardcoded "6-8 weeks" instead of template value

**Recent Improvements (2025-11-17 - v6.12):**
- ✅ **HTML Form Template Customization:**
  - Added comprehensive form template editor in Tab 2
  - Dropdown selector to choose which field to customize (8 options)
  - Default: Dropshipping Instructions (most commonly edited)
  - Customizable fields: form instructions, dropshipping instructions/placeholder, shipping/billing placeholders, customization placeholder, impact card options, payment options
  - Positioned before "Update Order Form" button for better workflow
  - All changes apply to generated HTML form in real-time
  - Centralized storage in `st.session_state.form_customizations` dictionary
  - Legacy compatibility maintained with `dropshipping_notes` for invoice generation
  - Fixed bug where client info wasn't appearing in HTML form (f-string interpolation issue)

**Recent Improvements (2025-11-17 - v6.11):**
- ✅ **Critical Bug Fix - Match Persistence:**
  - Fixed issue where confirmed matches were lost on rerun (dropping from 39 to 4)
  - Root cause: Match results were recalculated on every button click, clearing cache
  - Solution: Cache match_results in session state to persist across reruns
  - Matches now stay consistent throughout confirmation workflow

- ✅ **PowerPoint Section 4 UI Cleanup:**
  - Removed BETA label - feature is production-ready
  - Deleted Manual Match Override (133 lines of legacy code) - fully replaced by Match Review UI
  - Simplified Step 2 Impact Slides:
    - Clean summary message: "Impact slides found for: Partner X, Partner Y"
    - Customization controls hidden in optional expander (collapsed by default)
    - Removed messy inline Override/Apply/Cancel buttons
    - Simple dropdowns with auto-apply (no buttons needed)

- ✅ **Skip Product Feature:**
  - Added "Skip this product" button in Match Review UI when clicking "Change"
  - Available in both alternatives and search interfaces
  - Allows excluding products from PowerPoint without deleting from proposal

- ✅ **Code Cleanup:**
  - Removed debug output (🔍 DEBUG messages) from console
  - Kept minimal error logging for troubleshooting
  - Fixed missing Path import in Impact Slides section

**Recent Improvements (2025-11-17 - v6.10):**
- ✅ **Unified Match Review Table:**
  - Combined exact, fuzzy, and poor matches into single table (70-80% less scrolling)
  - Smart sorting: "needs review" items first, sorted by confidence (lowest first)
  - Clear status indicators: "Review" vs "Done"
  - Source column shows match origin: "Previously Confirmed", "Exact Match", "Auto-match", etc.
  - Simplified button logic:
    - **"Ready to use" products**: Only "Change" button
    - **"Need confirmation" products**: "Confirm" + "Change" buttons
  - All confirmations auto-save to Google Sheets for future sessions
  - Match summary shows clear breakdown: "X ready to use" vs "Y need your confirmation"

**Recent Improvements (2025-11-17 - v6.9):**
- ✅ **Match Memory System (Cloud-Persistent):**
  - Confirmed product-to-slide matches are now automatically saved to Google Sheets
  - When user confirms a fuzzy match, it's remembered for future sessions
  - Next PowerPoint generation with same products automatically uses confirmed matches (no re-confirmation needed)
  - Dataset-specific storage (demo matches ≠ real matches)
  - New module: [src/match_memory.py](src/match_memory.py) with Google Sheets backend
  - New spreadsheet: `saved_matches` (same location as saved_proposals/saved_orders)
  - Management UI in Tab 1: View/delete confirmed matches by dataset
  - Test script: [scripts/test_match_memory.py](scripts/test_match_memory.py)
  - Matching priority order: (1) Confirmed matches → (2) Manual overrides → (3) Fuzzy matching

**Recent Improvements (2025-11-11 - v6.8):**
- ✅ **Units per Package Column (Multi-Unit Product Support):**
  - Added support for "Units per Package" column in Google Sheets (case-sensitive: lowercase "per")
  - Automatically normalizes package costs to per-unit costs for accurate pricing
  - Fixes pricing issue for partners that sell in packages (e.g., Homeless Garden Project 6-packs)
  - Example: Partner charges $48 for 6-pack, MSRP is $12/unit → Normalizes to $8/unit cost, 50% markup
  - Default value: 1 (no change for most products)
  - Handles string or numeric values from Google Sheets (auto-converts to float)
  - Updated `get_unit_price_new_system()` in `src/pricing_engine.py` with string conversion
  - MSRP markup calculations now work correctly for package products
  - Edge cases handled: empty values, invalid values, missing column all default to 1

**Recent Improvements (2025-11-10 - v6.7):**
- ✅ **MSRP Pricing in Order Stage:**
  - Added "Use MSRP pricing" checkbox in Tab 3 (Order & Client Info) manual product selection
  - Defaults to checked - MSRP pricing applied automatically when adding products
  - Same behavior as Tab 1 proposal stage
  - Products with MSRP have markup auto-calculated to match MSRP
  - Products without MSRP use 100% markup
  - Markup still manually editable after adding
- ✅ **Date Serialization Fix:**
  - Fixed JSON serialization error when saving orders with date fields
  - Added helper functions to convert dates to/from ISO strings
  - Handles datetime.date and datetime.datetime objects recursively
- ✅ **Saved Orders Feature (Cloud-Persistent):**
  - Save orders with custom names across sessions
  - Optional creator name/email tracking
  - Load previously saved orders with all settings, products, and client info preserved
  - Delete unwanted orders with confirmation dialog
  - Duplicate name detection with automatic versioning (v2, v3, etc.)
  - Dataset mismatch warnings when loading cross-dataset orders
  - Google Sheets backend for cloud persistence and multi-user access
  - New module: [src/order_manager.py](src/order_manager.py)
  - Test script: [scripts/test_saved_orders.py](scripts/test_saved_orders.py)
  - Stored in: data/master/saved_orders spreadsheet
  - UI: Collapsible expander in Tab 3 (Order & Client Info), always visible at top

**Recent Improvements (2025-11-10 - v6.6):**
- ✅ **Saved Proposals Feature (Cloud-Persistent):**
  - Save proposals with custom names across sessions
  - Optional creator name/email tracking
  - Load previously saved proposals with all settings preserved
  - Delete unwanted proposals with confirmation dialog
  - Duplicate name detection with automatic versioning (v2, v3, etc.)
  - Dataset mismatch warnings when loading cross-dataset proposals
  - Google Sheets backend for cloud persistence and multi-user access
  - New module: [src/proposal_manager.py](src/proposal_manager.py)
  - Test script: [scripts/test_saved_proposals.py](scripts/test_saved_proposals.py)
  - Stored in: data/master/saved_proposals spreadsheet
  - UI: Collapsible expander in Tab 1, Section 2 (Saved Proposals)

**Recent Improvements (2025-11-10 - v6.5):**
- ✅ **MSRP Pricing Checkbox (Improved UX):**
  - Converted "Set All Prices to MSRP" button → "Use MSRP pricing when available" checkbox
  - **Defaults to CHECKED** - MSRP pricing applied automatically when products are added
  - Applies to both individual "Add to Proposal" and "Bulk Add" actions
  - Works at add-time (not retroactive) - more intuitive user experience
  - Smart calculation: markup % = ((MSRP / cost) - 1) × 100
  - Products without MSRP automatically use 100% markup
  - Edge case: MSRP below cost → 0% markup (break-even)
  - Markup still manually editable in product table after adding
  - Helper function: `calculate_msrp_markup()` for consistent calculation
- ✅ **Enhanced Products in Proposal Table:**
  - Added "PBP Cost" column showing base cost at quantity 100
  - Added "Client Price" column showing final price (cost + markup)
  - New layout: Product | PBP Cost | Markup % | Client Price | MSRP | Remove
  - Real-time client price updates when markup % is changed
  - Better visibility into pricing structure and profit margins

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
- ✅ Discount options (Non-profit preset 5% + custom discounts)
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
