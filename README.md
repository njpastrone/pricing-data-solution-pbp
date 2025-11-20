# Peace by Piece International - Order Management System

A Python/Streamlit application for creating proposals, managing orders, and generating invoices for artisan products.

**Current Status:** ✅ **IN PRODUCTION** - https://pricing-data-solution-pbp.onrender.com
**Version:** 6.18 - Codebase Cleanup & Code Clarity Improvements
**Data Status:** Partial partner data loaded (collecting remaining partners)

---

## 🚀 Quick Start

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

## 📁 Project Structure

```
pricing-data-solution-pbp/
├── app.py                      # Main application (PRODUCTION)
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Project rules & context
├── README.md                   # This file
│
├── .streamlit/
│   └── secrets.toml           # Google service account credentials (SECRET)
│
├── docs/                       # Documentation
│   ├── planning/              # Core project documentation
│   │   ├── PLANNING.md        # Project requirements & goals
│   │   ├── RESTRUCTURE_CONTEXT.md # Data structure reference
│   │   ├── METHODOLOGY_LOGIC.md   # Pricing calculations & business rules
│   │   └── INVOICE_AND_PROPOSAL_SPEC.md # Invoice/PO format
│   ├── powerpoint/            # PowerPoint automation documentation
│   │   ├── PHASE_2_COMPLETION_SUMMARY.md # Production-ready summary
│   │   └── PHASE_1_COMPLETION_SUMMARY.md # Technical deep dive
│   ├── archive/               # Historical documentation (preserved for reference)
│   │   ├── powerpoint-planning/ # PowerPoint planning docs (14 files)
│   │   └── tab2-improvements/   # UI redesign docs (9 files)
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   ├── SCROLL_PRESERVATION_PATTERN.md # Scroll preservation implementation
│   └── SESSION_STATE_AUDIT.md # Session state management
│
├── src/                        # Modular code (10 modules, ~4,918 lines)
│   ├── data_loader.py         # Google Sheets data loading
│   ├── helpers.py             # Utility functions
│   ├── pricing_engine.py      # Pricing calculations
│   ├── slide_matcher.py       # PowerPoint slide matching
│   ├── pptx_generator.py      # PowerPoint generation
│   ├── template_loader.py     # Cloud-based template loading
│   ├── match_manager.py       # Manual match storage (JSON)
│   ├── match_memory.py        # Confirmed match storage (Google Sheets)
│   ├── proposal_manager.py    # Save/load/delete proposals
│   └── order_manager.py       # Save/load/delete orders
│
├── scripts/                    # Essential utility scripts (6 files)
│   ├── test_connection.py     # Google Sheets API test (ESSENTIAL)
│   ├── investigate_data.py    # Data debugging tool
│   ├── test_saved_proposals.py # Test proposals feature
│   ├── test_saved_orders.py   # Test orders feature
│   ├── test_units_per_package.py # Test multi-unit products
│   └── test_match_memory.py   # Test match memory feature
│
└── backups/                    # Reference backup (1 file)
    └── app_before_modular_refactor_20251027.py  # Pre-modular structure
```

---

## 🎯 Features

### 4-Tab Workflow

#### Tab 1: Proposal Generator (for prospective clients)
- **Product Filtering:** Filter by price range, partner, country of origin
- **Product Catalog:** Browse all products with detailed specifications
- **Bulk Actions:** Add all products from selected partners at once
- **Proposal Configuration:** Set quantity, markup %, MSRP pricing (auto-calculated)
- **Saved Proposals:** Save and load proposals across sessions (cloud-persistent)
- **MOQ-Based Pricing Tables:** Automatic minimum order quantity calculations
- **PowerPoint Generation (v6.13):**
  - Automated slide matching and customized presentations
  - **Multi-variant product support:** Consolidates product variants (sizes/flavors) intelligently
  - **Smart pricing detection:** Automatically detects if variants have consistent pricing
  - **Conditional display options:** Simple single-row tables for consistent pricing, multi-row for variable pricing
  - **Price transparency:** Shows MOQ and price for each variant before generation
  - **Dynamic table layouts:** Adapts table format based on pricing (MOQ column vs Price @ 100 column)
- **CSV Downloads:** Export proposal tables

