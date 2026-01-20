# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

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