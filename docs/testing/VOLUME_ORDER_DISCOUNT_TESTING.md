# Volume Order Discount (5%) - Manual Testing Guide

**Date:** 2026-01-28
**Feature Version:** v8.1.0 (Unreleased)
**Test Duration:** ~15-20 minutes

---

## Pre-Testing Setup

### Environment
- [ ] App running locally: http://localhost:8501
- [ ] Test script running: http://localhost:8502 (optional)
- [ ] Demo dataset selected (recommended for testing)

### Initial State
- [ ] No products in proposal
- [ ] No products in order
- [ ] No saved proposals/orders loaded

---

## Test Suite 1: Tab 1 (Proposal Generator)

### Test 1.1: Dropdown Display
**Navigate:** Tab 1 → Section 2: Configure Proposal

**Expected:**
- [ ] "Client Discount" dropdown shows 4 options:
  - [ ] None
  - [ ] Non-profit (5%)
  - [ ] Volume Order (5%)  ← NEW
  - [ ] Custom

**Result:** ⬜ Pass ⬜ Fail

---

### Test 1.2: Volume Order Discount Selection
**Steps:**
1. Select "Volume Order (5%)" from dropdown
2. Add 2-3 products to proposal
3. Expand Section 3: Proposal Tables

**Expected:**
- [ ] Products show in "Products in Proposal" table
- [ ] Table header shows: "Client Price (5% Volume Order discount)"
- [ ] Prices are 5% lower than non-discounted prices

**Result:** ⬜ Pass ⬜ Fail

**Notes:**
_Record any unexpected behavior_

---

### Test 1.3: Non-profit Discount Comparison
**Steps:**
1. Change dropdown to "Non-profit (5%)"
2. Check table header updates

**Expected:**
- [ ] Table header changes to: "Client Price (5% Non-profit discount)"
- [ ] Prices remain the same (both are 5%)
- [ ] Label is different (Non-profit vs Volume Order)

**Result:** ⬜ Pass ⬜ Fail

---

### Test 1.4: Custom Discount
**Steps:**
1. Select "Custom" from dropdown
2. Enter 10%
3. Check table header

**Expected:**
- [ ] Custom discount input field appears
- [ ] Table header shows: "Client Price (10.0% discount)"
- [ ] Prices are 10% lower than non-discounted

**Result:** ⬜ Pass ⬜ Fail

---

### Test 1.5: Save Proposal with Volume Order Discount
**Steps:**
1. Set discount back to "Volume Order (5%)"
2. Expand "Saved Proposals" section
3. Enter name: "Test Volume Discount"
4. Click "Save Proposal"
5. Clear proposal (remove all products)
6. Load "Test Volume Discount" proposal

**Expected:**
- [ ] Proposal saves successfully
- [ ] After loading, dropdown shows "Volume Order (5%)"
- [ ] Products reload with Volume Order discount applied
- [ ] Table header shows correct label

**Result:** ⬜ Pass ⬜ Fail

**Notes:**
_Proposal ID:_ ___________

---

## Test Suite 2: Tab 3 (Order & Client Info)

### Test 2.1: Manual Product Selection with Volume Order
**Navigate:** Tab 3 → Section 1: Add Products

**Steps:**
1. Select "Volume Order (5%)" from dropdown under "Option D"
2. Add 2-3 products
3. Check Section 2: Current Order

**Expected:**
- [ ] Products added to order
- [ ] "Volume Order (5%)" still selected in dropdown
- [ ] Order summary shows 5% discount applied

**Result:** ⬜ Pass ⬜ Fail

---

### Test 2.2: Import Proposal with Volume Order Discount
**Navigate:** Tab 3 → Section 1: Add Products → Option C

**Steps:**
1. Go back to Tab 1
2. Create proposal with Volume Order (5%) discount
3. Return to Tab 3
4. Click "Import from Proposal"
5. Check Section 3: Order Settings

**Expected:**
- [ ] Products import successfully
- [ ] "Discount Quoted to Client" caption shows: "Volume Order Discount (5%)"  ← NEW
- [ ] Order discount dropdown still shows current selection
- [ ] Section 4: Order Summary shows discount applied

**Result:** ⬜ Pass ⬜ Fail

**Screenshot:** ⬜ Taken

---

### Test 2.3: Order Settings Discount Dropdown (Location 1)
**Navigate:** Tab 3 → Section 3: Order Settings

**Steps:**
1. Locate "Client Discount" dropdown
2. Click dropdown to view options

**Expected:**
- [ ] Dropdown shows 4 options:
  - [ ] None
  - [ ] Non-profit (5%)
  - [ ] Volume Order (5%)  ← NEW
  - [ ] Custom

**Result:** ⬜ Pass ⬜ Fail

---

### Test 2.4: Change Order Discount to Volume Order
**Steps:**
1. Select "Volume Order (5%)" from Order Settings dropdown
2. Check Section 4: Order Summary