#### Tab 2: Client Order Form Generator
- **Order Details:** Pre-fill client information (type, company, contact, email)
- **Form Template Customization:** Edit any template text with dropdown selector
  - 8 customizable fields (instructions, dropshipping, placeholders, options)
  - Real-time updates to generated form
- **Professional HTML Forms:** Email-ready order forms with styled tables
- **Multiple Formats:** Download as HTML, TXT, or CSV

#### Tab 3: Order & Client Info (main workflow)
- **Saved Orders:** Save and load orders across sessions (cloud-persistent)
- **3 Entry Points:**
  - Option A: Import completed HTML order forms (recommended)
  - Option B: Import products from Tab 1 proposals
  - Option C: Manual product selection with MSRP pricing
- **Multi-Product Ordering:** Add multiple products with add-to-cart pattern
- **Per-Product Markup:** Configure individual markup percentages
- **Tiered & Flat-Rate Pricing:** Flexible pricing models per product
- **Customization Options:** Setup fees + per-unit costs for custom branding
- **Order-Level Settings:** Shipping, tariffs, discounts, custom line items
- **Order Notes:** 5 categories (kitting, client requests, samples, artwork, general)

#### Tab 4: Execution & Accounting
- **Order Validation:** Completeness check with warnings
- **Editable Order Information:** Review and complete missing fields
- **4-Table Invoice/PO Format:** Bookkeeper-standardized template
  - Client/Company Information
  - Partners + Point of Contacts
  - Order Details
  - Invoice and PO Item Details
- **Dual Export Options:** CSV (bookkeeper) and HTML (client-facing)

### Formula

**Single Product:**
```
Product Total = (Base Price × Quantity) + Art Setup + Label Costs + Markup

Where:
- Markup = Base Price × Quantity × (Markup % / 100)
```

**Multi-Product Order:**
```
Total Order = Sum(All Product Totals) - Discount + Shipping + Tariff

Where:
- Discount applies to products subtotal (not shipping/tariff)
- Shipping and Tariff apply once to entire order
- Optional marketing rounding applies to final total
- Each product has independent markup percentage
```

---

## 📊 Data Source

**Active Sheet:** `master_pricing_template_10_14` (Google Sheets)

**Structure:** 3-sheet workbook
- **Template** (header at row 6): Partner-product pricing data
- **Metadata**: Deliverable field definitions
- **Partner-Specific Info**: Partner configuration reference

**Key Fields:**
- Partner, Product/Service, Purchase Description
- Pricing Tiers (Y/N) flag
- Flexible tier definitions (PBP Cost: Tier 1-6 OR PBP Cost (No Tiers))
- Customization Setup Fee, Customization Cost per Unit
- Tariff Estimate, Shipping

See [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) for complete details.

---

## 🔧 Configuration

### Pricing Tiers (Soft-Coded)
Edit tier ranges in `app.py` → `get_price_for_quantity()` function:

```python
tier_columns = [
    {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
    {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
    # ... more tiers
]
```

### Label Costs (Jaggery Partner)
- Label Art Setup: $70 (one-time)
- Label Unit Cost: From product data
- Label Minimum: 100 labels

Edit in `app.py` → `calculate_additional_costs()` function.

---

## 📚 Documentation

**Essential Reading:**
- [CLAUDE.md](CLAUDE.md) - Project rules & development guidelines
- [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) - Current data structure
- [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) - Pricing calculations
- [docs/INVOICE_AND_PROPOSAL_SPEC.md](docs/INVOICE_AND_PROPOSAL_SPEC.md) - Invoice & proposal formats

**Planning:**
- [docs/PLANNING.md](docs/PLANNING.md) - Project requirements
- [docs/CLIENT_QUESTIONS.md](docs/CLIENT_QUESTIONS.md) - Tracking open questions

---

## 🧪 Testing

### Manual Testing Checklist

**Product Selection & Customization:**
- [ ] Product selection dropdown works
- [ ] Quantity input validates minimum
- [ ] Tier selection matches quantity (e.g., 70 → 51-100 tier)
- [ ] Label checkbox adds correct costs
- [ ] Label minimum enforced (100 labels)
- [ ] Art setup fee only shows when labels selected
- [ ] Markup applies to product price only
- [ ] Per-product markup can be set independently

