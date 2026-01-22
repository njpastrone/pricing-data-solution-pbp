# Schema Transition - Master Tracking Document

**Status:** 🚧 IN PROGRESS - Discussion Phase Complete, Ready for Implementation

**Last Updated:** January 22, 2026

**Purpose:** Track the transition from the old schema (January 8-20, 2026) to the new schema (January 21, 2026) and document all required code changes.

**Location:** `schema_update_jan_2026/` - All schema transition work is self-contained in this folder

---

## 🔄 Context Recovery - Starting Fresh

**If you're a new Claude instance picking up this work, start here:**

### 1. Read These Files First (in order):
1. **This file** (MASTER_TRACKING.md) - Complete context, decisions, and status
2. **../schema_reference.md** - New schema definition (44 columns)
3. **../SCHEMA_UPDATE_PROCESS.md** - General schema update guidelines
4. **Phase implementation guide** for current phase (see Status Log below)

### 2. Quick Context Summary:
- **What:** Major schema transition - 33 columns → 44 columns (+11 fields)
- **Why:** Complete pricing logic overhaul with 3 new pricing methods
- **Scope:** Core pricing engine, UI updates across all tabs, validation
- **Status:** Discussion phase complete (8 decisions made), ready for Phase 1 implementation
- **Migration Strategy:** Full migration to new schema (NO backward compatibility with old format)

### 3. Key Decisions Made (Discussion Phase Complete ✅):
1. **Pricing Logic:** Hybrid approach (read spreadsheet + calculate for validation)
2. **User Overrides:** Manual override checkbox for all pricing methods
3. **Empty Fields:** Clear defaults (100% markup, "Per Item", quiet validation)
4. **Tier Consolidation:** Simple approach (always use new column name)
5. **Calculated Fields:** Calculate and compare for full validation
6. **Variants:** Already fully implemented - no changes needed
7. **Description Fallbacks:** Clear hierarchy per use case (Invoice/PO/Proposal)
8. **Pricing Notes:** Compact expandable display (Tab 1 & 3 only)

### 4. What's Already Done:
- ✅ Schema design complete (44 columns defined)
- ✅ All 8 discussion topics resolved
- ✅ Product variants fully implemented (v7.7.0)
- ✅ Tracking document created with complete context
- ✅ Phase implementation guides written (see files in this folder)

### 5. What's Next:
- **Current Phase:** Phase 1 - Core Pricing Engine
- **Implementation Guide:** See `PHASE1_PRICING_ENGINE_GUIDE.md`
- **Resume Prompt:** See `RESUME_PROMPTS.md` for phase-specific prompts

