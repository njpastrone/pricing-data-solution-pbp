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

**ALWAYS refer to [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) for the current data structure from master_pricing_template_10_14.**

**ALWAYS refer to [docs/PLANNING.md](docs/PLANNING.md) for project requirements, architecture decisions, and implementation plans before starting any work.**

**ALWAYS refer to [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) for pricing calculations, business rules, and partner-specific methodologies.**

**ALWAYS refer to [docs/INVOICE_REQUIREMENTS.md](docs/INVOICE_REQUIREMENTS.md) for invoice format specifications and required information.**

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

- **Frontend:** Streamlit (Python-based web app) with 3-tab structure
  - **Tab 1: Proposals** - Product catalog, filtering, proposal generation
  - **Tab 2: Order & Client Info** - Order management, client data collection
  - **Tab 3: Execution & Accounting** - Invoice/PO generation, bookkeeping
- **Data Source:** Google Sheets (master_pricing_template_10_14) with 3 sheets:
  - **Template**: Partner-product pricing data
  - **Metadata**: Deliverable field definitions
  - **Partner-Specific Info**: Partner configuration reference
- **Code Structure:** Modular with helper functions in `src/` directory
  - `src/data_loader.py` - Google Sheets data loading
  - `src/helpers.py` - Utility functions, conversions, validation
  - `src/pricing_engine.py` - Pricing calculations and quote generation
- **Authentication:** Google Cloud service account
- **Pricing Model:** Flexible tiered or flat-rate pricing per product
- **Workflow:**
  1. **Tab 1 (Proposals):** Browse products → Configure proposal → Download CSV/HTML client order form
  2. **Tab 2 (Orders):** Add products (import OR manual) → Edit each product inline (quantity, markup, customization) → Configure order settings → Collect client info
  3. **Tab 3 (Execution):** Review/edit order → Generate invoice & PO → Download for bookkeeping

## Current Features

### Tab 1: Proposals (for prospective clients)
- **Product Filtering:** Price range, partner, country of origin
- **Product Catalog:** Browse all products with detailed specifications
- **Proposal Configuration:** Quantity, markup %, customization options, MSRP comparison
- **MOQ-Based Pricing Tables:** Automatic minimum order quantity calculations
- **Copy Buttons:** Easy copy for Kitting Pricing & Terms sections
- **CSV Downloads:** Export proposal tables and client order forms
- **HTML Client Order Form:** Professional, email-ready order form with:
  - Styled table format (light/dark mode compatible)
  - Clear instructional prompts for clients
  - Pre-filled product names and quantities
  - Multiple choice delete-to-select format
  - Download as HTML, TXT, or CSV
- **Terms & Conditions:** Customizable terms loaded from config file

### Tab 2: Order & Client Info (main workflow)
- **Simplified Product Addition:** One-click add from dropdown (defaults: qty=1, markup=100%)
- **Proposal-to-Order Import:** Import all or individual products from Tab 1 (preserves quantity & markup only)
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
- **Section Flow:** 1. Add Products → 2. Configure Each Product → 3. Order Settings → 4. Notes → 5. Summary

### Tab 3: Execution & Accounting
- **Order Summary Preview:** Quick overview of client, products, and total quote
- **Order Validation:** Completeness check with warnings for missing fields
- **Editable Summary:** Quick edits for shipping, discounts, credit card fees
- **4-Table Invoice/PO Format:** Structured to match bookkeeper template requirements:
  - **Table 1: Client/Company Information** - Company name, contact, billing/shipping addresses, PO number
  - **Table 2: Partners + Point of Contacts** - All partners with POC details auto-populated from Google Sheets
  - **Table 3: Order Details** - Client in-hands date, ship method, payment terms/method, submission details
  - **Table 4: Invoice and PO Item Details** - Line items with partner, specs, quantity, in-hands date, cost, cost verification, sell price
