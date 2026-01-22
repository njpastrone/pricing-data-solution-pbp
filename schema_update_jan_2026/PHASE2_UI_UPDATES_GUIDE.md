# Phase 2: UI Updates (Tab 1 - Proposal Generator)

**Status:** 🟡 Not Started
**Estimated Time:** 3-4 hours
**Complexity:** MEDIUM
**Dependencies:** Phase 1 (Core Pricing Engine) must be complete

---

## Overview

Update Tab 1 (Proposal Generator) UI to:
1. Display new pricing method information
2. Show validation results (calculated vs spreadsheet)
3. Display pricing notes with compact expandable format
4. Add manual override checkbox
5. Use new pricing calculation functions

**Files to Modify:**
- `app.py` (Tab 1 sections only)

---

## Pre-Implementation Checklist

Before starting Phase 2, verify:
- [ ] Phase 1 is complete and tested
- [ ] `calculate_pbp_msrp()` function works correctly
- [ ] All 3 pricing methods tested (MSRP + %, MSRP capped, Standard markup)
- [ ] Validation logic works (calculated vs spreadsheet comparison)
- [ ] Read current Tab 1 code in app.py (search for "Tab 1" or "Proposal Generator")

---

## Step-by-Step Implementation

### Step 1: Update Product Display in Catalog (Section 1)

**Location:** "Browse & Filter Products" section in Tab 1

**Current behavior:** Shows basic product info (country, tiered pricing, MOQ, description)

**New behavior:** Add pricing method information

**Code changes:**

```python
# In the product catalog display loop, add after existing details:

# Show pricing method
pricing_logic = get_column_value(product, 'pricing_logic', None)
if pricing_logic:
    st.write(f"**Pricing Method:** {pricing_logic}")
else:
    st.write("**Pricing Method:** Standard markup (100%)")

# Show MSRP if available
vendor_msrp = get_column_value(product, 'vendor_published_msrp', None)
if vendor_msrp and pricing_logic in ["MSRP + % of cost", "MSRP capped – ship absorbed"]:
    st.write(f"**Vendor MSRP:** ${vendor_msrp:.2f}")

# Show cost basis
cost_basis = get_column_value(product, 'cost_basis', 'Per Item')
st.write(f"**Cost Basis:** {cost_basis}")
```

---

### Step 2: Update "Use MSRP Pricing" Checkbox Logic

**Location:** Section 2 - Proposal Configuration

**Current behavior:** Checkbox calculates markup to match MSRP when adding products

**New behavior:** Use new `calculate_pbp_msrp()` function to determine pricing

**Code changes:**

```python
# When adding product to proposal, replace old MSRP markup calculation with:

use_msrp_pricing = st.session_state.get('use_msrp_pricing', True)

if use_msrp_pricing:
    # Use new pricing calculation
    pricing_result = calculate_pbp_msrp(product_data, quantity=100)

    if pricing_result['method_used'] == "Standard markup":
        # No MSRP or method = standard markup, use diagnostic markup
        markup_pct = pricing_result['calculation_details'].get('diagnostic_markup', 100.0)
    else:
        # MSRP-based method, calculate markup to match PBP MSRP
        base_cost = pricing_result['calculation_details']['base_cost']
        pbp_msrp = pricing_result['pbp_msrp']

        if base_cost > 0:
            markup_pct = ((pbp_msrp / base_cost) - 1) * 100
        else:
            markup_pct = 100.0
else:
    # Use default 100% markup
    markup_pct = 100.0

# Store markup in proposal_products
proposal_products.append({
    'product': product_name,
    'partner': partner,
    'quantity': 1,
    'markup': markup_pct,
    'pricing_method': pricing_result['method_used'],  # NEW FIELD
    'pricing_notes': pricing_result.get('pricing_notes', ''),  # NEW FIELD
    # ... other fields
})
```

---

### Step 3: Add Manual Override Checkbox to Product Table