**Expected:**
- [ ] Discount updates to 5%
- [ ] Order summary recalculates
- [ ] Subtotal shows reduced prices

**Result:** ⬜ Pass ⬜ Fail

---

### Test 2.5: Confirm & Review Discount Dropdown (Location 2)
**Navigate:** Tab 3 → Section 5: Confirm & Review Order

**Steps:**
1. Scroll to "Order Adjustments" section
2. Locate "Client Discount" dropdown

**Expected:**
- [ ] Dropdown shows 4 options (same as Location 1)
- [ ] Currently selected: "Volume Order (5%)"
- [ ] Both dropdowns stay in sync (change one, other updates)

**Result:** ⬜ Pass ⬜ Fail

---

### Test 2.6: Save Order with Volume Order Discount
**Navigate:** Tab 3 → Top of page → "Saved Orders" expander

**Steps:**
1. Expand "Saved Orders"
2. Enter name: "Test Volume Order"
3. Click "Save Order"
4. Clear order (remove all products)
5. Load "Test Volume Order"

**Expected:**
- [ ] Order saves successfully
- [ ] After loading, discount dropdown shows "Volume Order (5%)"
- [ ] Products reload with discount applied
- [ ] Order summary shows correct discount

**Result:** ⬜ Pass ⬜ Fail

**Notes:**
_Order ID:_ ___________

---

## Test Suite 3: Tab 4 (Execution & Accounting)

### Test 3.1: Order Data Flow to Tab 4
**Navigate:** Tab 4 (from Tab 3 with Volume Order discount)

**Steps:**
1. Create order in Tab 3 with Volume Order (5%) discount
2. Navigate to Tab 4
3. Check "Order Adjustments" section

**Expected:**
- [ ] All order data appears in Tab 4
- [ ] "Client Discount" dropdown shows "Volume Order (5%)"
- [ ] Invoice preview shows discounted prices

**Result:** ⬜ Pass ⬜ Fail

---

### Test 3.2: Invoice Generation with Volume Order Discount
**Steps:**
1. Scroll to bottom of Tab 4
2. Click "Download Invoice & PO (CSV)"
3. Open downloaded CSV
4. Check discount line item

**Expected:**
- [ ] CSV downloads successfully
- [ ] Discount shows as "Volume Order Discount (5%)"
- [ ] Discount amount calculated correctly (5% of products subtotal)
- [ ] Total reflects discount

**Result:** ⬜ Pass ⬜ Fail

**Screenshot:** ⬜ Taken

---

## Test Suite 4: Integration Testing

### Test 4.1: Complete Workflow (Tab 1 → Tab 3 → Tab 4)
**Steps:**
1. **Tab 1:** Create proposal with Volume Order (5%), 3 products
2. **Tab 1:** Save proposal as "Integration Test"
3. **Tab 3:** Import "Integration Test" proposal
4. **Tab 3:** Verify "Discount Quoted to Client: Volume Order Discount (5%)"
5. **Tab 3:** Save order as "Integration Test Order"
6. **Tab 4:** Generate invoice

**Expected:**
- [ ] Discount persists across all tabs
- [ ] Labels consistent everywhere ("Volume Order" not "Non-profit")
- [ ] Calculations accurate at every step
- [ ] Invoice shows correct discount

**Result:** ⬜ Pass ⬜ Fail

**Notes:**
_Total time:_ _______ minutes

---

### Test 4.2: Switching Between Discount Types
**Navigate:** Tab 1 or Tab 3

**Steps:**
1. Start with "None"
2. Switch to "Non-profit (5%)"
3. Switch to "Volume Order (5%)"
4. Switch to "Custom" (enter 15%)
5. Switch back to "None"

**Expected:**
- [ ] Each change updates immediately
- [ ] Prices recalculate correctly
- [ ] Labels update in all locations
- [ ] No errors or crashes
- [ ] UI remains responsive

**Result:** ⬜ Pass ⬜ Fail

---

### Test 4.3: CSV Export Verification
**Navigate:** Tab 1 → Section 3: Proposal Tables

**Steps:**
1. Create proposal with Volume Order (5%)
2. Expand proposal table for a product
3. Click "Download this table (CSV)"
4. Open CSV
5. Check header row

**Expected:**
- [ ] CSV downloads successfully
- [ ] Header shows: "Client Price (5% Volume Order discount)"
- [ ] All prices match UI display
- [ ] Discount label is correct (not "Non-profit")

**Result:** ⬜ Pass ⬜ Fail

---

## Test Suite 5: Edge Cases & Backward Compatibility

### Test 5.1: Load Old Non-profit Proposal
**Navigate:** Tab 1 → Saved Proposals

**Steps:**
1. Load any old saved proposal with "Non-profit (5%)" discount
   (Created before Volume Order feature)
2. Check dropdown selection
3. Check table header

