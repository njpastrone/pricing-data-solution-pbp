# Custom Product Feature - Comprehensive Implementation Plan

**Created:** 2026-01-20
**Purpose:** Add ability to create entirely custom products not in the catalog
**Primary Use Case:** Tab 3 (Order & Client Info) - ordering stage
**Secondary Use Case:** Tab 1 (Proposal Generator) - with limitations

---

## Executive Summary

**What:** Allow users to create custom products with full pricing structure (not just simple line items)
**Why:** Handles one-off items, partner products not yet in catalog, executive samples, unique customizations
**Where:** Primarily Tab 3 (orders), optionally Tab 1 (proposals, but skip PowerPoint generation)
**How:** Multi-step form with progressive disclosure, sensible defaults, and optional advanced settings

**Key Insight:** Custom products need same data structure as catalog products for seamless integration with pricing engine, invoice generation, and order management.

---

## Current State Analysis

### Existing "Custom Line Items" (Simplified)
**Location:** Tab 3 and Tab 4 (Order Settings section)
**Structure:**
```python
{
    'product_name': "Custom Engraving Service",
    'custom_description': "Gold foil engraving on leather journals",
    'quantity': 50,
    'total_per_unit': 12.50,  # Total price, no markup calculation
    'product_total': 625.00,
    'is_custom': True,
    # Simplified fields - no partner, no base cost, no customization options
}
```

**Limitations:**
- No partner tracking
- No base cost / markup separation
- No customization setup fees or per-unit costs
- No tariff calculations
- No tiered pricing options
- No integration with MSRP or standard markup
- Can't be added to proposals (Tab 1)
- Shows as "Custom" partner in invoices

### Catalog Products (Full Structure)
**Location:** Tab 1, Tab 2, Tab 3, Tab 4
**Structure:**
```python
{
    'product_name': "Strawberry Jam - 4oz",
    'partner': "Homeless Garden Project",
    'product_data': {
        'Product/Service': "Strawberry Jam - 4oz",
        'Partner': "Homeless Garden Project",
        'Pricing Tiers (Y/N)': 'Y',
        'PBP Cost: Tier 1': 8.50,
        'T1 Start': 1, 'T1 End': 50,
        # ... all tier data
        'Country of Origin (Made In)': 'USA',
        'Country of Origin (Ships From)': 'USA',
        'Vendor Published MSRP': 18.00,
        'Customization Setup Fee': 150.00,
        'Customization Cost per Unit': 2.50,
        # ... etc
    },
    'quantity': 100,
    'markup_percent': 100.0,
    'base_price': 7.50,  # Auto-calculated based on tier
    'tier_range': 'T3: 101-200',
    'tier_column': 'PBP Cost: Tier 3',
    'include_customization': True,
    'customization_setup_total': 150.00,
    'customization_per_unit': 2.50,
    # ... full pricing breakdown
}
```

**Benefits:**
- Works with existing pricing engine
- Shows in proposals, orders, invoices
- Supports all features (markup, discounts, marketing rounding, etc.)
- Partner tracking for POCs and in-hands dates
- Tariff calculations
- Full customization support

---

## Feature Requirements

### Must Have (MVP)
1. **Basic Product Info**
   - Product name (required)
   - Partner selection OR "Custom/Other" (required)
   - Base cost per unit (required)
   - Pricing type: Flat-rate only (tiered pricing too complex for MVP)

2. **Pricing Integration**
   - Works with existing markup system
   - Compatible with discount application
   - Compatible with marketing rounding
   - Shows in order summary with correct calculations

3. **Order Integration**
   - Adds to Tab 3 order items with full structure
   - Shows in Tab 4 invoice/PO correctly
   - Partner tracking (for POC auto-population if partner selected)
   - Tariff calculation support

4. **UI/UX**
   - Simple, guided form with progressive disclosure
   - Required vs optional fields clearly marked
   - Sensible defaults where possible
   - Preview before adding
   - Validation and error messages

### Should Have (Phase 2)
5. **Advanced Options**
   - Country of origin (for tariff calculations)
   - Product description
   - Customization setup fee
   - Customization per-unit cost
   - MSRP (for markup suggestions)

