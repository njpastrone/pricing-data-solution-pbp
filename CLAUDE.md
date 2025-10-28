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
  1. **Tab 1 (Proposals):** Browse products → Configure proposal → Download CSV
  2. **Tab 2 (Orders):** Import from proposal OR add products manually → Collect client info → Configure order settings
  3. **Tab 3 (Execution):** Review/edit order → Generate invoice & PO → Download for bookkeeping

## Current Features

### Tab 1: Proposals (for prospective clients)
- **Product Filtering:** Price range, partner, country of origin
- **Product Catalog:** Browse all products with detailed specifications
- **Proposal Configuration:** Quantity, markup %, customization options, MSRP comparison
- **MOQ-Based Pricing Tables:** Automatic minimum order quantity calculations
- **CSV Downloads:** Export proposal tables and client order forms
- **Terms & Conditions:** Customizable terms loaded from config file

### Tab 2: Order & Client Info (main workflow)
- **Proposal-to-Order Connection:** Import products from Tab 1 proposals
- **Multi-Partner Support:** Select from multiple vendors/suppliers
- **Flexible Pricing:** Both tiered and flat-rate products supported
- **Dynamic Tier Parsing:** Tier ranges defined in data (not hardcoded)
- **Customization Options:** Setup fees + per-unit costs for custom branding
- **Smart Calculations:** Markup applies to product price only
- **Discount Options:** NGO preset (5%) + custom discounts
- **Marketing Rounding:** Charm pricing ($60 → $59)
- **Custom Line Items:** Add unique services/customizations
- **Order Notes:** 5 categories (kitting, client requests, samples, artwork, general)

### Tab 3: Execution & Accounting
- **Order Validation:** Completeness check with warnings
- **Editable Summary:** Quick edits for shipping, discounts, credit card fees
- **Invoice Generation:** Bookkeeper-standardized format
- **Purchase Order Generation:** Partner-specific PO with contact auto-extraction
- **CSV Export:** Download order data for accounting systems

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

**Version:** 4.0 - Complete UI Restructure with Proposal-to-Order Integration

**Last Updated:** 2025-10-28

**UI Restructure Complete:** All 5 phases implemented and tested
- ✅ Phase 1: 3-tab structure created
- ✅ Phase 2: Proposals extracted to Tab 1
- ✅ Phase 3: Invoice/PO moved to Tab 3
- ✅ Phase 4: Sidebar enhancements (progress indicator, clear all)
- ✅ Phase 5: UI polish (proposal-to-order connection, CSV downloads, editable summary)

**Features Implemented:**
- ✅ **3-Tab Workflow:** Proposals → Order & Client Info → Execution & Accounting
- ✅ **Proposal System:** Product filtering, catalog browser, MOQ-based pricing tables
- ✅ **Proposal-to-Order Connection:** Import products from proposals to orders
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
- ✅ **Editable order summary in Tab 3** (quick adjustments before invoice generation)
- ✅ **NEW: Partner contact auto-extraction from Google Sheets**
- ✅ **NEW: Comprehensive order notes system (5 categories)**
- ✅ **NEW: Field validation with user warnings**
- ✅ **NEW: Standardized payment/shipping dropdowns**
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
