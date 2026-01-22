# Custom Product Enhancement - Option 2 REVISED (Matching Catalog Product UX)

**Created:** 2026-01-20
**Revision:** Match existing catalog product add-to-order flow
**Key Insight:** Keep add form minimal, do all configuration inline (just like catalog products)

---

## UX Pattern: Match Catalog Product Flow

### Current Catalog Product Flow

**Step 1: Add to Order (Minimal Input)**
```
┌────────────────────────────────────────────────┐
│ Select Partner:  [Homeless Garden Project ▼]  │
│ Select Product:  [Strawberry Jam - 4oz    ▼]  │
│                  [Add to Order]                 │
└────────────────────────────────────────────────┘
```
- User selects partner + product
- Clicks "Add to Order"
- Product added with **defaults** (qty=1, default markup, no customization)

**Step 2: Configure Inline (Full Editing)**
```
Product appears in "2. Current Order" with inline editing:
- Quantity (number input)
- Markup % (number input)
- Client Price (bidirectional editing)
- Customization toggle + fields
- All settings right there on the product card
```

### New Custom Product Flow (MATCHING THE PATTERN)

**Step 1: Add Custom Product (Minimal Input)**
```
┌────────────────────────────────────────────────┐
│ Create Custom Product                          │
│                                                │
│ Product Name:    [Custom Gold Engraving____]  │
│ Partner:         [Select partner ▼] or Custom  │
│ Base Cost/Unit:  $[10.00]                     │
│                  [Add to Order]                 │
└────────────────────────────────────────────────┘
```
- User enters name, partner, base cost
- Clicks "Add to Order"
- Product added with **defaults** (qty=1, 100% markup, no customization)

**Step 2: Configure Inline (SAME as catalog products)**
```
Product appears in "2. Current Order" with SAME inline editing:
- Quantity (number input)
- Markup % (number input)
- Client Price (bidirectional editing)
- Customization toggle + fields
- Country fields (for tariff)
- All the same controls as catalog products
```

---

## Key Changes from Original Plan

### What Changes

**Before (Original Plan):**
- Big form with 15+ fields before adding
- Advanced options expander in add form
- Configure everything upfront

**After (Revised UX):**
- Minimal add form (3 fields only)
- Add with defaults
- Configure everything inline (just like catalog products)

### Why This is Better

1. **Consistency:** Matches existing UX pattern users already know
2. **Simplicity:** Add form takes 10 seconds instead of 30-90 seconds
3. **Flexibility:** Users configure as needed after adding
4. **Less Overwhelming:** Not a giant form to fill out
5. **Code Reuse:** Custom products use same inline editing code as catalog products

---

## Implementation Plan REVISED

### Step 1: Add Simple "Create Custom Product" Form

**Location:** Tab 3, after "Option C: Manual Product Selection"

