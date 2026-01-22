# Phase 3: UI Updates (Tab 3 - Order & Client Info)

**Status:** 🟡 Not Started
**Estimated Time:** 3-4 hours
**Complexity:** MEDIUM
**Dependencies:** Phase 1 & 2 must be complete

---

## Overview

Update Tab 3 (Order & Client Info) UI to:
1. Use new pricing logic consistently with Tab 1
2. Display validation results for order items
3. Show pricing notes with compact expandable format
4. Maintain manual override functionality
5. Ensure all 4 entry pathways use new pricing

**Files to Modify:**
- `app.py` (Tab 3 sections only)

---

## Pre-Implementation Checklist

Before starting Phase 3, verify:
- [ ] Phase 1 & 2 are complete and tested
- [ ] Tab 1 pricing works correctly with all 3 methods
- [ ] Manual override checkbox functional in Tab 1
- [ ] Read current Tab 3 code in app.py (search for "Tab 3" or "Order & Client Info")
- [ ] Understand 4 entry pathways (Google Form, HTML import, Proposal import, Manual add)

---

## Step-by-Step Implementation

### Step 1: Update Google Form Import (Option A)

**Location:** Option A - Google Form Import section

**Current behavior:** Imports products with default 100% markup

**New behavior:** Calculate markup using new pricing logic

**Code changes:**

```python
# In the form import function, after product matching:

for product_match in matched_products:
    product_data = # ... get from catalog
    quantity = product_match.get('quantity', 1)

    # Calculate pricing using new system
    pricing_result = calculate_pbp_msrp(product_data, quantity)

    # Determine markup based on pricing method
    if pricing_result['method_used'] == "Standard markup":
        markup_pct = pricing_result['calculation_details'].get('diagnostic_markup', 100.0)
    else:
        # MSRP-based method
        base_cost = pricing_result['calculation_details']['base_cost']
        pbp_msrp = pricing_result['pbp_msrp']

        if base_cost > 0:
            markup_pct = ((pbp_msrp / base_cost) - 1) * 100
        else:
            markup_pct = 100.0

    # Create order item with new pricing fields
    order_item = {
        'product': product_name,
        'partner': partner,
        'quantity': quantity,
        'markup': markup_pct,
        'pricing_method': pricing_result['method_used'],  # NEW
        'pricing_notes': pricing_result.get('pricing_notes', ''),  # NEW
        'validation_warning': pricing_result.get('validation_warning', None),  # NEW
        'manual_override': False,  # NEW
        # ... other fields (customization, tariff, etc.)
    }

    st.session_state.order_items.append(order_item)
```

---

### Step 2: Update HTML Order Form Import (Option B)

**Location:** Option B - HTML Order Form Import section

**Current behavior:** Adds products with default 100% markup

**New behavior:** Use new pricing calculation when adding products

**Code changes:**

```python
# In HTML import, after product matching and selection:

for selected_product in selected_products_to_add:
    product_data = # ... get from catalog

    # Use new pricing calculation
    pricing_result = calculate_pbp_msrp(product_data, quantity=1)

    if pricing_result['method_used'] == "Standard markup":
        markup_pct = pricing_result['calculation_details'].get('diagnostic_markup', 100.0)
    else:
        base_cost = pricing_result['calculation_details']['base_cost']
        pbp_msrp = pricing_result['pbp_msrp']
        if base_cost > 0:
            markup_pct = ((pbp_msrp / base_cost) - 1) * 100
        else:
            markup_pct = 100.0

    # Create order item with new fields
    order_item = {
        'product': selected_product['name'],
        'partner': selected_product['partner'],
        'quantity': 1,  # Default, user can edit
        'markup': markup_pct,
        'pricing_method': pricing_result['method_used'],
        'pricing_notes': pricing_result.get('pricing_notes', ''),
        'validation_warning': pricing_result.get('validation_warning', None),
        'manual_override': False,
        # ... other fields
    }

    st.session_state.order_items.append(order_item)
```

---

### Step 3: Update Proposal-to-Order Import (Option C)

**Location:** Option C - Import from Proposal section

**Current behavior:** Imports products from proposal with their markup values

**New behavior:** Preserve pricing method and notes from proposal

**Code changes:**

```python
# When importing from proposal (all products or individual):

for proposal_item in selected_items:
    # Import with all pricing information from proposal
    order_item = {
        'product': proposal_item['product'],
        'partner': proposal_item['partner'],
        'quantity': proposal_item['quantity'],
        'markup': proposal_item['markup'],
        'pricing_method': proposal_item.get('pricing_method', 'Standard markup'),  # NEW
        'pricing_notes': proposal_item.get('pricing_notes', ''),  # NEW
        'validation_warning': proposal_item.get('validation_warning', None),  # NEW
        'manual_override': proposal_item.get('manual_override', False),  # NEW
        # ... other fields
    }

    st.session_state.order_items.append(order_item)
```

