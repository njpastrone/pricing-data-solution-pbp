# Changelog

All notable changes to the Peace by Piece International Pricing App are documented in this file.

---

## [2.3] - Tab Transition UX & Critical Bug Fixes (October 2025)

### Added
- **Tab 1 → Tab 2 Transition Improvements:**
  - "Next Steps" guidance box at end of Tab 1 with dynamic messaging
  - Success banner in Tab 2 showing available proposal product count
  - "Import All Products from Proposal" primary button for one-click import
  - Reorganized proposal import UI with individual selection in expander
- **Analysis Documentation:**
  - Created TAB_TRANSITION_ANALYSIS.md with comprehensive workflow analysis
  - Identified 5 UX pain points with impact ratings
  - Documented 9 prioritized improvement recommendations

### Fixed
- **Critical KeyError Fixes:**
  - Fixed Client Order Form HTML/CSV generation when accessing proposal data
  - Fixed Tab 1 proposal CSV download with missing product data
  - Fixed Tab 2 individual product selection with missing fields
  - Fixed `convert_proposal_to_order` function in helpers.py
  - All proposal_products iteration now uses safe `.get()` method with defaults
- **Duplicate Element Key Error:**
  - Fixed duplicate 'remove_{idx}' keys in Tab 2 order items
  - Added unique prefixes: `remove_custom_{idx}` and `remove_product_{idx}`
  - Added unique prefix for edit button: `edit_product_{idx}`
- **UI Polish:**
  - Added placeholder text "[Input Qty]" for empty quantity cells in HTML form

### Improved
- **Data Safety:** All dictionary access now handles missing/malformed data gracefully
- **User Experience:** Clear guidance on workflow progression between tabs
- **Import Efficiency:** Reduced clicks for importing all proposal products
- **Visual Feedback:** Better visibility of available proposal products in Tab 2

---

## [2.2] - Proposals Tab UX Improvements (October 2025)

### Added
- **HTML Client Order Form:** Professional, email-ready order form with:
  - Styled table format with blue section headers and organized layout
  - Light/dark mode color compatibility with explicit color definitions
  - Clear instructional prompts for clients (delete-to-select for multiple choice)
  - Pre-filled product names and quantities from proposals
  - Download options: HTML (primary), TXT (backup), CSV (backup)
  - Preview functionality with expandable viewer
- **Copy Buttons for Sections 5 & 6:**
  - "Copy Pricing for Cards & Kitting" button
  - "Copy Terms & Conditions" button
  - Displays text in selectable code block format

### Changed
- **Client Order Form Format:** Replaced plain text form with professional HTML table
- **Form Instructions:** Updated with 5-step process for clients to fill out form
- **Form Title:** Changed to "PEACE BY PIECE CLIENT ORDER FORM"
- **Multiple Choice Fields:** Changed from checkboxes to [Delete one: X / Y] format
- **Text Fields:** Added clear prompts like [Type your answer here]

### Improved
- **User Workflow:** Streamlined process for sending proposals to clients
- **Email Integration:** Form maintains formatting when copied into email clients
- **Client Experience:** Clearer instructions reduce friction for clients filling out forms

---

## [2.1] - Bookkeeper-Aligned Invoice & PO (October 2025)

### Added
- **Restructured Invoice & PO:** Combined Invoice and Purchase Order Request Form matching bookkeeper's standardized template
- **Partner Contact Auto-Extraction:** Automatically pulls point-of-contact info from Partner-Specific Info sheet in Google Sheets
- **Comprehensive Order Notes System:** 5 categories of notes (Kitting Specs, Client Requests, Add-on Samples, Artwork Attachments, General Notes)
- **Field Validation:** Pre-export validation with user warnings for missing or incomplete required fields
- **Standardized Dropdowns:** Payment Terms, Payment Method, Ship Method with predefined options
- **Date Tracking:** Order Submitted Date, Cost Submitted Date with date picker inputs
- **Cost Verification Status:** Per-product "Cost Verified?" field (Yes/No/Pending)
- **Partner In-Hands Date:** Separate date tracking for when partner delivers to PBP vs client in-hands date

### Changed
- **Invoice Format:** Updated to match bookkeeper template with all required fields
- **CSV Export:** Enhanced to include header section, itemized table, totals, and notes sections
- **Client Information Form:** Expanded with new required fields for bookkeeper compliance

### Documentation
- Created `docs/INVOICE_REQUIREMENTS.md` - Invoice/PO format specification
- Created `docs/INVOICE_PO_RESTRUCTURE_PLAN.md` - Implementation plan and field mappings
- Updated templates with bookkeeper's standardized form

---

## [2.0] - Multi-Sheet Data System (October 2025)

### Added
- **3-Sheet Architecture:** Migrated from single-sheet (jaggery_demo) to 3-sheet system (master_pricing_template_10_14)
  - **Template Sheet:** Partner-product pricing data
  - **Metadata Sheet:** Deliverable field definitions
  - **Partner-Specific Info Sheet:** Partner configuration reference
- **Flexible Tier System:** Support for both tiered and flat-rate pricing per product
- **Dynamic Tier Parsing:** Tier ranges defined in data (not hardcoded in code)
- **Pricing Tiers (Y/N) Flag:** Product-level configuration for tiered vs flat pricing
- **Multi-Partner Support:** Infrastructure for multiple vendors/suppliers with different pricing structures
- **Product-Level Tariff System:** Tariff calculations per product with flexible rates

