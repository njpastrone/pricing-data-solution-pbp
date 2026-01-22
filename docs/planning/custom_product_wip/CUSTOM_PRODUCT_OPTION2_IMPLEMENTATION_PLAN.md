# Custom Product Enhancement - Option 2 Implementation Plan

**Created:** 2026-01-20
**Feature:** Enhanced Custom Line Items with Advanced Options
**Estimated Time:** 2-3 hours
**Risk Level:** Low

---

## Executive Summary

**What:** Enhance existing "Custom Line Items" feature with profit tracking and optional advanced features
**Why:** Users need to see profit margin on custom items and track partner associations
**How:** Add 3 required fields + collapsible advanced options section

**Key Benefits:**
- ✅ Profit margin visibility (base cost + markup)
- ✅ Partner tracking (for POC auto-population)
- ✅ Optional customization fees (setup + per-unit)
- ✅ Optional tariff support (via country field)
- ✅ Optional MSRP markup calculation
- ✅ Still simple and fast to use (advanced options hidden by default)

---

## Scope

### In Scope
1. **Required Fields (Always Visible):**
   - Product/Service Name
   - Partner selection (with "Custom/Other" option)
   - Base Cost per Unit (what PBP pays)
   - Quantity
   - Markup % (profit margin)
   - Description (optional)

2. **Advanced Options (Collapsible Expander):**
   - Country of origin (Made In / Ships From)
   - Customization setup fee
   - Customization per-unit cost
   - Customization description
   - MSRP with "Calculate Markup" button
   - Tariff estimate % (auto-calculated from country when possible)

3. **Features:**
   - Auto-calculate client price from base cost + markup
   - Real-time price preview
   - Integration with existing discount/marketing rounding
   - Partner POC auto-population in invoices
   - Works with CSV and HTML exports

### Out of Scope
- Tab 1 (Proposal Generator) integration
- Custom Product Library feature
- Tiered pricing support
- PowerPoint generation
- Saving custom products for reuse

---

## Current State

**Location:** `app.py` Tab 3, lines 5999-6069

**Current Fields:**
- Product/Service Name
- Quantity
- Description
- Total Price (user enters final price)

**Current Limitations:**
- No profit margin visibility
- Always shows "Custom" partner (no tracking)
- No markup calculation
- No customization fee support
- No tariff support

---

## New State (Option 2)