- **Line Item Details:** Each product shows base cost, customization (setup/per-unit), and tariffs as separate rows
- **Notes Section:** Displays all order notes (kitting specs, client requests, samples, artwork, general)
- **CSV Export:** Download complete invoice/PO with all tables for bookkeeper submission

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
├── docs/                       # Documentation
│   ├── PLANNING.md            # Project requirements & goals
│   ├── DATA_STRUCTURE.md      # jaggery_demo data structure
│   ├── METHODOLOGY_LOGIC.md   # Pricing calculations & business rules
│   ├── INVOICE_REQUIREMENTS.md # Invoice/PO format specification
│   ├── UI_RESTRUCTURE_PLAN.md # Original UI restructure plan
│   ├── UI_RESTRUCTURE_PROGRESS.md # Implementation progress (COMPLETE)
│   ├── UI_POLISH_PLAN.md      # Phase 5 implementation plan (COMPLETE)
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   └── MIGRATION_SUMMARY.md   # Migration history
│
├── src/                        # Modular code (extracted from app.py)
│   ├── data_loader.py         # Google Sheets data loading
│   ├── helpers.py             # Utility functions, conversions, validation
│   └── pricing_engine.py      # Pricing calculations and quote generation
│
├── templates/                  # Reference templates
│   ├── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md
│   └── TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf
│
├── scripts/                    # Utility scripts
│   ├── test_connection.py     # Test Google Sheets connection
│   ├── check_jaggery_demo.py  # Investigate jaggery_demo (Python)
│   └── investigate_jaggery_demo.py  # Investigate tool (Streamlit)
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

**Version:** 2.6 - Tab 3 Restructure with Bookkeeper Template Format

**Last Updated:** 2025-10-30

**Recent Improvements:**
- ✅ **Tab 3 4-Table Format:** Restructured Invoice/PO section to match bookkeeper template exactly
  - Table 1: Client/Company Information (name, contact, addresses, PO number)
  - Table 2: Partners + Point of Contacts (auto-populated from Google Sheets)
  - Table 3: Order Details (dates, shipping, payment terms/method)
  - Table 4: Invoice and PO Item Details (line items with cost verification)
- ✅ **Universal Customization:** All products now show customization options (defaults to $0 if no spreadsheet data)
- ✅ **Detailed Order Summary:** Line-item breakdown showing base cost, markup, and customization separately
- ✅ **Tab 2 Restructure:** Complete redesign following "add first, configure after" pattern
- ✅ **Simplified Product Addition:** One-click add with sensible defaults (qty=1, markup=100%)
- ✅ **Inline Editing:** All product settings always visible in Current Order section
- ✅ **Real-time Pricing:** Instant calculation updates as you edit quantity, markup, customization
- ✅ **Quantity Warning:** Visual warning when quantity=1 to prevent accidental single-unit orders
- ✅ **Streamlined Import:** Import from proposals preserves only quantity and markup (customization reset)
- ✅ **Cleaner Navigation:** Logical section flow (1. Add Products → 2. Configure → 3. Settings → 4. Notes → 5. Summary)

**Features Implemented:**
- ✅ **3-Tab Workflow:** Proposals → Order & Client Info → Execution & Accounting
- ✅ **Proposal System:** Product filtering, catalog browser, MOQ-based pricing tables
- ✅ **HTML Client Order Form:** Professional table format with clear instructions
- ✅ **Copy Buttons:** Easy copy for Kitting Pricing & Terms sections
- ✅ **Proposal-to-Order Connection:** Import all products or select individually
- ✅ **Next Steps Guidance:** Dynamic messaging in Tab 1 guiding to Tab 2
- ✅ **Success Banners:** Visual feedback on available proposal products
- ✅ **CSV Downloads:** Export proposals and client order forms
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
- ✅ Bookkeeper-standardized Invoice & PO template
- ✅ Editable order summary in Tab 3 (quick adjustments before invoice generation)
- ✅ Partner contact auto-extraction from Google Sheets
- ✅ Comprehensive order notes system (5 categories)
- ✅ Field validation with user warnings
- ✅ Standardized payment/shipping dropdowns
- ✅ **NEW: Date tracking for order/cost submission**

**Testing Status:**
- ✅ Data loads from master_pricing_template_10_14
- ✅ Tier parsing logic verified (T1-T6 ranges)
- ✅ Tier selection working correctly for various quantities
- ✅ New column structure compatible with app
- ✅ Partner filtering functional

**Production Status:** ✅ Ready for testing with real partners

---

## Future Enhancements

- Multi-partner support (different tier structures per partner)
- Partner-specific configuration file
- Auto-detect tier ranges from column headers
- Remove debug expanders (optional)
- Admin UI for managing partner configurations
