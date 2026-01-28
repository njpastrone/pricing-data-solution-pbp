# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### Added
- **Volume Order Discount (5%):** New discount option available in Tab 1 (Proposal Generator) and Tab 3 (Order & Client Info)
  - Provides clear distinction between non-profit discounts and volume-based discounts
  - Four discount options now available: None, Non-profit (5%), Volume Order (5%), Custom
  - Better tracking and reporting with distinct labels in order summaries
  - Works identically to Non-profit discount (5% applied to products, not customization)
  - Backward compatible with existing saved proposals and orders
  - Display updates in proposal tables show "5% Volume Order discount" label
  - "Discount Quoted to Client" warning in Tab 3 shows Volume Order discount when applicable

### Fixed
- **PowerPoint Discount Labels & Prices:** PowerPoint proposal tables now correctly display discount labels AND apply discounts to prices
  - **Issue 1 - Headers:** Fixed headers showing "Price @ Qty 100" instead of discount labels
    - Now shows "Client Price (5% Non-profit discount)" or "Client Price (5% Volume Order discount)" when applicable
    - Applies to all table formats: 2×3, 2×4, 3×4, and multi-row variant tables
    - Updated `update_pricing_table()` to accept `discount_percent` and `discount_type` parameters
    - Updated all 3 presentation generation functions to pass discount information through
  - **Issue 2 - Prices:** Fixed prices not being discounted due to settings_snapshot override
    - Settings snapshot was overriding discount_percent with old value (0%) from when products were added
    - Now uses current discount setting from parameter instead of snapshot
    - Discount is treated as global proposal setting (can be changed after adding products)
    - Rounding settings still use snapshot (per-product configuration)
  - **Result:** Tab 1 preview tables and PowerPoint exports now match perfectly (headers AND prices)

---

## [8.0.0] - 2026-01-22

### MAJOR SCHEMA TRANSITION (33 → 44 columns)

This is a major release with a complete schema overhaul introducing sophisticated pricing logic and improved data structure.

#### 🔥 Breaking Changes
- **New Schema:** Transitioned from 33 columns to 44 columns (+11 new fields)
- **Pricing Logic:** Replaced simple markup system with 3 distinct pricing methods
- **Column Renames:** Several columns renamed for clarity (see schema_reference.md)
- **Tier Consolidation:** Combined "PBP Cost (No Tiers)" and "Tier 1" into single column "PBP Cost (No Tiers/Tier 1)"
- **Description Fields:** Separated into Billing Description (invoices), Purchase Description (POs), and Marketing Description (proposals)

#### ✨ New Features

**Three Pricing Methods:**
1. **"MSRP + % of cost"** - Vendor MSRP plus shipping recovery (calculated as: Vendor MSRP + Shipping Add-On % × per-item cost)
2. **"MSRP capped – ship absorbed"** - Use vendor MSRP exactly, shipping costs absorbed by PBP
3. **"Standard markup"** - Traditional cost × (1 + markup%), with diagnostic markup support or 100% default

**Pricing Engine (Phase 1):**
- New `calculate_pbp_msrp()` function with method-specific logic
- Cost basis normalization: explicit "Per Item" vs "Per Package" handling
- Hybrid validation: compares calculated prices against spreadsheet values
- Diagnostic markup calculations for transparency (vendor markup and PBP markup)
- Empty field defaults (100% markup fallback, "Per Item" cost basis default)
- Manual override checkbox for all pricing methods (flexible pricing control)

**UI Updates (Phases 2-4):**
- **Tab 1 (Proposal Generator):**
  - Pricing method column in "Products in Proposal" table
  - Shows: Product → PBP Cost → Vendor MSRP → Pricing Method → PBP MSRP → Markup %
  - Rounding indicators when prices adjusted (shows original unrounded price)
  - Manual override checkbox for custom pricing
  - Pricing notes display (expandable, shows method-specific calculations)
  - Validation warnings for price discrepancies (non-blocking, informational)
  - $0.50 rounding integration (default enabled)
  - MSRP pricing checkbox uses new calculation logic

