# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### 🚧 In Progress (Week 2 Sprint - Jan 2026)
- Tab 3 Option B toast notification
- Execution form updates (New/Existing checkbox + MM/DD/YY dates)
- Customization Add-On feature for product editing

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