# Peace by Piece International - Data Schema Reference

Last Updated: January 8, 2026

---

## Overview

This document defines the canonical data schemas for Peace by Piece International's data system. All spreadsheets and future database tables should conform to these definitions.

---

## Table: Partner Product Purchasing List

**Purpose:** Tracks product and service costs, pricing tiers, customization options, and shipping/tariff information from partners.

**Source Spreadsheets:**
- Gronn Pricing
- Pricing Upload SS
- Master Pricing

### Column Definitions

| # | Field Name | Data Type | Description | Rules/Notes |
|---|------------|-----------|-------------|-------------|
| 1 | Partner | Text | Partner organization name | Required |
| 2 | Product/Service | Text | Name of the product or service | Required |
| 3 | Purchase Description | Text | Detailed description of the purchase item | |
| 4a | MOQ (Partner) | Number | Partner's minimum order quantity | Whole number (renamed from "MOQ") |
| 4b | MOV (Partner) | Currency | Partner's minimum order value | NEW - dollar amount |
| 4c | MOQ (PBP) | Number | PBP's minimum order quantity | NEW - whole number |
| 4d | MOV (PBP) | Currency | PBP's minimum order value | NEW - dollar amount |
| 5 | Pricing Tiers (Y/N) | Text | Whether tiered pricing applies | Y or N |
| 6 | Pricing Tiers Info | Text | Description of tier thresholds and structure | Required if Pricing Tiers = Y |
| 7 | PBP Cost (No Tiers) | Currency | PBP cost when no tiers apply | Use if Pricing Tiers = N |
| 8 | PBP Cost: Tier 1 | Currency | PBP cost at Tier 1 volume | |
| 9 | PBP Cost: Tier 2 | Currency | PBP cost at Tier 2 volume | |
| 10 | PBP Cost: Tier 3 | Currency | PBP cost at Tier 3 volume | |
| 11 | PBP Cost: Tier 4 | Currency | PBP cost at Tier 4 volume | |
| 12 | PBP Cost: Tier 5 | Currency | PBP cost at Tier 5 volume | |
| 13 | PBP Cost: Tier 6 | Currency | PBP cost at Tier 6 volume | |
| 14 | Units per Package | Number | Number of units included per package | Whole number |
| 15 | PBP Cost: Customization Setup Fee | Currency | One-time setup fee PBP pays for customization | |
| 16 | Client Price: Customization Setup Fee | Currency | One-time setup fee charged to client | |
| 17 | PBP Cost: Customization Cost per Unit | Currency | Per-unit customization cost PBP pays | |
| 18 | Client Price: Customization Cost per Unit | Currency | Per-unit customization cost charged to client | |
| 19 | Customization Info | Text | Description of customization options available | |
| 20 | PBP Standard Markup | Multiplier | Standard markup applied by PBP | Format: decimal (e.g., 2.5) |
| 21 | Vendor Published MSRP | Currency | Manufacturer's suggested retail price | |
| 22 | Country of Origin (Made In) | Text | Country where product is manufactured | |
| 23 | Country of Origin (Ships From) | Text | Country from where product ships (for tariff calculations) | |
| 24 | Marketing Description | Text | Client-facing product description | |
| 25 | Billing Description | Text | Description used on invoices | |
| 26 | PBP Cost: Shipping Cost per Unit | Currency | Per-unit shipping cost PBP pays | |
| 27 | Client Price: Shipping Price per Unit | Currency | Per-unit shipping price charged to client | |
| 28 | Shipping Details | Text | Additional shipping notes (carrier, timeline, etc.) | |
| 29 | Tariff Estimate ($) | Currency | Estimated tariff amount in dollars | |
| 30 | Tariff Estimate (%) | Percentage | Estimated tariff as percentage of cost | Format: decimal (e.g., 10%) |
| 31 | Tariff Info | Text | Notes on tariff classification or source | |
| 32 | Has Variants (Y/N) | Text | Whether product has variants (colors, flavors, sizes, etc.) | Y or N, default N if blank |
| 33 | Variant Type | Text | Available variant options for this product | Format: (x, y, z) - comma-separated in parentheses |

---

## Schema Change Log

| Date | Change | Updated By |
|------|--------|------------|
| 01/20/2026 | Added "Has Variants (Y/N)" and "Variant Type" columns for product variant support. Removed deprecated "Customizable Product" and "Variations" columns. Total columns: 36 (was 34, net +2) | |
| 01/19/2026 | Disaggregated MOQ into 4 columns: MOQ (Partner), MOV (Partner), MOQ (PBP), MOV (PBP). Total columns: 34 (was 31) | |
| 01/14/2026 | Split "Country of Origin" into two columns: "Country of Origin (Made In)" and "Country of Origin (Ships From)" | |
| 12/22/2025 | Standardized schema across all three pricing spreadsheets | |
| 12/22/2025 | Renamed customization and shipping fields to use "PBP Cost:" and "Client Price:" prefixes | |
| 12/22/2025 | Added MOQ, PBP Standard Markup, Billing Description, Shipping Details, Tariff Estimate (%) to Master Pricing | |

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