### UI Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Add Custom Line Item (3 added)                 [Expand/Collapse] │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Add unique services or customizations not in the catalog      │
│                                                                │
│ Product/Service Name *                                         │
│ [_________________________________________________________]   │
│                                                                │
│ Partner *                                                      │
│ [Select partner ▼]  (includes "Custom/Other")                │
│                                                                │
│ ┌─────────────────┬──────────────────┬──────────────────┐   │
│ │ Quantity *       │ Base Cost/Unit * │ Markup % *       │   │
│ │ [50] units      │ $[10.00]        │ [100.0] %       │   │
│ └─────────────────┴──────────────────┴──────────────────┘   │
│                                                                │
│ ℹ → Client Price: $20.00/unit × 50 = $1,000.00               │
│                                                                │
│ Description (optional)                                         │
│ [_________________________________________________________]   │
│                                                                │
│ ▶ Show advanced options (country, customization, MSRP)        │
│                                                                │
│ [Add Custom Item to Order]                                     │
└──────────────────────────────────────────────────────────────┘
```

**When Advanced Options Expanded:**

```
┌──────────────────────────────────────────────────────────────┐
│ ▼ Advanced Options (optional)                                 │
│                                                                │
│ Country of Origin                                              │
│ ┌──────────────────────────┬──────────────────────────────┐  │
│ │ Made In                  │ Ships From                   │  │
│ │ [USA ▼]                 │ [USA ▼]                     │  │
│ └──────────────────────────┴──────────────────────────────┘  │
│                                                                │
│ MSRP (Manufacturer's Suggested Retail Price)                   │
│ ┌──────────────────────────┬──────────────────────────────┐  │
│ │ $[25.00]                │ [Calculate Markup from MSRP] │  │
│ └──────────────────────────┴──────────────────────────────┘  │
│                                                                │
│ ☐ Include customization (setup fees & per-unit costs)         │
│   [If checked, shows:]                                         │
│   ┌──────────────────────────┬──────────────────────────┐    │
│   │ Setup Fee ($)            │ Per-Unit Cost ($)        │    │
│   │ $[150.00]               │ $[2.50]                 │    │
│   └──────────────────────────┴──────────────────────────┘    │
│                                                                │
│   Description                                                  │
│   [Gold foil logo on front cover_________________________]   │
│                                                                │
│   ℹ Customization Total: $150 setup + $125 (50 × $2.50)      │
│                                                                │
│ Tariff Estimate (%)                                            │
│ [10.5] % (auto-calculated based on country, or manual)       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Update UI (Basic Fields)

**File:** `app.py` Tab 3 section (around line 5999-6069)

**Changes:**

1. **Add partner selection dropdown**
   ```python
   # Partner selection (NEW)
   partner_options = ["Custom/Other"] + sorted(df_template['Partner'].unique().tolist())
   custom_partner = st.selectbox(
       "Partner*",
       options=partner_options,
       key="custom_partner",
       help="Select partner for POC tracking, or 'Custom/Other' for non-partner items"
   )
   ```

2. **Replace total price with base cost + markup**
   ```python
   # Quantity, Base Cost, Markup in 3 columns (NEW LAYOUT)
   col1, col2, col3 = st.columns(3)
   with col1:
       custom_quantity = st.number_input(
           "Quantity*",
           min_value=1,
           value=1,
           step=1,
           key="custom_quantity_input"
       )
   with col2:
       custom_base_cost = st.number_input(
           "Base Cost/Unit* (PBP pays)",
           min_value=0.01,
           value=10.00,
           step=0.50,
           key="custom_base_cost",
           format="%.2f",
           help="What PBP pays per unit before markup"
       )
   with col3:
       custom_markup = st.number_input(
           "Markup %*",
           min_value=-50.0,
           value=100.0,
           step=5.0,
           key="custom_markup",
           format="%.1f",
           help="Your profit margin. 100% = double the cost"
       )
   ```

3. **Add real-time client price preview**
   ```python
   # Auto-calculate and show client price (NEW)
   if custom_base_cost > 0 and custom_quantity > 0:
       client_price_per_unit = custom_base_cost * (1 + custom_markup / 100)
       total_client_price = client_price_per_unit * custom_quantity
       st.info(f"→ Client Price: ${client_price_per_unit:.2f}/unit × {custom_quantity} = ${total_client_price:,.2f}")

       # Warning for negative markup
       if custom_markup < 0:
           st.warning("⚠️ Negative markup - you're pricing below cost")
   ```

4. **Keep description field**
   ```python
   # Description (optional)
   custom_description = st.text_input(
       "Description (optional)",
       key="custom_description_input",
       placeholder="e.g., Laser engraving on wooden items"
   )
   ```

---

### Step 2: Add Advanced Options Section

**Add after description field:**

```python
# ============================================================
# ADVANCED OPTIONS (Collapsible)
# ============================================================
show_advanced = st.checkbox(
    "Show advanced options (country, customization, MSRP)",
    key="custom_show_advanced",
    value=False
)

# Initialize advanced option values with defaults
custom_made_in = ""
custom_ships_from = ""
custom_msrp = 0.0
custom_include_customization = False
custom_setup_fee = 0.0
custom_per_unit_cost = 0.0
custom_customization_desc = ""
custom_tariff = 0.0

if show_advanced:
    st.markdown("---")
    st.markdown("##### Advanced Options")

    # Country of origin
    st.markdown("**Country of Origin**")
    col1, col2 = st.columns(2)
    with col1:
        custom_made_in = st.selectbox(
            "Made In",
            options=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"],
            key="custom_made_in",
            help="Country where product is manufactured"
        )
    with col2:
        custom_ships_from = st.selectbox(
            "Ships From",
            options=["", "USA", "China", "India", "Vietnam", "Mexico", "Other"],
            key="custom_ships_from",
            help="Country where product ships from (affects tariffs)"
        )

    # MSRP with markup calculator
    st.markdown("**MSRP (Manufacturer's Suggested Retail Price)**")
    col1, col2 = st.columns([2, 1])
    with col1:
        custom_msrp = st.number_input(
            "MSRP per Unit ($)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="custom_msrp",
            format="%.2f",
            help="Manufacturer's suggested retail price (optional)"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Calculate Markup from MSRP", key="custom_calc_msrp_btn", use_container_width=True):
            if custom_msrp > 0 and custom_base_cost > 0:
                calculated_markup = ((custom_msrp / custom_base_cost) - 1) * 100
                st.session_state.custom_markup = max(0, calculated_markup)
                st.success(f"✓ Markup set to {calculated_markup:.1f}%")
                st.rerun()
            else:
                st.error("Enter both Base Cost and MSRP to calculate")

    # Customization
    st.markdown("**Customization**")
    custom_include_customization = st.checkbox(
        "Include customization (setup fees & per-unit costs)",
        key="custom_include_customization",
        value=False
    )

    if custom_include_customization:
        col1, col2 = st.columns(2)
        with col1:
            custom_setup_fee = st.number_input(
                "Setup Fee ($)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                key="custom_setup_fee",
                format="%.2f",
                help="One-time setup cost for customization"
            )
        with col2:
            custom_per_unit_cost = st.number_input(
                "Per-Unit Cost ($)",
                min_value=0.0,
                value=0.0,
                step=0.50,
                key="custom_per_unit_cost",
                format="%.2f",
                help="Customization cost per unit"
            )

        custom_customization_desc = st.text_input(
            "Customization Description",
            key="custom_customization_desc",
            placeholder="e.g., Gold foil logo on front cover"
        )

        # Show customization total
        if custom_setup_fee > 0 or custom_per_unit_cost > 0:
            customization_unit_total = custom_per_unit_cost * custom_quantity
            customization_total = custom_setup_fee + customization_unit_total
            st.info(f"ℹ Customization Total: ${custom_setup_fee:.2f} setup + ${customization_unit_total:.2f} ({custom_quantity} × ${custom_per_unit_cost:.2f})")

    # Tariff estimate
    st.markdown("**Tariff Estimate**")

    # Auto-calculate tariff from country if possible
    default_tariff = 0.0
    if custom_ships_from == "China":
        default_tariff = 25.0  # Example - adjust based on actual tariff rates
    elif custom_ships_from == "India":
        default_tariff = 10.0
    elif custom_ships_from == "Vietnam":
        default_tariff = 15.0

    custom_tariff = st.number_input(
        "Tariff Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=default_tariff,
        step=0.5,
        key="custom_tariff",
        format="%.1f",
        help="Estimated tariff rate (auto-calculated based on country, or enter manually)"
    )

    if default_tariff > 0 and custom_tariff == default_tariff:
        st.caption(f"ℹ Auto-calculated based on shipping from {custom_ships_from}")
```

---

### Step 3: Update Preview Section

**Replace old preview with comprehensive preview:**

```python
# ============================================================
# COMPREHENSIVE PREVIEW
# ============================================================
st.markdown("---")
st.markdown("##### Preview")

if custom_base_cost > 0 and custom_quantity > 0:
    # Base product calculations
    product_subtotal = custom_base_cost * custom_quantity
    markup_amount = product_subtotal * (custom_markup / 100)
    product_total = product_subtotal + markup_amount
    client_price_per_unit = product_total / custom_quantity

    # Customization calculations
    customization_setup = custom_setup_fee if custom_include_customization else 0
    customization_unit_total = (custom_per_unit_cost * custom_quantity) if custom_include_customization else 0
    customization_total = customization_setup + customization_unit_total

    # Total to client
    total_to_client = product_total + customization_total

    # Display preview
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Base Cost (PBP)", f"${product_subtotal:.2f}")
        st.caption(f"${custom_base_cost:.2f}/unit × {custom_quantity} units")
    with col2:
        st.metric("Client Price (Base Product)", f"${product_total:.2f}")
        st.caption(f"${client_price_per_unit:.2f}/unit (includes {custom_markup:.1f}% markup)")

    if customization_total > 0:
        st.info(f"➕ Customization: ${customization_setup:.2f} setup + ${customization_unit_total:.2f} per-unit = ${customization_total:.2f}")

    st.success(f"**Total to Client: ${total_to_client:,.2f}**")

    # Profit breakdown
    with st.expander("Show profit breakdown", expanded=False):
        profit = markup_amount + (customization_total if custom_include_customization else 0)
        profit_margin_pct = (profit / total_to_client * 100) if total_to_client > 0 else 0
        st.write(f"**Profit:** ${profit:,.2f} ({profit_margin_pct:.1f}% of total)")
        st.write(f"**PBP Cost:** ${product_subtotal:,.2f}")
        st.write(f"**Client Pays:** ${total_to_client:,.2f}")
```

---

### Step 4: Update Validation and Add Button

```python
# ============================================================
# VALIDATION AND ADD BUTTON
# ============================================================
st.markdown("---")

if st.button("Add Custom Item to Order", type="primary", use_container_width=True, key="add_custom_item_btn"):
    # Validation
    errors = []

    if not custom_name or len(custom_name.strip()) < 3:
        errors.append("Product name is required (min 3 characters)")

    if custom_base_cost <= 0:
        errors.append("Base cost must be greater than $0")

    if custom_quantity < 1:
        errors.append("Quantity must be at least 1 unit")

    if custom_include_customization and custom_setup_fee == 0 and custom_per_unit_cost == 0:
        errors.append("Customization is enabled but no fees entered - either add fees or uncheck customization")

    # Show all errors
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        # Proceed to create custom item (see Step 5)
        pass
```

---

### Step 5: Create Custom Item with Full Structure

```python
# ============================================================
# CREATE CUSTOM ITEM (Inside validation if block)
# ============================================================

# Calculate all pricing values
product_subtotal = custom_base_cost * custom_quantity
markup_amount = product_subtotal * (custom_markup / 100)
product_total = product_subtotal + markup_amount
total_per_unit = product_total / custom_quantity

# Customization totals
customization_setup_total = custom_setup_fee if custom_include_customization else 0
customization_per_unit = custom_per_unit_cost if custom_include_customization else 0
customization_unit_total = customization_per_unit * custom_quantity

# Create enhanced custom item structure
custom_item = {
    # Core identification
    'product_name': custom_name.strip(),
    'product_ref': "CUSTOM",
    'partner': custom_partner,

    # Quantities and markup
    'quantity': custom_quantity,
    'markup_percent': custom_markup,

    # Pricing breakdown
    'base_price': custom_base_cost,
    'tier_range': "No Tiers",
    'tier_column': "N/A",
    'product_subtotal': product_subtotal,
    'markup_amount': markup_amount,
    'product_total': product_total,
    'total_per_unit': total_per_unit,
    'subtotal_before_markup': product_subtotal,

    # Customization (NEW)
    'include_customization': custom_include_customization,
    'customization_setup_fee': custom_setup_fee,
    'customization_per_unit': custom_per_unit_cost,
    'customization_setup_total': customization_setup_total,
    'customization_unit_total': customization_unit_total,
    'customization_description': custom_customization_desc if custom_include_customization else '',

    # Partner customization costs (for invoice display)
    'partner_customization_setup_fee': custom_setup_fee,  # Assume same as client for custom items
    'partner_customization_per_unit': custom_per_unit_cost,
    'partner_customization_setup_total': customization_setup_total,
    'partner_customization_unit_total': customization_unit_total,

    # Country and tariff (NEW)
    'country_of_origin_made_in': custom_made_in if custom_made_in else '',
    'country_of_origin_ships_from': custom_ships_from if custom_ships_from else '',
    'tariff_rate_percent': custom_tariff,
    'tariff_info': '',
    'tariff_base': 0.0,
    'tariff_amount': 0.0,  # Calculated later in order summary

    # MSRP (NEW)
    'msrp': custom_msrp if custom_msrp > 0 else 0,

    # Description
    'custom_description': custom_description if custom_description else "Custom line item",
    'edited_description': '',

    # Standard fields
    'is_custom': True,
    'include_labels': False,
    'additional_costs': {},
    'art_setup_total': 0,
    'label_cost_total': 0,

    # Per-product kitting fields
    'include_kitting': False,
    'kitting_pbp_cost': 0.0,
    'kitting_client_price': 0.0,
    'kitting_description': ''
}

# Add to order
st.session_state.order_items.append(custom_item)

# Success message
success_msg = f"Added custom item: {custom_name.strip()}"
if custom_partner != "Custom/Other":
    success_msg += f" (Partner: {custom_partner})"
st.toast(success_msg)

st.rerun()
```

---

## Testing Checklist

### Basic Functionality
- [ ] **Test 1:** Add custom item with minimal fields (name, Custom/Other partner, base cost, quantity, markup)
- [ ] **Test 2:** Add custom item with real partner selection (verify partner appears correctly)
- [ ] **Test 3:** Verify client price auto-calculates correctly (base × markup)
- [ ] **Test 4:** Test negative markup (should show warning but allow)
- [ ] **Test 5:** Test quantity = 1 (should work, no special warning needed)

### Advanced Options
- [ ] **Test 6:** Add custom item with country selected (Made In: China, Ships From: China)
- [ ] **Test 7:** Verify tariff auto-calculates from country (China = 25%, India = 10%, etc.)
- [ ] **Test 8:** Add custom item with MSRP, click "Calculate Markup from MSRP" button
- [ ] **Test 9:** Verify calculated markup is correct: ((MSRP / base_cost) - 1) × 100
- [ ] **Test 10:** Add custom item with customization enabled (setup fee + per-unit cost)
- [ ] **Test 11:** Verify customization total shows in preview
- [ ] **Test 12:** Add custom item with all advanced options enabled

### Integration Tests
- [ ] **Test 13:** Custom item appears in Section 2 (Current Order) with correct values
- [ ] **Test 14:** Custom item appears in Section 4 (Order Summary) with correct totals
- [ ] **Test 15:** Custom item shows in Tab 4 invoice with correct partner
- [ ] **Test 16:** Partner POC auto-populates in invoice (if real partner selected)
- [ ] **Test 17:** Custom/Other partner shows as "Custom" in invoice
- [ ] **Test 18:** Custom item works with 5% discount
- [ ] **Test 19:** Custom item works with marketing rounding
- [ ] **Test 20:** Custom item works with $0.50 rounding

### Export Tests
- [ ] **Test 21:** CSV export includes custom item with all fields
- [ ] **Test 22:** HTML export includes custom item with correct formatting
- [ ] **Test 23:** Invoice shows customization as separate line items (setup + per-unit)

### Edge Cases
- [ ] **Test 24:** Add custom item with $0.01 base cost (minimum valid)
- [ ] **Test 25:** Add custom item with -50% markup (maximum negative allowed)
- [ ] **Test 26:** Add custom item with 500% markup (high but valid)
- [ ] **Test 27:** Toggle advanced options on/off multiple times (state preserved)
- [ ] **Test 28:** Enable customization but enter $0 for both setup and per-unit (should error)
- [ ] **Test 29:** Calculate markup from MSRP when base cost is $0 (should error)
- [ ] **Test 30:** Add 10 custom items with different partners (verify no conflicts)

### Saved Orders
- [ ] **Test 31:** Save order with custom items
- [ ] **Test 32:** Load saved order - custom items restore correctly
- [ ] **Test 33:** Delete custom item from order
- [ ] **Test 34:** Edit custom item inline (quantity, markup) - verify recalculates

---

## Edge Cases & Validation

### Edge Case 1: Negative Markup
**Scenario:** User sets markup to -20%
**Handling:** Allow, show warning "⚠️ Negative markup - you're pricing below cost"
**Rationale:** User may have strategic reasons (loss leader, donated product, etc.)

### Edge Case 2: Zero Base Cost
**Scenario:** User tries to set base cost to $0
**Handling:** Require minimum $0.01, show error
**Rationale:** Prevents division by zero, ensures cost tracking

### Edge Case 3: MSRP Below Base Cost
**Scenario:** MSRP is $5, base cost is $10
**Handling:** Calculate markup would be negative (-50%), set to 0% instead, show warning
**Rationale:** Prevents accidental below-cost pricing

### Edge Case 4: Customization Enabled but Zero Fees
**Scenario:** User checks "Include customization" but enters $0 for both setup and per-unit
**Handling:** Show error: "Customization is enabled but no fees entered"
**Rationale:** Prevent empty customization sections in invoice

### Edge Case 5: Very High Markup (500%+)
**Scenario:** User sets markup to 500%
**Handling:** Allow, no warning (user knows their business)
**Rationale:** Some luxury/specialty items have high markups

### Edge Case 6: Custom/Other Partner with Missing POC
**Scenario:** User selects "Custom/Other" partner
**Handling:** Show "N/A" for POC in invoice (expected behavior)
**Rationale:** Generic custom items don't have partner contacts

### Edge Case 7: Partner Selection Changed After Entry
**Scenario:** User adds custom item with Partner A, then edits to Partner B
**Handling:** Not supported in MVP (no inline edit for partner)
**Rationale:** User can delete and re-add if needed

### Edge Case 8: Tariff Auto-Calculation Override
**Scenario:** Country is China (auto-calc 25%), user changes to 10%
**Handling:** Allow manual override, respect user input
**Rationale:** User may have specific tariff agreement

---

## Code Organization

**All changes in one location:** `app.py` Tab 3 section

**Line estimate:**
- Current code: ~70 lines (lines 5999-6069)
- New code: ~170 lines
- Net addition: ~100 lines

**Sections:**
1. Basic fields (40 lines)
2. Advanced options (60 lines)
3. Preview (30 lines)
4. Validation (20 lines)
5. Create custom item (20 lines)

**No new files needed** - self-contained enhancement

---

## Documentation Updates

### CHANGELOG.md
```markdown
## [7.5.1] - 2026-01-20

### Enhanced
- **Custom Line Items with Profit Tracking:**
  - Added partner selection (replaces generic "Custom" partner)
  - Added base cost + markup % fields (replaces total price)
  - Real-time client price calculation
  - Optional advanced features (collapsible):
    - Country of origin (Made In / Ships From)
    - MSRP with automatic markup calculation
    - Customization fees (setup + per-unit)
    - Tariff estimate (auto-calculated from country)
  - Profit margin now visible in order summary
  - Partner POC auto-populates in invoices (when real partner selected)
  - Full integration with discounts, marketing rounding, $0.50 rounding
```

### README.md (Tab 3 section)
```markdown
### Tab 3: Order & Client Info

**Custom Line Items:**
- Add unique services/customizations not in the catalog
- Track profit margin with base cost + markup % pricing
- Select partner for POC tracking (or "Custom/Other")
- Optional advanced features:
  - Country of origin (for tariff calculations)
  - Customization fees (setup + per-unit costs)
  - MSRP with automatic markup calculation
  - Manual tariff override
```

---

## Success Metrics

**User Experience:**
- ✅ Add basic custom item in under 30 seconds
- ✅ Add fully-configured custom item in under 90 seconds
- ✅ Profit margin clearly visible in preview and order summary
- ✅ Partner POC auto-populates (when applicable)

**Technical:**
- ✅ No breaking changes to existing orders
- ✅ All 34 test scenarios pass
- ✅ Works with all existing features (discounts, rounding, etc.)
- ✅ CSV/HTML exports show correct data

**Business Value:**
- ✅ Users can see profit on custom items (previously unknown)
- ✅ Partner tracking improves coordination (POC, in-hands dates)
- ✅ Customization fees properly tracked and invoiced
- ✅ Tariff estimates accurate (based on country)

---

## Rollback Plan

**If issues arise:**
1. All changes are isolated to Tab 3 custom line items section
2. Old structure still works - just missing new fields
3. Revert with: `git revert <commit-hash>`
4. No data migration needed (existing orders unaffected)

**Safeguards:**
- Preserve old `is_custom: True` flag for backward compatibility
- New fields have sensible defaults (won't break old logic)
- Advanced options are optional (basic fields always work)

---

## Implementation Timeline

### Phase 1: Basic Fields (1 hour)
- [ ] Add partner selection dropdown
- [ ] Add base cost, markup fields
- [ ] Remove total price field
- [ ] Add client price preview
- [ ] Update validation
- [ ] Test basic functionality (Tests 1-5)

### Phase 2: Advanced Options (1 hour)
- [ ] Add collapsible "Show advanced options" section
- [ ] Add country selection fields
- [ ] Add MSRP field with calculate button
- [ ] Add customization checkbox + fields
- [ ] Add tariff estimate field
- [ ] Add auto-calculation logic
- [ ] Test advanced features (Tests 6-12)

### Phase 3: Integration & Testing (30-60 minutes)
- [ ] Update custom item structure
- [ ] Test integration with order flow (Tests 13-20)
- [ ] Test exports (Tests 21-23)
- [ ] Test edge cases (Tests 24-30)
- [ ] Test saved orders (Tests 31-34)

### Phase 4: Documentation (15 minutes)
- [ ] Update CHANGELOG.md
- [ ] Update README.md
- [ ] Update CLAUDE.md (if needed)

**Total Estimated Time:** 2.5 - 3.5 hours

---

## Post-Implementation

### User Feedback to Collect
1. Is profit margin visibility helpful?
2. Do users use advanced options often?
3. Which advanced options are most valuable?
4. Any missing fields or features?
5. Should this be added to Tab 1 (proposals)?

### Future Enhancements (Based on Feedback)
- Tab 1 integration (if users request it)
- Custom Product Library (if users create repeat custom items)
- Inline editing for custom items (currently delete/re-add)
- Bulk import from CSV (for multiple custom items)

---

## Open Questions

1. **Should tariff auto-calculation be aggressive or conservative?**
   - Recommendation: Conservative (lower estimates)
   - User can always increase manually

2. **Should we pre-fill "Ships From" when "Made In" is selected?**
   - Recommendation: Yes, default Ships From = Made In
   - User can change if different

3. **Should customization description be required when customization enabled?**
   - Recommendation: No, optional (user might want generic "Customization")
   - Helpful but not mandatory

4. **Should we validate MSRP > base cost?**
   - Recommendation: No, allow MSRP < base cost (show warning)
   - User may have legitimate reasons

5. **Should advanced options remember last state (expanded/collapsed)?**
   - Recommendation: No, always default to collapsed
   - Keeps UI clean for most common use case

---

## Conclusion

**Option 2 Implementation Plan Complete**

**Summary:**
- Enhance existing custom line items with profit tracking
- Add 3 required fields (partner, base cost, markup)
- Add 5 optional advanced fields (country, MSRP, customization, tariff)
- Progressive disclosure keeps UI simple
- 2.5-3.5 hours implementation time
- 34 test scenarios ensure quality

**Next Steps:**
1. Review plan and answer open questions
2. Implement Phase 1 (basic fields)
3. Test thoroughly
4. Implement Phase 2 (advanced options)
5. Test integration
6. Document and deploy

**Ready to implement when approved.**

---

**End of Implementation Plan**