- **Tab 3 (Order & Client Info):**
  - All 4 entry pathways updated (Google Form, HTML, Proposal import, Manual add)
  - Clean 6-column pricing table matching Tab 1 format
  - Pricing method preserved across imports
  - Manual override checkbox
  - Rounding applied by default with indicators
  - Real-time price recalculation with new methods
  - Quantity & Pricing section redesigned for clarity

- **Tab 4 (Execution & Accounting):**
  - Description field hierarchy for invoices: Billing → Marketing → Product Name
  - Description field hierarchy for POs: Purchase → Billing → Product Name
  - Split "ITEMS + SPECS" into two columns: "DESCRIPTION (Invoice)" and "DESCRIPTION (PO)"
  - Separate invoice and PO descriptions in HTML/CSV exports
  - Clean professional output (pricing notes hidden on invoices)
  - Pricing consistency with Tab 3 using new methods

**New Schema Columns:**
- `Pricing Logic` (column 23) - Defines which pricing method to use (3 allowed values)
- `Cost Basis (Per Item/Per Package)` (column 20) - Explicit cost type declaration
- `Shipping Add-On % (of Cost)` (column 24) - Percentage for "MSRP + % of cost" method
- `PBP Cost (Per-Unit, No Tiers, Calculated)` (column 22) - Normalized per-item cost (calculated)
- `PBP MSRP (Per-Unit, No Tiers, Calculated)` (column 29) - **AUTHORITATIVE PRICE** (calculated)
- `Vendor Markup (No Tiers, Calculated)` (column 27) - Diagnostic vendor markup % (calculated)
- `PBP Markup (Vendor+Add-On, No Tiers)` (column 28) - Diagnostic PBP markup % (calculated)
- `PBP MSRP (Website)` (column 30) - Website-displayed MSRP (reference)
- `Pricing Notes` (column 25) - Pricing assumptions and exceptions (informational)
- `Billing Description (to Client)` (column 6) - Client-facing invoice description
- `Purchase Description (to Partner)` (column 5) - Partner-facing PO description (renamed)
- `Marketing Description (Website)` (column 7) - Website/proposal description (renamed)
- `Data Collection Notes` (column 44) - Data quality and audit trail (governance)

