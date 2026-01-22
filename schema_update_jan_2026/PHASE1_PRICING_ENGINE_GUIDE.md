# Phase 1: Core Pricing Engine Implementation Guide

**Status:** 📋 Ready to Start

**Estimated Time:** 4-6 hours

**Complexity:** HIGH - Core business logic changes

---

## Prerequisites

**Must Read First:**
1. `MASTER_TRACKING.md` in this folder - Complete context and decisions
2. `../schema_reference.md` - New schema (44 columns)
3. `RESUME_PROMPTS.md` - Use Phase 1 resume prompt if starting fresh

**Dependencies:**
- Python 3.x
- pandas library
- Existing codebase knowledge (src/helpers.py, src/pricing_engine.py)

---

## Phase 1 Scope

**Goal:** Implement the new pricing calculation engine with 3 pricing methods, cost basis normalization, and validation.

**Files to Modify:**
1. `src/helpers.py` (~15 changes, ~100 lines added)
2. `src/pricing_engine.py` (~8 changes, ~200 lines added)

**Files to Create:**
3. `scripts/features/test_new_pricing_logic.py` (new test script)
4. `scripts/features/test_cost_basis.py` (new test script)

**What This Phase Does NOT Include:**
- UI updates (Phase 2)
- Tab-specific logic (Phase 2)
- Testing with live app (Phase 3)

---

## Implementation Checklist

### Step 1: Update Column Mappings in `src/helpers.py`

**Location:** `get_column_value()` function

**Changes Needed:**

```python
def get_column_value(row, canonical_name, default=None):
    """
    Get column value with empty cell handling.
    Assumes NEW schema format (Jan 2026+).
    """

    # ADD these new mappings:
    column_mappings = {
        # NEW: Pricing Logic field
        'pricing_logic': {
            'column': 'Pricing Logic',
            'default': 'Standard markup'  # If empty
        },

        # NEW: Cost Basis field
        'cost_basis': {
            'column': 'Cost Basis (Per Item/Per Package)',
            'default': 'Per Item'  # If empty
        },

        # NEW: Shipping Add-On % field
        'shipping_addon_pct': {
            'column': 'Shipping Add-On % (of Cost)',
            'default': 0.0  # If empty
        },

        # UPDATED: Tier 1/No Tiers consolidated column
        'pbp_cost_base': {
            'column': 'PBP Cost (No Tiers/Tier 1)',
            'default': 0.0
        },

        # UPDATED: Description fields with fallbacks
        'purchase_description': {
            'column': 'Purchase Description (to Partner)',
            'fallback_columns': ['Product/Service']
        },

        'billing_description': {
            'column': 'Billing Description (to Client)',
            'fallback_columns': [
                'Marketing Description (Website)',
                'Product/Service'
            ]
        },

        'marketing_description': {
            'column': 'Marketing Description (Website)',
            'fallback_columns': [
                'Billing Description (to Client)',
                'Product/Service'
            ]
        },

        # NEW: Calculated fields (for validation)
        'vendor_markup_calculated': {
            'column': 'Vendor Markup (No Tiers, Calculated)',
            'default': None  # Optional field
        },

        'pbp_markup_calculated': {
            'column': 'PBP Markup (Vendor+Add-On, No Tiers)',
            'default': None  # Optional field
        },

        'pbp_msrp_calculated': {
            'column': 'PBP MSRP (Per-Unit, No Tiers, Calculated)',
            'default': None  # Optional field
        },

        'pbp_msrp_website': {
            'column': 'PBP MSRP (Website)',
            'default': None  # Optional field
        },

        # NEW: Governance fields
        'pricing_notes': {
            'column': 'Pricing Notes',
            'default': ''  # Empty string if missing
        },

        'data_collection_notes': {
            'column': 'Data Collection Notes',
            'default': ''  # Empty string if missing
        },
    }

    # Implementation logic for fallback columns
    # ... (existing logic with updates)
```

**Test Criteria:**
- [ ] All new column names return correct values
- [ ] Default values work when cells are empty
- [ ] Fallback hierarchy works for description fields

---

### Step 2: Add Cost Basis Normalization Function

**Location:** `src/helpers.py` (new function)

**Add This Function:**

