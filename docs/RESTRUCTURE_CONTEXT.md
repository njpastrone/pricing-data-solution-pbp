# 🧩 Project Data Structure & Integration Context

## Overview

This document defines the **new standardized data structure** for the project.  
It explains how the app should interpret, display, and process data from the workbook **`Partner Specific Pricing Template.xlsx`** in the "templates" folder.

The workbook serves as the **master configuration source** for partner, product, pricing, customization, and tariff information used during quote generation, proposal creation, and purchase order processing.

The app is designed for internal users who generate quotes and validate partner pricing.  
When a user selects a **partner** and **product/service**, the app should automatically display:
- Pricing tiers and quantity ranges (if applicable)
- Customization setup fees and per-unit costs
- Tariff and shipping estimates
- All relevant descriptive and reference information

---

## Workbook Structure

| Sheet Name | Purpose |
|-------------|----------|
| **Template** | Main master sheet containing partner and product data, including pricing tier logic, customization details, tariff and shipping info, and descriptive metadata. |
| **Metadata** | Defines the data required for each deliverable type (proposals, purchase orders, invoices). Specifies which fields are user-entered, computed by the app, or pulled from the master sheet. |
| **Partner-Specific Info** | Reference sheet for partner-specific rules, pricing logic, tariff details, and customization notes. Used for validation and keeping the main template consistent. |

---

## Sheet 1 — `Template`

### Purpose
This sheet is the **core table** that powers the app.  
Each row represents a **partner–product combination**, with standardized fields describing how that partner’s pricing and customization work.

---

### Data Dictionary

| Column | Example | Description |
|---------|----------|-------------|
| **Partner** | `Partner X` | The name of the vendor, supplier, or manufacturer. |
| **Product/Service** | `Product Y` | The specific product or service offered by the partner. |
| **Purchase Description** | `Example Example` | Text used in purchase documentation; concise summary of what is being ordered. |
| **Pricing Tiers (Y/N)** | `Y` | Indicates whether this partner/product uses tier-based pricing (`Y`) or a single standard price (`N`). |
| **Pricing Tiers Info** | `T1: 1–25, T2: 26–50, T3: 51–100, T4: 101–250, T5: 251–500, T6: 501–1000` | Defines quantity ranges for each tier. Used by the app to map order quantities to the correct unit price column. |
| **PBP Cost (No Tiers)** | `NA` | Flat unit price for partners/products with no tiered pricing (`Pricing Tiers (Y/N)` = `N`). |
| **PBP Cost: Tier 1** | `$10.00` | Unit price for Tier 1 orders (based on `Pricing Tiers Info`). |
| **PBP Cost: Tier 2** | `$9.50` | Unit price for Tier 2 orders. |
| **PBP Cost: Tier 3** | `$9.00` | Unit price for Tier 3 orders. |
| **PBP Cost: Tier 4** | `$8.50` | Unit price for Tier 4 orders. |
| **PBP Cost: Tier 5** | `$8.00` | Unit price for Tier 5 orders. |
| **PBP Cost: Tier 6** | `$7.50` | Unit price for Tier 6 orders. |
| **Customization Setup Fee** | `$50.00` | One-time setup fee for product customization (e.g., logo printing, packaging design). |
| **Customization Cost per Unit** | `$4.00` | Additional cost per unit when customization is applied. |
| **Customization Info** | `Example` | Notes about customization logic or options. Could describe minimums, color options, or special terms. |
| **Country of Origin** | `India` | Country where the product is manufactured. |
| **Marketing Description** | `Example Example Example` | A sales/marketing-friendly description of the product. |
| **Shipping** | `$40.00` | Estimated shipping cost or notes (may include terms like “FOB Shanghai”). |
| **Tariff Estimate (if available)** | `50.00%` | Estimated tariff rate as a percentage of cost. |
| **Tariff Info** | `Example` | Notes or reference codes (e.g., HS Code, duty terms, or exceptions). |

---

### Pricing Logic

1. **Tiered vs Non-Tiered Products**
   - If `Pricing Tiers (Y/N)` = **`N`**:
     - Use the **PBP Cost (No Tiers)** value as the unit cost.
   - If `Pricing Tiers (Y/N)` = **`Y`**:
     - Parse the `Pricing Tiers Info` string to determine quantity ranges for T1–T6.
     - Match user-input quantity to the correct tier range.
     - Use the corresponding **PBP Cost: Tier N** column as the unit price.

2. **Customization**
   - If a customization is selected:
     - Add the **Customization Setup Fee** (once per order).
     - Add the **Customization Cost per Unit × Quantity**.
   - Display **Customization Info** in the app for reference.