6. **Reusability**
   - Save custom products to "Custom Product Library"
   - Quick add from library for repeat orders
   - Edit and update library products
   - Delete from library

7. **Tab 1 Integration**
   - Add custom products to proposals in Tab 1
   - Skip during PowerPoint generation (with warning message)
   - Include in proposal tables (CSV export)

### Could Have (Future)
8. **Tiered Pricing Support**
   - Define 2-3 simple tiers for custom products
   - Not full 6-tier system (too complex)

9. **PowerPoint Support**
   - Generate generic text slide for custom products
   - Show product name, quantity, price
   - No image or partner branding

10. **Batch Import**
    - CSV upload for multiple custom products
    - Useful for migrating old partner data

---

## Data Structure Design

### Option A: Extend Existing Custom Line Items (NOT RECOMMENDED)
**Pros:** Minimal code changes
**Cons:** Doesn't integrate well with pricing engine, invoice generation becomes complex

### Option B: Create Full Product Structure (RECOMMENDED)
**Pros:** Seamless integration, works with all existing systems, future-proof
**Cons:** More fields to collect from user

**Recommended Structure:**
```python
{
    # Core identification
    'product_name': "Custom Gold Engraving",
    'partner': "Custom/Other",  # Or selected partner
    'is_custom_product': True,  # Flag to distinguish from catalog products

    # Simplified product_data (only essentials)
    'product_data': {
        'Product/Service': "Custom Gold Engraving",
        'Partner': "Custom/Other",
        'Pricing Tiers (Y/N)': 'N',  # Always flat-rate for custom products
        'PBP Cost (No Tiers)': 15.00,  # User-provided base cost
        'Country of Origin (Made In)': user_input or '',
        'Country of Origin (Ships From)': user_input or '',
        'Vendor Published MSRP': user_input or 0,
        'Customization Setup Fee': user_input or 0,
        'Customization Cost per Unit': user_input or 0,
        'Marketing Description': user_input or '',
        'Tariff Estimate (%)': 0,  # Can calculate based on country
        # All other fields: default values
    },

    # Standard order item fields (auto-calculated)
    'quantity': 50,
    'markup_percent': 100.0,  # Default or MSRP-calculated
    'base_price': 15.00,
    'tier_range': "No Tiers",
    'tier_column': "PBP Cost (No Tiers)",
    'include_customization': False,  # User enables if needed
    # ... all other standard fields
}
```

---

## UI/UX Design

### Location: Tab 3 - New Section After Manual Product Selection

**Current Tab 3 Workflow:**
1. Getting Started - Choose Your Workflow
2. Option A: Import HTML Form (recommended)
3. Option B: Import from Proposal
4. Option C: Manual Product Selection
5. **NEW: Option D: Create Custom Product** ← Insert here
6. Section 2: Current Order
7. Section 3: Order Settings
8. Section 4: Order Summary
9. Section 5: Client & Order Information

**Alternative Location (if no proposal):**
- Option C becomes "Manual Product Selection"
- **NEW: Option D becomes "Create Custom Product"**

### UI Pattern: Progressive Disclosure Form

**Step 1: Basic Information** (always visible)
```
┌─────────────────────────────────────────────────┐
│ Create Custom Product                            │
│                                                  │
│ Product/Service Name *                           │
│ [_____________________________________]          │
│                                                  │
│ Partner                                          │
│ [Select partner ▼] or [ ] Custom/Other          │
│                                                  │
│ Base Cost per Unit * (what PBP pays)             │
│ $[_____]                                         │
│                                                  │
│ Quantity *                                       │
│ [____] units                                     │
│                                                  │
│ Markup % *                                       │
│ [100.0] % (100% = 2x cost)                      │
│                                                  │
│ [ ] Show advanced options                        │
│                                                  │
│ [Preview & Add to Order]                         │
└─────────────────────────────────────────────────┘
```