**Code:**
```python
# ============================================================
# OPTION D: CREATE CUSTOM PRODUCT
# ============================================================
st.divider()
st.subheader("Option D: Create Custom Product")
st.caption("Create unique products not in the catalog (one-off items, executive samples, etc.)")

with st.expander("Create Custom Product", expanded=False):
    st.caption("Enter basic info - you'll configure quantity, markup, and customization after adding")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        custom_product_name = st.text_input(
            "Product Name*",
            key="custom_product_name",
            placeholder="e.g., Custom Gold Engraving"
        )

    with col2:
        # Partner selection with "Custom/Other" as first option
        partner_options = ["Custom/Other"] + sorted(df_template['Partner'].unique().tolist())
        custom_partner = st.selectbox(
            "Partner*",
            options=partner_options,
            key="custom_partner",
            help="Select partner for POC tracking, or 'Custom/Other'"
        )

    with col3:
        custom_base_cost = st.number_input(
            "Base Cost/Unit*",
            min_value=0.01,
            value=10.00,
            step=0.50,
            key="custom_base_cost",
            format="%.2f",
            help="What PBP pays per unit"
        )

    # Add button
    if st.button("Add to Order", key="add_custom_product_btn", type="primary", use_container_width=True):
        # Validation
        if not custom_product_name or len(custom_product_name.strip()) < 3:
            st.error("Product name is required (min 3 characters)")
        elif custom_base_cost <= 0:
            st.error("Base cost must be greater than $0")
        else:
            # Create custom product with DEFAULTS (just like catalog products)
            # User will configure quantity, markup, customization inline after adding

            # Create minimal product_data dict (simulates spreadsheet row)
            custom_product_data = {
                'Product/Service': custom_product_name.strip(),
                'Partner': custom_partner,
                'Pricing Tiers (Y/N)': 'N',  # Always flat-rate for custom
                'PBP Cost (No Tiers)': custom_base_cost,
                'PBP Standard Markup': 100.0,  # Default markup
                'Country of Origin (Made In)': '',
                'Country of Origin (Ships From)': '',
                'Vendor Published MSRP': 0,
                'Customization Setup Fee': 0,
                'Customization Cost per Unit': 0,
                'Customization Info': '',
                'Marketing Description': '',
                'Tariff Estimate (%)': 0,
                'MOQ (PBP)': '',
                'MOV (PBP)': '',
                'MOQ (Partner)': '',
                'MOV (Partner)': '',
                'Tariff Info': '',
                'Purchase Description': '',
                'Units per Package': 1,
            }

            # Use same structure as catalog products (lines 4975-5019)
            base_price = custom_base_cost  # No tiers, so base price = entered cost
            tier_range = "No Tiers"
            tier_column = "PBP Cost (No Tiers)"
            markup = 100.0  # Default markup

            # Create order item with DEFAULTS (same structure as catalog products)
            new_item = {
                'product_name': custom_product_name.strip(),
                'partner': custom_partner,
                'product_data': custom_product_data,
                'quantity': 1,  # DEFAULT - user edits inline
                'markup_percent': markup,  # DEFAULT - user edits inline
                'selected_variant': None,
                'include_customization': False,  # DEFAULT - user enables inline
                'customization_setup_fee': 0.0,
                'customization_per_unit': 0.0,
                'customization_minimum_qty': 0,
                'apply_custom_minimum': False,
                'include_tariff': False,
                'is_custom_product': True,  # FLAG to distinguish from catalog
                'source': 'custom',
                # Per-product kitting fields
                'include_kitting': False,
                'kitting_pbp_cost': 0.0,
                'kitting_client_price': 0.0,
                'kitting_description': ''
            }

            # Add calculated fields (same as catalog products)
            new_item.update({
                'base_price': base_price,
                'tier_range': tier_range,
                'tier_column': tier_column,
                'product_ref': 'CUSTOM',
                'country_of_origin_made_in': '',
                'country_of_origin_ships_from': '',
                'customization_description': '',
                'product_subtotal': base_price * 1,
                'customization_setup_total': 0.0,
                'customization_unit_total': 0.0,
                'subtotal_before_markup': base_price * 1,
                'markup_amount': (base_price * 1) * (markup / 100),
                'product_total': (base_price * 1) + ((base_price * 1) * (markup / 100)),
                'total_per_unit': ((base_price * 1) + ((base_price * 1) * (markup / 100))) / 1,
                'tariff_rate_percent': 0.0,
                'tariff_amount': 0.0,
                'edited_description': ''
            })

            # Add to order
            st.session_state.order_items.append(new_item)

            # Success message
            success_msg = f"Added custom product: {custom_product_name.strip()}"
            if custom_partner != "Custom/Other":
                success_msg += f" (Partner: {custom_partner})"
            st.toast(success_msg)

            st.rerun()
```

**That's it for the add form! Only 3 fields.**

---

### Step 2: Enhance Inline Editing for Custom Products

**Location:** Tab 3, Section 2 "Current Order" (lines 5090-5105)