**Multi-Product Order Management:**
- [ ] Add to Order button adds product to order
- [ ] Current Order section displays all added products
- [ ] Edit button repopulates form with product details
- [ ] Update button replaces edited product in order
- [ ] Remove button deletes product from order
- [ ] Clear Entire Order button clears all products
- [ ] Order persists across product additions (session state)

**Order-Level Settings:**
- [ ] Shipping input only active when products in order
- [ ] Tariff input only active when products in order
- [ ] Shipping/tariff apply once to entire order

**Calculations & Display:**
- [ ] Product totals calculate correctly
- [ ] Order total sums all products + shipping + tariff
- [ ] Per-product breakdowns show in Current Order
- [ ] Order Summary shows all products with totals
- [ ] Proposal displays multi-product details correctly
- [ ] Invoice displays multi-product line items correctly

### Test Cases
See [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) for detailed single-product and multi-product test cases.

---

## 🚢 Deployment

### Render (Current Deployment)
**Live URL:** https://pricing-data-solution-pbp.onrender.com

**Configuration:**
- **Instance Type:** Standard ($25/month)
- **RAM:** 2GB
- **CPU:** 1 core
- **Automatic Deployment:** Connected to GitHub (deploys on push to main)
- **Environment Variables:** Set in Render dashboard (GCP credentials)
- **Startup Command:** Defined in `start.sh`

**Template Storage:**
- 43MB PowerPoint template stored in Google Drive
- Downloaded on-demand (not bundled with app)
- Cached in session for performance

**Local Development:**
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with GCP credentials
4. Run: `streamlit run app.py`

---

## 🔮 Future Enhancements

### Multi-Partner Support
Currently built for Jaggery partner. Future versions will support multiple partners with:
- Different pricing tier structures
- Different tier ranges
- Different cost components
- Partner-specific configurations

See [docs/APP_UPDATE_PLAN.md](docs/APP_UPDATE_PLAN.md) for multi-partner architecture strategy.

---

## 🛠️ Common Tasks

**Refresh pricing data:** Menu → "Rerun" in the app

**Update credentials:** Edit `.streamlit/secrets.toml`

**Test connection:** `streamlit run scripts/test_connection.py`

**Debug data:** `streamlit run scripts/investigate_data.py`

---

## 📝 Development Guidelines

See [CLAUDE.md](CLAUDE.md) for complete development rules, including:
- Always use Python & Streamlit
- Write beginner-friendly code
- Take the simplest route
- Soft-code everything for easy editing
- Minimize codebase size
- Avoid code duplication

---

## 📄 License

Peace by Piece International - Internal Tool

---

**Last Updated:** 2025-11-20
**Version:** 6.18 (Codebase Cleanup & Code Clarity)

## 🆕 Recent Updates (v6.18 - 2025-11-20)

### Codebase Simplification & Code Clarity
Major cleanup and refactoring to improve maintainability and beginner-friendliness:

**Cleanup Results:**
- **Deleted:** ~13,649 lines of Python code (49% reduction)
- **Archived:** 23 documentation files (preserved in docs/archive/)
- **Size reduction:** 22MB saved (142MB → 120MB)
- **Current codebase:** ~14,138 lines of clean, focused code

**What Was Removed:**
- Deleted entire archive/ directory (22.5MB of deprecated jaggery_demo code)
- Consolidated backups (3 of 4 deleted, kept modular refactor reference)
- Removed 13 obsolete test scripts (kept 6 essential ones)
- Archived 23 completed planning docs (PowerPoint + Tab 2 UI redesign)

**Code Clarity Improvements:**
- Renamed `normalize_product_name()` → `normalize_for_storage()` in match_manager.py
- Fixed confusing duplicate function names (one returned uppercase, one lowercase)
- Removed unused imports in slide_matcher.py
- Updated function docstrings for self-documenting code
- Now fully beginner-friendly and clear

**Why This Matters:**
The codebase is now significantly easier to navigate, understand, and maintain. All deleted code was either deprecated, redundant (covered by git history), or testing completed features. Documentation was archived (not deleted) for reference. The app maintains 100% functionality with a much leaner footprint.

---

## Previous Updates (v6.17 - 2025-11-20)

### Render Deployment & Memory Optimization
Successfully deployed to production on Render with cloud-based template management:

**Deployment Infrastructure:**
- Deployed to Render Standard tier (2GB RAM, $25/month)
- Created `start.sh` for Render startup configuration
- Added environment variable support to `data_loader.py` for credentials
- Moved 43MB PowerPoint template to Google Drive (prevents bundling in deployment)