**Step 2: Advanced Options** (collapsible expander)
```
┌─────────────────────────────────────────────────┐
│ ▼ Advanced Options (optional)                    │
│                                                  │
│ Product Description                              │
│ [_____________________________________]          │
│                                                  │
│ Country of Origin                                │
│ Made In: [USA ▼]  Ships From: [USA ▼]          │
│                                                  │
│ MSRP (Manufacturer's Suggested Retail Price)     │
│ $[_____] → [Calculate Markup from MSRP]         │
│                                                  │
│ Customization (setup fees & per-unit costs)      │
│ [ ] Include customization                        │
│   Setup Fee: $[_____]                           │
│   Per-Unit Cost: $[_____]                       │
│   Description: [_____________________]          │
│                                                  │
│ Tariff Estimate                                  │
│ [____] % (auto-calculated based on country)     │
│                                                  │
│ [ ] Save to Custom Product Library               │
│   (for quick reuse in future orders)            │
└─────────────────────────────────────────────────┘
```

**Step 3: Preview Before Adding**
```
┌─────────────────────────────────────────────────┐
│ Preview: Custom Gold Engraving                   │
│                                                  │
│ Partner: Custom/Other                            │
│ Base Cost: $15.00/unit × 50 units = $750.00     │
│ Markup: 100% → $15.00/unit profit               │
│ Client Price: $30.00/unit × 50 = $1,500.00      │
│                                                  │
│ Customization: Setup $150 + $2.50/unit          │
│                                                  │
│ Total to Client: $1,775.00                       │
│                                                  │
│ [Cancel] [Add to Order]                          │
└─────────────────────────────────────────────────┘
```

### Validation Rules

**Required Fields:**
- Product/Service Name (min 3 characters)
- Partner OR "Custom/Other" selected
- Base Cost per Unit (> 0)
- Quantity (> 0)
- Markup % (can be negative for below-cost, but warn user)

**Optional Fields:**
- All advanced options
- Default to empty string or 0

**Error Messages:**
- "Product name is required (min 3 characters)"
- "Please select a partner or choose 'Custom/Other'"
- "Base cost must be greater than $0"
- "Quantity must be at least 1 unit"

**Warning Messages:**
- "Markup is negative - you're pricing below cost"
- "No MSRP provided - using default 100% markup"
- "Quantity is 1 - did you mean to order more?"

---

## Implementation Plan

### Phase 1: MVP - Basic Custom Products (Tab 3 Only)

**Goal:** Add custom products to orders with flat-rate pricing

**Files to Modify:**
1. **app.py - Tab 3 Section** (lines ~4900-5100)
   - Add "Option D: Create Custom Product" section
   - Create form UI with basic fields
   - Validation logic
   - Preview display
   - Add to order_items with full product structure

