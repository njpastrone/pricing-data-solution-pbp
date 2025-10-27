# Markup & Pricing Section Refinement Plan

**Created:** 2025-10-15
**Status:** Planning
**Priority:** Medium - UX Enhancement

---

## Overview

Reorganize Section 3 into two separate sections: one focused on quantity/markup/pricing (new Section 3), and one focused on customization (new Section 4). This provides better separation of concerns and clearer pricing visibility.

---

## Current State Analysis

**Current Section 3 "Customize Product":**
- Contains: Quantity input, Markup % input, Customization checkbox, Customization cost inputs
- Issues: Mixes pricing/markup with customization, no clear view of customer pricing impact

**Current Section 4 "Product Preview":**
- Shows final totals and "Add to Order" button
- Will become new Section 5

---

## Proposed Changes

### **NEW SECTION 3: "Quantity & Pricing"**

**Purpose:** Focus on core pricing decisions - quantity, markup, and customer-facing price

**Layout:**
```
═══════════════════════════════════════════════════════════
Section 3: Quantity & Pricing

┌─────────────────────────────────────────────────────────┐
│ Quantity Selection                                       │
├─────────────────────────────────────────────────────────┤
│ Quantity: [____100____] units                           │
│                                                          │
│ Using pricing tier: 51-100 units | Base price: $9.00    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Partner MSRP (Reference)                                │
├─────────────────────────────────────────────────────────┤
│ [✓] Show Partner MSRP                                   │
│                                                          │
│ Partner MSRP: $_____ (Optional - for reference only)    │
│ ℹ️ This is the partner's suggested retail price         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Markup Configuration                                    │
├─────────────────────────────────────────────────────────┤
│ Markup %: [____100____]%                                │
│                                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ Pricing Breakdown (Before Customization)                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                          │
│ Base Cost (Partner):         $9.00/unit → $900.00 total│
│ Your Markup (100%):         $9.00/unit → $900.00 total │
│ ─────────────────────────────────────────────────────── │
│ Customer Price (No Custom): $18.00/unit → $1,800.00    │
│                                                          │
│ ℹ️ This is the base product price before customization, │
│    tariffs, or shipping                                 │
│                                                          │
│ [Optional] Compare to Partner MSRP:                     │
│ Partner MSRP:     $22.00/unit (if entered)              │
│ Your Price:       $18.00/unit                           │
│ Difference:       -$4.00 (18% below MSRP)               │
└─────────────────────────────────────────────────────────┘
═══════════════════════════════════════════════════════════
```

---

### **NEW SECTION 4: "Customization Options"**

**Purpose:** Handle all customization-related decisions separately

**Layout:**
```
═══════════════════════════════════════════════════════════
Section 4: Customization Options

Customization Options: Custom labels, branding, logo printing

[✓] Add customization to this product

┌─────────────────────────────────────────────────────────┐
│ Customization Costs                                      │
├─────────────────────────────────────────────────────────┤
│ Customization Setup Fee:    $___50.00___                │
│ Customization Cost per Unit: $___4.00___                │
│                                                          │
│ Total Customization Cost:                               │
│   Setup Fee:       $50.00 (one-time)                    │
│   Per-Unit Cost:   $4.00 × 100 = $400.00               │
│   ──────────────────────────────────────────────────────│
│   Total:           $450.00                              │
│   Per-Unit Impact: $4.50/unit                           │
└─────────────────────────────────────────────────────────┘
═══════════════════════════════════════════════════════════
```

---

### **NEW SECTION 5: "Product Preview"**

**Purpose:** Final pricing preview with all options included (same as current Section 4)

**Layout:**
```
═══════════════════════════════════════════════════════════
Section 5: Product Preview

Using pricing tier: 51-100 units | Base price: $9.00 per unit

✅ Product Total: $2,250.00 (100 units @ $22.50 each)

[➕ Add to Order] (full width button)

▼ Detailed Price Breakdown
┌─────────────────────────────────────────────────────────┐
│ Item                          │ Per Unit  │ Total       │
├─────────────────────────────────────────────────────────┤
│ Base Price (tier: 51-100)    │ $9.00     │ $900.00     │
│ Customization Setup Fee       │ $0.50     │ $50.00      │
│ Customization per Unit        │ $4.00     │ $400.00     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ **Subtotal**                  │ **$13.50**│ **$1,350.00**│
│ Markup (100%)                 │ $9.00     │ $900.00     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ **Product Total**             │ **$22.50**│ **$2,250.00**│
└─────────────────────────────────────────────────────────┘
═══════════════════════════════════════════════════════════
```

---

## Implementation Plan

### **Phase 1: Data Structure Updates**

**1.1 Add Partner MSRP to order_item dictionary:**
```python
order_item = {
    ...existing fields...
    'partner_msrp_per_unit': optional_msrp_value,  # User-entered or from spreadsheet
    'show_msrp_comparison': bool  # Whether to show MSRP comparison
}
```

**1.2 Check if spreadsheet has MSRP column:**
- Review RESTRUCTURE_CONTEXT.md for MSRP field
- If not present, add user input field only
- Store in session state for future reference

