# Phase 4: UI Updates (Tab 4 - Execution & Accounting)

**Status:** 🟡 Not Started
**Estimated Time:** 2-3 hours
**Complexity:** LOW-MEDIUM
**Dependencies:** Phase 1, 2, & 3 must be complete

---

## Overview

Update Tab 4 (Execution & Accounting) to:
1. Use correct description fields per use case (invoices vs POs)
2. Verify pricing matches Tab 3 calculations
3. Clean display (no pricing notes in final documents)
4. Use new pricing functions for consistency

**Key Principle:** Tab 4 is a **read-only execution** tab. All pricing logic should already be complete from Tab 3. Tab 4 just generates final documents with correct formatting and descriptions.

**Files to Modify:**
- `app.py` (Tab 4 sections only)

---

## Pre-Implementation Checklist

Before starting Phase 4, verify:
- [ ] Phase 1, 2, & 3 are complete and tested
- [ ] Tab 3 pricing works correctly with all methods
- [ ] Order summary calculations are accurate
- [ ] Read current Tab 4 code in app.py (search for "Tab 4" or "Execution & Accounting")
- [ ] Understand 4-table invoice/PO format

---

## Step-by-Step Implementation

### Step 1: Update Description Field Logic

**Location:** Throughout Tab 4 (invoice/PO generation)

**Decision Reference:** Discussion 7 - Description fallback hierarchy

**Current behavior:** Uses various description fields inconsistently

**New behavior:** Use correct description based on use case

**Code changes:**

```python
# Add helper function at top of Tab 4 section:

def get_description_for_invoice(product_data):
    """
    Get product description for client-facing invoices/proposals.

    Hierarchy:
    1. Billing Description
    2. Purchase Description
    3. Product/Service Name
    """
    billing_desc = get_column_value(product_data, 'billing_description', None)
    if billing_desc and billing_desc.strip():
        return billing_desc

    purchase_desc = get_column_value(product_data, 'purchase_description', None)
    if purchase_desc and purchase_desc.strip():
        return purchase_desc

    product_name = get_column_value(product_data, 'product_service_name', 'Unknown Product')
    return product_name


def get_description_for_po(product_data):
    """
    Get product description for partner purchase orders.

    Hierarchy:
    1. Purchase Description
    2. Billing Description
    3. Product/Service Name
    """
    purchase_desc = get_column_value(product_data, 'purchase_description', None)
    if purchase_desc and purchase_desc.strip():
        return purchase_desc

    billing_desc = get_column_value(product_data, 'billing_description', None)
    if billing_desc and billing_desc.strip():
        return billing_desc

    product_name = get_column_value(product_data, 'product_service_name', 'Unknown Product')
    return product_name
```

---

### Step 2: Update Table 4 (Invoice and PO Item Details)

**Location:** Table 4 generation in Tab 4

**Current behavior:** Uses product name directly

**New behavior:** Use appropriate description based on row type

**Code changes:**