**Code Structure:**
```python
# ============================================================
# OPTION D: CREATE CUSTOM PRODUCT
# ============================================================
st.divider()
st.subheader("Option D: Create Custom Product")
st.caption("Add unique products not in the catalog (one-off items, partner products pending catalog addition, executive samples)")

with st.expander("Create Custom Product", expanded=False):
    st.markdown("### Basic Information")

    # Product name
    custom_product_name = st.text_input(
        "Product/Service Name*",
        key="custom_product_name",
        placeholder="e.g., Gold Foil Engraving on Leather Journals"
    )

    # Partner selection
    col1, col2 = st.columns([2, 1])
    with col1:
        partner_options = ["Custom/Other"] + sorted(df_template['Partner'].unique().tolist())
        custom_partner = st.selectbox(
            "Partner*",
            options=partner_options,
            key="custom_partner",
            help="Select partner or 'Custom/Other' for non-catalog items"
        )

    # Base cost
    col1, col2, col3 = st.columns(3)
    with col1:
        custom_base_cost = st.number_input(
            "Base Cost per Unit* (what PBP pays)",
            min_value=0.01,
            value=10.00,
            step=0.50,
            key="custom_base_cost",
            help="Partner's price per unit before markup"
        )
    with col2:
        custom_quantity = st.number_input(
            "Quantity*",
            min_value=1,
            value=1,
            step=1,
            key="custom_quantity"
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

    # Warning if markup is negative
    if custom_markup < 0:
        st.warning("⚠️ Negative markup - you're pricing below cost")

    # Warning if quantity is 1
    if custom_quantity == 1:
        st.warning("⚠️ Quantity is 1 - did you mean to order more?")

    # Advanced options (collapsible)
    with st.expander("Advanced Options (optional)", expanded=False):
        # Description
        custom_description = st.text_area(
            "Product Description",
            key="custom_description",
            placeholder="Marketing description for client-facing documents"
        )

        # Country of origin
        col1, col2 = st.columns(2)
        with col1:
            custom_made_in = st.selectbox(
                "Made In",
                options=[""] + ["USA", "China", "India", "Vietnam", "Other"],
                key="custom_made_in"
            )
        with col2:
            custom_ships_from = st.selectbox(
                "Ships From",
                options=[""] + ["USA", "China", "India", "Vietnam", "Other"],
                key="custom_ships_from"
            )

        # MSRP
        col1, col2 = st.columns([2, 1])
        with col1:
            custom_msrp = st.number_input(
                "MSRP (Manufacturer's Suggested Retail Price)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="custom_msrp"
            )
        with col2:
            if st.button("Calculate Markup from MSRP", key="custom_calc_msrp"):
                if custom_msrp > 0 and custom_base_cost > 0:
                    msrp_markup = ((custom_msrp / custom_base_cost) - 1) * 100
                    st.session_state.custom_markup = max(0, msrp_markup)
                    st.success(f"Markup set to {msrp_markup:.1f}%")
                    st.rerun()

        # Customization
        custom_include_customization = st.checkbox(
            "Include customization (setup fees & per-unit costs)",
            key="custom_include_customization"
        )

        if custom_include_customization:
            col1, col2 = st.columns(2)
            with col1:
                custom_setup_fee = st.number_input(
                    "Setup Fee ($)",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    key="custom_setup_fee"
                )
            with col2:
                custom_per_unit_cost = st.number_input(
                    "Per-Unit Cost ($)",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    key="custom_per_unit_cost"
                )

            custom_customization_desc = st.text_input(
                "Customization Description",
                key="custom_customization_desc",
                placeholder="e.g., Gold foil logo on front cover"
            )

        # Tariff
        custom_tariff = st.number_input(
            "Tariff Estimate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            key="custom_tariff",
            help="Estimated tariff rate (auto-calculated based on country if available)"
        )

    # Preview
    st.markdown("---")
    st.markdown("### Preview")

    # Calculate preview totals
    if custom_base_cost > 0 and custom_quantity > 0:
        product_subtotal = custom_base_cost * custom_quantity
        markup_amount = product_subtotal * (custom_markup / 100)
        product_total = product_subtotal + markup_amount
        client_price_per_unit = product_total / custom_quantity

        # Customization
        customization_setup = custom_setup_fee if custom_include_customization else 0
        customization_unit_total = (custom_per_unit_cost * custom_quantity) if custom_include_customization else 0

        total_to_client = product_total + customization_setup + customization_unit_total

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Base Cost (PBP)", f"${product_subtotal:.2f}")
            st.caption(f"${custom_base_cost:.2f}/unit × {custom_quantity} units")
        with col2:
            st.metric("Client Price (Base Product)", f"${product_total:.2f}")
            st.caption(f"${client_price_per_unit:.2f}/unit (includes {custom_markup}% markup)")

        if custom_include_customization and (customization_setup > 0 or customization_unit_total > 0):
            st.info(f"Customization: ${customization_setup:.2f} setup + ${customization_unit_total:.2f} ({custom_quantity} × ${custom_per_unit_cost:.2f}/unit)")

        st.success(f"**Total to Client: ${total_to_client:,.2f}**")

    # Add button
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Add to Order", key="add_custom_product", type="primary", use_container_width=True):
            # Validation
            if not custom_product_name or len(custom_product_name.strip()) < 3:
                st.error("Product name is required (min 3 characters)")
            elif custom_base_cost <= 0:
                st.error("Base cost must be greater than $0")
            elif custom_quantity < 1:
                st.error("Quantity must be at least 1 unit")
            else:
                # Create product_data dict (matches catalog structure)
                custom_product_data = {
                    'Product/Service': custom_product_name.strip(),
                    'Partner': custom_partner,
                    'Pricing Tiers (Y/N)': 'N',
                    'PBP Cost (No Tiers)': custom_base_cost,
                    'Country of Origin (Made In)': custom_made_in if custom_made_in else '',
                    'Country of Origin (Ships From)': custom_ships_from if custom_ships_from else '',
                    'Vendor Published MSRP': custom_msrp,
                    'Customization Setup Fee': custom_setup_fee if custom_include_customization else 0,
                    'Customization Cost per Unit': custom_per_unit_cost if custom_include_customization else 0,
                    'Customization Info': custom_customization_desc if custom_include_customization else '',
                    'Marketing Description': custom_description if custom_description else '',
                    'Tariff Estimate (%)': custom_tariff,
                    'MOQ (PBP)': '',
                    'MOV (PBP)': '',
                    'MOQ (Partner)': '',
                    'MOV (Partner)': '',
                    'Tariff Info': '',
                    'Purchase Description': '',
                    'Units per Package': 1,
                    'PBP Standard Markup': custom_markup,
                    # All other fields get defaults
                }

                # Calculate pricing using existing pricing engine
                from src.pricing_engine import get_unit_price_new_system
                from src.helpers import calculate_product_tariff

                base_price, tier_range, tier_column = get_unit_price_new_system(custom_product_data, custom_quantity)

                # Calculate tariff
                tariff_rate, tariff_info = calculate_product_tariff(custom_product_data, custom_quantity)

                # Calculate all totals (matches standard product structure)
                product_subtotal = base_price * custom_quantity
                markup_amount = product_subtotal * (custom_markup / 100)
                product_total = product_subtotal + markup_amount

                # Customization totals
                customization_setup_total = custom_setup_fee if custom_include_customization else 0
                customization_unit_total = (custom_per_unit_cost * custom_quantity) if custom_include_customization else 0

                # Create order item (full structure)
                new_custom_product = {
                    'product_name': custom_product_name.strip(),
                    'partner': custom_partner,
                    'product_data': custom_product_data,
                    'quantity': custom_quantity,
                    'markup_percent': custom_markup,
                    'selected_variant': None,
                    'is_custom_product': True,  # FLAG for identification
                    'source': 'custom',

                    # Calculated fields
                    'base_price': base_price,
                    'tier_range': tier_range,
                    'tier_column': tier_column,
                    'product_ref': '',
                    'country_of_origin_made_in': custom_made_in if custom_made_in else '',
                    'country_of_origin_ships_from': custom_ships_from if custom_ships_from else '',
                    'customization_description': custom_customization_desc if custom_include_customization else '',
                    'product_subtotal': product_subtotal,
                    'customization_setup_total': customization_setup_total,
                    'customization_unit_total': customization_unit_total,
                    'subtotal_before_markup': product_subtotal,
                    'markup_amount': markup_amount,
                    'product_total': product_total,
                    'total_per_unit': product_total / custom_quantity,
                    'tariff_rate_percent': tariff_rate,
                    'tariff_amount': 0.0,  # Calculated later in order summary
                    'edited_description': '',
                    'include_customization': custom_include_customization,
                    'customization_setup_fee': custom_setup_fee if custom_include_customization else 0,
                    'customization_per_unit': custom_per_unit_cost if custom_include_customization else 0,
                    # All other standard fields...
                }

                # Add to order
                st.session_state.order_items.append(new_custom_product)
                st.toast(f"Added custom product: {custom_product_name.strip()}")
                st.rerun()
```

