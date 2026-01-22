# Phase 5: Testing & Validation

**Status:** 🟡 Not Started
**Estimated Time:** 4-6 hours
**Complexity:** HIGH
**Dependencies:** Phase 1, 2, 3, & 4 must be complete

---

## Overview

Comprehensive testing of the new pricing system across all tabs:
1. Test all 3 pricing methods thoroughly
2. Validate calculated vs spreadsheet prices
3. Test empty field handling and defaults
4. Verify description fallback logic
5. Test full workflow (Tab 1 → Tab 4)
6. Edge case testing
7. Cross-browser compatibility (if applicable)

**Goal:** Ensure the new pricing system is production-ready with no regressions.

**Files to Create/Modify:**
- `scripts/features/test_new_pricing_system.py` (new test script)
- `scripts/features/test_description_fallbacks.py` (new test script)
- Bug fixes in `src/` and `app.py` as issues are discovered

---

## Pre-Testing Checklist

Before starting Phase 5, verify:
- [ ] Phase 1, 2, 3, & 4 are complete
- [ ] All implementation guides marked complete
- [ ] App runs without errors
- [ ] Read all phase guides to understand what was implemented
- [ ] Have access to both demo and real datasets

---

## Testing Strategy

### 1. Unit Testing (Pricing Functions)
Test core pricing functions in isolation

### 2. Integration Testing (Full Workflows)
Test complete user workflows across multiple tabs

### 3. Edge Case Testing
Test unusual scenarios and boundary conditions

### 4. Regression Testing
Ensure existing features still work correctly

---

## Test Suite 1: Core Pricing Functions

### Test Script: `scripts/features/test_new_pricing_system.py`

Create comprehensive test script for pricing calculations:

```python
#!/usr/bin/env python3
"""
Test script for new pricing system (Schema Update Jan 2026)

Tests all 3 pricing methods:
1. MSRP + % of cost
2. MSRP capped – ship absorbed
3. Standard markup

Run: streamlit run scripts/features/test_new_pricing_system.py
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_data_cached
from src.pricing_engine import calculate_pbp_msrp
from src.helpers import get_column_value

st.title("🧪 New Pricing System Test Suite")

# Load data
with st.spinner("Loading pricing data..."):
    all_data = load_data_cached()

df_template = all_data['data']
partners = df_template['Partner'].unique()

st.write(f"**Total Products:** {len(df_template)}")
st.write(f"**Partners:** {', '.join(partners)}")

st.markdown("---")

# Test 1: Method Classification
st.header("Test 1: Pricing Method Classification")

method_counts = {
    "MSRP + % of cost": 0,
    "MSRP capped – ship absorbed": 0,
    "Standard markup": 0,
    "Unknown/Error": 0
}

for idx, product in df_template.iterrows():
    pricing_logic = get_column_value(product, 'pricing_logic', None)

    if pricing_logic in ["MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"]:
        method_counts[pricing_logic] += 1
    elif pricing_logic is None or pricing_logic == '':
        method_counts["Standard markup"] += 1  # Default
    else:
        method_counts["Unknown/Error"] += 1
        st.error(f"Unknown pricing logic for {product.get('Product/Service', 'Unknown')}: {pricing_logic}")

st.write("**Pricing Method Distribution:**")
for method, count in method_counts.items():
    st.write(f"- {method}: {count} products")

if method_counts["Unknown/Error"] > 0:
    st.error(f"⚠️ {method_counts['Unknown/Error']} products have unknown pricing logic!")
else:
    st.success("✓ All products have valid pricing methods")

st.markdown("---")

# Test 2: Calculate Prices for All Products
st.header("Test 2: Price Calculation Validation")

test_quantity = st.number_input("Test Quantity", min_value=1, value=100, step=1)

results = []
errors = []

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', f"Product {idx}")

    try:
        pricing_result = calculate_pbp_msrp(product, test_quantity)

        # Extract key info
        results.append({
            'Product': product_name,
            'Method': pricing_result['method_used'],
            'PBP MSRP': pricing_result['pbp_msrp'],
            'Spreadsheet MSRP': pricing_result.get('spreadsheet_msrp', None),
            'Validation': pricing_result.get('validation_status', 'N/A'),
            'Has Warning': bool(pricing_result.get('validation_warning'))
        })

    except Exception as e:
        errors.append({
            'Product': product_name,
            'Error': str(e)
        })

if errors:
    st.error(f"⚠️ {len(errors)} products failed to calculate")
    with st.expander("View Errors"):
        for err in errors:
            st.write(f"**{err['Product']}:** {err['Error']}")
else:
    st.success(f"✓ All {len(results)} products calculated successfully")

# Show validation summary
validation_counts = {
    'MATCH': 0,
    'MISMATCH': 0,
    'NO_SPREADSHEET_VALUE': 0,
    'MANUAL_OVERRIDE': 0
}

for result in results:
    status = result['Validation']
    if status in validation_counts:
        validation_counts[status] += 1
    else:
        validation_counts['NO_SPREADSHEET_VALUE'] += 1

st.write("**Validation Status Distribution:**")
for status, count in validation_counts.items():
    st.write(f"- {status}: {count} products")

# Show products with warnings
products_with_warnings = [r for r in results if r['Has Warning']]
if products_with_warnings:
    st.warning(f"⚠️ {len(products_with_warnings)} products have validation warnings")

    with st.expander("View Products with Warnings"):
        for result in products_with_warnings:
            st.write(f"**{result['Product']}** ({result['Method']})")
            st.write(f"- Calculated: ${result['PBP MSRP']:.2f}")
            st.write(f"- Spreadsheet: ${result['Spreadsheet MSRP']:.2f}")
            st.write("")

st.markdown("---")

# Test 3: Cost Basis Normalization
st.header("Test 3: Cost Basis Normalization")

products_with_packages = []

for idx, product in df_template.iterrows():
    cost_basis = get_column_value(product, 'cost_basis', 'Per Item')
    units_per_package = get_column_value(product, 'units_per_package', 1)

    if cost_basis == "Per Package" or units_per_package > 1:
        products_with_packages.append({
            'Product': get_column_value(product, 'product_service_name', f"Product {idx}"),
            'Cost Basis': cost_basis,
            'Units per Package': units_per_package
        })

if products_with_packages:
    st.write(f"**Products with Package Pricing:** {len(products_with_packages)}")
    with st.expander("View Details"):
        for p in products_with_packages:
            st.write(f"**{p['Product']}** - {p['Cost Basis']}, {p['Units per Package']} units/package")
else:
    st.info("No products with package pricing found")

st.markdown("---")

# Test 4: Empty Field Handling
st.header("Test 4: Empty Field Handling")

empty_field_counts = {
    'pricing_logic': 0,
    'vendor_published_msrp': 0,
    'pbp_standard_markup': 0,
    'shipping_add_on_pct': 0
}

for idx, product in df_template.iterrows():
    for field in empty_field_counts.keys():
        value = get_column_value(product, field, None)
        if value is None or value == '' or (isinstance(value, float) and value == 0):
            empty_field_counts[field] += 1

st.write("**Empty Field Counts:**")
for field, count in empty_field_counts.items():
    st.write(f"- {field}: {count} products")

st.success("✓ Empty field handling test complete")

st.markdown("---")

st.success("🎉 All tests complete!")
```