```python
def normalize_cost_to_per_item(product_data, base_cost):
    """
    Normalize cost to per-item basis using Cost Basis field.

    Args:
        product_data: Product row from spreadsheet
        base_cost: Base cost from tier or no-tier column

    Returns:
        float: Per-item cost

    Examples:
        >>> # Per Item basis (no normalization)
        >>> normalize_cost_to_per_item({'Cost Basis': 'Per Item'}, 10.0)
        10.0

        >>> # Per Package basis (normalize)
        >>> normalize_cost_to_per_item({
        ...     'Cost Basis (Per Item/Per Package)': 'Per Package',
        ...     'Units per Package': 6
        ... }, 48.0)
        8.0  # 48 / 6 = 8 per item
    """
    # Get cost basis (default to "Per Item" if empty)
    cost_basis = get_column_value(product_data, 'cost_basis', 'Per Item')

    if cost_basis == "Per Package":
        # Get units per package (required if Per Package)
        units_per_package = get_column_value(product_data, 'units_per_package', 1)

        # Validate
        if units_per_package <= 0:
            print(f"⚠️ Warning: Invalid Units per Package ({units_per_package}) for {product_data.get('Product/Service', 'Unknown')}. Using 1.")
            units_per_package = 1

        # Normalize: divide package cost by units
        per_item_cost = base_cost / units_per_package
        return per_item_cost

    else:  # "Per Item" or empty
        # Already per-item, no normalization needed
        return base_cost
```

**Test Criteria:**
- [ ] Per Item basis returns cost unchanged
- [ ] Per Package basis divides by units correctly
- [ ] Empty cost basis defaults to "Per Item"
- [ ] Invalid units per package defaults to 1 with warning

---

### Step 3: Add Pricing Logic Helper Functions

**Location:** `src/helpers.py` (new functions)

**Add These Functions:**

```python
def get_pricing_logic(product_data):
    """
    Get pricing logic method for product.

    Returns:
        str: One of "MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"

    Example:
        >>> get_pricing_logic(product_data)
        'MSRP + % of cost'
    """
    return get_column_value(product_data, 'pricing_logic', 'Standard markup')


def get_shipping_addon_percent(product_data):
    """
    Get shipping add-on percentage for MSRP-based pricing.

    Returns:
        float: Percentage (0-100)

    Example:
        >>> get_shipping_addon_percent(product_data)
        25.0  # 25% of cost
    """
    return get_column_value(product_data, 'shipping_addon_pct', 0.0)
```

**Test Criteria:**
- [ ] Returns correct pricing logic from spreadsheet
- [ ] Defaults to "Standard markup" if empty
- [ ] Shipping add-on returns float percentage

---

### Step 4: Implement Three Pricing Methods

**Location:** `src/pricing_engine.py` (new function)

**Add This Core Function:**