**Testing Checklist:**
- [ ] Add custom product with minimal fields (name, partner, cost, quantity, markup)
- [ ] Add custom product with all advanced options
- [ ] Verify shows correctly in Section 2 (Current Order)
- [ ] Verify shows correctly in Section 4 (Order Summary)
- [ ] Verify shows correctly in Tab 4 invoice/PO
- [ ] Test with "Custom/Other" partner
- [ ] Test with real partner selection
- [ ] Test with customization enabled
- [ ] Test with negative markup (should warn)
- [ ] Test with quantity = 1 (should warn)
- [ ] Test MSRP markup calculation button
- [ ] Test validation (empty name, zero cost, etc.)
- [ ] Test CSV export includes custom product
- [ ] Test HTML export includes custom product
- [ ] Test saved orders include custom products

**Estimated Time:** 4-6 hours

---

### Phase 2: Custom Product Library (Reusability)

**Goal:** Save custom products for quick reuse in future orders

**New Storage:** Google Sheets - `custom_product_library` spreadsheet

**UI Location:** Tab 3 - Before "Create Custom Product" section

**Features:**
1. View saved custom products
2. Quick add from library (1-click)
3. Edit library products
4. Delete from library
5. Library is dataset-agnostic (works across demo and real datasets)

**Code Structure:**
```python
# ============================================================
# CUSTOM PRODUCT LIBRARY
# ============================================================
st.divider()
st.subheader("Custom Product Library")
st.caption("Quick add from previously saved custom products")

with st.expander("Manage Custom Product Library", expanded=False):
    # Load library
    custom_library = load_custom_product_library()  # New function in helpers

    if len(custom_library) == 0:
        st.info("No saved custom products yet. Create one below and check 'Save to Library'")
    else:
        # Display library items
        for idx, lib_product in enumerate(custom_library):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{lib_product['name']}**")
                st.caption(f"Partner: {lib_product['partner']} | Base Cost: ${lib_product['base_cost']:.2f}/unit")
            with col2:
                if st.button("Add to Order", key=f"lib_add_{idx}", use_container_width=True):
                    # Add to order with library product data
                    # ... (same logic as manual create, but pre-filled)
                    pass
            with col3:
                if st.button("Delete", key=f"lib_delete_{idx}", type="secondary", use_container_width=True):
                    # Delete from library
                    delete_custom_product_from_library(lib_product['id'])
                    st.success(f"Deleted {lib_product['name']}")
                    st.rerun()
```