```python
# In Table 4 generation loop:

for item in st.session_state.order_items:
    product_data = # ... get from catalog

    # Get base product pricing (using new system)
    pricing_result = calculate_pbp_msrp(
        product_data,
        quantity=item['quantity'],
        user_markup_override=item['markup'] if item.get('manual_override') else None
    )

    base_cost = pricing_result['calculation_details']['base_cost']
    pbp_msrp = pricing_result['pbp_msrp']

    # === BASE PRODUCT ROW ===
    # For invoice: use get_description_for_invoice()
    # For PO: use get_description_for_po()

    invoice_description = get_description_for_invoice(product_data)
    po_description = get_description_for_po(product_data)

    table_rows.append({
        'Partner': item['partner'],
        'Specs/Description (Invoice)': invoice_description,  # Client-facing
        'Specs/Description (PO)': po_description,  # Partner-facing
        'Quantity': item['quantity'],
        'In-Hands Date': item.get('in_hands_date', ''),
        'Cost/Unit': f"${base_cost:.2f}",
        'Total Cost': f"${base_cost * item['quantity']:.2f}",
        'Sell Price/Unit': f"${pbp_msrp:.2f}",
        'Total Sell Price': f"${pbp_msrp * item['quantity']:.2f}",
    })

    # === CUSTOMIZATION SETUP FEE ROW (if applicable) ===
    if item.get('add_customization') and item.get('customization_setup_fee', 0) > 0:
        setup_fee = item['customization_setup_fee']

        # Invoice description: clear client-facing description
        invoice_customization_desc = f"{invoice_description} - Customization Setup Fee"
        # PO description: clear partner communication
        po_customization_desc = f"{po_description} - Setup"

        table_rows.append({
            'Partner': item['partner'],
            'Specs/Description (Invoice)': invoice_customization_desc,
            'Specs/Description (PO)': po_customization_desc,
            'Quantity': 1,
            'In-Hands Date': item.get('in_hands_date', ''),
            'Cost/Unit': f"${setup_fee:.2f}",
            'Total Cost': f"${setup_fee:.2f}",
            'Sell Price/Unit': f"${setup_fee:.2f}",  # Pass-through
            'Total Sell Price': f"${setup_fee:.2f}",
        })

    # === CUSTOMIZATION PER-UNIT ROW (if applicable) ===
    if item.get('add_customization') and item.get('customization_per_unit', 0) > 0:
        per_unit_cost = item['customization_per_unit']

        invoice_per_unit_desc = f"{invoice_description} - Customization (per unit)"
        po_per_unit_desc = f"{po_description} - Per Unit Customization"

        table_rows.append({
            'Partner': item['partner'],
            'Specs/Description (Invoice)': invoice_per_unit_desc,
            'Specs/Description (PO)': po_per_unit_desc,
            'Quantity': item['quantity'],
            'In-Hands Date': item.get('in_hands_date', ''),
            'Cost/Unit': f"${per_unit_cost:.2f}",
            'Total Cost': f"${per_unit_cost * item['quantity']:.2f}",
            'Sell Price/Unit': f"${per_unit_cost:.2f}",  # Pass-through
            'Total Sell Price': f"${per_unit_cost * item['quantity']:.2f}",
        })

    # === TARIFF ROW (if applicable) ===
    if item.get('apply_tariff') and item.get('tariff_amount', 0) > 0:
        tariff_total = item['tariff_amount']
        tariff_per_unit = tariff_total / item['quantity'] if item['quantity'] > 0 else 0

        country = get_column_value(product_data, 'country_of_origin', 'Unknown')
        tariff_rate = get_column_value(product_data, 'tariff_estimate_pct', 0)

        invoice_tariff_desc = f"{invoice_description} - Tariff ({country}, {tariff_rate:.1f}%)"
        po_tariff_desc = f"{po_description} - Tariff"

        table_rows.append({
            'Partner': item['partner'],
            'Specs/Description (Invoice)': invoice_tariff_desc,
            'Specs/Description (PO)': po_tariff_desc,
            'Quantity': item['quantity'],
            'In-Hands Date': item.get('in_hands_date', ''),
            'Cost/Unit': f"${tariff_per_unit:.2f}",
            'Total Cost': f"${tariff_total:.2f}",
            'Sell Price/Unit': f"${tariff_per_unit:.2f}",  # Pass-through
            'Total Sell Price': f"${tariff_total:.2f}",
        })
```

---

### Step 3: Update CSV Export

**Location:** CSV download button in Tab 4

**Current behavior:** Exports table data as-is

**New behavior:** Include both invoice and PO descriptions as separate columns

**Code changes:**

```python
# In CSV export logic:

import pandas as pd
from io import StringIO

# Create DataFrame with both description columns
df_export = pd.DataFrame(table_rows)

# Ensure column order for clarity:
column_order = [
    'Partner',
    'Specs/Description (Invoice)',  # For client-facing documents
    'Specs/Description (PO)',  # For partner-facing documents
    'Quantity',
    'In-Hands Date',
    'Cost/Unit',
    'Total Cost',
    'Sell Price/Unit',
    'Total Sell Price'
]

df_export = df_export[column_order]

# Convert to CSV
csv_buffer = StringIO()
df_export.to_csv(csv_buffer, index=False)
csv_string = csv_buffer.getvalue()

st.download_button(
    label="Download Invoice/PO as CSV",
    data=csv_string,
    file_name=f"invoice_po_{order_date}.csv",
    mime="text/csv"
)
```

