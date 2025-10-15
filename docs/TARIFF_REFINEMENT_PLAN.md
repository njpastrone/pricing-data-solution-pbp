# Tariff Refinement Implementation Plan

**Created:** 2025-10-15
**Status:** Planning
**Priority:** High - Response to recent tariff policy changes

---

## Overview

Refactor tariff implementation from order-level flat fee to product-specific calculations based on Country of Origin and tariff rates. This mirrors the customization implementation pattern completed earlier.

---

## Current State Analysis

**Current Implementation:**
- Tariffs are a single order-level dollar amount in Section 6 "Order Settings"
- User manually enters total tariff cost for entire order
- No connection to product data or country of origin

**Issues:**
- Tariffs vary by product based on Country of Origin
- Tariff rates change frequently (recent policy changes)
- Should be calculated as percentages of product cost, not flat fees
- Need flexibility to override default rates per product

**Data Available in Spreadsheet:**
- `Country of Origin` - Manufacturing country for each product
- `Tariff Estimate (if available)` - Default tariff rate as percentage (e.g., "50.00%")
- `Tariff Info` - Notes/reference codes (HS Code, duty terms, exceptions)

---

## Proposed Solution

### Architecture Changes

**Tariff Calculation Model:**
```
Tariff applies to: (Base Product Cost + Markup)
Tariff does NOT apply to: Customization, Shipping, Other Tariffs

Formula:
Tariff Base = (Base Price × Quantity) + Markup Amount
Tariff Amount = Tariff Base × (Tariff Rate % / 100)
```

**Per-Product Tariff Tracking:**
- Each product stores its own tariff rate and amount
- Default tariff rate pulled from spreadsheet data
- User can override tariff rate per product
- Tariff appears as separate line item in all deliverables

---

## Implementation Phases

### **Phase 1: Update Session State & Data Structure**

**Add to order_item dictionary:**
```python
order_item = {
    ...existing fields...
    'country_of_origin': product_data.get("Country of Origin", ""),
    'tariff_rate_percent': default_tariff_percent,  # From "Tariff Estimate" column
    'tariff_info': product_data.get("Tariff Info", ""),
    'tariff_amount': calculated_tariff_dollar_amount
}
```

**Initialize session state for tariff overrides:**
```python
# Initialize per-product tariff overrides
if 'product_tariff_overrides' not in st.session_state:
    st.session_state.product_tariff_overrides = {}
    # Format: {product_index: tariff_percent}
```

**Remove old session state:**
```python
# REMOVE: st.session_state.order_tariff
```

---

### **Phase 2: Add Helper Functions**

**File:** `app.py` (add near other helper functions at top)

```python
def parse_tariff_rate(tariff_string):
    """
    Parse tariff percentage from spreadsheet strings.

    Examples:
        "50.00%" -> 50.0
        "50%" -> 50.0
        "25.5%" -> 25.5
        "" -> 0.0
        "NA" -> 0.0

    Returns:
        float: Tariff rate as decimal percentage (0.0 if invalid)
    """
    if not tariff_string or tariff_string == '' or tariff_string == 'NA':
        return 0.0
    try:
        cleaned = str(tariff_string).replace('%', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0

def calculate_product_tariff(product_cost_with_markup, tariff_rate_percent):
    """
    Calculate tariff on product cost.

    Args:
        product_cost_with_markup: Base product cost (price + markup, excluding customization)
        tariff_rate_percent: Tariff rate as percentage (e.g., 50.0 for 50%)

    Returns:
        float: Tariff dollar amount

    Example:
        product_cost = $4,000 (base $2,000 + markup $2,000)
        tariff_rate = 50.0%
        tariff_amount = $2,000
    """
    if tariff_rate_percent <= 0:
        return 0.0
    return product_cost_with_markup * (tariff_rate_percent / 100)
```

---

### **Phase 3: Update Section 3 (Customize Product)**

**When adding a product to order:**

1. Parse default tariff rate from product data
2. Calculate tariff on product cost (base + markup, no customization)
3. Store tariff fields in order_item

**Code location:** Section 4 "Product Preview" - in the "Add to Order" button logic

```python
# After calculating product_total, add tariff calculation
tariff_estimate_raw = product_data.get('Tariff Estimate (if available)', '')
default_tariff_rate = parse_tariff_rate(tariff_estimate_raw)

# Calculate tariff base (product + markup, no customization)
tariff_base = product_subtotal + markup_amount
tariff_amount = calculate_product_tariff(tariff_base, default_tariff_rate)

# Add to order_item dict
order_item = {
    ...existing fields...
    'country_of_origin': product_data.get("Country of Origin", ""),
    'tariff_rate_percent': default_tariff_rate,
    'tariff_info': product_data.get("Tariff Info", ""),
    'tariff_base': tariff_base,  # Cost that tariff applies to
    'tariff_amount': tariff_amount
}
```

---

### **Phase 4: Create New Section 6.5 "Tariff Configuration"**

**Location:** After Section 6 "Shipping" subsection, before "Discount Options"

**UI Layout:**