**New Module:** `src/custom_product_manager.py`
```python
def save_custom_product_to_library(product_data: dict) -> bool:
    """Save custom product to Google Sheets library for reuse"""
    pass

def load_custom_product_library() -> list:
    """Load all saved custom products from library"""
    pass

def delete_custom_product_from_library(product_id: str) -> bool:
    """Delete custom product from library"""
    pass

def update_custom_product_in_library(product_id: str, product_data: dict) -> bool:
    """Update existing custom product in library"""
    pass
```

**Estimated Time:** 3-4 hours

---

### Phase 3: Tab 1 Integration (Proposals with Custom Products)

**Goal:** Add custom products to proposals in Tab 1

**Considerations:**
- Custom products skip PowerPoint generation (no slide match)
- Include in proposal tables (CSV export)
- Show warning during PowerPoint generation
- User can choose to skip PowerPoint or generate with warning

**UI Location:** Tab 1 - After "Bulk Actions" section

**Code Changes:**
1. Add "Create Custom Product" form in Tab 1 (similar to Tab 3)
2. Add to `proposal_products` with custom flag
3. Skip during PowerPoint matching (Phase 1)
4. Show in proposal tables (already works if structure matches)
5. Warning message: "X custom products will be skipped in PowerPoint generation"

**PowerPoint Generation Logic Update:**
```python
# In PowerPoint generation section
custom_product_count = sum(1 for item in st.session_state.proposal_products if item.get('is_custom_product', False))

if custom_product_count > 0:
    st.warning(f"⚠️ {custom_product_count} custom product(s) will be skipped during PowerPoint generation (no slide matches available). They will still appear in proposal tables.")

    proceed = st.checkbox("Proceed with PowerPoint generation (skip custom products)", key="proceed_with_custom_skip")
    if not proceed:
        st.info("Enable checkbox above to proceed")
        st.stop()
```

**Alternative: Generic Text Slide for Custom Products (Future)**
```python
# Generate simple text-only slide for custom products
def create_generic_product_slide(prs, product_name, quantity, price):
    """Create basic slide with product name, quantity, and price"""
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout
    # Add title
    title = slide.shapes.title
    title.text = product_name
    # Add text box with details
    # ...
    return slide
```

**Estimated Time:** 2-3 hours

---

### Phase 4: Advanced Features (Future Enhancements)

**Tiered Pricing for Custom Products**
- Allow 2-3 simple tiers (not full 6-tier system)
- UI: Add tier ranges manually
- Complexity: Medium

**PowerPoint Generic Slides**
- Auto-generate text slide for custom products
- Include pricing table
- Complexity: Medium

**Batch Import (CSV)**
- Upload CSV with multiple custom products
- Map columns to required fields
- Complexity: High

**Custom Product Analytics**
- Most frequently used custom products
- Suggest adding to official catalog
- Complexity: Low

---

## Success Metrics