---

### Step 4: Update Manual Product Selection (Option D)

**Location:** Option D - Manual Product Selection section

**Current behavior:** "Use MSRP pricing" checkbox calculates markup

**New behavior:** Use new pricing calculation system

**Code changes:**

```python
# When adding product manually via dropdown:

if st.button("Add to Order"):
    selected_product_data = # ... get from catalog

    use_msrp_pricing = st.session_state.get('use_msrp_pricing_tab3', True)

    if use_msrp_pricing:
        # Use new pricing calculation
        pricing_result = calculate_pbp_msrp(selected_product_data, quantity=1)

        if pricing_result['method_used'] == "Standard markup":
            markup_pct = pricing_result['calculation_details'].get('diagnostic_markup', 100.0)
        else:
            base_cost = pricing_result['calculation_details']['base_cost']
            pbp_msrp = pricing_result['pbp_msrp']
            if base_cost > 0:
                markup_pct = ((pbp_msrp / base_cost) - 1) * 100
            else:
                markup_pct = 100.0
    else:
        markup_pct = 100.0
        pricing_result = calculate_pbp_msrp(selected_product_data, quantity=1)

    # Create order item with new pricing fields
    order_item = {
        'product': selected_product_name,
        'partner': selected_partner,
        'quantity': 1,
        'markup': markup_pct,
        'pricing_method': pricing_result['method_used'],
        'pricing_notes': pricing_result.get('pricing_notes', ''),
        'validation_warning': pricing_result.get('validation_warning', None),
        'manual_override': not use_msrp_pricing,  # If MSRP unchecked, treat as override
        # ... other fields
    }

    st.session_state.order_items.append(order_item)
    st.toast(f"✓ Added {selected_product_name} to order")
```

---

### Step 5: Update Order Item Display (Section 2)

**Location:** Section 2 - Current Order (inline product editing)

**Current display:** Product details with quantity, markup, pricing, customization controls

**New display:** Add pricing method indicator and manual override checkbox

**Code changes:**

```python
# In the order items display loop:

for idx, item in enumerate(st.session_state.order_items):
    st.write(f"**{item['product']}** ({item['partner']})")

    # Add pricing method indicator (NEW)
    pricing_method = item.get('pricing_method', 'Standard markup')
    manual_override = item.get('manual_override', False)

    if manual_override:
        st.caption("🔓 Manual Price Override (pricing method ignored)")
    else:
        st.caption(f"Pricing Method: {pricing_method}")

    # Existing controls (quantity, markup, etc.)
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        new_quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=item['quantity'],
            key=f"qty_{idx}",
        )
        if new_quantity != item['quantity']:
            st.session_state.order_items[idx]['quantity'] = new_quantity
            st.rerun()

    with col2:
        new_markup = st.number_input(
            "Markup %",
            min_value=0.0,
            value=item['markup'],
            step=1.0,
            key=f"markup_tab3_{idx}",
        )
        if new_markup != item['markup']:
            st.session_state.order_items[idx]['markup'] = new_markup
            st.session_state.order_items[idx]['manual_override'] = True  # Mark as manual override
            st.rerun()

    with col3:
        # Manual Override Checkbox (NEW)
        override_checked = st.checkbox(
            "Manual Override",
            value=manual_override,
            key=f"override_tab3_{idx}",
            help="Check to manually override pricing method"
        )
        if override_checked != manual_override:
            st.session_state.order_items[idx]['manual_override'] = override_checked
            st.rerun()

    # ... rest of product controls (customization, etc.)
```

---

### Step 6: Add Pricing Notes Display (Tab 3)

**Location:** After Section 2 - Current Order

**Format:** Compact expandable display (same as Tab 1)

**Code changes:**

```python
# After the order items display, add pricing notes section:

# Collect all order items with pricing notes
items_with_notes = [
    item for item in st.session_state.order_items
    if item.get('pricing_notes') and not item.get('manual_override', False)
]

if items_with_notes:
    with st.expander(f"ℹ️ Pricing Information ({len(items_with_notes)} products)", expanded=False):
        for item in items_with_notes:
            st.write(f"**{item['product']}**")
            st.caption(item['pricing_notes'])
            st.write("")  # Spacing
```

---

### Step 7: Add Validation Warnings Display (Tab 3)

**Location:** After pricing notes

**Purpose:** Show products where calculated price doesn't match spreadsheet

**Code changes:**

```python
# Add validation warnings section:

items_with_warnings = [
    item for item in st.session_state.order_items
    if item.get('validation_warning') and not item.get('manual_override', False)
]

if items_with_warnings:
    st.warning(f"⚠️ {len(items_with_warnings)} product(s) have pricing discrepancies")

    with st.expander("View Validation Details", expanded=False):
        for item in items_with_warnings:
            st.write(f"**{item['product']}**")
            st.caption(item['validation_warning'])
            st.write("")
```

