# Schema Update Testing Guide

## App Access
The app is now running at: **http://localhost:8501**

Open this URL in your browser to test the following features.

## Test Checklist

### 1. Initial Load Test ✅
- [ ] App loads without errors
- [ ] No "query_params" error message
- [ ] No pandas Series evaluation errors

### 2. Tab 1: Proposal Generator Tests

#### A. Product Catalog Display
- [ ] Products display correctly in the catalog
- [ ] No errors when scrolling through products
- [ ] MOQ values display (either from spreadsheet or calculated)
- [ ] MSRP values display if available

#### B. Filter Tests
- [ ] Client Budget filter works (filters by client price, not PBP cost)
- [ ] Partner filter works
- [ ] Country filter works

#### C. Product Addition Tests
1. **Test Default Markup:**
   - [ ] Add a product to proposal
   - [ ] Check if markup is 100% (or different if PBP Standard Markup exists in data)

2. **Test MSRP Pricing:**
   - [ ] Enable "Use MSRP pricing when available" checkbox
   - [ ] Add a product with MSRP
   - [ ] Verify markup is calculated to match MSRP

#### D. Bulk Actions
- [ ] Try "Add All Products" button
- [ ] Try bulk add from selected partners
- [ ] Verify products are added with correct markups

#### E. Proposal Tables
- [ ] Generate proposal tables
- [ ] Check MOQ calculations (spreadsheet value should take priority if available)
- [ ] Verify customization costs display correctly

### 3. Tab 2: Client Order Form Generator
- [ ] Generate an order form
- [ ] Verify all fields populate correctly
- [ ] Download HTML form

### 4. Tab 3: Order & Client Info

#### A. Manual Product Selection
- [ ] Add a product manually
- [ ] Verify default markup is applied (100% or PBP Standard Markup)
- [ ] Enable "Use MSRP pricing" and add another product
- [ ] Verify MSRP markup is calculated correctly

#### B. Customization Tests
- [ ] Expand customization for a product
- [ ] Verify setup fee and per-unit costs are displayed
- [ ] Check that values come from correct columns (Client Price: columns)

#### C. Order Summary
- [ ] Review order summary
- [ ] Check tariff calculations (should use % or $ from new columns)
- [ ] Verify shipping costs display correctly

### 5. Tab 4: Execution & Accounting
- [ ] Generate invoice/PO
- [ ] Verify all product details are correct
- [ ] Check customization line items
- [ ] Verify tariff calculations in final invoice

## Schema Compatibility Tests

### Backward Compatibility
The app should work with both old and new column names:

**Old → New Column Mappings:**
- "MSRP" → "Vendor Published MSRP" ✅
- "Customization Setup Fee" → "Client Price: Customization Setup Fee" ✅
- "Customization Cost per Unit" → "Client Price: Customization Cost per Unit" ✅
- "Shipping Cost (PBP)" → "PBP Cost: Shipping Cost per Unit" ✅
- "Shipping Price (Client)" → "Client Price: Shipping Price per Unit" ✅
- "Tariff Rate" → "Tariff Estimate (%)" or "Tariff Estimate ($)" ✅

### New Features
1. **MOQ from Spreadsheet:**
   - If "MOQ" column has a value, it should be used
   - Otherwise, calculate based on $1000 minimum

2. **PBP Standard Markup:**
   - If "PBP Standard Markup" column exists (e.g., "2.0" = 100% markup)
   - Products should use this as default instead of hardcoded 100%

3. **Tariff Flexibility:**
   - App should handle both percentage format (25%)
   - And dollar format ($50) with automatic conversion

## Expected Behavior

### Product Addition Flow
1. When adding a product without MSRP pricing enabled:
   - Check for PBP Standard Markup in data
   - If exists: use that markup (e.g., 2.0 = 100% markup)
   - If not: use default 100% markup

2. When adding a product with MSRP pricing enabled:
   - Calculate markup to reach MSRP price
   - Override any default markup

### MOQ Display
- In product catalog: Should show spreadsheet MOQ if available
- In proposal tables: Should use spreadsheet MOQ for calculations
- Fallback: Calculate based on $1000 minimum order

## Monitoring App Logs

Watch for any errors in the terminal where the app is running:
- No "AttributeError: query_params" ✅ (Fixed)
- No "ValueError: Series ambiguous" ✅ (Fixed)
- No "KeyError" for missing columns (backward compatibility working)

## Test Data Locations

The demo dataset (master_pricing_template_10_14) may not have all new columns.
The real dataset (master_pricing) should have the new schema.

You can switch between datasets using the sidebar selector.

## Troubleshooting

If you encounter any errors:
1. Check the terminal for error messages
2. Note which tab and action caused the error
3. Try with both demo and real datasets to isolate the issue

## Success Indicators

✅ App loads and runs without errors
✅ Products can be added to proposals/orders
✅ Customization costs display correctly
✅ MOQ values are reasonable (from spreadsheet or calculated)
✅ Invoices generate successfully
✅ No error messages in console

---

## Stop the App

When testing is complete, you can stop the app by:
1. Going to the terminal
2. Pressing Ctrl+C
3. Or closing the terminal window