**MVP Success Criteria:**
1. ✅ User can create custom product with 5 required fields in under 60 seconds
2. ✅ Custom product appears in Tab 3 order with correct pricing
3. ✅ Custom product appears in Tab 4 invoice/PO correctly
4. ✅ Custom product exports to CSV and HTML correctly
5. ✅ Custom product calculates markup, discounts, marketing rounding correctly
6. ✅ Validation prevents invalid data entry
7. ✅ All 14 test scenarios pass

**Phase 2 Success Criteria:**
1. ✅ User can save custom product to library
2. ✅ User can quick-add from library in under 10 seconds
3. ✅ Library persists across sessions
4. ✅ User can delete library products

**Phase 3 Success Criteria:**
1. ✅ User can add custom product to Tab 1 proposal
2. ✅ Custom products appear in proposal tables
3. ✅ PowerPoint generation skips custom products gracefully
4. ✅ Warning message is clear and actionable

---

## Edge Cases & Error Handling

**Edge Case 1: Negative Markup**
- **Scenario:** User sets markup to -20% (pricing below cost)
- **Handling:** Show warning, allow (client may have strategic reasons)
- **UI:** "⚠️ Negative markup - you're pricing below cost"

**Edge Case 2: Zero Base Cost**
- **Scenario:** User sets base cost to $0 (donated product?)
- **Handling:** Require > $0.01, show error
- **UI:** "Base cost must be greater than $0"

**Edge Case 3: Extremely High Markup**
- **Scenario:** User sets markup to 500%
- **Handling:** Allow, but confirm
- **UI:** "High markup detected (500%) - is this correct?"

**Edge Case 4: Duplicate Product Names**
- **Scenario:** Custom product name matches catalog product
- **Handling:** Allow (may be intentional variant), add "(Custom)" suffix in display
- **UI:** Display as "Gold Engraving (Custom)" to distinguish

**Edge Case 5: Partner Selection with Missing POC**
- **Scenario:** User selects partner that has no POC data
- **Handling:** Allow, show "N/A" in invoice POC section
- **UI:** No special handling needed

**Edge Case 6: Custom Product in Saved Order**
- **Scenario:** Load saved order containing custom products
- **Handling:** Load normally (custom products stored in order data)
- **UI:** Show "(Custom)" indicator next to product name