**Test Execution:**

Run the test script:
```bash
streamlit run scripts/features/test_new_pricing_system.py
```

**Expected Results:**
- [ ] All products classified into one of 3 pricing methods
- [ ] All products calculate prices without errors
- [ ] Validation warnings only appear for genuine mismatches
- [ ] Package pricing normalization works correctly
- [ ] Empty fields handled with appropriate defaults

---

## Test Suite 2: Description Fallback Logic

### Test Script: `scripts/features/test_description_fallbacks.py`

```python
#!/usr/bin/env python3
"""
Test description fallback logic for invoices and POs

Run: streamlit run scripts/features/test_description_fallbacks.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_data_cached
from src.helpers import get_column_value

st.title("🧪 Description Fallback Test")

# Load data
all_data = load_data_cached()
df_template = all_data['data']

st.write(f"**Total Products:** {len(df_template)}")

st.markdown("---")

# Test description fallback logic
st.header("Invoice Description Fallback Test")

invoice_fallback_stats = {
    'Used Billing Description': 0,
    'Used Purchase Description': 0,
    'Used Product Name': 0
}

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    billing_desc = get_column_value(product, 'billing_description', None)
    purchase_desc = get_column_value(product, 'purchase_description', None)

    # Invoice hierarchy: Billing → Purchase → Name
    if billing_desc and billing_desc.strip():
        invoice_fallback_stats['Used Billing Description'] += 1
    elif purchase_desc and purchase_desc.strip():
        invoice_fallback_stats['Used Purchase Description'] += 1
    else:
        invoice_fallback_stats['Used Product Name'] += 1

st.write("**Invoice Description Sources:**")
for source, count in invoice_fallback_stats.items():
    st.write(f"- {source}: {count} products")

st.markdown("---")

st.header("PO Description Fallback Test")

po_fallback_stats = {
    'Used Purchase Description': 0,
    'Used Billing Description': 0,
    'Used Product Name': 0
}

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    billing_desc = get_column_value(product, 'billing_description', None)
    purchase_desc = get_column_value(product, 'purchase_description', None)

    # PO hierarchy: Purchase → Billing → Name
    if purchase_desc and purchase_desc.strip():
        po_fallback_stats['Used Purchase Description'] += 1
    elif billing_desc and billing_desc.strip():
        po_fallback_stats['Used Billing Description'] += 1
    else:
        po_fallback_stats['Used Product Name'] += 1

st.write("**PO Description Sources:**")
for source, count in po_fallback_stats.items():
    st.write(f"- {source}: {count} products")

st.markdown("---")

# Show products with missing descriptions
st.header("Products with Missing Descriptions")

missing_both = []

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    billing_desc = get_column_value(product, 'billing_description', None)
    purchase_desc = get_column_value(product, 'purchase_description', None)

    if not (billing_desc and billing_desc.strip()) and not (purchase_desc and purchase_desc.strip()):
        missing_both.append(product_name)

if missing_both:
    st.warning(f"⚠️ {len(missing_both)} products missing both descriptions (will use product name)")
    with st.expander("View Products"):
        for name in missing_both:
            st.write(f"- {name}")
else:
    st.success("✓ All products have at least one description field")

st.success("🎉 Description fallback test complete!")
```