```
═══════════════════════════════════════════════════════════
Section 6.5: Tariff Configuration

Tariffs are import duties based on product country of origin.
Rates default to current estimates but can be adjusted as needed.

┌─────────────────────────────────────────────────────────────────┐
│ Product          │ Country  │ Tariff Rate (%) │ Tariff Amount  │
├─────────────────────────────────────────────────────────────────┤
│ Product Y        │ India    │ [50.0]          │ $500.00        │
│ Product Z        │ Vietnam  │ [25.0]          │ $150.00        │
│ Custom Item      │ N/A      │ [0.0]           │ $0.00          │
└─────────────────────────────────────────────────────────────────┘

Total Tariff for Order: $650.00

ℹ️ Tariff is calculated on product cost + markup (excludes customization fees)
═══════════════════════════════════════════════════════════
```

**Implementation:**

```python
st.divider()
st.subheader("Tariff Configuration")

st.markdown("""
Tariffs are import duties based on product country of origin.
Rates default to current estimates but can be adjusted as needed.
""")

# Build editable tariff table
for idx, item in enumerate(st.session_state.order_items):
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        st.write(item['product_name'])

    with col2:
        country = item.get('country_of_origin', 'N/A')
        st.write(country if country else 'N/A')

    with col3:
        # Editable tariff rate
        current_rate = item.get('tariff_rate_percent', 0.0)
        new_rate = st.number_input(
            f"Rate {idx}",
            min_value=0.0,
            max_value=100.0,
            value=current_rate,
            step=0.5,
            key=f"tariff_rate_{idx}",
            label_visibility="collapsed"
        )

        # Update if changed
        if new_rate != current_rate:
            item['tariff_rate_percent'] = new_rate
            tariff_base = item.get('tariff_base', 0.0)
            item['tariff_amount'] = calculate_product_tariff(tariff_base, new_rate)

    with col4:
        tariff_amount = item.get('tariff_amount', 0.0)
        st.write(f"${tariff_amount:.2f}")

    # Show tariff info if available
    tariff_info = item.get('tariff_info', '')
    if tariff_info and tariff_info.strip():
        st.caption(f"ℹ️ {tariff_info}")

# Show total tariff
total_tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)
st.markdown(f"**Total Tariff for Order:** ${total_tariff:.2f}")

st.caption("ℹ️ Tariff is calculated on product cost + markup (excludes customization fees)")
```

---

### **Phase 5: Update Section 6 "Order Settings"**

**Changes:**
1. Rename "Shipping & Tariff" subsection to just "Shipping"
2. Remove tariff number input field
3. Keep only shipping cost input

**Code changes:**
```python
# OLD:
st.subheader("Shipping & Tariff")

# NEW:
st.subheader("Shipping")

# REMOVE these lines:
with col2:
    st.session_state.order_tariff = st.number_input(
        "Tariff Cost ($)",
        ...
    )
```

---

### **Phase 6: Update Section 5 (Current Order)**

**Show tariff in line item breakdown:**

When displaying products with tariffs, add tariff to the line items display:

```python
# After customization line items, add tariff if applicable
tariff_amount = item.get('tariff_amount', 0)
if tariff_amount > 0:
    country = item.get('country_of_origin', 'Unknown')
    tariff_rate = item.get('tariff_rate_percent', 0)
    line_items_display.append([
        f"{line_num}. Tariff ({tariff_rate}% - {country})",
        1,
        f"${tariff_amount:.2f}",
        f"${tariff_amount:.2f}"
    ])
```

---

### **Phase 7: Update Section 7 (Order Summary)**

**Replace single tariff line with per-product tariff breakdown:**

```python
# OLD:
summary_items.append(["Tariff", "", "", f"${tariff:.2f}"])

# NEW: Add tariff for each product (if > 0)
for item in st.session_state.order_items:
    tariff_amount = item.get('tariff_amount', 0)
    if tariff_amount > 0:
        country = item.get('country_of_origin', 'Unknown')
        tariff_rate = item.get('tariff_rate_percent', 0)
        summary_items.append([
            f"Tariff: {item['product_name']} ({tariff_rate}% - {country})",
            "",
            "",
            f"${tariff_amount:.2f}"
        ])
```

---

### **Phase 8: Update Section 8 (Proposal)**

**Include tariff information in proposal notes:**

```python
# After customization fees, add tariff information
if item.get('tariff_amount', 0) > 0:
    tariff_rate = item.get('tariff_rate_percent', 0)
    country = item.get('country_of_origin', 'Unknown')
    tariff_amount = item.get('tariff_amount', 0)

    st.markdown("**Tariff Information:**")
    st.caption(f"Import duty: {tariff_rate}% (from {country}) = ${tariff_amount:.2f}")

    tariff_info = item.get('tariff_info', '')
    if tariff_info:
        st.caption(f"Note: {tariff_info}")
```

---

### **Phase 9: Update Section 9 (Invoice)**

**Add tariff as separate line items (like customization):**