```python
def calculate_pbp_msrp(product_data, quantity, user_markup_override=None):
    """
    Calculate PBP MSRP using one of three pricing methods.

    Pricing Methods:
    1. "MSRP + % of cost" - Add shipping recovery to vendor MSRP
    2. "MSRP capped – ship absorbed" - Use vendor MSRP exactly
    3. "Standard markup" - Traditional cost × (1 + markup%)

    Args:
        product_data: Product row from spreadsheet
        quantity: Order quantity
        user_markup_override: Optional user override for markup % (Standard markup only)

    Returns:
        dict: {
            'pbp_msrp': float,              # Final calculated price
            'method_used': str,             # Which pricing method was used
            'calculation_details': dict,     # Breakdown of calculation
            'spreadsheet_msrp': float,      # MSRP from spreadsheet (for comparison)
            'validation_status': str        # 'match', 'mismatch', or 'no_spreadsheet_value'
        }

    Example:
        >>> result = calculate_pbp_msrp(product_data, quantity=100)
        >>> result['pbp_msrp']
        11.00
        >>> result['method_used']
        'MSRP + % of cost'
    """
    from src.helpers import (
        get_pricing_logic,
        get_shipping_addon_percent,
        get_column_value,
        normalize_cost_to_per_item
    )

    # Step 1: Get base cost for quantity (from existing get_unit_price_new_system)
    base_cost, tier_info, tier_num = get_unit_price_new_system(product_data, quantity)

    # Step 2: Normalize cost to per-item basis
    per_item_cost = normalize_cost_to_per_item(product_data, base_cost)

    # Step 3: Get pricing logic method
    pricing_logic = get_pricing_logic(product_data)

    # Step 4: Calculate based on method
    calculation_details = {
        'per_item_cost': per_item_cost,
        'quantity': quantity,
        'tier_info': tier_info
    }

    if pricing_logic == "MSRP + % of cost":
        # Method 1: MSRP + shipping add-on
        vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None)

        if vendor_msrp is None or vendor_msrp == 0:
            # Fallback: No MSRP available, use Standard markup
            print(f"⚠️ Warning: No MSRP available for '{product_data.get('Product/Service', 'Unknown')}' - using Standard markup instead")
            pricing_logic = "Standard markup"
            # Continue to Standard markup logic below
        else:
            shipping_addon_pct = get_shipping_addon_percent(product_data)
            shipping_addon_amount = (shipping_addon_pct / 100) * per_item_cost
            pbp_msrp = vendor_msrp + shipping_addon_amount

            calculation_details.update({
                'vendor_msrp': vendor_msrp,
                'shipping_addon_pct': shipping_addon_pct,
                'shipping_addon_amount': shipping_addon_amount
            })

            method_used = "MSRP + % of cost"

    if pricing_logic == "MSRP capped – ship absorbed":
        # Method 2: MSRP exactly
        vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None)

        if vendor_msrp is None or vendor_msrp == 0:
            # Fallback: No MSRP available, use Standard markup
            print(f"⚠️ Warning: No MSRP available for '{product_data.get('Product/Service', 'Unknown')}' - using Standard markup instead")
            pricing_logic = "Standard markup"
            # Continue to Standard markup logic below
        else:
            pbp_msrp = vendor_msrp

            calculation_details.update({
                'vendor_msrp': vendor_msrp,
                'shipping_absorbed': True
            })

            method_used = "MSRP capped – ship absorbed"

    if pricing_logic == "Standard markup":
        # Method 3: Traditional markup
        if user_markup_override is not None:
            markup_percent = user_markup_override
        else:
            # Default to 100% markup (cost × 2.0)
            markup_percent = 100.0

        pbp_msrp = per_item_cost * (1 + markup_percent / 100)

        calculation_details.update({
            'markup_percent': markup_percent,
            'markup_amount': per_item_cost * (markup_percent / 100)
        })

        method_used = "Standard markup"

    # Step 5: Get spreadsheet calculated MSRP for validation
    spreadsheet_msrp = get_column_value(product_data, 'pbp_msrp_calculated', None)

    # Step 6: Validate against spreadsheet
    if spreadsheet_msrp is not None:
        # Compare with epsilon tolerance
        if abs(pbp_msrp - spreadsheet_msrp) < 0.01:
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
            print(f"⚠️ Validation: Price mismatch for '{product_data.get('Product/Service', 'Unknown')}'")
            print(f"   Spreadsheet: ${spreadsheet_msrp:.2f} | Calculated: ${pbp_msrp:.2f}")
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'pbp_msrp': pbp_msrp,
        'method_used': method_used,
        'calculation_details': calculation_details,
        'spreadsheet_msrp': spreadsheet_msrp,
        'validation_status': validation_status
    }
```

**Test Criteria:**
- [ ] MSRP + % of cost calculates correctly
- [ ] MSRP capped uses vendor MSRP exactly
- [ ] Standard markup applies 100% default correctly
- [ ] Fallback to Standard markup when MSRP missing
- [ ] Validation compares to spreadsheet values
- [ ] Returns complete calculation details

---

### Step 5: Add Diagnostic Markup Calculation Functions

**Location:** `src/pricing_engine.py` (new functions)

**Add These Functions:**