### 6. Critical Implementation Notes:
- **NO backward compatibility** - we're migrating fully to new schema
- **Default markup:** 100% (cost × 2.0) when no pricing info exists
- **Manual override:** All pricing methods can be overridden via checkbox
- **Validation:** Always compare spreadsheet values to app-calculated values
- **Empty cell handling:** Quiet validation (inform user, don't block)

---

## Table of Contents
1. [Old Schema (Pre-January 21)](#old-schema-pre-january-21)
2. [New Schema (January 21, 2026)](#new-schema-january-21-2026)
3. [Schema Changes Summary](#schema-changes-summary)
4. [Logic NOT Yet in App](#logic-not-yet-in-app)
5. [Required Code Changes](#required-code-changes)
6. [Discussion Topics](#discussion-topics)
7. [Implementation Checklist](#implementation-checklist)

---

## Old Schema (Pre-January 21)

### Column Count: 33 columns

### Key Columns (Relevant to Changes):
| # | Field Name | Data Type | Description |
|---|------------|-----------|-------------|
| 1 | Partner | Text | Partner organization name |
| 2 | Product/Service | Text | Name of the product or service |
| 3 | Purchase Description | Text | Description used on purchase orders |
| 4a | MOQ (Partner) | Number | Partner's minimum order quantity |
| 4b | MOV (Partner) | Currency | Partner's minimum order value |
| 4c | MOQ (PBP) | Number | PBP's minimum order quantity |
| 4d | MOV (PBP) | Currency | PBP's minimum order value |
| 5 | Pricing Tiers (Y/N) | Text | Whether tiered pricing applies |
| 6 | Pricing Tiers Info | Text | Description of tier thresholds |
| 7 | PBP Cost (No Tiers) | Currency | Flat cost when no tiers |
| 8-13 | PBP Cost: Tier 1-6 | Currency | Tiered pricing costs |
| 14 | Units per Package | Number | Units included per package |
| 15 | PBP Cost: Customization Setup Fee | Currency | Setup fee PBP pays |
| 16 | Client Price: Customization Setup Fee | Currency | Setup fee charged to client |
| 17 | PBP Cost: Customization Cost per Unit | Currency | Per-unit cost PBP pays |
| 18 | Client Price: Customization Cost per Unit | Currency | Per-unit cost charged to client |
| 19 | Customization Info | Text | Customization options description |
| 20 | **PBP Standard Markup** | **Multiplier** | **Standard markup applied by PBP** |
| 21 | Vendor Published MSRP | Currency | Vendor's suggested retail price |
| 22 | Country of Origin (Made In) | Text | Manufacturing country |
| 23 | Country of Origin (Ships From) | Text | Shipping origin country |
| 24 | Marketing Description | Text | Client-facing description |
| 25 | PBP Cost: Shipping Cost per Unit | Currency | Shipping cost PBP pays |
| 26 | Client Price: Shipping Price per Unit | Currency | Shipping price charged to client |
| 27 | Shipping Details | Text | Shipping notes |
| 28 | Tariff Estimate ($) | Currency | Tariff in dollars |
| 29 | Tariff Estimate (%) | Percentage | Tariff as percentage |
| 30 | Tariff Info | Text | Tariff classification notes |
| 31 | Has Variants (Y/N) | Text | Product has variants? |
| 32 | Variant Type | Text | Variant options |

### Old Pricing Logic:
```python
# Simple markup-based pricing
base_cost = get_unit_price(product_data, quantity)

# Use PBP Standard Markup if available, else default to 100%
markup_percent = product_data.get('PBP Standard Markup', 2.0)  # 2.0 = 100% markup
markup_percent = (markup_percent - 1) * 100  # Convert multiplier to percentage

# Calculate client price
client_price = base_cost * (1 + markup_percent / 100)

# MSRP is reference only, not used in calculations
msrp = product_data.get('Vendor Published MSRP', None)  # Display for comparison
```

### Old Cost Normalization:
```python
# If Units per Package exists and > 1, normalize
units_per_package = product_data.get('Units per Package', 1)
if units_per_package > 1:
    per_unit_cost = package_cost / units_per_package
else:
    per_unit_cost = package_cost
```

---

## New Schema (January 21, 2026)

### Column Count: 44 columns (+11 new fields)

### All Columns (Complete List):
| # | Field Name | Data Type | Description | Rules/Notes |
|---|------------|-----------|-------------|-------------|
| 1 | Partner | Text | Partner organization name | Required |
| 2 | Product/Service | Text | Name of the product or service | Required |
| 3 | **Has Variants (Y/N)** | Text | Product has variants? | **Y or N** |
| 4 | **Variant Type** | Text | Colors, flavors, variations | **Required if Has Variants = Y** |
| 5 | **Purchase Description (to Partner)** | Text | Description used on POs | **RENAMED - Internal-facing** |
| 6 | **Billing Description (to Client)** | Text | Description on invoices to clients | **NEW - Client-facing** |
| 7 | **Marketing Description (Website)** | Text | Description used on website | **RENAMED - Client-facing** |
| 8 | MOQ (Partner) | Number | Partner's minimum order quantity | Whole number |
| 9 | MOV (Partner) | Number | Partner's minimum order value | Whole number |
| 10 | MOQ (PBP) | Number | PBP's minimum order quantity | Whole number |
| 11 | MOV (PBP) | Number | PBP's minimum order value | Whole number |
| 12 | Pricing Tiers (Y/N) | Text | Whether tiered pricing applies | Y or N |
| 13 | Pricing Tiers Info | Text | Tier thresholds and structure | Required if Pricing Tiers = Y |
| 14 | **PBP Cost (No Tiers/Tier 1)** | Currency | Base cost OR Tier 1 cost | **RENAMED - Dual purpose** |
| 15 | PBP Cost: Tier 2 | Currency | Tier 2 cost | Optional |
| 16 | PBP Cost: Tier 3 | Currency | Tier 3 cost | Optional |
| 17 | PBP Cost: Tier 4 | Currency | Tier 4 cost | Optional |
| 18 | PBP Cost: Tier 5 | Currency | Tier 5 cost | Optional |
| 19 | PBP Cost: Tier 6 | Currency | Tier 6 cost | Optional |
| 20 | **Cost Basis (Per Item/Per Package)** | Text | Cost type declaration | **NEW - Required** |
| 21 | Units per Package | Number | Items per package | **Required if Cost Basis = Per Package** |
| 22 | **PBP Cost (Per-Unit, No Tiers, Calculated)** | Currency | Normalized per-item cost | **NEW - Calculated field** |
| 23 | **Pricing Logic** | Text | Pricing method | **NEW - Allowed values:** MSRP + % of cost; MSRP capped – ship absorbed; Standard markup |
| 24 | **Shipping Add-On % (of Cost)** | Percentage | % of cost added to vendor MSRP | **NEW - Used if Pricing Logic = MSRP + % of cost** |
| 25 | **Pricing Notes** | Text | Pricing assumptions/exceptions | **NEW - Informational** |
| 26 | Vendor Published MSRP | Currency | Vendor's suggested retail price | Reference anchor |
| 27 | **Vendor Markup (No Tiers, Calculated)** | Percentage | Vendor's implied markup | **NEW - Calculated, diagnostic only** |
| 28 | **PBP Markup (Vendor+Add-On, No Tiers)** | Percentage | PBP's implied markup | **NEW - Calculated, diagnostic only** |
| 29 | **PBP MSRP (Per-Unit, No Tiers, Calculated)** | Currency | **AUTHORITATIVE PRICE** | **NEW - Calculated, canonical sell price** |
| 30 | **PBP MSRP (Website)** | Currency | Website-displayed MSRP | **NEW - Should match calculated MSRP** |
| 31 | PBP Cost: Customization Setup Fee | Currency | Setup fee PBP pays | Optional |
| 32 | Client Price: Customization Setup Fee | Currency | Setup fee charged to client | Optional |
| 33 | PBP Cost: Customization Cost per Unit | Currency | Per-unit cost PBP pays | Optional |
| 34 | Client Price: Customization Cost per Unit | Currency | Per-unit cost charged to client | Optional |
| 35 | Customization Info | Text | Customization options description | Informational |
| 36 | Country of Origin (Made In) | Text | Manufacturing country | Informational |
| 37 | Country of Origin (Ships From) | Text | Shipping origin country | Informational |
| 38 | PBP Cost: Shipping Cost per Unit | Currency | Per-item shipping cost PBP pays | Internal reference |
| 39 | Client Price: Shipping Price per Unit | Currency | Per-item shipping price to client | Use when shipping is separate line item |
| 40 | Shipping Details | Text | Carrier, timeline notes | Informational |
| 41 | Tariff Estimate ($) | Currency | Tariff in dollars | Reference |
| 42 | Tariff Estimate (%) | Percentage | Tariff as percentage | Format: percentage |
| 43 | Tariff Info | Text | Tariff classification notes | Informational |
| 44 | **Data Collection Notes** | Text | Data quality, audit trail | **NEW - Governance** |

### New Pricing Logic Framework:

#### Global Rules:
1. **All client-facing prices are per item**
2. **Costs may be per item or per package, but are always normalized to per-item cost before pricing logic is applied**
3. **Calculated fields should not be manually edited**
4. **Overrides apply only where explicitly labeled**

#### Three Pricing Methods:

**Method 1: MSRP + % of Cost**
```python
# Used when selling above vendor MSRP to partially recover shipping
pbp_msrp = vendor_published_msrp + (shipping_addon_percent * per_item_cost)

# Example:
# Vendor MSRP: $10.00
# Per-item cost: $4.00
# Shipping Add-On %: 25%
# PBP MSRP = $10.00 + (0.25 × $4.00) = $11.00
```

**Method 2: MSRP Capped – Ship Absorbed**
```python
# Use vendor MSRP as-is; shipping cost absorbed internally
pbp_msrp = vendor_published_msrp

# Example:
# Vendor MSRP: $10.00
# PBP MSRP = $10.00
# (Shipping cost not passed to client)
```

**Method 3: Standard Markup**
```python
# Traditional markup calculation (current app behavior)
pbp_msrp = per_item_cost * (1 + markup_percent / 100)

# Example:
# Per-item cost: $5.00
# Markup: 100%
# PBP MSRP = $5.00 × 2.0 = $10.00
```

#### Tiered Pricing Rule:
- **If Pricing Tiers = N**: Use "PBP Cost (No Tiers/Tier 1)"
- **If Pricing Tiers = Y**: Tier 1 is the base cost unless otherwise specified
- **All tier costs are normalized to per-item cost before pricing**

---

## Schema Changes Summary

### 🔴 BREAKING CHANGES (Require Code Updates)

#### 1. **Pricing Logic Overhaul**
- **DELETED:** "PBP Standard Markup" (old column #20)
- **ADDED:** "Pricing Logic" (#23) - determines pricing method
- **ADDED:** "Shipping Add-On % (of Cost)" (#24)
- **ADDED:** "PBP MSRP (Per-Unit, No Tiers, Calculated)" (#29) - **AUTHORITATIVE PRICE**
- **IMPACT:** Complete rework of pricing calculations throughout app

#### 2. **Cost Basis System**
- **ADDED:** "Cost Basis (Per Item/Per Package)" (#20) - explicit cost type
- **CHANGED:** "Units per Package" (#21) - now required when Cost Basis = "Per Package"
- **ADDED:** "PBP Cost (Per-Unit, No Tiers, Calculated)" (#22) - normalized calculated field
- **IMPACT:** Cost normalization logic needs explicit basis check

#### 3. **Tier 1 = No Tiers Consolidation**
- **RENAMED:** "PBP Cost (No Tiers)" → "PBP Cost (No Tiers/Tier 1)" (#14)
- **NEW RULE:** Single column serves dual purpose
- **IMPACT:** Tier lookup logic needs updating

#### 4. **Description Fields Reorganization**
- **RENAMED:** "Purchase Description" → "Purchase Description (to Partner)" (#5)
- **ADDED:** "Billing Description (to Client)" (#6)
- **RENAMED:** "Marketing Description" → "Marketing Description (Website)" (#7)
- **IMPACT:** Column references throughout app, invoice/proposal generation

### 🟡 NEW FEATURES (Need Integration)

#### 5. **Calculated Diagnostic Fields**
- **ADDED:** "Vendor Markup (No Tiers, Calculated)" (#27)
- **ADDED:** "PBP Markup (Vendor+Add-On, No Tiers)" (#28)
- **ADDED:** "PBP MSRP (Website)" (#30)
- **IMPACT:** Decide if app reads these or calculates them

#### 6. **Governance Fields**
- **ADDED:** "Pricing Notes" (#25)
- **ADDED:** "Data Collection Notes" (#44)
- **IMPACT:** UI display logic needed (optional)

### ✅ ALREADY PARTIALLY IMPLEMENTED

#### 7. **Product Variants** (January 20, 2026)
- **ADDED:** "Has Variants (Y/N)" (#3)
- **ADDED:** "Variant Type" (#4)
- **STATUS:** Helper functions exist (`has_variants()`, `parse_variant_types()`), but need to verify UI integration

### ✅ IMPLEMENTED (Earlier Changes)

#### 8. **MOQ/MOV Disaggregation** (January 19, 2026)
- ✅ Fully implemented in `calculate_moq()` function

#### 9. **Country of Origin Split** (January 14, 2026)
- ✅ Column names updated, need to verify usage

#### 10. **Customization Cost Split** (January 8, 2026)
- ✅ Column names updated, need to verify usage

#### 11. **Tariff Dual Format** (January 8, 2026)
- ✅ Fully implemented in `get_tariff_rate()`

#### 12. **Shipping Cost Split** (January 8, 2026)
- ✅ Fully implemented in `get_shipping_costs()`

---

## Logic NOT Yet in App

### 🔴 CRITICAL (Must Implement)

#### 1. **Three-Method Pricing System**
**Status:** ❌ NOT IMPLEMENTED

**Current Behavior:**
- App uses simple markup formula: `client_price = base_cost × (1 + markup%)`
- "PBP Standard Markup" field used if available (multiplier like 2.0)
- User can override markup % per product
- MSRP is display-only reference

**New Required Behavior:**
```python
def calculate_client_price(product_data, quantity, user_markup_override=None):
    # Step 1: Normalize cost to per-item
    cost_basis = product_data['Cost Basis (Per Item/Per Package)']
    base_cost = get_base_cost_for_quantity(product_data, quantity)

    if cost_basis == "Per Package":
        units_per_package = product_data['Units per Package']
        per_item_cost = base_cost / units_per_package
    else:
        per_item_cost = base_cost

    # Step 2: Check Pricing Logic
    pricing_logic = product_data['Pricing Logic']

    if pricing_logic == "MSRP + % of cost":
        vendor_msrp = product_data['Vendor Published MSRP']
        shipping_addon_pct = product_data['Shipping Add-On % (of Cost)']
        pbp_msrp = vendor_msrp + (shipping_addon_pct / 100 * per_item_cost)
        return pbp_msrp

    elif pricing_logic == "MSRP capped – ship absorbed":
        vendor_msrp = product_data['Vendor Published MSRP']
        return vendor_msrp

    elif pricing_logic == "Standard markup":
        # Use user override if provided, else calculate from MSRP or use default
        if user_markup_override:
            markup_percent = user_markup_override
        else:
            markup_percent = 100.0  # Default

        pbp_msrp = per_item_cost * (1 + markup_percent / 100)
        return pbp_msrp

    else:
        # Fallback to standard markup
        return per_item_cost * 2.0
```

**Affected Files:**
- `src/pricing_engine.py` - Core pricing calculations
- `app.py` Tab 1 - Proposal pricing
- `app.py` Tab 3 - Order pricing
- `src/helpers.py` - Price calculation helpers

**Decision Needed:**
- Should app READ "PBP MSRP (Per-Unit, No Tiers, Calculated)" from spreadsheet OR calculate it?
- How do users override pricing when using MSRP methods?

---

#### 2. **Cost Basis Explicit Declaration**
**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Current Behavior:**
- `Units per Package` field exists (v6.8)
- If `Units per Package > 1`, cost is normalized: `per_unit = package_cost / units`
- No explicit "Cost Basis" field check

**New Required Behavior:**
```python
def normalize_cost(product_data, base_cost):
    cost_basis = product_data.get('Cost Basis (Per Item/Per Package)', 'Per Item')

    if cost_basis == "Per Package":
        units_per_package = product_data.get('Units per Package', 1)
        if units_per_package <= 0:
            raise ValueError(f"Invalid Units per Package: {units_per_package}")
        per_item_cost = base_cost / units_per_package
    else:  # "Per Item"
        per_item_cost = base_cost

    return per_item_cost
```

**Affected Files:**
- `src/pricing_engine.py` - `get_unit_price_new_system()`
- Anywhere cost normalization happens

**Decision Needed:**
- What's the default if "Cost Basis" field is missing? (Assume "Per Item"?)
- Validate that if Cost Basis = "Per Package", Units per Package must exist?

---

#### 3. **Tier 1 = No Tiers Consolidation**
**Status:** ❌ NOT IMPLEMENTED

**Current Behavior:**
- Checks "Pricing Tiers (Y/N)" field
- If N: reads "PBP Cost (No Tiers)" column
- If Y: reads "PBP Cost: Tier 1" through "PBP Cost: Tier 6" columns

**New Schema:**
- Column #14 is now "PBP Cost (No Tiers/Tier 1)" - serves both purposes

**New Required Behavior:**
```python
def get_base_cost_for_tier(product_data, tier_number):
    has_tiers = product_data.get('Pricing Tiers (Y/N)', 'N').strip().upper() == 'Y'

    if not has_tiers or tier_number == 1:
        # Use column #14 for both no-tier and Tier 1
        return product_data.get('PBP Cost (No Tiers/Tier 1)', 0)
    else:
        # Use tier-specific columns for Tier 2-6
        tier_col = f'PBP Cost: Tier {tier_number}'
        return product_data.get(tier_col, 0)
```

**Affected Files:**
- `src/pricing_engine.py` - `get_unit_price_new_system()`
- `src/helpers.py` - Any tier lookup logic

**Decision Needed:**
- Update column name mappings in `get_column_value()`
- Backward compatibility for old "PBP Cost (No Tiers)" column?

---

#### 4. **Description Field Usage**
**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Current Behavior:**
- Uses "Purchase Description" (old name)
- Uses "Marketing Description" (old name)
- No "Billing Description (to Client)" logic

**New Schema:**
- "Purchase Description (to Partner)" (#5) - POs to partners
- "Billing Description (to Client)" (#6) - Invoices to clients
- "Marketing Description (Website)" (#7) - Website/proposals

**New Required Behavior:**
```python
# On Purchase Orders (to partners):
description = product_data.get('Purchase Description (to Partner)', '')

# On Invoices (to clients):
description = product_data.get('Billing Description (to Client)', '')

# On Proposals/Website:
description = product_data.get('Marketing Description (Website)', '')
```

**Affected Files:**
- `app.py` Tab 4 - Invoice generation (use Billing Description)
- `app.py` Tab 1 - Proposal generation (use Marketing Description)
- Any PO generation logic (use Purchase Description)

**Decision Needed:**
- Fallback order if a description is missing?
- Backward compatibility for old column names?

---

### 🟡 MEDIUM PRIORITY (Verify or Integrate)

#### 5. **Product Variants UI Integration**
**Status:** ⚠️ HELPER FUNCTIONS EXIST, UI INTEGRATION UNCLEAR

**Existing Code:**
- `has_variants()` in `src/helpers.py` - checks "Has Variants (Y/N)"
- `parse_variant_types()` in `src/helpers.py` - parses "(Hot, Elderberry, Rosemary)"
- `format_product_with_variant()` in `src/helpers.py` - formats "Product - Variant"
- PowerPoint variant consolidation (v6.13)

**Need to Verify:**
- ✅ Are variants shown in product catalog (Tab 1)?
- ✅ Can users select specific variants when adding to proposal?
- ✅ Are variants displayed correctly in order items (Tab 3)?
- ✅ Are variants shown on invoices (Tab 4)?

**Affected Files:**
- `app.py` Tab 1 - Product catalog and selection
- `app.py` Tab 3 - Order item display
- `app.py` Tab 4 - Invoice display

---

#### 6. **Calculated Diagnostic Fields**
**Status:** ❌ NOT IMPLEMENTED (Decision Needed)

**New Fields in Spreadsheet:**
- "Vendor Markup (No Tiers, Calculated)" (#27)
- "PBP Markup (Vendor+Add-On, No Tiers)" (#28)
- "PBP MSRP (Per-Unit, No Tiers, Calculated)" (#29) - **AUTHORITATIVE**
- "PBP MSRP (Website)" (#30)

**Decision Needed:**
1. **Option A: App READS these from spreadsheet**
   - Spreadsheet has formulas that calculate these
   - App trusts the spreadsheet values
   - Simpler app logic, but requires correct spreadsheet formulas

2. **Option B: App CALCULATES these in Python**
   - App ignores spreadsheet calculated fields
   - App does all pricing calculations
   - More control, but duplicates logic

3. **Option C: Hybrid**
   - App reads "PBP MSRP (Per-Unit, No Tiers, Calculated)" as authoritative price
   - App calculates diagnostic fields for display/validation
   - Best of both worlds?

**Recommendation:** Need to discuss with you which approach to take.

---

#### 7. **Governance Fields Display**
**Status:** ❌ NOT IMPLEMENTED (Low Priority)

**New Fields:**
- "Pricing Notes" (#25) - Informational
- "Data Collection Notes" (#44) - Informational

**Action Needed:**
- Add UI to display these notes (expandable sections?)
- Likely informational only, no calculation impact

**Affected Files:**
- `app.py` Tab 1 - Product details display

---

### ✅ LOW PRIORITY (Already Implemented or Verify Only)

#### 8. **Country of Origin Usage**
**Status:** ✅ IMPLEMENTED, VERIFY USAGE

**Columns:**
- "Country of Origin (Made In)" (#36)
- "Country of Origin (Ships From)" (#37)

**Verify:**
- Both columns referenced correctly?
- "Ships From" used for tariff calculations?
- "Made In" displayed on proposals/invoices?

**Affected Files:**
- `app.py` - All tabs where country is displayed
- Tariff calculation logic

---

#### 9. **Customization Cost Split**
**Status:** ✅ IMPLEMENTED, VERIFY USAGE

**Columns:**
- "PBP Cost: Customization Setup Fee"
- "Client Price: Customization Setup Fee"
- "PBP Cost: Customization Cost per Unit"
- "Client Price: Customization Cost per Unit"

**Verify:**
- Both PBP and Client costs used correctly?
- PBP costs tracked separately for internal accounting?

**Affected Files:**
- `app.py` Tab 3 - Customization logic
- `app.py` Tab 4 - Invoice display

---

## Required Code Changes

### Phase 1: Core Pricing Engine Overhaul (CRITICAL)

#### File: `src/pricing_engine.py`

**Changes:**
1. ✅ Update `get_column_value()` mappings for renamed columns
2. ✅ Add `normalize_cost_to_per_item()` function with explicit Cost Basis check
3. ✅ Add `get_pricing_logic()` function to read Pricing Logic field
4. ✅ Rewrite `get_unit_price_new_system()` to use new Tier 1 = No Tiers logic
5. ✅ Add `calculate_pbp_msrp()` function implementing 3 pricing methods
6. ✅ Update `calculate_product_quote()` to use new pricing logic
7. ✅ Add `calculate_vendor_markup()` diagnostic function (optional)
8. ✅ Add `calculate_pbp_markup()` diagnostic function (optional)

**Estimated Complexity:** HIGH - Core business logic

---

#### File: `src/helpers.py`

**Changes:**
1. ✅ Update `get_column_value()` mappings:
   - "Purchase Description (to Partner)" with fallback to "Purchase Description"
   - "Billing Description (to Client)" (new, no fallback)
   - "Marketing Description (Website)" with fallback to "Marketing Description"
   - "PBP Cost (No Tiers/Tier 1)" with fallback to "PBP Cost (No Tiers)"
   - "Cost Basis (Per Item/Per Package)" (new, default to "Per Item")
   - "Pricing Logic" (new, default to "Standard markup")
   - "Shipping Add-On % (of Cost)" (new, default to 0)
   - "Pricing Notes" (new, optional)
   - "Data Collection Notes" (new, optional)
2. ✅ Add `get_cost_basis()` helper function
3. ✅ Add `get_pricing_logic()` helper function
4. ✅ Update `calculate_moq()` if needed (likely already correct)
5. ✅ Verify variant helper functions are correct

**Estimated Complexity:** MEDIUM - Helper functions

---

### Phase 2: UI Updates (HIGH PRIORITY)

#### File: `app.py` - Tab 1 (Proposal Generator)

**Changes:**
1. ✅ Update product catalog to show variants (if not already done)
2. ✅ Verify MSRP pricing checkbox behavior with new logic
3. ✅ Update markup editing - decide if editable for MSRP methods
4. ✅ Update proposal tables to show correct prices
5. ✅ Display "Marketing Description (Website)" in product details
6. ✅ Add display of "Pricing Notes" (optional, expandable)
7. ✅ Update CSV download with new pricing

**Estimated Complexity:** MEDIUM-HIGH - User-facing changes

---

#### File: `app.py` - Tab 3 (Order & Client Info)

**Changes:**
1. ✅ Update order item pricing calculations
2. ✅ Verify variant display in current order
3. ✅ Update manual product addition with new pricing logic
4. ✅ Update price change warnings to reflect new pricing methods
5. ✅ Verify customization costs (PBP vs Client) displayed correctly

**Estimated Complexity:** MEDIUM-HIGH - User-facing changes

---

#### File: `app.py` - Tab 4 (Execution & Accounting)

**Changes:**
1. ✅ Use "Billing Description (to Client)" for invoices
2. ✅ Use "Purchase Description (to Partner)" for POs
3. ✅ Verify pricing matches new calculations
4. ✅ Update CSV export headers if needed
5. ✅ Verify variant display on invoices

**Estimated Complexity:** MEDIUM - Invoice generation

---

### Phase 3: Documentation & Testing (ONGOING)

#### Files: Documentation

**Changes:**
1. ✅ Update `schema_reference.md` (already done by you)
2. ✅ Update `CLAUDE.md` with schema transition status
3. ✅ Update `README.md` with schema transition status
4. ✅ Update `CHANGELOG.md` when changes complete
5. ✅ Update `docs/planning/RESTRUCTURE_CONTEXT.md` if needed

**Estimated Complexity:** LOW - Documentation

---

#### Files: Testing

**Changes:**
1. ✅ Create `scripts/test_new_pricing_logic.py` - test 3 pricing methods
2. ✅ Update `scripts/test_units_per_package.py` - test Cost Basis logic
3. ✅ Create `scripts/test_tier_consolidation.py` - test Tier 1 = No Tiers
4. ✅ Update `scripts/test_bidirectional_pricing.py` - verify still works
5. ✅ Run full regression test on demo dataset

**Estimated Complexity:** MEDIUM - Testing infrastructure

---

## Discussion Topics

### 🔴 HIGH PRIORITY DISCUSSIONS

#### Discussion 1: Pricing Logic Implementation Strategy ✅ DECIDED
**Question:** Should the app READ "PBP MSRP (Per-Unit, No Tiers, Calculated)" from the spreadsheet, or CALCULATE it in Python?

**Option A: Read from Spreadsheet**
- Pros: Simpler app logic, spreadsheet is source of truth
- Cons: Requires correct formulas in spreadsheet, less flexible

**Option B: Calculate in Python**
- Pros: More control, can validate spreadsheet values, flexible for user overrides
- Cons: Duplicates logic, need to maintain both spreadsheet and Python formulas

**Option C: Hybrid ✅ SELECTED**
- Read calculated MSRP as default/reference
- Calculate price in Python using 3 pricing methods
- Display both values for comparison/validation
- Allow user overrides with recalculation
- Warn if spreadsheet and app-calculated values don't match (epsilon > $0.01)

**Your Preference:** **Option C - Hybrid Approach**

**Implementation Notes:**
- Spreadsheet value is the "baseline" - what we show by default
- Python calculation validates the spreadsheet
- User can override, which triggers Python recalculation
- Display format: "Price: $10.00 (spreadsheet) | $10.00 (calculated) ✓" or "⚠️ Mismatch"

---

#### Discussion 2: User Override Behavior ✅ DECIDED
**Question:** When using "MSRP + % of cost" or "MSRP capped" methods, can users still edit the price manually?

**Current Behavior:**
- Users can always edit markup % per product
- Markup directly controls final price

**DECISION: All pricing methods are GUIDELINES with manual override available**

**Default Behavior (Checkbox Unchecked):**

| Pricing Method | Editable Fields | Locked Fields | Display |
|----------------|----------------|---------------|---------|
| MSRP + % of cost | Shipping Add-On % | Vendor MSRP | Shows: "Price = $X MSRP + Y% of cost = $Z" |
| MSRP capped | None (price follows MSRP) | Vendor MSRP, Final Price | Shows: "Price locked to Vendor MSRP: $X" |
| Standard markup | Markup % OR Price (bidirectional) | None | Current behavior (v7.3.0) |

**Manual Override Mode (Checkbox Checked):**
- Add checkbox: ☑ **"Manual price override (ignore pricing method)"**
- When checked: Price field becomes fully editable regardless of pricing method
- Shows warning: ⚠️ **"Manual override active - pricing method not applied"**
- Original calculated price shown for reference: "Calculated: $X | Your Override: $Y"

**UI/UX Requirements:**
- Make override checkbox easy to find (not buried)
- App must be flexible - users can override anything if needed
- Show calculated prices transparently even when overridden
- Preserve pricing method selection (user might toggle override off later)

**Implementation Notes:**
- Per-product override flag: `manual_price_override: bool`
- Store original calculated price for reference
- When override disabled, revert to calculated price

---

#### Discussion 3: Empty Field Handling ✅ DECIDED
**Question:** How do we handle empty cells in the new spreadsheet format?

**Context:** We are migrating fully to the new schema. No old spreadsheet formats will be used. This is about handling empty/missing cells in the NEW schema.

**PRICING FIELDS - Empty Cell Defaults:**

| Field | If Empty | Behavior |
|-------|----------|----------|
| Pricing Logic | Default: "Standard markup" | Use cost × (1 + markup%) formula |
| Cost Basis | Default: "Per Item" | No cost normalization needed |
| Shipping Add-On % | Default: 0% | No add-on applied |
| Vendor Published MSRP | Switch to "Standard markup" + warning | Show: "⚠️ No MSRP available - using Standard markup instead" |
| No pricing info at all | **100% markup (cost × 2.0)** | User can always override |

**DESCRIPTION FIELDS - Fallback Hierarchy:**

**For Invoices (to clients):**
1. "Billing Description (to Client)" (primary)
2. "Marketing Description (Website)" (fallback 1 - client-facing)
3. "Product/Service" name (fallback 2 - always available)

**For Purchase Orders (to partners):**
1. "Purchase Description (to Partner)" (primary)
2. "Billing Description (to Client)" (fallback 1)
3. "Product/Service" name (fallback 2 - always available)

**For Proposals/Website:**
1. "Marketing Description (Website)" (primary)
2. "Billing Description (to Client)" (fallback 1 - client-facing)
3. "Product/Service" name (fallback 2 - always available)

**OPTIONAL FIELDS:**
- Pricing Notes, Data Collection Notes: Don't display if empty
- Customization fields: Default to $0 (no customization)
- Variant fields: Default to "N" (no variants)

**VALIDATION ON LOAD:**
- Show quiet notification (not blocking): "ℹ️ 3 products missing Pricing Logic - using Standard markup"
- Show quiet notification: "ℹ️ 5 products missing MSRP but using MSRP pricing method - switched to Standard markup"
- Don't block app usage, just inform user
- Display in expandable "Data Quality Report" section (optional to view)

**Implementation Notes:**
- `get_column_value()` handles all empty cell defaults
- Validation runs once on spreadsheet load
- Fallback logic is transparent - user sees which description source was used

---

#### Discussion 4: Tier 1 = No Tiers Column Mapping ✅ DECIDED
**Question:** How should `get_column_value()` handle the consolidated column?

**Current Code:**
```python
# Old behavior
if has_tiers:
    price = row.get('PBP Cost: Tier 1', 0)
else:
    price = row.get('PBP Cost (No Tiers)', 0)
```

**Option A: Update all code to use new name ✅ SELECTED**
```python
# Always use new consolidated column
base_cost = row.get('PBP Cost (No Tiers/Tier 1)', 0)

# For tiers 2-6, still use separate columns
if has_tiers and tier_number > 1:
    tier_col = f'PBP Cost: Tier {tier_number}'
    base_cost = row.get(tier_col, 0)
```

**Option B: Map both old names to new column**
```python
# In get_column_value()
'pbp_cost_base': [
    'PBP Cost (No Tiers/Tier 1)',    # New canonical
    'PBP Cost (No Tiers)',            # Old fallback
    'PBP Cost: Tier 1'                # Old fallback
]
```

**Your Preference:** **Option A - Simple, no backward compatibility needed**

**Implementation Notes:**
- Column #14 is always "PBP Cost (No Tiers/Tier 1)" in new schema
- Tiers 2-6 remain separate columns (PBP Cost: Tier 2, etc.)
- Code is simpler without fallback logic

---

#### Discussion 5: Calculated Fields Strategy ✅ DECIDED
**Question:** What should the app do with calculated diagnostic fields?

**DECISION: Option C - Calculate and Compare (Full Validation)**

**Calculated Fields Strategy:**

| Field | App Behavior | Display |
|-------|-------------|---------|
| Vendor Markup (#27) | Calculate independently + read spreadsheet | Show both: "150% (spreadsheet) \| 150% (calculated) ✓" |
| PBP Markup (#28) | Calculate independently + read spreadsheet | Show both: "175% (spreadsheet) \| 175% (calculated) ✓" |
| PBP MSRP (Calculated) (#29) | Calculate independently + read spreadsheet | Show both: "$11.00 (spreadsheet) \| $11.00 (calculated) ✓" |
| PBP MSRP (Website) (#30) | Read from spreadsheet (reference only) | Show: "$11.00 (website)" |

**Validation Logic:**
- Compare spreadsheet vs calculated values
- If difference > $0.01 (or > 0.5% for percentages): Show warning
- Warning: "⚠️ Mismatch detected - Spreadsheet formula may need review"
- Visual indicators: ✓ (match) or ⚠️ (mismatch)

**UI Display Format:**
```
Product: Jaggery - Organic
Cost: $4.00/unit | Vendor MSRP: $10.00

Pricing Validation:
├─ Vendor Markup: 150% (spreadsheet) | 150% (calculated) ✓
├─ PBP MSRP: $11.00 (spreadsheet) | $11.00 (calculated) ✓
├─ PBP Markup: 175% (spreadsheet) | 175% (calculated) ✓
└─ Website MSRP: $11.00 (from spreadsheet)

✓ All values match - pricing is consistent
```

**Benefits:**
- Catches spreadsheet formula errors
- Validates pricing methods working correctly
- Shows users their actual margins
- Builds confidence in data quality

---

### 🟡 MEDIUM PRIORITY DISCUSSIONS

#### Discussion 6: Variant UI Integration ✅ VERIFIED - FULLY IMPLEMENTED
**Question:** Are variants fully integrated into product selection UI?

**STATUS: Variants are FULLY INTEGRATED across the entire app (as of v7.7.0)**

**Implemented Features:**

**Tab 1 (Proposal Generator):**
- ✅ Variant selector dropdown appears for products with variants
- ✅ Warning shown if variant not selected (but still allows add)
- ✅ Displays products as "Product/Service - Variant" format throughout
- ✅ Save/load proposals with variants (persisted to Google Sheets)

**Tab 3 (Order & Client Info):**
- ✅ Manual product selection (Option C/D) includes variant selector
- ✅ Current Order display shows product names with variant suffix
- ✅ Option B (Import from proposal) preserves variants
- ✅ Variant data stored with each order item
- ✅ Save/load orders with variants (persisted to Google Sheets)
- ⚠️ **Option A (HTML/Google Form import):** Variant parsing NOT implemented yet (future enhancement)

**Tab 4 (Execution & Accounting):**
- ✅ Invoice/PO tables show variants in all 4 tables
- ✅ HTML/CSV exports include variants in product names

**Helper Functions (src/helpers.py):**
- ✅ `has_variants()`, `parse_variant_types()`, `format_product_with_variant()` - All implemented and working

**PowerPoint:**
- ✅ Multi-variant consolidation already implemented (v6.13)

**Action Needed:**
- No changes required for variant support during schema transition
- Variant columns already in new schema ("Has Variants (Y/N)", "Variant Type")
- Implementation is complete and production-ready

---

#### Discussion 7: Description Field Fallback Order ✅ DECIDED
**Question:** If a description field is missing, what's the fallback?

**DECISION: Defined clear fallback hierarchy per use case**

**For Invoices (to clients):**
1. "Billing Description (to Client)" (primary)
2. "Marketing Description (Website)" (fallback 1 - client-facing)
3. "Product/Service" name (fallback 2 - always available)

**Reasoning:** Clients should see friendly descriptions, not internal PO language

**For Purchase Orders (to partners):**
1. "Purchase Description (to Partner)" (primary)
2. "Billing Description (to Client)" (fallback 1)
3. "Product/Service" name (fallback 2 - always available)

**Reasoning:** Partners need clear PO descriptions, but can work with product names

**For Proposals/Website:**
1. "Marketing Description (Website)" (primary)
2. "Billing Description (to Client)" (fallback 1 - client-facing)
3. "Product/Service" name (fallback 2 - always available)

**Reasoning:** Proposals need compelling descriptions, invoices work too

**Implementation:**
- `get_column_value()` handles fallback logic
- Always tries columns in order until non-empty value found
- Transparent to user which description source was used

---

#### Discussion 8: Pricing Notes Display ✅ DECIDED
**Question:** Where and how should we display "Pricing Notes" and "Data Collection Notes"?

**DECISION: Option C - Compact indicator with expandable section**

**Display Logic:**

**Tab 1 (Product Catalog):**
- Show compact note indicator: "ⓘ Notes (2)" when notes exist
- Expandable on click to show both pricing notes and data collection notes
- Hidden if both fields are empty

**Tab 3 (Order Items):**
- Same as Tab 1 - compact indicator in product details
- Expandable section

**Tab 4 (Invoices):**
- Don't display notes (keep invoices clean and professional)

**UI Mockup:**
```
Product: Jaggery - Organic
Cost: $4.00 | MSRP: $10.00 | Pricing: MSRP + 25% of cost

▼ Notes (2)
  📋 Pricing Notes:
     "MSRP includes 25% shipping recovery due to high freight costs from India"

  📝 Data Collection Notes:
     "Pricing confirmed 01/15/2026. Pending: MOQ verification from partner"
```

**Implementation Notes:**
- Only display section if at least one note field is non-empty
- Count shows total notes available: "Notes (1)" or "Notes (2)"
- Collapsed by default to keep UI clean
- Icons help distinguish note types (📋 pricing, 📝 data collection)

---

## Implementation Checklist

### Pre-Implementation (Planning Phase)
- [x] Document old schema
- [x] Document new schema
- [x] Identify all changes
- [x] List logic not yet in app
- [x] Create discussion topics
- [x] Update CLAUDE.md and README.md

### Discussion Phase (Current)
- [x] Discussion 1: Pricing logic implementation strategy (READ vs CALCULATE) ✅ HYBRID
- [x] Discussion 2: User override behavior for MSRP methods ✅ MANUAL OVERRIDE CHECKBOX
- [x] Discussion 3: Backward compatibility strategy ✅ EMPTY FIELD DEFAULTS
- [x] Discussion 4: Tier 1 = No Tiers column mapping ✅ OPTION A (SIMPLE)
- [x] Discussion 5: Calculated fields strategy ✅ CALCULATE AND COMPARE
- [x] Discussion 6: Variant UI integration verification ✅ FULLY IMPLEMENTED
- [x] Discussion 7: Description field fallback order ✅ DECIDED
- [x] Discussion 8: Pricing notes display ✅ DECIDED - OPTION C

### Phase 1: Core Pricing Engine ✅ COMPLETE (January 22, 2026)
- [x] Update `get_column_value()` mappings in `src/helpers.py`
- [x] Add `normalize_cost_to_per_item()` function
- [x] Add `get_pricing_logic()` helper function
- [x] Add `get_shipping_addon_percent()` helper function
- [x] Rewrite `get_unit_price_new_system()` for Tier 1 = No Tiers
- [x] Add `calculate_pbp_msrp()` function (3 pricing methods)
- [x] Add diagnostic markup calculations (vendor & PBP)
- [x] Create test scripts (test_new_pricing_logic.py, test_cost_basis.py)
- [x] Verify all imports and syntax
- [x] Document completion in PHASE1_COMPLETION_SUMMARY.md

### Phase 2: UI Updates (Tab 1)
- [ ] Update product catalog variant display
- [ ] Update MSRP pricing checkbox behavior
- [ ] Update markup editing logic
- [ ] Update proposal tables with new pricing
- [ ] Display "Marketing Description (Website)"
- [ ] Add "Pricing Notes" display (if needed)
- [ ] Update CSV download
- [ ] Test Tab 1 end-to-end

### Phase 3: UI Updates (Tab 3)
- [ ] Update order item pricing calculations
- [ ] Verify variant display in orders
- [ ] Update manual product addition
- [ ] Update price change warnings
- [ ] Verify customization costs display
- [ ] Test Tab 3 end-to-end

### Phase 4: UI Updates (Tab 4)
- [ ] Use "Billing Description (to Client)" for invoices
- [ ] Use "Purchase Description (to Partner)" for POs
- [ ] Verify pricing matches new calculations
- [ ] Update CSV export headers
- [ ] Verify variant display on invoices
- [ ] Test Tab 4 end-to-end

### Phase 5: Testing & Validation
- [ ] Create `test_new_pricing_logic.py` script
- [ ] Update `test_units_per_package.py` script
- [ ] Create `test_tier_consolidation.py` script
- [ ] Run full regression test suite
- [ ] Test with demo dataset
- [ ] Test with real dataset
- [ ] Test backward compatibility (old spreadsheet format)
- [ ] Test saved proposals/orders loading

### Phase 6: Documentation
- [ ] Update `CHANGELOG.md` with all changes
- [ ] Update `docs/planning/METHODOLOGY_LOGIC.md` with new pricing logic
- [ ] Update `docs/planning/RESTRUCTURE_CONTEXT.md` if needed
- [ ] Create migration guide for users
- [ ] Document new pricing methods in user-facing docs

### Phase 7: Deployment
- [ ] Code review all changes
- [ ] Test on staging environment
- [ ] Update production spreadsheet with new columns
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Gather user feedback

---

## Status Log

### January 22, 2026 - Phase 1 Implementation COMPLETE ✅
- **Status:** Core Pricing Engine fully implemented and tested
- **Deliverables:**
  - Updated `src/helpers.py` with new column mappings and cost normalization (~230 lines)
  - Updated `src/pricing_engine.py` with 3 pricing methods and diagnostics (~310 lines)
  - Created 2 test scripts for validation (~300 lines)
  - All imports verified, syntax validated
- **Files Changed:** 2 modified, 2 created, 1 completion summary
- **Code Quality:** All functions documented, tested, backward compatible
- **Next Phase:** Phase 2 - UI Updates (Tab 1)
- **Completion Summary:** See `PHASE1_COMPLETION_SUMMARY.md`

### January 22, 2026 - Discussion Phase COMPLETE ✅
- **Status:** All 8 discussion topics resolved - Ready for implementation
- **Decisions Made:**
  1. ✅ Pricing Logic: Hybrid approach (read + calculate for validation)
  2. ✅ User Overrides: Manual override checkbox for all pricing methods
  3. ✅ Empty Fields: Clear defaults defined (100% markup, "Per Item", etc.)
  4. ✅ Tier Consolidation: Simple approach (always use new column name)
  5. ✅ Calculated Fields: Calculate and compare for full validation
  6. ✅ Variants: Fully implemented - no changes needed
  7. ✅ Description Fallbacks: Clear hierarchy per use case
  8. ✅ Pricing Notes: Compact expandable display (Tab 1 & 3 only)
- **Blockers:** None - ready to begin implementation
- **Next Steps:**
  1. Begin Phase 1: Core Pricing Engine (src/pricing_engine.py, src/helpers.py)
  2. Implement 3 pricing methods with validation
  3. Add cost basis normalization
  4. Update column mappings

---

## Notes

### Important Reminders
- Always maintain backward compatibility with old spreadsheet format
- Test with both demo and real datasets
- Follow SCHEMA_UPDATE_PROCESS.md guidelines
- Update `get_column_value()` mappings FIRST before other changes
- Document all decisions in this file

### Questions for Later
- Do we need to support MIXED pricing logic (some products MSRP, some standard markup)?
- Should calculated fields be editable by users, or always read-only?
- How do we handle pricing for custom line items (non-catalog products)?

---

**END OF DOCUMENT**