**Test Execution:**

Run the test script:
```bash
streamlit run scripts/features/test_description_fallbacks.py
```

**Expected Results:**
- [ ] Invoice descriptions follow correct hierarchy
- [ ] PO descriptions follow correct hierarchy
- [ ] Products without descriptions fall back to product name
- [ ] No errors or empty descriptions in output

---

## Test Suite 3: Full Workflow Testing

### Manual Test Procedure

**Test 3.1: MSRP + % of cost Method**

1. **Tab 1 - Proposal:**
   - [ ] Find product with "MSRP + % of cost" method
   - [ ] Add to proposal with "Use MSRP pricing" checked
   - [ ] Verify markup calculated correctly
   - [ ] Check pricing notes show method and shipping add-on
   - [ ] Generate proposal table, verify prices

2. **Tab 3 - Order:**
   - [ ] Import product from proposal (Option C)
   - [ ] Verify pricing method preserved
   - [ ] Verify markup matches Tab 1
   - [ ] Edit quantity, verify price recalculates correctly
   - [ ] Check order summary matches

3. **Tab 4 - Invoice/PO:**
   - [ ] Generate invoice and PO
   - [ ] Verify descriptions are appropriate
   - [ ] Verify prices match Tab 3 exactly
   - [ ] Download CSV, verify data
   - [ ] Download HTML, verify format

**Expected Result:** Prices consistent across all 3 tabs, appropriate descriptions used.

---

**Test 3.2: MSRP capped – ship absorbed Method**

1. **Tab 1 - Proposal:**
   - [ ] Find product with "MSRP capped – ship absorbed" method
   - [ ] Add to proposal
   - [ ] Verify markup calculated to match MSRP exactly
   - [ ] Check pricing notes mention ship absorbed
   - [ ] Generate proposal table

2. **Tab 3 - Order:**
   - [ ] Import from proposal
   - [ ] Verify pricing method preserved
   - [ ] Edit markup manually, check override checkbox
   - [ ] Verify pricing note disappears when override checked

3. **Tab 4 - Invoice/PO:**
   - [ ] Generate documents
   - [ ] Verify prices match Tab 3
   - [ ] Verify no pricing notes in final documents

**Expected Result:** MSRP matched exactly, manual override works.

---

**Test 3.3: Standard markup Method**

1. **Tab 1 - Proposal:**
   - [ ] Find product with "Standard markup" or no pricing logic
   - [ ] Add to proposal
   - [ ] Verify uses diagnostic markup from spreadsheet (or 100% default)
   - [ ] Check pricing notes explain standard markup used

2. **Tab 3 - Order:**
   - [ ] Import from proposal
   - [ ] Verify markup preserved
   - [ ] Edit markup, verify calculations update correctly

3. **Tab 4 - Invoice/PO:**
   - [ ] Generate documents
   - [ ] Verify pricing correct

**Expected Result:** Standard markup applied correctly, flexible editing works.

---

## Test Suite 4: Edge Case Testing

### Edge Case 1: Empty Pricing Logic Field
**Scenario:** Product has no pricing logic specified

**Test:**
1. Find or create product with empty/null pricing_logic
2. Add to proposal
3. Verify defaults to "Standard markup" with 100% markup
4. Verify no errors occur