---

### Step 4: Update HTML Export

**Location:** HTML download button in Tab 4

**Current behavior:** Shows single description column

**New behavior:** Use invoice descriptions for client-facing HTML, create separate PO HTML if needed

**Code changes:**

```python
# For HTML export, create TWO separate documents:

# 1. INVOICE (Client-facing) - uses "Specs/Description (Invoice)" column
invoice_html = f"""
<html>
<head>
    <style>
        /* ... existing styles ... */
    </style>
</head>
<body>
    <h2>Client Invoice</h2>
    <!-- Tables 1-3 as before -->

    <!-- Table 4: Invoice Items (CLIENT-FACING) -->
    <table>
        <thead>
            <tr>
                <th>Partner</th>
                <th>Description</th>
                <th>Quantity</th>
                <th>In-Hands Date</th>
                <th>Price/Unit</th>
                <th>Total Price</th>
            </tr>
        </thead>
        <tbody>
"""

for row in table_rows:
    invoice_html += f"""
            <tr>
                <td>{row['Partner']}</td>
                <td>{row['Specs/Description (Invoice)']}</td>
                <td>{row['Quantity']}</td>
                <td>{row['In-Hands Date']}</td>
                <td>{row['Sell Price/Unit']}</td>
                <td>{row['Total Sell Price']}</td>
            </tr>
    """

invoice_html += """
        </tbody>
    </table>
</body>
</html>
"""

# 2. PURCHASE ORDER (Partner-facing) - uses "Specs/Description (PO)" column
po_html = f"""
<html>
<head>
    <style>
        /* ... existing styles ... */
    </style>
</head>
<body>
    <h2>Purchase Order</h2>
    <!-- Tables 1-3 as before -->

    <!-- Table 4: PO Items (PARTNER-FACING) -->
    <table>
        <thead>
            <tr>
                <th>Partner</th>
                <th>Description</th>
                <th>Quantity</th>
                <th>In-Hands Date</th>
                <th>Cost/Unit</th>
                <th>Total Cost</th>
            </tr>
        </thead>
        <tbody>
"""

for row in table_rows:
    po_html += f"""
            <tr>
                <td>{row['Partner']}</td>
                <td>{row['Specs/Description (PO)']}</td>
                <td>{row['Quantity']}</td>
                <td>{row['In-Hands Date']}</td>
                <td>{row['Cost/Unit']}</td>
                <td>{row['Total Cost']}</td>
            </tr>
    """

po_html += """
        </tbody>
    </table>
</body>
</html>
"""

# Provide both downloads:
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Download Client Invoice (HTML)",
        data=invoice_html,
        file_name=f"client_invoice_{order_date}.html",
        mime="text/html"
    )

with col2:
    st.download_button(
        label="Download Purchase Order (HTML)",
        data=po_html,
        file_name=f"purchase_order_{order_date}.html",
        mime="text/html"
    )
```

---

### Step 5: Remove Pricing Notes from Tab 4

**Location:** Anywhere pricing notes might appear in Tab 4

**Rationale:** Final documents should be clean and professional, no technical pricing notes

**Code changes:**

```python
# Ensure NO pricing notes or validation warnings appear in Tab 4

# DO NOT show:
# - Pricing method indicators
# - Validation warnings
# - Pricing notes expandable sections
# - Manual override indicators

# Tab 4 should only show:
# - Final calculated prices
# - Clean product descriptions
# - Professional invoice/PO format
```

---

### Step 6: Verify Pricing Consistency

**Location:** Tab 4 price calculations

**Goal:** Ensure Tab 4 prices EXACTLY match Tab 3 prices

**Code changes:**