3. **Shipping & Tariffs**
   - Use **Shipping** and **Tariff Estimate** fields to display cost breakdowns.
   - **Tariff Info** provides contextual details for validation (e.g., “15% import duty” or “Exempt under US-India trade agreement”).

---

## Sheet 2 — `Metadata`

### Purpose
Defines what data each deliverable (e.g., quote, purchase order, invoice) must contain.  
It clarifies:
- What is **entered by the user**
- What is **computed** by the app
- What is **pulled directly** from the master `Template` sheet

### Example Structure

| Deliverable | Field Name | Source | Description |
|--------------|-------------|---------|--------------|
| Proposal | Partner | User Input | Selected partner. |
| Proposal | Product/Service | User Input | Selected product. |
| Proposal | Quantity | User Input | Quantity ordered. |
| Proposal | Unit Price | Computed | Based on tier or flat rate logic. |
| Proposal | Customization Cost | Computed | Setup + per-unit cost (if applicable). |
| Proposal | Tariff Estimate | From Template | Tariff % associated with product. |
| Proposal | Total | Computed | Sum of all applicable costs. |

---

## Sheet 3 — `Partner-Specific Info`

### Purpose
Stores detailed reference information for each partner, such as:
- Tier breakdowns and thresholds
- Customization fee rules
- Tariff rules and exceptions
- Notes for app validation and data updates

### Example Columns

| Partner | Tier Logic | Customization Notes | Tariff Notes | Last Updated |
|----------|-------------|--------------------|--------------|---------------|
| Partner X | `T1: 1–25, T2: 26–50, T3: 51–100, ...` | `+$50 setup, +$4/unit` | `50% import duty` | `2025-10-01` |

---

## Integration & App Behavior

When a user interacts with the app:

1. **Selects a Partner → Product/Service**
   - App retrieves the corresponding row from `Template`.
   - Displays key fields:  
     `Pricing Tiers Info`, `Customization Info`, `Tariff Estimate`, and `Tariff Info`.

2. **If Tiered Pricing = Y**
   - Parse the tier info string.
   - Match entered quantity to the correct tier.
   - Apply the price from `PBP Cost: Tier N`.

3. **If Tiered Pricing = N**
   - Use the `PBP Cost (No Tiers)` field as the price.

4. **If Customization Selected**
   - Add `Customization Setup Fee` (once per order).
   - Add `Customization Cost per Unit × Quantity`.
   - Display all related info for internal validation.

5. **Tariffs & Shipping**
   - Display `Tariff Estimate` and `Tariff Info` for user review.
   - Use `Shipping` field for total cost calculations if required.

6. **Deliverable Generation**
   - Use `Metadata` to ensure all necessary data is available.
   - Pull `Partner-Specific Info` as a reference to cross-check logic and maintain accuracy.

---

## Development Notes

- Existing logic for pricing and customization should be **updated** to reflect:
  - The **`Pricing Tiers (Y/N)` flag**  
  - New column names (`PBP Cost: Tier 1` → `PBP Cost: Tier 6`)  
  - Split of setup and per-unit customization costs

- Implementation Steps:
  1. Connect the app to `Partner Specific Pricing Template.xlsx`.
  2. Parse and store tier definitions from the `Pricing Tiers Info` column.
  3. Create helper functions to:
     - Determine applicable tier based on quantity.
     - Compute final cost (base + customization + tariff + shipping).
  4. Reference `Metadata` to validate deliverable fields.
  5. Use `Partner-Specific Info` to verify partner rules and support debugging.

---

## Example Workflow

1. **User Selection**
   - Partner: `Partner X`
   - Product: `Product Y`
   - Quantity: `180`
   - Customization: `Yes`

2. **App Logic**
   - Finds the product in `Template`.
   - Confirms `Pricing Tiers (Y/N)` = `Y`.
   - Parses `Pricing Tiers Info`:  
     `T1: 1–25, T2: 26–50, T3: 51–100, T4: 101–250, T5: 251–500, T6: 501–1000`
   - Determines applicable tier = **Tier 4**.
   - Uses `PBP Cost: Tier 4` = `$8.50`.
   - Applies customization fees:
     - `$50.00` setup + `$4.00 × 180 = $720.00`
   - Applies tariff: `50%` estimate.
   - Displays full breakdown for review.

3. **Output**
   - Base cost, customization, shipping, and tariff shown clearly.
   - Data ready for proposal or purchase order generation.

---

## Summary

The **`Partner Specific Pricing Template.xlsx`** file is now the authoritative schema for partner pricing and configuration.  
It provides a consistent, flexible structure for managing:
- Tiered and non-tiered pricing
- Customization fees and setup logic
- Tariff and shipping information

The app must read from this file to dynamically compute accurate pricing, display partner data for verification, and generate deliverables aligned with the `Metadata` definitions.

---