**Expected:** Graceful handling, 100% default markup applied

---

### Edge Case 2: MSRP Below Cost
**Scenario:** Vendor MSRP is lower than PBP cost

**Test:**
1. Find or create product where MSRP < cost
2. Add to proposal with "MSRP + % of cost" method
3. Verify markup set to 0% (break-even)
4. Verify validation warning appears

**Expected:** 0% markup, validation warning shows discrepancy

---

### Edge Case 3: Missing Shipping Add-On %
**Scenario:** "MSRP + % of cost" method but no shipping add-on value

**Test:**
1. Product with "MSRP + % of cost" but empty shipping_add_on_pct
2. Add to proposal
3. Verify defaults to 0% (no shipping recovery)
4. Verify pricing notes mention 0% shipping

**Expected:** Defaults to 0%, calculation completes successfully

---

### Edge Case 4: Package Pricing with 0 Units
**Scenario:** Cost basis "Per Package" but units_per_package = 0

**Test:**
1. Create test product with invalid package data
2. Attempt pricing calculation
3. Verify defaults to 1 unit (prevents division by zero)

**Expected:** Graceful handling, default to 1 unit

---

### Edge Case 5: Manual Override Persistence
**Scenario:** Ensure manual override survives workflow

**Test:**
1. Add product to proposal
2. Check manual override box
3. Edit markup to custom value
4. Import to Tab 3
5. Verify override checkbox still checked
6. Verify pricing notes hidden
7. Generate invoice in Tab 4
8. Verify custom pricing preserved

**Expected:** Override persists across tabs, pricing notes hidden

---

## Test Suite 5: Regression Testing

Ensure existing features still work:

### Regression Test 1: Saved Proposals
- [ ] Save proposal with new pricing
- [ ] Load proposal in new session
- [ ] Verify all pricing fields preserved (method, notes, override)

### Regression Test 2: Saved Orders
- [ ] Save order with new pricing
- [ ] Load order in new session
- [ ] Verify all fields preserved

### Regression Test 3: Google Form Import
- [ ] Import form response
- [ ] Verify products added with correct pricing method
- [ ] Verify no errors

### Regression Test 4: HTML Form Import
- [ ] Import HTML form
- [ ] Verify products added with correct pricing
- [ ] Verify all 11 client info fields extracted

### Regression Test 5: Customization and Tariffs
- [ ] Add product with customization
- [ ] Verify customization costs separate from base price
- [ ] Verify markup applies to product only (not customization)
- [ ] Add tariff
- [ ] Verify tariff calculated correctly

### Regression Test 6: Discounts and Marketing Rounding
- [ ] Apply non-profit discount (5%)
- [ ] Verify discount applies to all products
- [ ] Enable marketing rounding
- [ ] Verify charm pricing (e.g., $60 → $59)

---

## Bug Tracking Template

**Use this template to document any bugs found:**

```markdown
### Bug #X: [Short Description]

**Severity:** [Critical / High / Medium / Low]

**Location:** [Tab X, Section Y]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Error Messages:**
[Any console errors or warnings]

**Fix Required:**
[Brief description of fix needed]

**Status:** [Open / In Progress / Fixed / Verified]
```

---

## Phase 5 Completion Checklist

Before proceeding to Phase 6, verify:

**Core Functionality:**
- [ ] All 3 pricing methods calculate correctly
- [ ] Validation logic works (calculated vs spreadsheet)
- [ ] Empty field handling works with correct defaults
- [ ] Description fallbacks work for invoices and POs
- [ ] Manual override checkbox functional across all tabs

**Workflow Testing:**
- [ ] Tab 1 → Tab 3 → Tab 4 workflow works
- [ ] All 4 Tab 3 entry pathways work correctly
- [ ] Saved proposals/orders load with new fields
- [ ] Google Form and HTML imports work

**Edge Cases:**
- [ ] All edge cases handled gracefully
- [ ] No errors or crashes
- [ ] Validation warnings appropriate

**Regression Testing:**
- [ ] All existing features still work
- [ ] No unintended side effects
- [ ] Performance acceptable

**Documentation:**
- [ ] All bugs documented and fixed
- [ ] Test results recorded
- [ ] Any workarounds documented

---

## Next Phase

Once Phase 5 is complete and all tests pass, proceed to:
**Phase 6: Documentation & Deployment**

Use the resume prompt from RESUME_PROMPTS.md to start Phase 6 with full context.

---

**Phase 5 Complete:** ✅ [Date completed]
**Tested By:** [Your name]
**Bugs Found:** [Number]
**Bugs Fixed:** [Number]
**Notes:** [Any important observations or outstanding issues]