---

### **Phase 2: Create New Section 3 "Quantity & Pricing"**

**Location:** Replace current Section 3 header and quantity/markup inputs (around line 748)

**2.1 Quantity Selection Subsection:**
```python
st.header("3. Quantity & Pricing")

st.subheader("Quantity Selection")
quantity = st.number_input(
    "Quantity",
    min_value=1,
    value=1,
    step=1,
    key="input_quantity"
)

# Show tier being used
base_price, tier_range, tier_column = get_unit_price_new_system(product_data, quantity)
if base_price:
    if tier_range == "No Tiers":
        st.caption(f"Flat pricing: ${base_price:.2f} per unit")
    else:
        st.caption(f"Using pricing tier: {tier_range} units | Base price: ${base_price:.2f} per unit")
```

**2.2 Partner MSRP Subsection:**
```python
st.divider()
st.subheader("Partner MSRP (Reference)")

show_msrp = st.checkbox(
    "Show Partner MSRP comparison",
    value=False,
    key="show_msrp_checkbox",
    help="Display partner's suggested retail price for reference"
)

if show_msrp:
    # Check if MSRP exists in spreadsheet
    default_msrp = clean_price(product_data.get('Partner MSRP', '')) or 0.0

    partner_msrp = st.number_input(
        "Partner MSRP (per unit)",
        min_value=0.0,
        value=float(default_msrp),
        step=1.0,
        key="input_partner_msrp",
        help="Optional - Partner's suggested retail price for reference"
    )

    st.caption("This is the partner's suggested retail price - for reference only")
```

**2.3 Markup Configuration Subsection:**
```python
st.divider()
st.subheader("Markup Configuration")

markup_percent = st.number_input(
    "Markup %",
    min_value=0.0,
    value=100.0,
    step=5.0,
    key="input_markup",
    help="Your profit margin. 100% = double the cost (2x), 50% = 1.5x the cost, 200% = triple the cost (3x)"
)

# Calculate pricing breakdown (no customization yet)
product_subtotal = base_price * quantity
markup_amount = product_subtotal * (markup_percent / 100)
customer_price_no_custom = product_subtotal + markup_amount
customer_price_per_unit = customer_price_no_custom / quantity

# Display pricing breakdown
st.markdown("**Pricing Breakdown (Before Customization)**")

breakdown_data = [
    ["Base Cost (Partner)", f"${base_price:.2f}/unit", f"${product_subtotal:.2f} total"],
    ["Your Markup ({:.0f}%)".format(markup_percent), f"${markup_amount/quantity:.2f}/unit", f"${markup_amount:.2f} total"],
    ["", "", ""],
    ["**Customer Price (No Custom)**", f"**${customer_price_per_unit:.2f}/unit**", f"**${customer_price_no_custom:.2f}**"]
]

breakdown_df = pd.DataFrame(breakdown_data, columns=["Item", "Per Unit", "Total"])
st.table(breakdown_df)

st.caption("This is the base product price before customization, tariffs, or shipping")

# MSRP Comparison (if enabled)
if show_msrp and partner_msrp > 0:
    st.markdown("**Compare to Partner MSRP:**")

    msrp_diff = customer_price_per_unit - partner_msrp
    msrp_diff_percent = (msrp_diff / partner_msrp * 100) if partner_msrp > 0 else 0

    comparison_data = [
        ["Partner MSRP", f"${partner_msrp:.2f}/unit"],
        ["Your Price", f"${customer_price_per_unit:.2f}/unit"],
        ["Difference", f"${msrp_diff:.2f} ({msrp_diff_percent:+.1f}%)"]
    ]

    comparison_df = pd.DataFrame(comparison_data, columns=["Item", "Price"])
    st.table(comparison_df)

    if msrp_diff < 0:
        st.caption(f"Your price is {abs(msrp_diff_percent):.1f}% below Partner MSRP")
    elif msrp_diff > 0:
        st.caption(f"Your price is {msrp_diff_percent:.1f}% above Partner MSRP")
    else:
        st.caption("Your price matches Partner MSRP")
```

---

### **Phase 3: Update Section 4 "Customization Options"**

**Location:** Move existing customization code down, rename header

**3.1 Update Header:**
```python
st.divider()
st.header("4. Customization Options")
```

**3.2 Keep existing customization code:**
- Customization info display
- Checkbox for "Add customization"
- Setup fee and per-unit cost inputs

**3.3 Add customization cost summary:**
```python
if include_customization:
    # ... existing input fields ...

    # Show customization cost summary
    st.markdown("**Total Customization Cost:**")

    customization_setup_total = customization_setup_fee_input
    customization_unit_total = customization_per_unit_input * quantity
    total_customization = customization_setup_total + customization_unit_total
    per_unit_impact = total_customization / quantity if quantity > 0 else 0

    summary_data = [
        ["Setup Fee", f"${customization_setup_total:.2f} (one-time)"],
        ["Per-Unit Cost", f"${customization_per_unit_input:.2f} × {quantity} = ${customization_unit_total:.2f}"],
        ["", ""],
        ["**Total**", f"**${total_customization:.2f}**"],
        ["**Per-Unit Impact**", f"**${per_unit_impact:.2f}/unit**"]
    ]

    summary_df = pd.DataFrame(summary_data, columns=["Item", "Amount"])
    st.table(summary_df)
```

