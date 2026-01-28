# Manual Testing Guide: Per-Product Kitting as Separate Line Items

**Date:** 2026-01-28
**Feature:** Convert per-product kitting from merged display to separate line items
**Related:** Meeting notes 01/28/25, CHANGELOG.md

---

## Test Checklist

### Tab 3: Order Summary Display

#### Test 1: Single Product with Kitting
- [ ] Navigate to Tab 3 (Order & Client Info)
- [ ] Add a product using Option D (Manual Product Selection)
- [ ] Enable "Include Per-Product Kitting" checkbox for the product
- [ ] Set kitting values:
  - PBP Cost: $25
  - Client Price: $40
  - Description: "Premium gift box"
- [ ] Scroll to Section 4: Order Summary
- [ ] **Verify:** Product line shows base product WITHOUT kitting note
- [ ] **Verify:** "Per-Product Kitting" section appears after Customization
- [ ] **Verify:** Kitting line shows:
  - Description: "{Product Name} - Premium gift box"
  - Quantity: "one-time"
  - PBP Cost per unit: $25.00
  - PBP Cost total: $25.00
  - Client Price per unit: $40.00
  - Client Price total: $40.00
- [ ] **Verify:** "Per-Product Kitting Subtotal" row appears
- [ ] **Verify:** Order total includes kitting costs

#### Test 2: Multiple Products with Different Kitting
- [ ] Add a second product
- [ ] Enable kitting with different values:
  - PBP Cost: $10
  - Client Price: $15
  - Description: "Repackaging"
- [ ] **Verify:** Both kitting lines appear in "Per-Product Kitting" section
- [ ] **Verify:** Subtotal correctly sums both kitting costs
- [ ] **Verify:** Order total includes both kitting amounts

#### Test 3: Mix of Products With/Without Kitting
- [ ] Add a third product WITHOUT kitting enabled
- [ ] **Verify:** Product without kitting does NOT appear in kitting section
- [ ] **Verify:** Only products with kitting appear in kitting section
- [ ] **Verify:** Subtotal only includes products with kitting

#### Test 4: Product with Customization AND Kitting
- [ ] Add a product with both customization and kitting enabled
- [ ] **Verify:** Customization appears in "Customization" section
- [ ] **Verify:** Kitting appears in "Per-Product Kitting" section
- [ ] **Verify:** Both sections have separate subtotals
- [ ] **Verify:** Order total includes both customization and kitting

#### Test 5: Global Kitting + Per-Product Kitting
- [ ] In Section 3: Order Settings, add global kitting:
  - PBP Cost: $50
  - Client Price: $75
- [ ] **Verify:** Global kitting appears in main order line items
- [ ] **Verify:** Per-product kitting still appears in separate section
- [ ] **Verify:** Order total includes BOTH global and per-product kitting

---

### Tab 4: Invoice Generation

#### Test 6: Invoice Line Items
- [ ] Complete all required order information
- [ ] Navigate to Tab 4 (Execution & Accounting)
- [ ] Scroll to invoice preview
- [ ] **Verify:** Product line shows base cost WITHOUT kitting
- [ ] **Verify:** Separate kitting line appears with:
  - Indented description: "  └ Premium gift box"
  - QTY: 1
  - COST/UNIT: $25.00
  - TOTAL COST: $25.00
  - SELL PRICE/UNIT: $40.00
  - TOTAL SELL PRICE: $40.00
- [ ] **Verify:** Indentation matches customization line items (└ prefix)
- [ ] **Verify:** Partner column matches parent product

#### Test 7: Multiple Products in Invoice
- [ ] **Verify:** Each product's kitting appears as separate line below product
- [ ] **Verify:** All kitting lines use quantity = 1
- [ ] **Verify:** Indentation shows hierarchy (product → kitting)

#### Test 8: CSV Export
- [ ] Click "Download Invoice/PO as CSV"
- [ ] Open CSV file
- [ ] **Verify:** Product line shows base costs
- [ ] **Verify:** Kitting appears as separate row with indented description
- [ ] **Verify:** All kitting lines have QTY = 1
- [ ] **Verify:** Totals in CSV match on-screen totals

#### Test 9: HTML Export
- [ ] Click "Download Invoice/PO as HTML"
- [ ] Open HTML file in browser
- [ ] **Verify:** Kitting lines appear with indentation
- [ ] **Verify:** Formatting is clear and professional
- [ ] **Verify:** Totals match Tab 4 display