**Location:** Section 2 - "Products in Your Proposal" table

**Current display:** Product | PBP Cost | Markup % | Client Price | MSRP | Remove

**New display:** Product | PBP Cost | Markup % | Client Price | MSRP | Manual Override | Remove

**Code changes:**

```python
# In the proposal products table, add a new column for manual override:

for idx, item in enumerate(st.session_state.proposal_products):
    col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1, 1])

    with col1:
        st.write(item['product'])
        # Show pricing method indicator
        pricing_method = item.get('pricing_method', 'Standard markup')
        st.caption(f"Method: {pricing_method}")

    with col2:
        # PBP Cost (at quantity 100)
        cost = calculate_cost_for_quantity(item, 100)
        st.write(f"${cost:.2f}")

    with col3:
        # Markup % - editable
        new_markup = st.number_input(
            "Markup %",
            min_value=0.0,
            value=item['markup'],
            step=1.0,
            key=f"markup_{idx}",
            label_visibility="collapsed"
        )
        if new_markup != item['markup']:
            st.session_state.proposal_products[idx]['markup'] = new_markup
            st.session_state.proposal_products[idx]['manual_override'] = True
            st.rerun()

    with col4:
        # Client Price
        client_price = cost * (1 + new_markup / 100)
        st.write(f"${client_price:.2f}")

    with col5:
        # MSRP comparison
        msrp = item.get('msrp', None)
        if msrp:
            st.write(f"${msrp:.2f}")
        else:
            st.write("—")

    with col6:
        # Manual Override Checkbox (NEW)
        manual_override = item.get('manual_override', False)
        override_checked = st.checkbox(
            "Override",
            value=manual_override,
            key=f"override_{idx}",
            help="Check to manually override pricing method",
            label_visibility="collapsed"
        )
        if override_checked != manual_override:
            st.session_state.proposal_products[idx]['manual_override'] = override_checked
            st.rerun()

    with col7:
        if st.button("Remove", key=f"remove_{idx}"):
            st.session_state.proposal_products.pop(idx)
            st.rerun()
```

---

### Step 4: Add Pricing Notes Display (Expandable)

**Location:** Below the products table in Section 2

**Format:** Compact expandable display (Decision 8 - Option C)

**Code changes:**

```python
# After the products table, add a section for pricing notes:

# Collect all products with pricing notes
products_with_notes = [
    item for item in st.session_state.proposal_products
    if item.get('pricing_notes') and not item.get('manual_override', False)
]

if products_with_notes:
    with st.expander(f"ℹ️ Pricing Information ({len(products_with_notes)} products)", expanded=False):
        for item in products_with_notes:
            st.write(f"**{item['product']}**")
            st.caption(item['pricing_notes'])
            st.write("")  # Spacing
```

---

### Step 5: Add Validation Warnings Display

**Location:** Below pricing notes in Section 2

**Purpose:** Show products where calculated price doesn't match spreadsheet price

**Code changes:**

```python
# Add validation warnings section:

# Collect products with validation warnings
products_with_warnings = [
    item for item in st.session_state.proposal_products
    if item.get('validation_warning') and not item.get('manual_override', False)
]

if products_with_warnings:
    st.warning(f"⚠️ {len(products_with_warnings)} product(s) have pricing discrepancies")

    with st.expander("View Validation Details", expanded=False):
        for item in products_with_warnings:
            st.write(f"**{item['product']}**")
            st.caption(item['validation_warning'])
            st.write("")
```

---

### Step 6: Update Proposal Tables (Section 3)

**Location:** MOQ-based pricing tables

**Current behavior:** Shows calculated prices based on markup

**New behavior:** Same calculation, but ensure it uses new pricing functions

**Code changes:**