```python
# After customization line items, add tariff line item
if item.get('tariff_amount', 0) > 0:
    tariff_amount = item.get('tariff_amount', 0)
    country = item.get('country_of_origin', 'Unknown')
    tariff_rate = item.get('tariff_rate_percent', 0)

    invoice_line_items.append({
        'Product/Service Name': f"Tariff: {item['product_name']}",
        'Description': f"Import duty ({tariff_rate}% from {country})",
        'Quantity': 1,
        'Pricing Tier': "N/A",
        'Price (Per-Unit)': f"${tariff_amount:.2f}",
        'Total (Per-Item)': f"${tariff_amount:.2f}"
    })
```

---

### **Phase 10: Update Section 10 (Purchase Order)**

**Add tariff line items (same as invoice):**

```python
# After customization line items, add tariff line item
if item.get('tariff_amount', 0) > 0:
    tariff_amount = item.get('tariff_amount', 0)
    country = item.get('country_of_origin', 'Unknown')
    tariff_rate = item.get('tariff_rate_percent', 0)

    po_line_items.append({
        'Partner': partner,
        'Product/Service': f"Tariff: {item['product_name']}",
        'Product Ref': product_ref,
        'Quantity': 1,
        'Unit Cost': f"${tariff_amount:.2f}",
        'Total': f"${tariff_amount:.2f}",
        'Notes': f"Import duty ({tariff_rate}% from {country})"
    })
```

---

### **Phase 11: Update Total Calculations**

**Replace `order_tariff` with calculated tariff sum:**

```python
# OLD:
tariff = st.session_state.order_tariff

# NEW:
tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)
```

**Update all locations:**
- Section 7: Order Summary
- Section 8: Proposal
- Section 9: Invoice
- Section 10: Purchase Order
- Sidebar: Download Order CSV

---

## Example Scenario

### Order with 2 Products

**Product 1: Product Y from India**
- Base cost: $2,000 (100 units @ $20 each)
- Markup: $2,000 (100%)
- Customization: $300
- **Tariff base:** $4,000 (base + markup only)
- **Tariff rate:** 50% (from spreadsheet)
- **Tariff amount:** $2,000

**Product 2: Product Z from Vietnam**
- Base cost: $600 (50 units @ $12 each)
- Markup: $600 (100%)
- Customization: $100
- **Tariff base:** $1,200 (base + markup only)
- **Tariff rate:** 25% (default), **user changes to 20%**
- **Tariff amount:** $240

**Order Total Calculation:**
```
Product 1:                 $4,300
  - Base + Markup:         $4,000
  - Customization:         $300

Product 2:                 $1,300
  - Base + Markup:         $1,200
  - Customization:         $100

Products Subtotal:         $5,600

Tariff (Product Y - India):  $2,000
Tariff (Product Z - Vietnam): $240
Shipping:                    $300

TOTAL ORDER:               $8,140
```

---

## Key Business Rules

1. **Tariff Base:** Tariff applies to (Base Product Cost + Markup) ONLY
2. **Tariff Exclusions:** Does NOT apply to customization fees, shipping, or other tariffs
3. **Per-Product Rates:** Each product has its own tariff rate based on country of origin
4. **Editable Rates:** Defaults to spreadsheet data but user can override per product
5. **Separate Line Items:** Tariffs show as separate line items in all deliverables
6. **Custom Items:** Can have tariffs with user-specified rate (no country default)
7. **Zero Tariffs:** Products with 0% tariff rate or no country data show $0.00 tariff

---

## Testing Checklist

- [ ] Parse tariff rates from spreadsheet correctly (50.00%, 50%, 25.5%)
- [ ] Calculate tariff on correct base (product + markup, no customization)
- [ ] Default tariff rates populate when adding products
- [ ] Tariff rate changes update tariff amount in real-time
- [ ] Tariff appears correctly in Section 5 (Current Order)
- [ ] Tariff sums correctly in Section 7 (Order Summary)
- [ ] Tariff shows in Section 8 (Proposal) with country info
- [ ] Tariff appears as line items in Section 9 (Invoice)
- [ ] Tariff appears as line items in Section 10 (Purchase Order)
- [ ] Multiple products with different tariff rates calculate correctly
- [ ] Products with no tariff data show 0% / $0.00
- [ ] Custom line items allow tariff rate input
- [ ] Download CSV files include tariff line items
- [ ] Order history preserves tariff information

---

## Migration Notes

**Breaking Changes:**
- `st.session_state.order_tariff` removed (was order-level flat fee)
- Tariff now calculated per-product and stored in order_item
- Section 6 "Order Settings" no longer has tariff input

**Backward Compatibility:**
- Existing orders in session history may have old tariff structure
- Consider adding migration logic or clearing order history on first load with new version

---

## References

- [RESTRUCTURE_CONTEXT.md](RESTRUCTURE_CONTEXT.md) - Data structure with tariff fields
- [METHODOLOGY_LOGIC.md](METHODOLOGY_LOGIC.md) - Calculation formulas
- Implementation mirrors [Customization refinement](../CLAUDE.md#recent-changes) completed 2025-10-15

---

**Status:** Ready for implementation
**Estimated Effort:** 3-4 hours
**Priority:** High - Business critical due to tariff policy changes