```python
def calculate_vendor_markup(product_data, per_item_cost):
    """
    Calculate vendor's implied markup percentage.

    Formula: ((Vendor MSRP / per-item cost) - 1) × 100

    Args:
        product_data: Product row from spreadsheet
        per_item_cost: Normalized per-item cost

    Returns:
        dict: {
            'vendor_markup_pct': float or None,
            'spreadsheet_value': float or None,
            'validation_status': str
        }

    Example:
        >>> calculate_vendor_markup(product_data, 4.0)
        {'vendor_markup_pct': 150.0, 'spreadsheet_value': 150.0, 'validation_status': 'match'}
    """
    from src.helpers import get_column_value

    vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None)

    if vendor_msrp is None or vendor_msrp == 0 or per_item_cost == 0:
        return {
            'vendor_markup_pct': None,
            'spreadsheet_value': None,
            'validation_status': 'no_msrp'
        }

    # Calculate markup
    vendor_markup_pct = ((vendor_msrp / per_item_cost) - 1) * 100

    # Get spreadsheet value for comparison
    spreadsheet_value = get_column_value(product_data, 'vendor_markup_calculated', None)

    # Validate
    if spreadsheet_value is not None:
        if abs(vendor_markup_pct - spreadsheet_value) < 0.5:  # 0.5% tolerance
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'vendor_markup_pct': vendor_markup_pct,
        'spreadsheet_value': spreadsheet_value,
        'validation_status': validation_status
    }


def calculate_pbp_markup(pbp_msrp, per_item_cost, product_data):
    """
    Calculate PBP's final markup percentage.

    Formula: ((PBP MSRP / per-item cost) - 1) × 100

    Args:
        pbp_msrp: PBP's calculated MSRP
        per_item_cost: Normalized per-item cost
        product_data: Product row from spreadsheet

    Returns:
        dict: {
            'pbp_markup_pct': float,
            'spreadsheet_value': float or None,
            'validation_status': str
        }

    Example:
        >>> calculate_pbp_markup(11.0, 4.0, product_data)
        {'pbp_markup_pct': 175.0, 'spreadsheet_value': 175.0, 'validation_status': 'match'}
    """
    from src.helpers import get_column_value

    if per_item_cost == 0:
        return {
            'pbp_markup_pct': 0.0,
            'spreadsheet_value': None,
            'validation_status': 'invalid_cost'
        }

    # Calculate markup
    pbp_markup_pct = ((pbp_msrp / per_item_cost) - 1) * 100

    # Get spreadsheet value for comparison
    spreadsheet_value = get_column_value(product_data, 'pbp_markup_calculated', None)

    # Validate
    if spreadsheet_value is not None:
        if abs(pbp_markup_pct - spreadsheet_value) < 0.5:  # 0.5% tolerance
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'pbp_markup_pct': pbp_markup_pct,
        'spreadsheet_value': spreadsheet_value,
        'validation_status': validation_status
    }
```

**Test Criteria:**
- [ ] Vendor markup calculates correctly
- [ ] PBP markup calculates correctly
- [ ] Validation compares to spreadsheet values
- [ ] Handles missing MSRP gracefully

---

### Step 6: Update Tier Lookup Logic

**Location:** `src/pricing_engine.py` - `get_unit_price_new_system()` function

**Changes Needed:**

```python
def get_unit_price_new_system(product_data, quantity):
    """
    Get unit price based on quantity and tier structure.

    UPDATED: Now uses consolidated "PBP Cost (No Tiers/Tier 1)" column

    ... existing docstring ...
    """
    from src.helpers import get_column_value, parse_tier_info

    # Check if product has tiers
    has_tiers = str(product_data.get('Pricing Tiers (Y/N)', 'N')).strip().upper() == 'Y'

    if not has_tiers:
        # No tiers - use consolidated column
        base_price = get_column_value(product_data, 'pbp_cost_base', 0.0)
        return base_price, 'No Tiers', None

    # Has tiers - parse tier info and determine tier
    tier_info_str = product_data.get('Pricing Tiers Info', '')
    tier_dict = parse_tier_info(tier_info_str)

    if not tier_dict:
        # Tier parsing failed - use consolidated column as fallback
        base_price = get_column_value(product_data, 'pbp_cost_base', 0.0)
        return base_price, 'No Tiers', None

    # Determine which tier this quantity falls into
    tier_num = determine_tier_number(quantity, tier_dict)

    if tier_num == 1:
        # Tier 1 - use consolidated column
        base_price = get_column_value(product_data, 'pbp_cost_base', 0.0)
    else:
        # Tier 2-6 - use tier-specific columns
        tier_col = f'PBP Cost: Tier {tier_num}'
        base_price = get_column_value(product_data, tier_col, 0.0)

    # Get tier range for display
    tier_range = tier_dict.get(tier_num, ('Unknown', 'Unknown'))
    tier_range_str = f"{tier_range[0]}-{tier_range[1]}" if tier_range[1] != float('inf') else f"{tier_range[0]}+"

    return base_price, tier_range_str, tier_num
```

**Test Criteria:**
- [ ] No tiers uses consolidated column
- [ ] Tier 1 uses consolidated column
- [ ] Tiers 2-6 use tier-specific columns
- [ ] Tier parsing works correctly
- [ ] Fallback to consolidated column if parsing fails

---

### Step 7: Create Test Scripts

**File 1:** `scripts/features/test_new_pricing_logic.py`