**New Module: template_loader.py**
- Cloud-based PowerPoint template management
- On-demand download from Google Drive
- Session-based caching for performance
- Supports both Google Drive and local fallback modes

**Memory Optimization Infrastructure (v6.16):**
- Added `USE_MEMORY_OPTIMIZATION` toggle (currently disabled)
- Lazy loading support with `use_cache=False` parameter
- Garbage collection after heavy operations in `pptx_generator.py`
- Optimization disabled after tier upgrade (caching provides better UX)
- Template downloads once and stays cached (no duplicate downloads)

**Branding:**
- Added peace dove icon (🕊️) to replace Streamlit crown
- Visible in browser tab and bookmarks

**Key Files:**
- `start.sh` - Render deployment configuration
- `src/template_loader.py` - Cloud template management
- Updated `src/data_loader.py` - Environment variable support
- Updated `app.py` - Memory optimization toggle

**Production URL:** https://pricing-data-solution-pbp.onrender.com

---

## Previous Updates (v6.15 - 2025-11-19)

### HTML Order Form Product Extraction
Complete automation of client order form import with product parsing:

**Key Features:**
- Automatically extracts product names from Order Details table in HTML forms
- Smart product matching: exact match first, then partial match
- Checkbox selection UI (same as Option B for consistency)
- Shows match type (Exact/Partial) and warns about unmatched products
- Adds products with default settings (quantity 1, 100% markup) ready for editing

**Benefits:**
- One-click import of both client info AND products from completed forms
- No more manual product entry after receiving client forms
- Intelligent matching catches variations in product names
- Clear visibility of which products matched and which didn't

**Workflow:**
1. Upload completed HTML order form (Tab 3, Option A)
2. Review extracted client info and products
3. Click "Import Client Information"
4. Select which matched products to add
5. Click "Add Selected Products to Order"
6. Edit quantities, markup, customization in Section 2

---

## Previous Updates (v6.14 - 2025-11-19)

### Toast Notifications for Better User Feedback
Improved user experience with toast notifications that appear in the bottom-right corner:

**Key Improvements:**
- Replaced static success messages with toast notifications for all product additions
- Notifications visible regardless of scroll position (major UX win)
- Auto-dismiss after 4 seconds (non-intrusive)
- Professional appearance without emoji icons

**Applied to:**
- Adding individual products to proposal (Tab 1)
- Bulk adding products to proposal (Tab 1)
- Importing products from proposal to order (Tab 3)
- Adding custom line items (Tab 3 & Tab 4)

**Why This Matters:**
Previously, success messages appeared at the top of sections and were invisible when users scrolled down in the product catalog. Now, users always see confirmation of their actions.

---

## Previous Updates (v6.13 - 2025-11-19)

### Multi-Variant Product Consolidation
Intelligent handling of product variants (different sizes/flavors) that map to the same PowerPoint slide:

**Smart Pricing Detection:**
- Automatically detects if variants have identical MOQ and pricing
- Shows visual indicators: ✅ Consistent Pricing or ⚠️ Variable Pricing
- Displays MOQ and price for each variant for transparency

**Conditional Display Options:**
- **Consistent Pricing:** Recommends single-row table (avoids redundant multi-row display)
- **Variable Pricing:** Recommends multi-row table (shows price differences clearly)
- User can still override automatic recommendations

**Dynamic Table Layouts:**
- **Single-row variant table:** `MOQ | Price Ea @ MOQ | Price @ Qty 100 | Delivery`
- **Multi-row variant table (simplified):** `Variant | MOQ | Price Ea @ MOQ | Delivery`
- **Multi-row variant table (full):** `Variant | Price @ MOQ | Price @ Qty 100 | Delivery`

**Examples:**
- **Honey Flavors (same price):** Single-row table, one price applies to all flavors
- **Beeswax Candles (different prices):** Multi-row table, shows each size with its price

**Technical Improvements:**
- New function: `check_pricing_consistency()` - Compares MOQ and price across variants
- Enhanced variant detection UI with pricing info displayed inline
- Delivery time preservation from PowerPoint template (fixes hardcoded fallback bug)
- Price @ Qty 100 calculation added to all pricing data