**Current code for custom items:**
```python
# Skip custom items for now (they have different structure)
if item.get('is_custom', False):
    st.write("---")
    st.subheader(f"{item['product_name']}")
    st.caption(f"Custom Line Item")

    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"**Description:** {item.get('custom_description', 'N/A')}")
        st.write(f"**Quantity:** {item['quantity']} | **Unit Price:** ${item['total_per_unit']:.2f} | **Total:** ${item['product_total']:.2f}")
    with col2:
        if st.button("Remove", key=f"remove_custom_{idx}", type="secondary"):
            st.session_state.order_items.pop(idx)
            st.rerun()
    continue  # Skips the rest of the loop
```

**NEW code - treat custom products like catalog products:**
```python
# Check if this is OLD-STYLE custom line item (before enhancement)
if item.get('is_custom', False) and not item.get('is_custom_product', False):
    # Old custom line items - show simplified view
    st.write("---")
    st.subheader(f"{item['product_name']}")
    st.caption(f"Custom Line Item (Legacy)")

    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"**Description:** {item.get('custom_description', 'N/A')}")
        st.write(f"**Quantity:** {item['quantity']} | **Unit Price:** ${item['total_per_unit']:.2f} | **Total:** ${item['product_total']:.2f}")
    with col2:
        if st.button("Remove", key=f"remove_custom_{idx}", type="secondary"):
            st.session_state.order_items.pop(idx)
            st.rerun()
    continue

# NEW custom products (is_custom_product=True) fall through to regular product editing
# They use the SAME inline editing as catalog products (lines 5107-5500+)
```

**Then add custom product indicator in the header:**
```python
# Regular product card (INCLUDING new custom products)
st.write("---")

# Header with product name and remove button
col_header, col_remove = st.columns([5, 1])
with col_header:
    # Display product name with variant (if applicable)
    from src.helpers import format_product_with_variant
    product_display_name = format_product_with_variant(
        item['product_name'],
        item.get('selected_variant')
    )
    st.subheader(f"{product_display_name}")

    # Show partner and origin (with custom product indicator)
    if item.get('is_custom_product', False):
        st.caption(f"✨ Custom Product | Partner: {item['partner']} | Base Cost: ${item['base_price']:.2f}/unit")
    else:
        st.caption(f"Partner: {item['partner']} | Origin: {item.get('country_of_origin', 'N/A')}")
```

**Add country fields for custom products (in customization section):**
```python
# After customization section, add country/tariff for custom products
if item.get('is_custom_product', False):
    st.markdown("##### Country & Tariff (Custom Product)")

    col1, col2 = st.columns(2)
    with col1:
        country_made = st.selectbox(
            "Made In",
            options=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"],
            index=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"].index(
                item.get('country_of_origin_made_in', '')
            ) if item.get('country_of_origin_made_in', '') in ["", "USA", "China", "India", "Vietnam", "Mexico", "Other"] else 0,
            key=f"custom_made_in_{idx}"
        )

        # Update item if changed
        if country_made != item.get('country_of_origin_made_in', ''):
            st.session_state.order_items[idx]['country_of_origin_made_in'] = country_made
            # Auto-set ships from to same as made in if not set
            if not item.get('country_of_origin_ships_from'):
                st.session_state.order_items[idx]['country_of_origin_ships_from'] = country_made

    with col2:
        country_ships = st.selectbox(
            "Ships From",
            options=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"],
            index=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"].index(
                item.get('country_of_origin_ships_from', '')
            ) if item.get('country_of_origin_ships_from', '') in ["", "USA", "China", "India", "Vietnam", "Mexico", "Other"] else 0,
            key=f"custom_ships_from_{idx}"
        )

        # Update item if changed
        if country_ships != item.get('country_of_origin_ships_from', ''):
            st.session_state.order_items[idx]['country_of_origin_ships_from'] = country_ships

    # Tariff estimate
    st.caption("Tariff estimate (optional, for reference)")
    tariff_pct = st.number_input(
        "Tariff Estimate (%)",
        min_value=0.0,
        max_value=100.0,
        value=item.get('tariff_rate_percent', 0.0),
        step=0.5,
        key=f"custom_tariff_{idx}",
        help="Estimated tariff rate based on country and product type"
    )

    if tariff_pct != item.get('tariff_rate_percent', 0.0):
        st.session_state.order_items[idx]['tariff_rate_percent'] = tariff_pct
```