```python
"""
Test new pricing logic with 3 pricing methods.

Usage:
    streamlit run scripts/features/test_new_pricing_logic.py
"""

import streamlit as st
from src.data_loader import load_pricing_data
from src.pricing_engine import calculate_pbp_msrp

st.title("Test New Pricing Logic")

# Load data
df_template, _, _ = load_pricing_data('demo')

st.write(f"Loaded {len(df_template)} products")

# Test each pricing method
st.header("Pricing Method Tests")

for idx, row in df_template.iterrows():
    product_name = row.get('Product/Service', 'Unknown')
    pricing_logic = row.get('Pricing Logic', 'Standard markup')

    st.subheader(f"{product_name}")
    st.write(f"Pricing Logic: **{pricing_logic}**")

    # Calculate price at quantity 100
    result = calculate_pbp_msrp(row, quantity=100)

    st.write(f"**Calculated PBP MSRP:** ${result['pbp_msrp']:.2f}")
    st.write(f"**Method Used:** {result['method_used']}")

    if result['spreadsheet_msrp']:
        st.write(f"**Spreadsheet MSRP:** ${result['spreadsheet_msrp']:.2f}")

        if result['validation_status'] == 'match':
            st.success("✓ Validation: Match")
        elif result['validation_status'] == 'mismatch':
            st.error(f"⚠️ Validation: Mismatch (${abs(result['pbp_msrp'] - result['spreadsheet_msrp']):.2f} difference)")

    with st.expander("Calculation Details"):
        st.json(result['calculation_details'])

    st.divider()
```

**File 2:** `scripts/features/test_cost_basis.py`

```python
"""
Test cost basis normalization (Per Item vs Per Package).

Usage:
    streamlit run scripts/features/test_cost_basis.py
"""

import streamlit as st
from src.data_loader import load_pricing_data
from src.helpers import normalize_cost_to_per_item

st.title("Test Cost Basis Normalization")

# Load data
df_template, _, _ = load_pricing_data('demo')

st.write(f"Loaded {len(df_template)} products")

# Test normalization
st.header("Cost Basis Tests")

for idx, row in df_template.iterrows():
    product_name = row.get('Product/Service', 'Unknown')
    cost_basis = row.get('Cost Basis (Per Item/Per Package)', 'Per Item')
    base_cost = row.get('PBP Cost (No Tiers/Tier 1)', 0)

    if cost_basis == 'Per Package':
        st.subheader(f"{product_name} (Per Package)")

        units_per_package = row.get('Units per Package', 1)
        per_item_cost = normalize_cost_to_per_item(row, base_cost)

        st.write(f"**Package Cost:** ${base_cost:.2f}")
        st.write(f"**Units per Package:** {units_per_package}")
        st.write(f"**Per-Item Cost:** ${per_item_cost:.2f}")
        st.write(f"**Formula:** ${base_cost:.2f} / {units_per_package} = ${per_item_cost:.2f}")

        st.divider()
```

**Test Criteria:**
- [ ] Test script runs without errors
- [ ] All pricing methods tested
- [ ] Cost basis normalization tested
- [ ] Validation results displayed correctly

---

## Validation Checklist

After completing all steps, verify:

- [ ] All new functions have docstrings with examples
- [ ] All functions handle empty/missing values correctly
- [ ] Test scripts run successfully
- [ ] No hardcoded column names (all use get_column_value())
- [ ] Validation warnings print to console
- [ ] Code follows existing style conventions
- [ ] No breaking changes to existing functions (unless documented)

---

## Success Criteria

**Phase 1 is complete when:**

1. ✅ All column mappings updated in `get_column_value()`
2. ✅ Cost basis normalization function implemented and tested
3. ✅ Three pricing methods implemented in `calculate_pbp_msrp()`
4. ✅ Diagnostic markup functions implemented
5. ✅ Tier lookup updated to use consolidated column
6. ✅ Test scripts created and passing
7. ✅ Validation logic compares spreadsheet to calculated values
8. ✅ Code reviewed for quality and style

**Verification:**
- Run `streamlit run scripts/features/test_new_pricing_logic.py`
- Run `streamlit run scripts/features/test_cost_basis.py`
- All tests pass, no errors

---

## Next Phase

**After Phase 1 is complete:**
- Move to Phase 2: UI Updates (Tab 1)
- See `PHASE2_UI_UPDATES_GUIDE.md`
- Use Phase 2 resume prompt from `RESUME_PROMPTS.md`

---

## Notes

- Keep all code beginner-friendly and well-commented
- Print warnings for data quality issues (don't fail silently)
- Always compare calculated values to spreadsheet values
- Test with both demo and real datasets before marking complete

---

**END OF PHASE 1 GUIDE**