**Expected:**
- [ ] Proposal loads successfully
- [ ] Dropdown shows "Non-profit (5%)"
- [ ] Table header shows "5% Non-profit discount"
- [ ] No errors or data loss

**Result:** ⬜ Pass ⬜ Fail

**Notes:**
_Backward compatibility verified_

---

### Test 5.2: Load Old Non-profit Order
**Navigate:** Tab 3 → Saved Orders

**Steps:**
1. Load any old saved order with Non-profit discount
2. Check both discount dropdowns (Sections 3 & 5)
3. Check order summary

**Expected:**
- [ ] Order loads successfully
- [ ] Both dropdowns show "Non-profit (5%)"
- [ ] Order summary shows correct discount
- [ ] No errors or data loss

**Result:** ⬜ Pass ⬜ Fail

---

### Test 5.3: Mixed Discount Types in Session
**Steps:**
1. Create proposal with "Volume Order (5%)" in Tab 1
2. Import to Tab 3
3. Change order discount to "Non-profit (5%)"
4. Check both values are tracked independently

**Expected:**
- [ ] Proposal discount: "Volume Order (5%)"
- [ ] Order discount: "Non-profit (5%)"
- [ ] "Discount Quoted to Client" warning shows Volume Order
- [ ] Order uses Non-profit for calculations
- [ ] No conflicts or errors

**Result:** ⬜ Pass ⬜ Fail

---

### Test 5.4: Zero Product Edge Case
**Steps:**
1. Set discount to "Volume Order (5%)"
2. Don't add any products
3. Check if discount setting persists
4. Add products later

**Expected:**
- [ ] No errors with empty proposal/order
- [ ] Discount setting remembered
- [ ] When products added, discount applies correctly

**Result:** ⬜ Pass ⬜ Fail

---

### Test 5.5: Dataset Switching
**Navigate:** Sidebar

**Steps:**
1. Create proposal with Volume Order discount (Demo dataset)
2. Save proposal
3. Switch to Real dataset
4. Try to load Demo proposal

**Expected:**
- [ ] Warning: "Dataset mismatch"
- [ ] Option to proceed or cancel
- [ ] If proceed, discount loads correctly
- [ ] No data corruption

**Result:** ⬜ Pass ⬜ Fail

---

## Test Suite 6: Automated Test Script

### Test 6.1: Run Automated Test Suite
**Navigate:** http://localhost:8502 (if running test script)

**Steps:**
1. Open test script: `streamlit run scripts/features/test_volume_order_discount.py`
2. Run through all 7 tests
3. Verify all pass

**Expected:**
- [ ] Test 1: Session State Initialization ✅
- [ ] Test 2: Tab 1 Proposal Discount Dropdown ✅
- [ ] Test 3: Proposal Table Header Display ✅
- [ ] Test 4: Tab 3 Order Discount Dropdown ✅
- [ ] Test 5: Discount Quoted to Client Warning ✅
- [ ] Test 6: Backward Compatibility Test ✅
- [ ] Test 7: Index Calculation Test ✅

**Result:** ⬜ Pass ⬜ Fail

---

## Summary & Sign-Off

### Test Results Summary

| Test Suite | Total Tests | Passed | Failed | Notes |
|------------|-------------|--------|--------|-------|
| Suite 1: Tab 1 | 5 | ___ | ___ | |
| Suite 2: Tab 3 | 6 | ___ | ___ | |
| Suite 3: Tab 4 | 2 | ___ | ___ | |
| Suite 4: Integration | 3 | ___ | ___ | |
| Suite 5: Edge Cases | 5 | ___ | ___ | |
| Suite 6: Automated | 1 | ___ | ___ | |
| **TOTAL** | **22** | ___ | ___ | |

### Critical Issues Found
_List any critical issues that must be fixed before deployment:_

1.
2.
3.

### Minor Issues Found
_List any minor issues or UX improvements:_

1.
2.
3.

### Recommendations
_Any recommendations for improvement or follow-up work:_

1.
2.
3.

---

## Sign-Off

**Tester Name:** ___________________________

**Date:** ___________________________

**Time Spent:** _______ minutes

**Overall Result:** ⬜ PASS - Ready for Deployment  ⬜ FAIL - Issues must be resolved

**Approved for Production:** ⬜ Yes  ⬜ No

**Signature:** ___________________________

---

## Deployment Checklist

After all tests pass:

- [ ] Code changes committed to git
- [ ] CHANGELOG.md updated
- [ ] Documentation updated (if needed)
- [ ] Test script added to scripts/features/
- [ ] Implementation summary documented
- [ ] Version number incremented (v8.1.0)
- [ ] Deployed to production
- [ ] Production smoke test completed
- [ ] User communication sent (if needed)
- [ ] Close related issues/tasks

---

## Notes

**Environment Details:**
- Python version: ___________
- Streamlit version: ___________
- Browser: ___________
- OS: ___________

**Additional Notes:**
_Any other observations or context:_