---

## Benefits of This Revised Approach

### 1. Consistency
- Users already know the pattern: add with minimal info → configure inline
- No learning curve

### 2. Simplicity
- Add form: 3 fields (name, partner, base cost)
- Takes 10 seconds instead of 30-90 seconds

### 3. Code Reuse
- Custom products use **same inline editing code** as catalog products
- Quantity, markup, customization, kitting - all the same
- Less code to maintain

### 4. Flexibility
- User decides what to configure (not forced to fill out everything upfront)
- Can add quickly and configure later
- Same flexibility as catalog products

### 5. Less Overwhelming
- Not a giant form before adding
- Progressive configuration as needed

---

## Comparison: Original vs. Revised

| Aspect | Original Plan | Revised UX |
|--------|--------------|------------|
| **Add Form Fields** | 15+ fields | 3 fields |
| **Time to Add** | 30-90 seconds | 10 seconds |
| **Configuration** | Upfront in add form | Inline after adding |
| **Advanced Options** | Collapsible expander | Edit inline (same as catalog) |
| **Code Complexity** | ~170 lines new code | ~80 lines new code |
| **UX Consistency** | Different from catalog | Matches catalog exactly |
| **Learning Curve** | New pattern to learn | Zero (uses existing pattern) |

---

## What Users Experience

### Adding a Custom Product

**Step 1: Quick Add (10 seconds)**
```
Option D: Create Custom Product
┌────────────────────────────────────────┐
│ Product Name:    [Gold Engraving___]  │
│ Partner:         [HGP ▼]              │
│ Base Cost/Unit:  $[12.00]             │
│                                        │
│         [Add to Order]                 │
└────────────────────────────────────────┘
```

**Step 2: Product Appears in Order (Same as Catalog)**
```
───────────────────────────────────────────
Gold Engraving
✨ Custom Product | Partner: HGP | Base Cost: $12.00/unit

Quantity & Pricing
┌─────────┬──────────┬────────────┐
│ Qty     │ Markup % │ Price/Unit │
│ [1]     │ [100.0]  │ $[24.00]   │
└─────────┴──────────┴────────────┘

☐ Include customization
  [If checked, shows same fields as catalog products]

☐ Include per-product kitting
  [If checked, shows same fields as catalog products]

Country & Tariff
┌──────────┬─────────────┐
│ Made In  │ Ships From  │
│ [USA ▼]  │ [USA ▼]     │
└──────────┴─────────────┘
Tariff: [0.0] %
```

**Step 3: Edit as Needed**
- Change quantity to 50
- Adjust markup to 120%
- Enable customization, add $150 setup fee
- Set country to China, tariff auto-suggests 25%
- All updates are real-time (just like catalog products)

---

## Implementation Checklist

### Phase 1: Add Form (30 minutes)
- [ ] Add "Option D: Create Custom Product" expander
- [ ] 3 input fields: name, partner, base cost
- [ ] Validation: name min 3 chars, base cost > $0
- [ ] Create order item with defaults (quantity=1, markup=100%, no customization)
- [ ] Use flag `is_custom_product: True` to distinguish from legacy custom items
- [ ] Toast success message
- [ ] Test adding custom products with different partners

### Phase 2: Inline Editing Enhancement (45 minutes)
- [ ] Update "Current Order" section to handle new custom products
- [ ] Add custom product indicator in header (✨ Custom Product | Partner: X | Base Cost: $Y)
- [ ] Add country selection fields (Made In / Ships From) - only for custom products
- [ ] Add tariff estimate field - only for custom products
- [ ] Test inline editing: quantity, markup, price, customization all work
- [ ] Verify country and tariff fields only show for custom products

