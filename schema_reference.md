# Peace by Piece International - Data Schema Reference

Last Updated: January 28, 2026

---

## ✅ SCHEMA UPDATE COMPLETE - Version 8.1.0 (January 2026)

**Status:** Schema transition complete - Now using 45-column schema
**Version:** 8.1.0
**Release Date:** January 28, 2026

**Transition Details:**
- Complete documentation: [schema_update_jan_2026/MASTER_TRACKING.md](schema_update_jan_2026/MASTER_TRACKING.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md#800---2026-01-22)
- Pricing methodology: [docs/planning/METHODOLOGY_LOGIC.md](docs/planning/METHODOLOGY_LOGIC.md)

**Major Changes (v8.0.0 - Jan 22):**
- Expanded from 33 to 44 columns (+11 new fields)
- Three pricing methods: "MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"
- Cost basis system: "Per Item" vs "Per Case" normalization
- Calculated diagnostic fields for validation
- Description field reorganization (Billing, Purchase, Marketing)

**Recent Updates (v8.1.0 - Jan 28):**
- Added "Other Add-On % (of Cost)" column for non-shipping markup add-ons
- Added fourth pricing method: "MSRP + Other Add-On % (of Cost)"
- Renamed "Package" → "Case" terminology throughout (columns 20-21)
- Both add-ons now summed in MSRP-based pricing calculations

---

## Overview

This document defines the canonical data schemas for Peace by Piece International's data system. All spreadsheets and future database tables should conform to these definitions.

---

## Table: Partner Product Purchasing List

**Purpose:** Tracks product and service costs, pricing tiers, customization options, and shipping/tariff information from partners.

**Source Spreadsheets:**
- Master Pricing (production - 51 products)
- Master Pricing Template 10_14 (demo - 19 products)

**Total Columns:** 45 (updated January 2026)

### Column Definitions

| # | Field Name | Data Type | Description | Rules/Notes |
|---|------------|-----------|-------------|-------------|
| 1 | Partner | Text | Partner organization name | Required |
| 2 | Product/Service | Text | Name of the product or service | Required |
| 3 | Has Variants (Y/N) | Text | Product has variants (colors, flavors, sizes, etc.)? | Y or N, default N if blank |
| 4 | Variant Type | Text | Available variant options for this product | Format: (x, y, z) - comma-separated in parentheses. Required if Has Variants = Y |
| 5 | Purchase Description (to Partner) | Text | Description used on purchase orders to partners | Internal-facing, partner PO details |
| 6 | Billing Description (to Client) | Text | Description used on invoices to clients | Client-facing, invoice line item description |
| 7 | Marketing Description (Website) | Text | Description used on website and proposals | Client-facing, marketing copy |
| 8 | MOQ (Partner) | Number | Partner's minimum order quantity | Whole number |
| 9 | MOV (Partner) | Currency | Partner's minimum order value | Dollar amount |
| 10 | MOQ (PBP) | Number | PBP's minimum order quantity | Whole number |
| 11 | MOV (PBP) | Currency | PBP's minimum order value | Dollar amount |
| 12 | Pricing Tiers (Y/N) | Text | Whether tiered pricing applies | Y or N |
| 13 | Pricing Tiers Info | Text | Tier thresholds and structure | Required if Pricing Tiers = Y. Format: "T1: 1-25, T2: 26-50..." |
| 14 | **PBP Cost (No Tiers/Tier 1)** | Currency | Base cost OR Tier 1 cost | **DUAL PURPOSE:** Use for non-tiered products and as Tier 1 for tiered products |
| 15 | PBP Cost: Tier 2 | Currency | Tier 2 cost | Optional, for tiered products |
| 16 | PBP Cost: Tier 3 | Currency | Tier 3 cost | Optional, for tiered products |
| 17 | PBP Cost: Tier 4 | Currency | Tier 4 cost | Optional, for tiered products |
| 18 | PBP Cost: Tier 5 | Currency | Tier 5 cost | Optional, for tiered products |
| 19 | PBP Cost: Tier 6 | Currency | Tier 6 cost | Optional, for tiered products |
| 20 | **Cost Basis (Per Item/Per Case)** | Text | Cost type declaration | **UPDATED JAN 2026:** "Per Item" or "Per Case". Required. Default: "Per Item" |
| 21 | Units per Case | Number | Items per case | Required if Cost Basis = "Per Case". Default: 1 |
| 22 | **PBP Cost (Per-Unit, No Tiers, Calculated)** | Currency | Normalized per-item cost | **CALCULATED:** Base cost normalized to per-item (divides by Units per Case if needed) |
| 23 | **Pricing Logic** | Text | Pricing method | **CRITICAL:** Allowed values: MSRP + % of cost; MSRP + Other Add-On % of Cost; MSRP capped – ship absorbed; Standard markup |
| 24 | **Shipping Add-On % (of Cost)** | Percentage | % of cost added to vendor MSRP | Used if Pricing Logic includes MSRP-based methods. Format: 15 (means 15%). Default: 0 |
| 25 | **Other Add-On % (of Cost)** | Percentage | % of cost added to vendor MSRP (non-shipping) | **NEW JAN 2026:** Used for non-shipping markup add-ons. Format: 10 (means 10%). Default: 0 |
| 26 | **Pricing Notes** | Text | Pricing assumptions/exceptions | Informational, explains pricing method details |
| 27 | Vendor Published MSRP | Currency | Vendor's suggested retail price | Reference anchor for MSRP-based pricing methods |
| 28 | **Vendor Markup (No Tiers, Calculated)** | Percentage | Vendor's implied markup | **CALCULATED - DIAGNOSTIC:** ((MSRP / Cost) - 1) × 100 |
| 29 | **PBP Markup (Vendor+Add-On, No Tiers)** | Percentage | PBP's implied markup | **CALCULATED - DIAGNOSTIC:** ((PBP MSRP / Cost) - 1) × 100 |
| 30 | **PBP MSRP (Per-Unit, No Tiers, Calculated)** | Currency | **AUTHORITATIVE PRICE** | **CALCULATED - PRIMARY:** Canonical sell price calculated using Pricing Logic method |
| 31 | **PBP MSRP (Website)** | Currency | Website-displayed MSRP | Should match calculated MSRP (column 30). For validation/reference. |
| 32 | PBP Cost: Customization Setup Fee | Currency | Setup fee PBP pays | One-time fee per order |
| 33 | Client Price: Customization Setup Fee | Currency | Setup fee charged to client | One-time fee per order |
| 34 | PBP Cost: Customization Cost per Unit | Currency | Per-unit cost PBP pays | Per-unit customization cost |
| 35 | Client Price: Customization Cost per Unit | Currency | Per-unit cost charged to client | Per-unit customization cost |
| 36 | Customization Info | Text | Customization options description | Informational |
| 37 | Country of Origin (Made In) | Text | Manufacturing country | Informational |
| 38 | Country of Origin (Ships From) | Text | Shipping origin country | Used for tariff calculations |
| 39 | PBP Cost: Shipping Cost per Unit | Currency | Per-item shipping cost PBP pays | Internal reference |
| 40 | Client Price: Shipping Price per Unit | Currency | Per-item shipping price to client | Use when shipping is separate line item |
| 41 | Shipping Details | Text | Carrier, timeline notes | Informational |
| 42 | Tariff Estimate ($) | Currency | Tariff in dollars | Reference, per-item or total |
| 43 | Tariff Estimate (%) | Percentage | Tariff as percentage | Format: 10 (means 10%) |
| 44 | Tariff Info | Text | Tariff classification notes | Informational |
| 45 | **Data Collection Notes** | Text | Data quality, audit trail | **GOVERNANCE:** Notes on data collection, validation status, etc. |

---

## Schema Change Log

| Date | Change | Updated By | Version |
|------|--------|------------|---------|
| 01/28/2026 | **SCHEMA UPDATE (v8.1.0):** Added "Other Add-On % (of Cost)" column (new column 25). Added fourth pricing method "MSRP + Other Add-On % (of Cost)". Renamed "Package" → "Case" in Cost Basis and Units columns (20-21). Both add-ons now summed in MSRP-based pricing. Total columns: 45 (was 44, +1) | Nicolo | v8.1.0 |
| 01/22/2026 | **MAJOR SCHEMA TRANSITION (v8.0.0):** Expanded from 33 to 44 columns (+11 fields). Added 3 pricing methods, cost basis system, calculated diagnostic fields, reorganized descriptions. Complete pricing engine overhaul. See CHANGELOG.md for full details. Total columns: 44 | Schema Transition Team | v8.0.0 |
| 01/20/2026 | Added "Has Variants (Y/N)" and "Variant Type" columns for product variant support. Removed deprecated "Customizable Product" and "Variations" columns. Total columns: 36 (was 34, net +2) | | v7.5.0 |
| 01/19/2026 | Disaggregated MOQ into 4 columns: MOQ (Partner), MOV (Partner), MOQ (PBP), MOV (PBP). Total columns: 34 (was 31) | | v7.4.0 |
| 01/14/2026 | Split "Country of Origin" into two columns: "Country of Origin (Made In)" and "Country of Origin (Ships From)" | | v7.x |
| 12/22/2025 | Standardized schema across all three pricing spreadsheets | | v6.x |
| 12/22/2025 | Renamed customization and shipping fields to use "PBP Cost:" and "Client Price:" prefixes | | v6.x |
| 12/22/2025 | Added MOQ, PBP Standard Markup, Billing Description, Shipping Details, Tariff Estimate (%) to Master Pricing | | v6.x |

**v8.1.0 Schema Changes Summary (Jan 28, 2026):**
- **New Column (1):** Other Add-On % (of Cost) - column 25
- **Renamed Columns (2):** Cost Basis (Per Item/Per Package) → Cost Basis (Per Item/Per Case); Units per Package → Units per Case
- **New Pricing Method:** "MSRP + Other Add-On % (of Cost)" added to Pricing Logic allowed values
- **Pricing Calculation Update:** Both Shipping Add-On % and Other Add-On % are now summed together in MSRP-based pricing methods
- **Total Columns:** 45 (was 44, +1 field)

**v8.0.0 Schema Changes Summary (Jan 22, 2026):**
- **New Columns (11):** Pricing Logic, Cost Basis, Shipping Add-On %, Pricing Notes, PBP Cost (Per-Unit Calculated), Vendor Markup (Calculated), PBP Markup (Calculated), PBP MSRP (Calculated), PBP MSRP (Website), Billing Description (to Client), Data Collection Notes
- **Renamed Columns (3):** Purchase Description → Purchase Description (to Partner), Marketing Description → Marketing Description (Website), PBP Cost (No Tiers) → PBP Cost (No Tiers/Tier 1)
- **Repositioned Columns:** Has Variants and Variant Type moved to columns 3-4 (were 32-33)
- **Description Reorganization:** Split into 3 distinct fields for different audiences (Partner POs, Client Invoices, Website/Proposals)
- **Total Columns:** 44 (was 33, +11 fields)

---

## Future Tables

*(Add new table schemas here as the data system grows)*

---

## Notes

- Date format standard: MM/DD/YYYY
- **Variant Type Format:** List variant options in parentheses, comma-separated: `(Hot, Elderberry, Rosemary, Creamed)`
- **Product Consolidation:** Products with identical pricing can be consolidated into one row with variants instead of separate rows per variant
- **Example:** Instead of 4 rows (9oz Hot Honey, 9oz Elderberry Honey, 9oz Rosemary Honey, 9oz Creamed Honey), use 1 row: Product = "9oz Honey", Variant Type = "(Hot, Elderberry, Rosemary, Creamed)"
- **Display Format:** App displays products with variants as "Product/Service - Variant" (e.g., "9oz Honey - Hot")
