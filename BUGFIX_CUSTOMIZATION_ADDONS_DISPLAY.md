# Bug Fix: Customization Add-Ons Per-Unit Cost Display

**Date:** 2026-01-19
**Status:** ✅ FIXED

## Problem

After adding customization add-ons, the **Pricing Breakdown table** and **Order Summary** were showing incorrect per-unit costs:
- **PBP Cost (Per Unit)** column was blank or showing $0.00
- **Client Price (Per Unit)** was only showing the main customization cost, not including add-ons

## Root Cause

Two locations in the code were using stored field values (`new_partner_perunit_cost` and `new_perunit_cost`) which only contained the main customization costs, **not the add-on costs**.

The totals (`partner_customization_unit_total` and `customization_unit_total`) correctly included add-ons, but the per-unit display was not dividing these totals by quantity.

## Locations Fixed

### 1. Pricing Breakdown Table (Tab 3, Section 2)
**File:** `app.py` lines 5467-5483

**Before:**
```python
breakdown_data.append(
    format_pricing_breakdown_row(
        "Customization Per-Unit",
        effective_custom_qty,
        new_partner_perunit_cost,  # ❌ ONLY main customization
        partner_customization_unit_total,
        new_perunit_cost,  # ❌ ONLY main customization
        customization_unit_total
    )
)
```

**After:**
```python
# Calculate per-unit costs including add-ons
partner_per_unit_with_addons = partner_customization_unit_total / effective_custom_qty if effective_custom_qty > 0 else 0
client_per_unit_with_addons = customization_unit_total / effective_custom_qty if effective_custom_qty > 0 else 0
breakdown_data.append(
    format_pricing_breakdown_row(
        "Customization Per-Unit",
        effective_custom_qty,
        partner_per_unit_with_addons,  # ✅ Includes add-ons
        partner_customization_unit_total,
        client_per_unit_with_addons,  # ✅ Includes add-ons
        customization_unit_total
    )
)
```

### 2. Order Summary (Tab 3, Section 4)
**File:** `app.py` lines 6053-6065

**Before:**
```python
effective_custom_qty = item.get('customization_minimum_qty', item['quantity']) if item.get('apply_custom_minimum', False) else item['quantity']
custom_per_unit = item.get('customization_per_unit', 0)  # ❌ Stored value, no add-ons
pbp_custom_per_unit = unit_pbp / effective_custom_qty if effective_custom_qty > 0 else 0

summary_items.append([
    f"{item['product_name']} - Per Unit",
    effective_custom_qty,
    f"${partner_per_unit:.2f}",  # ❌ Used wrong variable
    f"${unit_pbp:.2f}",
    f"${custom_per_unit:.2f}",  # ❌ ONLY main customization
    f"${unit_client:.2f}"
])
```

**After:**
```python
effective_custom_qty = item.get('customization_minimum_qty', item['quantity']) if item.get('apply_custom_minimum', False) else item['quantity']
# Calculate per-unit costs including add-ons
pbp_custom_per_unit = unit_pbp / effective_custom_qty if effective_custom_qty > 0 else 0
client_custom_per_unit = unit_client / effective_custom_qty if effective_custom_qty > 0 else 0

summary_items.append([
    f"{item['product_name']} - Per Unit",
    effective_custom_qty,
    f"${pbp_custom_per_unit:.2f}",  # ✅ Includes add-ons
    f"${unit_pbp:.2f}",
    f"${client_custom_per_unit:.2f}",  # ✅ Includes add-ons
    f"${unit_client:.2f}"
])
```

## What Changed

1. **Pricing Breakdown Table:** Now calculates per-unit costs by dividing totals (which include add-ons) by quantity
2. **Order Summary:** Now uses calculated per-unit values instead of stored field values
3. Both locations now show accurate per-unit costs including all add-ons

## Example

**Setup:**
- Main Customization: $1.00/unit (to client), $0.50/unit (from partner)
- Add-On #1: $0.50/unit (to client), $0.25/unit (from partner)
- Quantity: 100 units

**Before Fix:**
- PBP Cost (Per Unit): $0.50 ❌ (missing add-on)
- Client Price (Per Unit): $1.00 ❌ (missing add-on)

**After Fix:**
- PBP Cost (Per Unit): $0.75 ✅ ($0.50 + $0.25)
- Client Price (Per Unit): $1.50 ✅ ($1.00 + $0.50)

## Testing

To verify the fix:
1. Navigate to Tab 3
2. Add a product with customization enabled
3. Add a customization add-on with non-zero per-unit costs
4. Check **Section 2 (Pricing Breakdown table)** - verify per-unit costs include add-ons
5. Check **Section 4 (Order Summary)** - verify per-unit costs include add-ons
6. Both sections should show identical per-unit values

## Related

This fix completes the customization add-ons feature implemented earlier today, which added separate PBP Cost vs Client Price fields to add-ons.