---

### **Phase 4: Update Section 5 "Product Preview"**

**Location:** Rename from Section 4 to Section 5 (around line 813)

**4.1 Update header:**
```python
st.divider()
st.header("5. Product Preview")
```

**4.2 Keep existing logic:**
- All calculation logic stays the same
- Display tier being used
- Show final product total
- Detailed breakdown expander
- Add to Order button

**4.3 Update order_item to include MSRP:**
```python
# In the "Add to Order" button logic:
order_item = {
    ...existing fields...
    'partner_msrp_per_unit': partner_msrp if show_msrp else 0.0,
    'show_msrp_comparison': show_msrp
}
```

---

### **Phase 5: Update All Subsequent Sections**

**5.1 Renumber sections:**
- Current Section 5 → Section 6 "Current Order"
- Current Section 6 → Section 7 "Order Settings"
- Current Section 7 → Section 8 "Order Summary"
- Current Section 8 → Section 9 "Proposal"
- Current Section 9 → Section 10 "Invoice"
- Current Section 10 → Section 11 "Purchase Order"

**5.2 Update headers in code:**
```python
# Find and replace:
st.header("5. Current Order")  → st.header("6. Current Order")
st.header("6. Order Settings") → st.header("7. Order Settings")
st.header("7. Order Summary")  → st.header("8. Order Summary")
st.header("8. Proposal")       → st.header("9. Proposal")
st.header("9. Invoice")        → st.header("10. Invoice")
st.header("10. Purchase Order")→ st.header("11. Purchase Order")
```

---

### **Phase 6: Update Instructions Sidebar**

**6.1 Update step numbers:**
```python
# In sidebar "How to Use This App" (around line 200):
"""
**Step-by-step guide:**

1. **Enter Client Information** - Company, contact, payment terms (optional but recommended)
2. **Select Partner & Product** - Choose from dropdowns
3. **Set Quantity & Markup** - See pricing breakdown and markup impact
4. **Add Customization (Optional)** - Custom labels, branding, etc.
5. **Review Product Preview** - Check the final pricing breakdown
6. **Add to Order** - Click "Add to Order" button
7. **Repeat** - Add more products if needed
8. **Configure Order Settings** - Shipping, tariff, discounts, credit card fees
9. **Generate Deliverables** - Proposal (with MOQ), Invoice, or Purchase Order
"""
```

---

## Benefits of This Approach

1. **Clearer Separation of Concerns:**
   - Section 3: Core pricing decisions (quantity, markup)
   - Section 4: Optional customization
   - Section 5: Final preview

2. **Better Pricing Visibility:**
   - Users see exactly how markup affects customer pricing
   - Per-unit and total costs clearly displayed
   - MSRP comparison provides market context

3. **More Intuitive Flow:**
   - Quantity → Base Pricing → Markup → Customization → Preview
   - Each section builds on the previous

4. **Reference Information:**
   - Partner MSRP provides helpful pricing context
   - Optional field doesn't clutter interface if not needed

5. **Maintains Simplicity:**
   - All existing calculations remain unchanged
   - Just reorganized and clarified
   - No breaking changes to data structure

---

## Testing Checklist

- [ ] Quantity selection updates base price correctly
- [ ] Tier information displays properly
- [ ] Partner MSRP checkbox shows/hides MSRP input
- [ ] MSRP comparison calculates correctly (difference and percentage)
- [ ] Markup breakdown shows accurate per-unit and total costs
- [ ] Pricing breakdown table displays properly
- [ ] Customization section displays cost summary
- [ ] Customization per-unit impact calculates correctly
- [ ] Product Preview calculates final totals correctly
- [ ] All sections properly numbered (3, 4, 5, 6, 7, 8, 9, 10, 11)
- [ ] Sidebar instructions match new section numbers
- [ ] Add to Order button includes MSRP data in order_item
- [ ] Order item stores all new fields correctly
- [ ] MSRP data persists when editing products
- [ ] MSRP comparison doesn't show if MSRP is 0 or not entered

---

## Notes

**MSRP Field in Spreadsheet:**
- Need to check if "Partner MSRP" column exists in master_pricing_template_10_14
- If not available, MSRP will be user-input only
- Future: Can add MSRP column to spreadsheet for automatic population

**Variable Scope:**
- `quantity` and `markup_percent` moved to Section 3
- Need to ensure these variables are accessible in Section 4 (Customization)
- Variables should naturally flow down due to linear execution

**Edge Cases:**
- Handle division by zero when quantity = 0
- Handle MSRP comparison when MSRP = 0
- Ensure pricing breakdown shows correctly for both tiered and non-tiered products

---

**Status:** Ready for implementation
**Estimated Effort:** 2-3 hours
**Priority:** Medium - UX enhancement
