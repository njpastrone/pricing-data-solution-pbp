# Tab 5: Executive Pricing Tool - Stress Test Checklist

## 🎯 Testing Overview
**Test URL:** http://172.20.10.3:8501/ (Tab 5: Executive Pricing Tool)
**Test Date:** January 13, 2026
**Purpose:** Comprehensive stress testing to ensure all functionality works without errors

---

## ✅ Section 1: Basic Loading & Interface

### Initial Page Load
- [ ] Tab 5 loads without errors
- [ ] Header displays: "Executive Pricing Tool"
- [ ] Caption displays: "Build and analyze pricing scenarios with detailed cost breakdowns"
- [ ] Data loads correctly (no "Please load pricing data first" error)
- [ ] Product Selector expander is visible and expanded (when no products added)

### Data Validation
- [ ] Partner dropdown populates with all partners
- [ ] Product dropdown updates when partner is selected
- [ ] All partners have products available
- [ ] No empty dropdowns or missing data

---

## ✅ Section 2: Product Selection & Addition

### Basic Product Addition
- [ ] Select different partners and verify product lists change
- [ ] Add a product from Partner 1
- [ ] Add a product from Partner 2  
- [ ] Add a product from Partner 3
- [ ] Add a product from Partner 4
- [ ] Toast notifications appear for successful additions
- [ ] "Product already added" warning works when trying to add duplicates

### Product Selector Behavior
- [ ] Selector expands when no products are added
- [ ] Selector collapses after adding first product
- [ ] "Add Another Product" button shows selector again
- [ ] All UI interactions are responsive

---

## ✅ Section 3: Product Configuration Testing

### Quantity Testing
- [ ] Default quantity is 100
- [ ] Can change quantity to 1, 50, 250, 500, 1000
- [ ] Tier information updates correctly with quantity changes
- [ ] PBP Cost displays correctly for different tiers
- [ ] All calculations update in real-time

### Bidirectional Price Editing
- [ ] Default markup is 100% (verify in multiple products)
- [ ] Change markup from 100% to 50% - client price updates
- [ ] Change markup from 100% to 150% - client price updates
- [ ] Change client price directly - markup % recalculates
- [ ] No circular update loops or freezing
- [ ] Both fields update correctly without conflicts

### Customization Options
- [ ] Customization checkbox defaults to unchecked
- [ ] Enable customization - setup fee and per-unit fields appear
- [ ] Setup fee defaults from spreadsheet data (if available)
- [ ] Per-unit cost defaults from spreadsheet data (if available)
- [ ] PBP cost displays correctly below each field
- [ ] Can enter custom values (override defaults)
- [ ] Changes reflect in pricing breakdown immediately

### Tariff Configuration
- [ ] Tariff checkbox auto-checks for non-USA products
- [ ] Tariff checkbox defaults unchecked for USA products
- [ ] Country of origin displays correctly
- [ ] Percentage vs Dollar input method works
- [ ] Default tariff rates load from spreadsheet
- [ ] Can override tariff rates manually
- [ ] Tariff calculations are correct (% of commercial value)
- [ ] Pass-through cost displays correctly

---

## ✅ Section 4: Pricing Calculations & Breakdowns

### Basic Pricing Verification
- [ ] Base product cost × markup = client price
- [ ] Margin calculations are correct
- [ ] Markup % and margin % display correctly
- [ ] Total margin = margin per unit × quantity

### Customization Calculations
- [ ] Setup fee appears as one-time cost
- [ ] Per-unit customization × quantity = total customization cost
- [ ] PBP costs vs client prices are calculated separately
- [ ] Customization doesn't affect base product markup

### Tariff Calculations
- [ ] Tariff percentage mode: % × client price = tariff per unit
- [ ] Tariff dollar mode: fixed amount per unit
- [ ] Tariffs are pass-through (same for PBP cost and client price)
- [ ] Tariff country and rate display correctly
- [ ] Total tariffs = per unit × quantity

### Pricing Breakdown Table
- [ ] Base product line shows correct costs and prices
- [ ] Customization setup shows as "one-time" quantity
- [ ] Customization per-unit shows correct quantity
- [ ] Tariff line shows country and percentage
- [ ] All PBP costs and client prices are accurate
- [ ] Table formatting is clean and readable

### Subtotal Calculations
- [ ] PBP subtotal includes base + customization + tariffs
- [ ] Client subtotal includes base + markup + customization + tariffs
- [ ] Margin calculation excludes tariffs (pass-through)
- [ ] Margin percentage is based on revenue (excluding tariffs)
- [ ] All subtotals display with proper formatting

---

## ✅ Section 5: Multiple Product Testing

### Multi-Product Scenarios
- [ ] Add 3-4 different products from different partners
- [ ] Each product maintains independent settings
- [ ] Quantities can be different across products
- [ ] Markups can be different across products
- [ ] Customization settings are independent
- [ ] Tariff settings are independent per product