### Phase 3: Legacy Compatibility (15 minutes)
- [ ] Keep old custom line items working (`is_custom: True` but no `is_custom_product`)
- [ ] Show simplified view for legacy custom items
- [ ] Add "(Legacy)" caption to distinguish

### Phase 4: Testing (30 minutes)
- [ ] Test 1: Add custom product with "Custom/Other" partner
- [ ] Test 2: Add custom product with real partner (verify POC shows in invoice)
- [ ] Test 3: Edit quantity and markup inline
- [ ] Test 4: Enable customization inline
- [ ] Test 5: Set country and tariff
- [ ] Test 6: Verify order summary calculates correctly
- [ ] Test 7: Verify Tab 4 invoice shows custom product correctly
- [ ] Test 8: CSV export includes custom product
- [ ] Test 9: HTML export includes custom product
- [ ] Test 10: Save and load order with custom products

**Total Time: ~2 hours**

---

## Code Changes Summary

### Files Modified
1. **app.py - Tab 3**
   - Lines ~4900: Add "Option D: Create Custom Product" (~40 lines)
   - Lines ~5090: Update custom item handling to distinguish new vs. legacy (~10 lines)
   - Lines ~5110: Add custom product indicator in header (~5 lines)
   - Lines ~5300 (after customization): Add country/tariff fields for custom products (~40 lines)

**Total: ~95 lines (vs. 170 in original plan)**

### No New Files Needed
All changes in existing `app.py` Tab 3 section

---

## Testing Scenarios

### Basic Flow
1. **Add minimal custom product**
   - Name: "Test Product"
   - Partner: "Custom/Other"
   - Base Cost: $5.00
   - **Expected:** Appears in order with qty=1, markup=100%, price=$10/unit

2. **Add with real partner**
   - Name: "Custom Jam Flavor"
   - Partner: "Homeless Garden Project"
   - Base Cost: $8.00
   - **Expected:** Shows HGP partner, POC auto-populates in invoice

3. **Configure inline**
   - Change quantity to 50
   - Change markup to 150%
   - **Expected:** Price updates to $20/unit, total $1,000

4. **Enable customization**
   - Check "Include customization"
   - Setup fee: $200
   - Per-unit: $3
   - **Expected:** Customization total shows, invoice has separate line items

5. **Set country and tariff**
   - Made In: China
   - Ships From: China
   - **Expected:** Tariff field available, can enter manually

### Integration
6. **Order summary** - Custom product totals match regular products
7. **Invoice** - Shows partner, all line items, POC if applicable
8. **CSV export** - Includes custom product fields
9. **HTML export** - Formats custom product correctly
10. **Saved orders** - Custom products save and load properly

---

## Success Metrics

**User Experience:**
- ✅ Add custom product in under 15 seconds
- ✅ Configure inline using familiar controls
- ✅ No learning curve (matches existing pattern)

**Technical:**
- ✅ 95% code reuse (inline editing shared with catalog products)
- ✅ ~95 lines of new code (vs. 170 in original plan)
- ✅ Backward compatible with legacy custom items
- ✅ All tests pass

**Business:**
- ✅ Profit visibility (base cost vs. client price)
- ✅ Partner tracking (POC auto-population)
- ✅ Customization fees properly tracked
- ✅ Tariff estimates available

---

## Conclusion

**Revised UX is MUCH better:**
- Matches existing catalog product flow (consistency)
- Minimal add form (simplicity)
- All configuration inline (flexibility)
- 95% code reuse (maintainability)
- 2 hours implementation (vs. 3-4 hours original)

**Users get:**
- Fast product creation (10 seconds)
- Familiar configuration interface (zero learning curve)
- Full customization options (when needed)
- Profit visibility (base + markup = price)
- Partner tracking (POC, in-hands dates)

**Ready to implement when approved.**

---

**End of Revised UX Plan**