**Edge Case 7: Dataset Switch with Custom Products**
- **Scenario:** User switches from Demo to Real dataset with custom products in order
- **Handling:** Keep custom products (they're dataset-agnostic), clear catalog products
- **UI:** "Dataset changed - cleared catalog products, kept custom products"

---

## Documentation Updates

**Files to Update:**
1. **README.md** - Add "Custom Products" to features list
2. **CLAUDE.md** - Add custom product workflow to Tab 3 section
3. **ACTIVE_DEVELOPMENT_TODO.md** - Track implementation progress
4. **CHANGELOG.md** - Document feature addition in appropriate version

**User Guide Section:**
```markdown
### Creating Custom Products

Custom products allow you to add items that aren't in the catalog:
- One-off items for specific clients
- Partner products pending catalog addition
- Executive samples
- Unique customizations

**To create a custom product:**
1. Go to Tab 3 (Order & Client Info)
2. Find "Option D: Create Custom Product"
3. Fill in required fields:
   - Product name
   - Partner (or "Custom/Other")
   - Base cost per unit
   - Quantity
   - Markup %
4. (Optional) Add advanced options:
   - Description
   - Country of origin
   - MSRP
   - Customization fees
5. Preview pricing
6. Click "Add to Order"

**Custom products work just like catalog products:**
- Full pricing calculations (markup, discounts, rounding)
- Appear in order summary
- Export to CSV and HTML
- Show in invoices/POs

**Limitations:**
- No PowerPoint slide matching (skip during generation)
- Flat-rate pricing only (no tiers in MVP)
```

---

## Testing Plan

### Unit Tests
1. Create custom product with minimal fields
2. Create custom product with all advanced options
3. Validate required fields (empty name, zero cost, etc.)
4. Calculate pricing correctly (base cost + markup)
5. Calculate customization correctly (setup + per-unit)
6. Calculate tariff correctly (based on country)
7. MSRP markup calculation
8. Negative markup warning
9. Quantity = 1 warning

### Integration Tests
10. Add custom product to Tab 3 order
11. Custom product appears in Section 2 (Current Order)
12. Custom product appears in Section 4 (Order Summary)
13. Custom product appears in Tab 4 invoice/PO
14. Custom product exports to CSV correctly
15. Custom product exports to HTML correctly
16. Custom product saves with order
17. Custom product loads from saved order
18. Dataset switch keeps custom products

### Phase 2 Tests (Library)
19. Save custom product to library
20. Load library products
21. Quick-add from library
22. Delete library product
23. Library persists across sessions

### Phase 3 Tests (Tab 1)
24. Add custom product to Tab 1 proposal
25. Custom product appears in proposal tables
26. PowerPoint generation skips custom products
27. Warning message shows custom product count
28. Custom product exports to proposal CSV

---

## Rollback Plan

**If Phase 1 causes issues:**
1. All changes are isolated to new section in Tab 3
2. Remove "Option D: Create Custom Product" section
3. No changes to existing functionality
4. Revert commit with: `git revert <commit-hash>`

**If data structure causes problems:**
1. Custom products use same structure as catalog products
2. Flag `is_custom_product: True` allows easy filtering
3. Can hide custom products with: `if not item.get('is_custom_product')`

**If pricing calculations fail:**
1. Use existing pricing engine (no new calculation logic)
2. Debug pricing preview before allowing add
3. Validation prevents invalid data entry

---

## Future Considerations

**Custom Product Catalog Migration**
- Most frequently used custom products should be added to official catalog
- Analytics to track custom product usage
- Suggest migration to catalog when product used 3+ times

**Partner-Specific Custom Products**
- Partner provides custom pricing file
- Import partner data as custom products
- Useful for partners not yet fully onboarded

**Executive Samples Workflow**
- Specialized custom product type
- Pre-configured templates (e.g., "Executive Gift Set - 3 items")
- Quick customization options

**Variant Support**
- Custom products with multiple variants
- Share base cost, different customization
- Complexity: High

---

## Open Questions

1. **Should custom products support tiered pricing in MVP?**
   - **Recommendation:** No, flat-rate only (simpler)
   - **Reasoning:** Tiered pricing is complex, most custom products are one-off

2. **Should custom products be searchable in catalog filter?**
   - **Recommendation:** No, separate library for custom products
   - **Reasoning:** Keeps catalog clean, prevents confusion

3. **Should custom products have partner POC auto-population?**
   - **Recommendation:** Yes, if partner is selected (not "Custom/Other")
   - **Reasoning:** Consistent behavior with catalog products

4. **Should we allow editing custom products after adding?**
   - **Recommendation:** Yes, same inline editing as catalog products
   - **Reasoning:** User may need to adjust quantity, markup, customization

5. **Should library products be editable?**
   - **Recommendation:** Phase 2 feature, not MVP
   - **Reasoning:** Adds complexity, can add new product instead of editing

6. **Should custom products support $0.50 rounding?**
   - **Recommendation:** Yes, same as catalog products
   - **Reasoning:** No reason to exclude, uses existing logic

7. **Should custom products calculate MOQ?**
   - **Recommendation:** No, flat-rate pricing doesn't need MOQ
   - **Reasoning:** MOQ is for tiered pricing optimization

8. **Should we limit number of custom products per order?**
   - **Recommendation:** No limit
   - **Reasoning:** No technical constraint, user knows their needs

---

## Conclusion

**Summary:** Custom products feature adds significant value for edge cases (one-off items, pending catalog additions, executive samples) while integrating seamlessly with existing pricing engine and order management systems.

**Recommendation:** Implement Phase 1 (MVP) first, gather user feedback, then proceed to Phase 2 (library) and Phase 3 (Tab 1 integration) based on usage patterns.

**Key Benefit:** Full product structure ensures custom products work identically to catalog products across all tabs and exports, minimizing code complexity and maintenance burden.

**Next Steps:**
1. Review plan with stakeholders
2. Clarify open questions
3. Implement Phase 1 (MVP)
4. Test thoroughly (14 test scenarios)
5. Deploy and monitor usage
6. Iterate based on feedback

---

**End of Plan**