### Product Management
- [ ] Remove individual products (Remove button)
- [ ] Product list updates correctly after removal
- [ ] No orphaned data or UI elements after removal
- [ ] Can re-add previously removed products

---

## ✅ Section 6: Order-Level Settings (Section 3)

### Shipping Configuration
- [ ] Default shipping cost ($70.00)
- [ ] Can modify shipping cost
- [ ] Shipping applies to entire order
- [ ] Shipping calculations are correct

### Credit Card Fee
- [ ] CC fee checkbox defaults to unchecked
- [ ] CC fee percentage defaults to 3.0%
- [ ] Can modify CC fee percentage
- [ ] CC fee applies to order total
- [ ] CC fee calculations are correct

---

## ✅ Section 7: Order Summary & Matrix

### Summary Calculations
- [ ] Products subtotal sums all individual product subtotals
- [ ] Shipping adds correctly to order total
- [ ] CC fee applies to (subtotal + shipping) if enabled
- [ ] Final total is accurate
- [ ] All currency formatting is consistent ($X.XX)

### Executive Matrix Display
- [ ] Matrix shows all products in organized table
- [ ] Partner groupings (if applicable)
- [ ] Quantity, unit cost, total cost columns
- [ ] Markup and client price columns
- [ ] Margin columns (per unit and total)
- [ ] Grand totals row
- [ ] Professional formatting for executive presentation

---

## ✅ Section 8: Export Functionality

### CSV Export
- [ ] "Export to CSV" button works
- [ ] CSV downloads successfully
- [ ] CSV contains all product data
- [ ] CSV includes order-level settings
- [ ] CSV formatting is clean and importable
- [ ] Filename includes timestamp

### PDF Export (if implemented)
- [ ] "Export to PDF" button works
- [ ] PDF generates successfully
- [ ] PDF contains executive summary format
- [ ] PDF includes pricing matrix
- [ ] PDF is professional quality
- [ ] PDF filename includes timestamp

---

## ⚠️ Section 9: Edge Cases & Error Handling

### Data Edge Cases
- [ ] Products with no MSRP data
- [ ] Products with no customization data  
- [ ] Products with no tariff data
- [ ] Products with unusual tier structures
- [ ] Products with zero or very low costs

### User Input Edge Cases
- [ ] Quantity = 1 (minimum)
- [ ] Quantity = 10,000 (maximum)
- [ ] Markup = -50% (minimum)
- [ ] Markup = 500% (maximum)
- [ ] Zero customization costs
- [ ] Very high customization costs
- [ ] Zero tariff rates
- [ ] 100% tariff rates

### UI Stress Testing
- [ ] Add maximum products (test performance)
- [ ] Rapid clicking on buttons
- [ ] Quick successive quantity changes
- [ ] Fast toggling of checkboxes
- [ ] Browser refresh - data persistence
- [ ] Tab switching and return

### Error Scenarios
- [ ] Network interruption during data load
- [ ] Invalid data in spreadsheet
- [ ] Missing required columns
- [ ] Browser console shows no JavaScript errors
- [ ] All Streamlit components render properly

---

## 📊 Section 10: Performance & UX Testing

### Performance
- [ ] Page loads in < 3 seconds
- [ ] Calculations update in < 1 second
- [ ] No lag when adding/removing products
- [ ] Export functions complete in reasonable time
- [ ] No memory leaks during extended use

### User Experience
- [ ] All buttons are clearly labeled
- [ ] Help text is informative and accurate
- [ ] Error messages are clear and actionable
- [ ] Success messages are confirmatory
- [ ] UI layout is logical and intuitive
- [ ] Mobile responsiveness (if applicable)

---

## 🔍 Section 11: Data Integrity Verification

### Cross-Tab Consistency
- [ ] Products from Tab 1 can be added to Tab 5
- [ ] Pricing calculations match between tabs
- [ ] Partner data is consistent across tabs
- [ ] Product data accuracy across application

### Calculation Verification
- [ ] Manual calculation spot checks
- [ ] Compare with Tab 3 pricing for same products
- [ ] Verify against original spreadsheet data
- [ ] Check tier boundary calculations
- [ ] Confirm markup vs margin calculations

---

## 📝 Bug Report Template

**Bug ID:** #
**Severity:** Critical/High/Medium/Low
**Section:** 
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:** 
**Actual Result:** 
**Browser/Environment:** 
**Screenshot/Console Errors:** 

---

## ✅ Final Verification Checklist

- [ ] All sections tested without critical errors
- [ ] Performance is acceptable for executive use
- [ ] Data accuracy is verified
- [ ] Export functions work properly
- [ ] UI is professional and intuitive
- [ ] Ready for stakeholder demonstration

**Test Completion Date:** _______________
**Tested By:** _______________
**Overall Status:** ✅ PASS / ❌ FAIL / ⚠️ ISSUES FOUND

**Executive Summary:**
_Brief summary of testing results, any issues found, and recommendations_