---

### Step 8: Update Order Summary Calculations (Section 4)

**Location:** Section 4 - Order Summary

**Current behavior:** Shows line-item breakdown with subtotals

**New behavior:** Ensure calculations use new pricing functions

**Code changes:**

```python
# In order summary calculation, ensure we're using calculate_pbp_msrp():

for item in st.session_state.order_items:
    product_data = # ... get from catalog

    # Calculate price using new system
    pricing_result = calculate_pbp_msrp(
        product_data,
        quantity=item['quantity'],
        user_markup_override=item['markup'] if item.get('manual_override') else None
    )

    base_price = pricing_result['pbp_msrp']

    # Calculate line total
    line_total = base_price * item['quantity']

    # Add customization costs if applicable
    if item.get('add_customization'):
        setup_fee = item.get('customization_setup_fee', 0)
        per_unit_cost = item.get('customization_per_unit', 0)
        line_total += setup_fee + (per_unit_cost * item['quantity'])

    # Add to subtotal
    products_subtotal += line_total

# ... continue with discount, shipping, tariffs, etc.
```

---

### Step 9: Test Tab 3 Changes

**Test Checklist:**

1. **Google Form Import (Option A):**
   - [ ] Products imported with correct pricing method
   - [ ] Markup calculated based on pricing method
   - [ ] Pricing notes populated
   - [ ] Validation warnings appear if discrepancies exist

2. **HTML Import (Option B):**
   - [ ] Products added with correct pricing method
   - [ ] Default markup based on pricing method
   - [ ] All new fields populated

3. **Proposal Import (Option C):**
   - [ ] Pricing method preserved from proposal
   - [ ] Manual override status preserved
   - [ ] Pricing notes transferred correctly

4. **Manual Add (Option D):**
   - [ ] "Use MSRP pricing" checkbox works with new logic
   - [ ] Products added with correct markup
   - [ ] Pricing method set correctly

5. **Order Item Display:**
   - [ ] Pricing method shown for each product
   - [ ] Manual override indicator displays correctly
   - [ ] Override checkbox functional
   - [ ] Editing markup sets manual override flag

6. **Pricing Notes:**
   - [ ] Expandable section shows only items with notes
   - [ ] Count is accurate
   - [ ] Notes hidden when override is checked
   - [ ] Collapsed by default

7. **Validation Warnings:**
   - [ ] Warning appears when calculated ≠ spreadsheet
   - [ ] Expandable details show discrepancies
   - [ ] Warnings hidden when override is checked

8. **Order Summary:**
   - [ ] Calculations use new pricing functions
   - [ ] Totals match displayed prices
   - [ ] Customization costs added correctly

---

## Common Issues & Solutions

### Issue 1: Order Items Missing New Fields
**Problem:** Old order items (from before Phase 3) don't have new fields
**Solution:** Add migration logic at top of Tab 3:
```python
# Migrate old order items to new format
for item in st.session_state.order_items:
    if 'pricing_method' not in item:
        item['pricing_method'] = 'Standard markup'
    if 'pricing_notes' not in item:
        item['pricing_notes'] = ''
    if 'manual_override' not in item:
        item['manual_override'] = False
    if 'validation_warning' not in item:
        item['validation_warning'] = None
```

### Issue 2: Saved Orders Not Loading
**Problem:** Orders saved before Phase 3 missing new fields
**Solution:** Update `order_manager.py` load function to add defaults:
```python
def load_order(order_data):
    # ... existing load logic
    for item in order_data['order_items']:
        item.setdefault('pricing_method', 'Standard markup')
        item.setdefault('pricing_notes', '')
        item.setdefault('manual_override', False)
        item.setdefault('validation_warning', None)
```

### Issue 3: Pricing Notes Not Showing
**Problem:** Pricing notes empty after calculation
**Solution:** Ensure `calculate_pbp_msrp()` always returns notes in result dict

---

## Validation Before Moving to Phase 4

Before proceeding to Phase 4, verify:
- [ ] All 4 entry pathways use new pricing logic
- [ ] Manual override checkbox functional in Tab 3
- [ ] Pricing notes display properly
- [ ] Validation warnings appear when expected
- [ ] Order summary calculations correct
- [ ] No console errors or warnings
- [ ] All existing Tab 3 features still work (saved orders, custom line items, etc.)
- [ ] Tab 1 → Tab 3 workflow works correctly

---

## Next Phase

Once Phase 3 is complete and validated, proceed to:
**Phase 4: UI Updates (Tab 4 - Execution & Accounting)**

Use the resume prompt from RESUME_PROMPTS.md to start Phase 4 with full context.

---

**Phase 3 Complete:** ✅ [Date completed]
**Tested By:** [Your name]
**Notes:** [Any important observations or issues encountered]