---

### Product Detail Breakdown

#### Test 10: Product Editing View
- [ ] In Tab 3, expand a product with kitting enabled
- [ ] Look at the pricing breakdown table
- [ ] **Verify:** Kitting row appears in breakdown table with description
- [ ] **Verify:** Shows "one-time" quantity
- [ ] **Verify:** Shows both PBP cost and client price
- [ ] **Verify:** Totals summary at bottom does NOT include kitting
  - (Kitting shown separately in breakdown, not in total line)

---

### Edge Cases

#### Test 11: Zero-Cost Kitting
- [ ] Set kitting with PBP Cost = $0, Client Price = $0
- [ ] **Verify:** Kitting section does NOT appear (no kitting with $0 client price)

#### Test 12: Saved Orders
- [ ] Save an order with per-product kitting
- [ ] Close and reopen app
- [ ] Load saved order
- [ ] **Verify:** Kitting data persists
- [ ] **Verify:** Kitting displays correctly in order summary
- [ ] **Verify:** Kitting appears correctly in invoice

#### Test 13: Legacy Orders (Pre-Change)
- [ ] Load an order saved BEFORE this change
- [ ] **Verify:** Order loads without errors
- [ ] **Verify:** If order has kitting, it displays in new format
- [ ] **Verify:** Totals are correct

---

## Expected Results

### Tab 3 Order Summary (Section 4)
```
Products:
  Base Product: Strawberry Jam          50    $10.00    $500.00    $20.00    $1000.00

Products Subtotal                                      $500.00               $1000.00

Per-Product Kitting:
  Strawberry Jam - Premium gift box     one-time  $25.00  $25.00   $40.00   $40.00

Per-Product Kitting Subtotal                           $25.00                $40.00

[... rest of order summary ...]
```

### Tab 4 Invoice (Table 4)
```
PARTNER | DESCRIPTION (Invoice) | QTY | COST/UNIT | TOTAL COST | SELL PRICE/UNIT | TOTAL SELL PRICE
-----------------------------------------------------------------------------------------------
Partner X | Strawberry Jam       | 50  | $10.00    | $500.00    | $20.00          | $1000.00
Partner X |   └ Premium gift box | 1   | $25.00    | $25.00     | $40.00          | $40.00
```

---

## Automated Test Coverage

Run automated tests to verify implementation:

```bash
# Run per-product kitting test suite
python scripts/features/test_per_product_kitting.py

# Expected output:
# ============================================================
# PER-PRODUCT KITTING FEATURE - TEST SUITE
# ============================================================
#
# === Test 1: Order Item Structure ===
# ✓ Order item structure includes all kitting fields
#
# === Test 2: Kitting Calculations ===
# ✓ Kitting calculations correct
#
# === Test 3: Migration of Old Orders ===
# ✓ Migration successful - old orders will work correctly
#
# === Test 4: Display Logic ===
# ✓ Display logic correct - kitting shown as separate line item
#
# === Test 5: Invoice Specs ===
# ✓ Invoice specs generation correct - kitting as separate line item with indentation
#
# ============================================================
# TEST RESULTS: 5 passed, 0 failed
# ============================================================
#
# ✓ ALL TESTS PASSED - Feature ready for production!
```

---

## Regression Checks

Verify these features still work correctly:

- [ ] Products without kitting display normally
- [ ] Global kitting still works (separate from per-product)
- [ ] Customization line items display correctly
- [ ] Tariff line items display correctly
- [ ] Discount calculations are accurate
- [ ] Marketing rounding works
- [ ] CSV exports match UI display
- [ ] HTML exports are formatted correctly
- [ ] Order totals are accurate
- [ ] Saved orders load correctly

---

## Known Issues

None currently.

---

## Documentation Updated

- [x] CHANGELOG.md - Added entry for v8.2.0 (Unreleased)
- [x] CLAUDE.md - Updated Tab 3 and Tab 4 feature descriptions
- [x] Test script updated - `scripts/features/test_per_product_kitting.py`
- [x] This manual testing guide created

---

## Sign-Off

**Implementation Complete:** ✅
**Automated Tests Passing:** ✅
**Manual Testing:** [ ] (To be completed)
**Documentation Updated:** ✅
**Ready for Production:** [ ] (After manual testing)