```python
# In Tab 4, use SAME pricing calculation as Tab 3:

def calculate_tab4_pricing(item, product_data):
    """
    Calculate pricing for Tab 4 invoice/PO.
    MUST match Tab 3 calculations exactly.
    """
    pricing_result = calculate_pbp_msrp(
        product_data,
        quantity=item['quantity'],
        user_markup_override=item['markup'] if item.get('manual_override') else None
    )

    return {
        'base_cost': pricing_result['calculation_details']['base_cost'],
        'pbp_msrp': pricing_result['pbp_msrp'],
        'method_used': pricing_result['method_used']
    }

# Use this function consistently in all Tab 4 calculations
```

---

### Step 7: Test Tab 4 Changes

**Test Checklist:**

1. **Description Fields:**
   - [ ] Invoice descriptions use correct hierarchy (Billing → Purchase → Name)
   - [ ] PO descriptions use correct hierarchy (Purchase → Billing → Name)
   - [ ] Customization rows have clear descriptions
   - [ ] Tariff rows show country and rate

2. **Pricing Accuracy:**
   - [ ] Base product prices match Tab 3 exactly
   - [ ] Customization costs match Tab 3 exactly
   - [ ] Tariff amounts match Tab 3 exactly
   - [ ] Totals match order summary in Tab 3

3. **CSV Export:**
   - [ ] Both description columns included
   - [ ] Column order logical and clear
   - [ ] All pricing data accurate
   - [ ] File downloads successfully

4. **HTML Export:**
   - [ ] Client invoice uses billing descriptions
   - [ ] Purchase order uses purchase descriptions
   - [ ] Both documents format correctly
   - [ ] Pricing matches source data
   - [ ] Professional appearance (no technical notes)

5. **Clean Display:**
   - [ ] No pricing notes visible in Tab 4
   - [ ] No validation warnings shown
   - [ ] No pricing method indicators
   - [ ] No manual override indicators
   - [ ] Professional, clean output

---

## Common Issues & Solutions

### Issue 1: Description Fields Empty
**Problem:** Some products missing billing/purchase descriptions
**Solution:** Fallback to product name works correctly with `get_column_value()`:
```python
if not billing_desc or not billing_desc.strip():
    # Fall back to next level
```

### Issue 2: Prices Don't Match Tab 3
**Problem:** Tab 4 calculations differ from Tab 3
**Solution:** Use EXACT same function calls with same parameters:
```python
# Tab 3 and Tab 4 should both call:
pricing_result = calculate_pbp_msrp(
    product_data,
    quantity=item['quantity'],
    user_markup_override=item['markup'] if item.get('manual_override') else None
)
```

### Issue 3: HTML Format Broken
**Problem:** HTML tables don't display correctly
**Solution:** Validate HTML with simple test, check table structure and CSS

---

## Validation Before Moving to Phase 5

Before proceeding to Phase 5, verify:
- [ ] Description hierarchies work correctly for invoices and POs
- [ ] Pricing matches Tab 3 exactly (no discrepancies)
- [ ] CSV export includes both description columns
- [ ] HTML exports generate successfully (invoice + PO)
- [ ] No pricing notes or technical details in final documents
- [ ] Professional appearance maintained
- [ ] No console errors or warnings
- [ ] Complete Tab 1 → Tab 3 → Tab 4 workflow works correctly

---

## Cross-Tab Validation Test

**Critical Test:** End-to-end pricing consistency

1. **Tab 1:** Add product with MSRP pricing
   - Note the pricing method and calculated markup
2. **Tab 3:** Import product from proposal (Option C)
   - Verify pricing method preserved
   - Verify markup matches Tab 1
   - Check order summary total
3. **Tab 4:** Generate invoice/PO
   - Verify prices match Tab 3 order summary
   - Verify descriptions are appropriate
   - Download CSV and verify data matches UI

**Expected Result:** All prices match exactly across all 3 tabs.

---

## Next Phase

Once Phase 4 is complete and validated, proceed to:
**Phase 5: Testing & Validation**

Use the resume prompt from RESUME_PROMPTS.md to start Phase 5 with full context.

---

**Phase 4 Complete:** ✅ [Date completed]
**Tested By:** [Your name]
**Notes:** [Any important observations or issues encountered]