**Backward Compatibility:**
- `get_column_value()` helper supports old and new column names seamlessly
- Graceful handling of empty fields with sensible defaults
- Works with spreadsheets missing new columns (falls back to old names)
- Quiet validation (informs user of missing data, doesn't block functionality)

#### 🧪 Testing (Phase 5)
- Comprehensive test suite created (5 new test scripts)
- All 3 pricing methods validated with real dataset (51 products, 44 columns)
- Pricing method distribution verified: MSRP + % (47.1%), MSRP capped (37.3%), Standard markup (15.7%)
- Empty field handling tested (defaults work correctly)
- Description fallback logic verified (3-level hierarchy per use case)
- Full workflow testing (Tab 1 → Tab 3 → Tab 4)
- Edge case testing (MSRP below cost, missing fields, invalid values)
- Regression testing (existing features preserved - variants, saved proposals/orders)
- Backward compatibility confirmed (old demo dataset still works)
- **Test Results:** 100% success rate, no critical errors, production-ready

**Bugs Fixed During Testing:**
- Fixed pandas NA handling in `get_column_value()` (TypeError with pd.isna())
- Fixed MSRP string conversion in `calculate_pbp_msrp()` (TypeError with clean_price())
- Fixed header row reading for real dataset (row 7 vs row 6)

#### 📚 Documentation (Phase 6)
- Created `schema_update_jan_2026/` workspace with:
  - `MASTER_TRACKING.md` - Complete context, decisions, and implementation tracking
  - 6 phase-specific implementation guides (PHASE1-6_*.md)
  - `RESUME_PROMPTS.md` - Context recovery for new sessions
  - `PHASE5_COMPLETION_SUMMARY.md` - Complete testing results and bug fixes
- Updated `schema_reference.md` - Complete 44-column schema documentation
- Updated `METHODOLOGY_LOGIC.md` - Added new pricing methods section (detailed)
- Updated all README and CLAUDE.md references
- Created deployment checklist for production readiness

#### 🔧 Bug Fixes
- Fixed session state management for new pricing fields
- Fixed manual override persistence across tabs
- Fixed description field fallback logic (3-level hierarchy working correctly)
- Fixed validation warning display conditions (non-blocking, informational only)
- Fixed pricing calculation consistency across all tabs
- Fixed false "price changed" warnings when importing from proposal (rounding mismatch)
- Fixed rounding integration in PowerPoint generation

#### 💡 Technical Improvements
- Modular pricing engine architecture (clean separation of concerns)
- Clear separation of concerns (calculation vs display vs validation)
- Consistent function signatures across tabs (calculate_pbp_msrp used everywhere)
- Improved error handling and validation (graceful degradation)
- Better user feedback (pricing notes, validation warnings, rounding indicators)
- Hybrid validation approach (read spreadsheet + calculate for comparison)
- Cost normalization with explicit basis checks ("Per Item" vs "Per Package")

#### 🚀 Deployment Notes
- Full schema migration completed across all phases (1-6)
- All phases tested and validated (comprehensive test coverage)
- Production-ready as of 2026-01-22
- No backward compatibility issues (clean migration with fallbacks)
- Real dataset verified (51 products, 44 columns, all pricing methods working)
- Demo dataset still works (backward compatibility confirmed)

#### 📖 Documentation References
- **Schema Definition:** `schema_reference.md` (44 columns documented)
- **Transition Context:** `schema_update_jan_2026/MASTER_TRACKING.md` (complete tracking)
- **Implementation Guides:** `schema_update_jan_2026/PHASE[1-6]_*.md` (step-by-step)
- **Pricing Methodology:** `docs/planning/METHODOLOGY_LOGIC.md` (new methods section)
- **Testing Results:** `schema_update_jan_2026/PHASE5_COMPLETION_SUMMARY.md`
- **Deployment Checklist:** `schema_update_jan_2026/DEPLOYMENT_CHECKLIST.md`

#### ⚠️ Migration Notes for Users
- New spreadsheet format required (44 columns - see schema_reference.md)
- Products without pricing logic default to "Standard markup" (100%)
- MSRP-based products calculate markup automatically from vendor MSRP
- Manual override checkbox available on all products for flexible pricing
- Validation warnings inform of price discrepancies (non-blocking, can be ignored)
- Empty fields handled gracefully with sensible defaults
- Old spreadsheets still work (backward compatibility via get_column_value)

#### 🎉 Implementation Statistics
- **Total Phases:** 6 (all complete)
- **Files Modified:** 3 core files (app.py, src/helpers.py, src/pricing_engine.py)
- **Lines Changed:** ~1,000+ lines (new pricing logic, UI updates, validation)
- **Test Scripts Created:** 5 comprehensive test files
- **Documentation Created:** 8 new markdown files
- **Test Coverage:** 100% of critical pricing paths
- **Production Status:** ✅ Ready for deployment

---

## [7.6.0] - 2026-01-20

### Added
- **Google Forms Integration (Tab 2 → Tab 3)** - Modern workflow for client order collection
  - **Tab 2: Form Generation**
    - Pre-fill Google Forms with proposal products and client info
    - Clean UI: Select products from proposal, adjust quantities, generate URL
    - One-click URL generation with copy button and preview link
    - Supports up to 10 product lines per form
  - **Tab 3: Response Import**
    - Load recent form responses from Google Sheets
    - Preview before importing: client info, products, shipping, payment details
    - One-click import populates all client fields and adds products to order
    - Automatic product matching (exact match, case-insensitive)
    - Default settings: quantities from form, 100% markup
    - Tracking columns prevent duplicate imports (Imported?, Order ID, Import Date)
  - **New modules:**
    - `src/forms_config.py` - Form URLs, entry IDs, column mappings (249 lines)
    - `src/forms_helper.py` - URL generation, response parsing, import tracking (~350 lines)
  - **Documentation:**
    - `docs/planning/GOOGLE_FORMS_IMPLEMENTATION_COMPLETE.md` - Complete feature guide with testing checklist
    - `docs/planning/GOOGLE_FORM_CREATION_GUIDE.md` - Step-by-step form creation instructions
  - **Benefits:**
    - Replaces "finnicky HTML" workflow with professional Google Forms
    - 50-70% faster than HTML workflow (45-60 seconds vs 2-3 minutes)
    - Better client experience and data quality
    - Pure Python implementation (no Apps Script)
  - **Bug fixes during testing:**
    - Fixed nested expanders UI issue
    - Fixed product import with proper dict conversion and pricing structure
    - Fixed client_info field mapping (all required fields)
    - Fixed response column mappings (asterisks for required fields)
    - Fixed date parsing (string to date object)
    - Fixed per-unit pricing calculations

- **Custom Product Creation** - Create unique products not in the catalog (Tab 3)
  - **Quick add form:** 3 fields only (Product Name, Partner, Base Cost/Unit)
  - **Partner selection:** Choose real partner for POC tracking, or "Custom/Other"
  - **Inline configuration:** After adding, configure quantity, markup, customization using same controls as catalog products
  - **Country & Tariff fields:** Set country of origin (Made In / Ships From) and tariff estimate for custom products
  - **Full integration:** Works with all existing features (discounts, marketing rounding, kitting, etc.)
  - **Profit visibility:** Base cost + markup % = client price (transparent pricing)
  - **Invoice integration:** Partner POC auto-populates when real partner selected
  - **UX consistency:** Matches catalog product add-to-order flow (add quick, configure inline)
  - **Legacy support:** Old custom line items still work, shown with "(Legacy)" label

### 🚧 In Progress (Week 2 Sprint - Jan 2026)
- Customization Add-On feature for product editing
- Execution form updates (New/Existing checkbox + MM/DD/YY dates)
- Tab 3 Option A (HTML import): Parse variants from client order forms

---

## [7.5.1] - 2026-01-20

### Changed
- **Order Notes reorganization (Breaking Change)** - Restructured from 5 topic-based categories to 4 audience-based categories
  - **Old structure (5 categories):** Kitting Specs, Client Requests, Samples Required, Artwork Details, General Notes
  - **New structure (4 categories):**
    - Internal Notes (For PBP Team) - Team coordination, workflow notes, internal reminders
    - Internal Notes (For Bookkeeping) - Accounting, billing, payment tracking
    - External Notes (For Partners/POs) - Instructions for partners, PO details, shipping requirements
    - External Notes (For Clients/Invoices) - Client-facing information, special requests, delivery instructions
  - **UI improvements:**
    - Tab 3: Clean 2×2 layout (Internal row, External row)
    - Tab 4: All 4 categories displayed with clear section headers
    - Better organization by audience (internal vs external)
  - **Backward compatibility:** Old saved orders with 5-category notes are discarded on load (replaced with fresh 4-category structure)
  - **Test data only:** All existing saved orders contain test data, so no production data is lost

### Updated
- **Documentation** - Updated INVOICE_AND_PROPOSAL_SPEC.md with new order_notes structure
- **Test scripts** - Updated test_tab3_to_tab4_data_flow.py and test_saved_orders.py with new structure

---

## [7.5.0] - 2026-01-20

### Added
- **Product Variant Support** - Full schema update to support product variants (colors, flavors, sizes, etc.)
  - Added 2 new columns to schema: "Has Variants (Y/N)" and "Variant Type" (36 total columns, was 34)
  - **Tab 1 (Proposal Generator):**
    - Variant selector dropdown appears for products with variants
    - Warning shown if variant not selected (but still allows add)
    - Displays products as "Product/Service - Variant" format throughout
  - **Tab 3 (Order & Client Info):**
    - Manual product selection (Option C) includes variant selector
    - Current Order display shows product names with variant suffix
    - Variant data stored with each order item
  - **New helper functions in src/helpers.py:**
    - `has_variants()` - Checks if product has variants (Y/N flag)
    - `parse_variant_types()` - Parses variant list from "(x, y, z)" format
    - `format_product_with_variant()` - Formats display name as "Product - Variant"
- **Schema documentation updated** - Added variant columns to schema_reference.md with format examples
- **Backward compatibility** - Works with spreadsheets that don't have variant columns (defaults to N)

### Changed
- **Product display format** - All product names now show variant when applicable: "9oz Honey - Hot"
- **Variant consolidation support** - Products with same pricing can be consolidated into single row with variant list
  - Example: Instead of 4 separate rows (9oz Hot Honey, 9oz Elderberry Honey, etc.), use 1 row with Variant Type = "(Hot, Elderberry, Rosemary, Creamed)"
- **Proposal items structure** - Now includes `selected_variant` field (None if no variant selected)
- **Order items structure** - Now includes `selected_variant` field (None if no variant selected)

### Fixed
- **Tab 3 Option B:** Variant data now preserved when importing from proposals
- **Tab 4:** Product names in invoice/PO tables now include variant suffix
- **CSV exports:** Variants included in all CSV downloads
- **Saved data:** Proposals and orders automatically save/load variant selections via JSON

### Complete Variant Workflow
- ✅ Tab 1: Select variant and add to proposal
- ✅ Save/load proposals with variants (persisted to Google Sheets)
- ✅ Tab 3 Option B: Import from proposal preserves variants
- ✅ Tab 3 Option C: Manual selection includes variant selector
- ✅ Tab 3: Current Order displays product names with variants
- ✅ Save/load orders with variants (persisted to Google Sheets)
- ✅ Tab 4: Invoice/PO tables show variants in all 4 tables
- ✅ HTML/CSV exports include variants in product names

### Notes
- Future data migration: Will consolidate variant products into single rows with variant lists
- App supports BOTH old format (separate product rows) and new format (variants in one row) simultaneously
- PowerPoint generation already has multi-variant support (v6.13) - will work with new variant format
- Remaining: Tab 3 Option A (HTML import) variant parsing (future enhancement)

---

## [7.4.0] - 2026-01-08

### Added
- **Full schema update with backward compatibility** - Implemented new canonical pricing data schema (30 columns)
- **MOQ field support** - App now uses MOQ from spreadsheet when available, calculates otherwise
- **PBP Standard Markup field** - Partner-specific default markups replace hardcoded 100%
- **Dual tariff format support** - Handles both percentage (%) and dollar ($) tariff estimates
- **Backward compatibility helper** - `get_column_value()` function ensures seamless old→new transitions
- **Comprehensive documentation** - Added schema_reference.md and testing guides

### Changed
- **Column name updates** - All references updated to new canonical names with fallback support:
  - "MSRP" → "Vendor Published MSRP"
  - "Customization Setup Fee" → "Client Price: Customization Setup Fee"
  - "Customization Cost per Unit" → "Client Price: Customization Cost per Unit"
  - "Shipping Cost (PBP)" → "PBP Cost: Shipping Cost per Unit"
  - "Shipping Price (Client)" → "Client Price: Shipping Price per Unit"
  - "Tariff Rate" → "Tariff Estimate (%)" with fallback to "Tariff Estimate ($)"
- **Default markup logic** - Products now use PBP Standard Markup when available instead of hardcoded 100%

### Fixed
- **Critical: Streamlit query_params compatibility** - Fixed AttributeError with older Streamlit versions
- **Critical: pandas Series evaluation error** - Fixed ValueError in calculate_moq with DataFrame rows
- Both errors were blocking app functionality - now resolved

---

## [7.3.0] - 2025-12-20

### Added
- **Bidirectional price editing in Tab 3** - Users can now directly edit client price per unit, not just markup %
- **Directory reorganization** - Cleaner structure with organized docs/ and scripts/ folders

### Changed
- **NGO → Non-profit terminology** - Updated all references throughout the app for better inclusivity

### Fixed
- Critical error in Tab 3 where `new_markup` variable was undefined

---

## [7.2.0] - 2024-12-13

### Added
- **Multiple contacts support** - Dynamic add/remove functionality for multiple POCs
- **Partner POC investigation** - Debug logging and comprehensive test scripts
- **Comprehensive Tab 3→4 test suite** - Automated tests for data flow

### Fixed
- Partner POC pipeline - Corrected header row detection for different datasets
- Multiple contacts now display ALL contacts in Tab 4, not just primary

---

## [7.1.0] - 2024-12-11

### Added
- **Payment terms Net 15** - Added Net 15 and custom payment terms option
- **Editable product descriptions** - Tab 4 "Item + Specs" column now editable
- **Kitting Pricing section** - Separate PBP and client kitting costs
- **Improved Order Notes UX** - 5 always-visible text areas instead of dropdown
- **Sales tax field** - Estimated sales tax percentage input

### Fixed
- Tab 3 to Tab 4 data flow (4 critical issues resolved)
- Client info persistence in Tab 4
- Kitting costs now appear in invoice generation

---

## [7.0.0] - 2024-12-10

### Added
- **Search bar in Tab 1** - Quick product search functionality
- **Bidirectional price editing in Tab 1** - Edit markup or price directly
- **Cancel button for match changes** - Easy cancellation in PowerPoint matching
- **$0.50 rounding option** - All pricing tabs support fifty-cent rounding
- **Table restructuring** - PBP Cost vs Client Price columns in Tab 3

### Fixed
- Shipping columns in spreadsheet structure
- Price calculation accuracy with rounding

---

## [6.18.0] - 2024-11-20

### Added
- **Codebase simplification** - Removed 13,649 lines of obsolete code
- **Documentation cleanup** - Archived 23 completed planning docs
- **Code clarity improvements** - Renamed confusing functions, removed unused imports

### Technical
- Reduced codebase by 49% (now ~14,138 lines)
- Saved 22MB by removing deprecated files
- Improved beginner-friendliness

---

## [6.0.0 - 6.17.0] - 2024-11-05 to 2024-11-19

### Major Features
- **4-Tab Structure** - Split Tab 1 into Proposal Generator and Client Order Form
- **PowerPoint Automation** - Complete Phases 1 & 2 with 78.9% match accuracy
- **Saved Proposals/Orders** - Cloud-persistent save/load functionality
- **HTML Form Import** - Parse completed client forms (11 fields extracted)
- **Multi-variant PowerPoint** - Handle products with multiple variants
- **Units per Package** - Support for package-based pricing
- **Match Memory System** - Remember confirmed product-to-slide matches
- **MSRP Pricing** - Automatic markup calculation to match MSRP
- **Bulk Add Products** - Add all products from selected partners
- **Dataset Selector** - Switch between Demo and Real pricing data
- **Render Deployment** - Successfully deployed to production

### Infrastructure
- Cloud-based PowerPoint template loading
- Environment variable support for Render
- Memory optimization for 2GB RAM tier
- Scroll preservation system (95-98% effective)

---

## Version History

- **v7.x** - December 2024: Stakeholder feedback implementation
- **v6.x** - November 2024: PowerPoint automation & infrastructure
- **v5.x** - October 2024: Core order management
- **v4.x** - September 2024: Pricing engine implementation
- **v3.x** - August 2024: Google Sheets integration
- **v2.x** - July 2024: Basic Streamlit UI
- **v1.x** - June 2024: Initial prototype

---

## Statistics

### Codebase Size
- **Current:** ~14,138 lines of Python
- **Peak:** ~28,000 lines (before cleanup)
- **Reduction:** 49% smaller, more maintainable

### Features Completed
- **Critical Fixes:** 4/4 (100%)
- **High Priority:** 13/13 (100%)
- **Week 1 Sprint:** Complete
- **Week 2 Sprint:** 3/6 (50%)

### Testing Coverage
- **Core Tests:** 2 scripts
- **Feature Tests:** 19 scripts
- **Investigation Scripts:** 7 scripts
- **Total:** 28 test scripts

---

## Contributors
- Human Developer
- Claude AI Assistant (Co-Author)

---

## Links
- [Production App](https://pricing-data-solution-pbp.onrender.com)
- [Documentation](docs/README.md)
- [Active Development](ACTIVE_DEVELOPMENT_TODO.md)