### Changed
- **Data Source:** Switched from `jaggery_demo` to `master_pricing_template_10_14`
- **Column Names:** Updated to new standardized naming convention
  - Old: "PBP Cost w/o shipping (1-25)"
  - New: "PBP Cost: Tier 1"
- **Header Row Locations:** Template sheet header at row 6, others at row 2
- **Tier Logic:** From hardcoded 7-tier system to flexible tier parsing from "Pricing Tiers Info" column

### Documentation
- Created `docs/RESTRUCTURE_CONTEXT.md` - Current data structure documentation
- Updated `docs/METHODOLOGY_LOGIC.md` - Revised for new tier system
- Created `docs/TARIFF_REFINEMENT_PLAN.md` - Product-level tariff implementation plan

---

## [1.2] - Customization Minimum Feature (October 2025)

### Added
- **Customization Minimum Quantity:** User can specify minimum quantity for customization to apply
- **Conditional Customization:** Setup fees and per-unit costs only apply if order quantity meets minimum threshold
- **UI Enhancements:** Customization minimum input field with validation

### Changed
- **Customization Logic:** Modified to respect minimum quantity requirements
- **Breakdown Display:** Shows when customization is/isn't applied based on minimum

---

## [1.1] - Multi-Product Ordering (October 2025)

### Added
- **Add-to-Cart Pattern:** Users can add multiple products to a single order
- **Per-Product Markup:** Individual markup percentages configurable for each product
- **Order Management UI:** View, edit, remove products from order
- **Order-Level Costs:** Shipping and tariff applied once to entire multi-product order
- **Discount Options:**
  - Preset NGO discount (5%)
  - Custom discounts with description and percentage
- **Marketing Rounding:** Optional charm pricing (e.g., $60 → $59) for whole dollar amounts
- **Custom Line Items:** Add unique services/customizations not in product catalog

### Changed
- **Session State Management:** Enhanced to track multiple products in order
- **Proposal Format:** Updated to display multi-product orders with per-product breakdowns
- **Invoice Format:** Updated to show line items for all products in order
- **Pricing Display:** Shows per-product totals and order-level summary

### Documentation
- Updated `docs/PLANNING.md` with multi-product requirements
- Added multi-product test cases to `docs/METHODOLOGY_LOGIC.md`

---

## [1.0] - MVP (September 2025)

### Added
- **Single Product Quoting:** Calculate quotes for individual products
- **Tiered Pricing:** 7 quantity-based pricing tiers (1-25, 26-50, 51-100, 101-250, 251-500, 501-1000, 1000+)
- **Custom Labels:** Optional label costs with minimum quantity enforcement (100 labels)
- **Art Setup Fee:** One-time setup fee per product
- **Markup Calculation:** Applies markup to product price only (not fees/shipping/tariff)
- **Google Sheets Integration:** Loads pricing data from jaggery_demo spreadsheet
- **Data Caching:** 5-minute cache for performance optimization
- **Proposal Generation:** Client-facing pricing proposal with breakdown
- **Invoice Generation:** Professional invoice table with line items and totals
- **CSV Export:** Download proposals and invoices as CSV files

### Core Features
- **Product Selection:** Dropdown selector with product reference numbers
- **Quantity Input:** Validates minimum order quantities
- **Tier Selection:** Automatic tier selection based on quantity
- **Customization Options:** Toggle for labels and setup fees
- **Markup Input:** Percentage-based markup configuration
- **Shipping & Tariff:** Order-level cost inputs
- **Cost Breakdown:** Detailed per-unit and total cost breakdowns
- **Session State:** Preserves data across user interactions

### Documentation
- Created `CLAUDE.md` - Project rules and development guidelines
- Created `README.md` - Quick start and project overview
- Created `docs/PLANNING.md` - Project requirements and goals
- Created `docs/DATA_STRUCTURE.md` - Data structure documentation (jaggery_demo)
- Created `docs/METHODOLOGY_LOGIC.md` - Pricing calculations and business rules

### Technical Implementation
- **Technology Stack:** Python 3.x + Streamlit
- **Data Source:** Google Sheets (jaggery_demo)
- **Authentication:** Google Cloud service account
- **Libraries:** streamlit, pandas, gspread, google-auth

---

## Version History Summary

| Version | Date | Key Feature | Status |
|---------|------|-------------|--------|
| 2.3 | Oct 2025 | Tab transition UX & critical bug fixes | ✅ Current |
| 2.2 | Oct 2025 | Proposals Tab UX improvements | ✅ Implemented |
| 2.1 | Oct 2025 | Bookkeeper-aligned Invoice & PO | ✅ Implemented |
| 2.0 | Oct 2025 | Multi-sheet data system | ✅ Implemented |
| 1.2 | Oct 2025 | Customization minimum feature | ✅ Implemented |
| 1.1 | Oct 2025 | Multi-product ordering | ✅ Implemented |
| 1.0 | Sep 2025 | MVP - Single product quoting | ✅ Implemented |

---

## Upcoming Changes (Planned)

### Code Reorganization (In Progress)
- Extract business logic into modular `src/` directory
  - `src/data_loader.py` - Google Sheets integration
  - `src/pricing_engine.py` - Pricing calculations
  - `src/helpers.py` - Utility functions
- Reduce `app.py` from 2,339 lines to ~1,500 lines
- Improve code maintainability and testability

### Testing Infrastructure
- Unit tests for pricing engine
- Integration tests for data loading
- Regression testing suite

### Documentation Cleanup
- Consolidate overlapping documentation files
- Archive outdated/completed plans
- Create documentation index

---

**Document Maintained By:** Development Team
**Last Updated:** 2025-10-29
