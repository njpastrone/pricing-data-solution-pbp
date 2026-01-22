# Custom Product Feature - Simplified Solution Analysis

**Created:** 2026-01-20
**Purpose:** Evaluate minimal viable enhancement to existing custom line items
**Compare To:** Full plan in `CUSTOM_PRODUCT_FEATURE_PLAN.md`

---

## Current State: "Custom Line Items" (Existing Feature)

**What it does:**
- Add unique services/customizations not in catalog
- Simple 4-field form: name, quantity, description, total price
- No partner tracking, no markup separation, no customization fees
- Shows as "Custom" partner in invoices

**What it lacks:**
- No base cost tracking (can't see PBP cost vs. client price)
- No markup calculation (profit margin unknown)
- No partner selection (loses partner POC tracking)
- No customization options (setup fees, per-unit costs)
- No tariff support
- Can't be added to proposals (Tab 1)
- Can't see profit on custom items

**Current code location:** Tab 3 lines 5999-6069

---

## Problem Analysis: Why Enhance?

**User Pain Points:**
1. **"I don't know my profit margin on custom items"**
   - Current: Total price only ($625)
   - Need: Base cost ($500) + markup (25%) = total ($625)

2. **"I can't track which partner provides custom items"**
   - Current: Always shows "Custom" partner
   - Need: Select actual partner (for POC, in-hands dates, etc.)

3. **"Custom items can't go in proposals"**
   - Current: Tab 3 only (orders)
   - Need: Tab 1 support (but skip PowerPoint)

4. **"I can't add customization fees to custom products"**
   - Current: Single total price field
   - Need: Base product + optional setup fee + per-unit customization

---

## Simplified Solution Options

### Option 1: Minimal Enhancement (Enhance Existing Custom Line Items)

**Changes:**
1. Add "Base Cost" field (what PBP pays)
2. Add "Markup %" field (profit margin)
3. Auto-calculate "Client Price" (base × markup)
4. Add partner selection dropdown (with "Custom/Other" option)
5. Keep existing simplicity - no advanced options

**UI Changes:**
```
┌─────────────────────────────────────────────────┐
│ Add Custom Line Item (3 added)                  │
│                                                  │
│ Product/Service Name *                           │
│ [________________________________]               │
│                                                  │
│ Partner                                          │
│ [Select partner ▼] (includes "Custom/Other")    │
│                                                  │
│ Quantity *        Base Cost/Unit *   Markup % * │
│ [50] units        $[10.00]          [100.0] %   │
│                                                  │
│ → Client Price: $20.00/unit × 50 = $1,000       │
│                                                  │
│ Description                                      │
│ [________________________________]               │
│                                                  │
│ [Add Custom Item to Order]                       │
└─────────────────────────────────────────────────┘
```

**Code Changes:**
- **File:** `app.py` Tab 3 section (lines 5999-6069)
- **Changes:** ~50 lines modified
- **New Fields:** `partner`, `base_cost`, `markup_percent`
- **Calculation:** `client_price = base_cost * (1 + markup/100)`

**What This Solves:**
- ✅ User sees profit margin on custom items
- ✅ Partner tracking for POC auto-population
- ✅ Works with existing discount/rounding systems
- ✅ Still simple and fast to use
- ✅ Minimal code changes

**What This Doesn't Solve:**
- ❌ No customization setup fees (user can work around with separate line item)
- ❌ No Tab 1 proposal support (still Tab 3 only)
- ❌ No custom product library (no reusability)
- ❌ No tariff calculations (unless we add country field)

**Time Estimate:** 1-2 hours

---

### Option 2: Middle Ground (Add Collapsible Advanced Options)

**Changes:**
1. All Option 1 changes PLUS:
2. Collapsible "Advanced Options" expander with:
   - Country of origin (for tariff calculations)
   - Customization setup fee
   - Customization per-unit cost
   - MSRP (for markup suggestions)

**UI Changes:**
```
┌─────────────────────────────────────────────────┐
│ Add Custom Line Item (3 added)                  │
│                                                  │
│ [Basic fields from Option 1]                    │
│                                                  │
│ [ ] Show advanced options                        │
│                                                  │
│   [If checked, shows:]                           │
│   Country: [USA ▼]                              │
│   Customization Setup: $[0]                     │
│   Customization/Unit: $[0]                      │
│   MSRP: $[0] [Calculate Markup]                 │
│                                                  │
│ [Add Custom Item to Order]                       │
└─────────────────────────────────────────────────┘
```

**Code Changes:**
- **File:** `app.py` Tab 3 section
- **Changes:** ~100 lines (add advanced section)
- **Integration:** Uses existing customization calculation logic

**What This Solves:**
- ✅ Everything from Option 1
- ✅ Customization fees (setup + per-unit)
- ✅ Tariff calculations (based on country)
- ✅ MSRP markup suggestions
- ✅ Still simple by default (advanced hidden)

**What This Doesn't Solve:**
- ❌ No Tab 1 proposal support
- ❌ No custom product library

**Time Estimate:** 2-3 hours

---

### Option 3: Full Solution (From Original Plan)

**Changes:**
- Full product structure (not simplified line items)
- Tab 1 integration (proposals with PowerPoint skip)
- Custom Product Library for reusability
- All advanced options
- 3-phase implementation

**What This Solves:**
- ✅ Everything from Option 1 & 2
- ✅ Tab 1 proposal support
- ✅ Custom product library (reusability)
- ✅ PowerPoint generation (skip with warning)
- ✅ Future-proof architecture

**Time Estimate:** 9-13 hours (all 3 phases)

---

## Recommendation: Start with Option 1, Evolve to Option 2

### Phase 1: Minimal Enhancement (Option 1)

**Rationale:**
- Solves the #1 pain point: profit margin visibility
- Adds partner tracking (important for POC auto-population)
- Minimal code changes (low risk)
- Fast to implement (1-2 hours)
- Users can test and provide feedback quickly

**Implementation:**
```python
# ENHANCED Custom Line Item (Tab 3)
with st.expander(f"Add Custom Line Item ({custom_item_count} added)", expanded=False):
    st.caption("Add unique services or customizations not in the catalog")

    # Product name
    custom_name = st.text_input(
        "Product/Service Name*",
        key="custom_name_input",
        placeholder="e.g., Custom Gold Engraving"
    )

    # Partner selection (NEW)
    partner_options = ["Custom/Other"] + sorted(df_template['Partner'].unique().tolist())
    custom_partner = st.selectbox(
        "Partner",
        options=partner_options,
        key="custom_partner",
        help="Select partner for POC tracking, or 'Custom/Other' for non-partner items"
    )

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
            help="What PBP pays per unit before markup"
        )
    with col3:
        custom_markup = st.number_input(
            "Markup %*",
            min_value=-50.0,
            value=100.0,
            step=5.0,
            key="custom_markup",
            help="Your profit margin. 100% = double the cost"
        )

    # Auto-calculate client price (NEW)
    if custom_base_cost > 0 and custom_quantity > 0:
        client_price_per_unit = custom_base_cost * (1 + custom_markup / 100)
        total_client_price = client_price_per_unit * custom_quantity
        st.info(f"→ Client Price: ${client_price_per_unit:.2f}/unit × {custom_quantity} = ${total_client_price:,.2f}")

    # Description
    custom_description = st.text_input(
        "Description",
        key="custom_description_input",
        placeholder="e.g., Laser engraving on wooden items"
    )

    # Add button
    if st.button("Add Custom Item to Order", type="secondary", use_container_width=True, key="add_custom_item_btn"):
        # Validation
        if not custom_name or len(custom_name.strip()) < 3:
            st.error("Product name is required (min 3 characters)")
        elif custom_base_cost <= 0:
            st.error("Base cost must be greater than $0")
        elif custom_quantity < 1:
            st.error("Quantity must be at least 1 unit")
        else:
            # Calculate totals (NEW CALCULATION)
            product_subtotal = custom_base_cost * custom_quantity
            markup_amount = product_subtotal * (custom_markup / 100)
            product_total = product_subtotal + markup_amount
            total_per_unit = product_total / custom_quantity

            # Create custom item (ENHANCED STRUCTURE)
            custom_item = {
                'product_name': custom_name.strip(),
                'product_ref': "CUSTOM",
                'partner': custom_partner,  # NEW - was always "Custom"
                'quantity': custom_quantity,
                'markup_percent': custom_markup,  # NEW - was always 0
                'include_labels': False,
                'base_price': custom_base_cost,  # NEW - was total_price / quantity
                'tier_range': "N/A",
                'tier_column': "N/A",
                'additional_costs': {},
                'product_subtotal': product_subtotal,  # NEW - calculated from base
                'art_setup_total': 0,
                'label_cost_total': 0,
                'subtotal_before_markup': product_subtotal,  # NEW
                'markup_amount': markup_amount,  # NEW - was always 0
                'product_total': product_total,
                'total_per_unit': total_per_unit,
                'is_custom': True,
                'custom_description': custom_description if custom_description else "Custom line item",
                'country_of_origin': '',
                'tariff_rate_percent': 0.0,
                'tariff_info': '',
                'tariff_base': 0.0,
                'tariff_amount': 0.0,
                'edited_description': '',
                # Per-product kitting fields
                'include_kitting': False,
                'kitting_pbp_cost': 0.0,
                'kitting_client_price': 0.0,
                'kitting_description': ''
            }

            st.session_state.order_items.append(custom_item)
            st.toast(f"Added custom item: {custom_name.strip()}")
            st.rerun()
```

**Testing:**
1. Add custom item with partner selection
2. Add custom item with "Custom/Other"
3. Verify profit margin shows in order summary
4. Verify partner POC auto-populates in invoice (if partner selected)
5. Verify works with discounts, marketing rounding
6. Test CSV and HTML exports

---

### Phase 2: Add Advanced Options (Option 2) - Based on User Feedback

**If users request:**
- Customization fees → Add collapsible advanced section
- Tariff support → Add country field
- MSRP markup → Add MSRP field with calculate button

**Don't implement unless requested** - keeps solution simple

---

## Comparison Table

| Feature | Current | Option 1 | Option 2 | Option 3 |
|---------|---------|----------|----------|----------|
| **Basic Info** | ✅ | ✅ | ✅ | ✅ |
| **Partner Tracking** | ❌ | ✅ | ✅ | ✅ |
| **Base Cost/Markup** | ❌ | ✅ | ✅ | ✅ |
| **Profit Visibility** | ❌ | ✅ | ✅ | ✅ |
| **Customization Fees** | ❌ | ❌ | ✅ | ✅ |
| **Tariff Support** | ❌ | ❌ | ✅ | ✅ |
| **Tab 1 Proposals** | ❌ | ❌ | ❌ | ✅ |
| **Product Library** | ❌ | ❌ | ❌ | ✅ |
| **PowerPoint Skip** | ❌ | ❌ | ❌ | ✅ |
| **Code Changes** | - | ~50 lines | ~100 lines | ~400 lines |
| **Time to Implement** | - | 1-2 hrs | 2-3 hrs | 9-13 hrs |
| **Testing Effort** | - | 6 tests | 10 tests | 28 tests |
| **Risk** | - | Low | Low | Medium |

---

## Why Option 1 is Best Starting Point

### 1. **Pareto Principle (80/20 Rule)**
- Option 1 solves 80% of user pain points with 20% of the effort
- Most critical need: profit margin visibility
- Second most critical: partner tracking

### 2. **Fast Feedback Loop**
- Implement in 1-2 hours
- Users test within same day
- Gather real usage data before investing more time

### 3. **Low Risk**
- Minimal code changes (only ~50 lines)
- Enhances existing feature (doesn't replace)
- Easy to revert if issues arise

### 4. **Iterative Enhancement**
- Can add advanced options later (Option 2) if needed
- Can evolve to full solution (Option 3) if demand exists
- No rework needed - Option 1 is subset of Option 2/3

### 5. **User-Centric**
- Solves actual pain points (not theoretical features)
- Simple UI (no overwhelm with advanced options)
- Works with existing workflows

---

## What Users Get (Option 1)

**Before (Current Custom Line Items):**
```
Added: "Custom Gold Engraving"
Total Price: $1,000
Profit: Unknown
Partner: "Custom" (generic)
```

**After (Enhanced Custom Line Items):**
```
Added: "Custom Gold Engraving"
Partner: Homeless Garden Project
Base Cost: $500 (50 units × $10/unit)
Markup: 100%
Profit: $500 (visible in order summary)
Client Price: $1,000

✅ Partner POC auto-populated in invoice
✅ Profit margin tracked and visible
✅ Works with discount/rounding settings
```

---

## Migration Path (If Choosing Full Solution Later)

**Option 1 → Option 2:**
- Add collapsible expander below basic fields
- Add 4 advanced fields (country, customization setup/unit, MSRP)
- No breaking changes to existing data

**Option 2 → Option 3:**
- Refactor to full product structure (requires data migration)
- Add Tab 1 support
- Add custom product library
- Breaking change - but can migrate existing custom items

**Recommendation:** Start with Option 1, observe usage for 2-4 weeks, then decide if Option 2 or Option 3 is needed.

---

## Open Questions (Option 1 Only)

1. **Should we set a default markup?**
   - Recommendation: 100% (matches catalog products)
   - User can always change

2. **Should we validate markup is positive?**
   - Recommendation: Allow negative (below-cost pricing), but show warning
   - Some clients may have strategic reasons for below-cost

3. **Should we allow $0 base cost?**
   - Recommendation: No, require minimum $0.01
   - Prevents division by zero errors

4. **Should custom items appear in Tab 1 proposals?**
   - Recommendation: No, not in Option 1 (keep scope minimal)
   - Can add in future if requested

5. **Should custom items work with MSRP pricing checkbox?**
   - Recommendation: No, not in Option 1
   - Can add MSRP field in Option 2 if needed

---

## Implementation Checklist (Option 1)

### Code Changes
- [ ] Add partner selection dropdown (with "Custom/Other")
- [ ] Add base cost input field
- [ ] Add markup % input field
- [ ] Remove total price input (auto-calculated now)
- [ ] Add client price preview display
- [ ] Update validation logic
- [ ] Update custom item structure (add partner, markup fields)
- [ ] Update calculation logic (base × markup instead of total price)

### Testing
- [ ] Add custom item with partner selection
- [ ] Add custom item with "Custom/Other"
- [ ] Verify profit shows in order summary
- [ ] Verify partner POC auto-populates in invoice
- [ ] Verify works with 5% discount
- [ ] Verify works with marketing rounding
- [ ] Verify CSV export shows correct values
- [ ] Verify HTML export shows correct values
- [ ] Test negative markup (should warn)
- [ ] Test quantity = 1 (should warn)

### Documentation
- [ ] Update CHANGELOG.md
- [ ] Update README.md (if needed)
- [ ] Add usage note in Tab 3 caption

---

## Success Metrics (Option 1)

**User Experience:**
- ✅ Add custom item in under 30 seconds (was ~20 seconds, minimal slowdown)
- ✅ Profit margin visible in order summary
- ✅ Partner tracking works correctly

**Technical:**
- ✅ No breaking changes to existing orders
- ✅ Works with all existing features (discounts, rounding, etc.)
- ✅ CSV/HTML exports show correct data

**Business:**
- ✅ Users can see profit on custom items (previously unknown)
- ✅ Partner POCs auto-populate (better coordination)
- ✅ Custom items integrate better with order workflow

---

## Conclusion

**Recommendation: Implement Option 1 (Minimal Enhancement)**

**Why:**
- Solves critical user pain points (profit visibility, partner tracking)
- Fast to implement (1-2 hours)
- Low risk (minimal code changes)
- Easy to enhance later if needed
- No user overwhelm (simple UI)

**What User Gets:**
- Base cost + markup = client price (transparent pricing)
- Partner selection (proper POC tracking)
- Works with existing discount/rounding systems
- Still fast and simple to use

**Next Steps:**
1. Implement Option 1 (~1-2 hours)
2. Test thoroughly (6 scenarios)
3. Deploy and gather user feedback
4. After 2-4 weeks, evaluate:
   - Are users requesting customization fees? → Option 2
   - Are users requesting Tab 1 support? → Option 3
   - Are users happy with current? → Stop here

**Bottom Line:** Option 1 delivers 80% of value with 20% of effort. Start here.

---

**End of Simplified Solution Analysis**