```python
# In the proposal table generation, ensure we're using calculate_pbp_msrp():

for product_item in st.session_state.proposal_products:
    product_data = # ... get from catalog

    # For each MOQ tier in the table:
    for moq in [moq1, moq2, moq3, moq4]:
        # Calculate price using new system
        pricing_result = calculate_pbp_msrp(
            product_data,
            quantity=moq,
            user_markup_override=product_item.get('markup') if product_item.get('manual_override') else None
        )

        base_price = pricing_result['pbp_msrp']

        # Apply discount if any
        if discount_pct > 0:
            discounted_price = base_price * (1 - discount_pct / 100)
        else:
            discounted_price = base_price

        # Apply marketing rounding if enabled
        if marketing_rounding:
            discounted_price = apply_marketing_rounding(discounted_price)

        # Add to table
        table_data.append({
            'Product': product_item['product'],
            'MOQ': moq,
            'Price': f"${discounted_price:.2f}",
            # ... other columns
        })
```

---

### Step 7: Test Tab 1 Changes

**Test Checklist:**

1. **Product Display:**
   - [ ] Pricing method shown for each product in catalog
   - [ ] MSRP shown when applicable
   - [ ] Cost basis displayed correctly

2. **Add to Proposal:**
   - [ ] "Use MSRP pricing" checkbox works with new logic
   - [ ] Products added with correct markup based on pricing method
   - [ ] Standard markup products default to 100%
   - [ ] MSRP-based products calculate correct markup

3. **Manual Override:**
   - [ ] Override checkbox appears in product table
   - [ ] Checking override allows manual markup editing
   - [ ] Override prevents validation warnings
   - [ ] Pricing notes hidden when override is checked

4. **Pricing Notes:**
   - [ ] Expandable section shows only products with notes
   - [ ] Notes describe pricing method used
   - [ ] Count is accurate
   - [ ] Collapsed by default

5. **Validation Warnings:**
   - [ ] Warning appears when calculated ≠ spreadsheet
   - [ ] Expandable details show discrepancy amounts
   - [ ] Warning count is accurate
   - [ ] Warnings hidden when override is checked

6. **Proposal Tables:**
   - [ ] Tables show correct prices using new calculation
   - [ ] Discounts apply correctly
   - [ ] Marketing rounding works
   - [ ] CSV export matches display

---

## Common Issues & Solutions

### Issue 1: Session State Key Conflicts
**Problem:** New fields (`pricing_method`, `manual_override`) not persisting
**Solution:** Ensure all new fields are initialized when products are added:
```python
proposal_products.append({
    # ... existing fields
    'pricing_method': pricing_result['method_used'],
    'pricing_notes': pricing_result.get('pricing_notes', ''),
    'manual_override': False,  # Default to False
    'validation_warning': pricing_result.get('validation_warning', None),
})
```

### Issue 2: Manual Override Not Working
**Problem:** Checkbox state not updating markup behavior
**Solution:** Check `manual_override` flag before showing validation warnings:
```python
if item.get('validation_warning') and not item.get('manual_override', False):
    # Show warning
```

### Issue 3: Pricing Notes Not Appearing
**Problem:** Notes field is empty or not passed from calculation
**Solution:** Ensure `calculate_pbp_msrp()` returns pricing notes in result dict

---

## Validation Before Moving to Phase 3

Before proceeding to Phase 3, verify:
- [ ] All 3 pricing methods work correctly in Tab 1
- [ ] Manual override checkbox functional
- [ ] Pricing notes display properly
- [ ] Validation warnings appear when expected
- [ ] Proposal tables use new pricing calculation
- [ ] No console errors or warnings
- [ ] All existing Tab 1 features still work (filters, bulk add, saved proposals)

---

## Next Phase

Once Phase 2 is complete and validated, proceed to:
**Phase 3: UI Updates (Tab 3 - Order & Client Info)**

Use the resume prompt from RESUME_PROMPTS.md to start Phase 3 with full context.

---

**Phase 2 Complete:** ✅ [Date completed]
**Tested By:** [Your name]
**Notes:** [Any important observations or issues encountered]
