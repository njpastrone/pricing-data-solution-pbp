# Tab 3 to Tab 4 Data Flow Testing Checklist

**Purpose:** Ensure all inputs from Tab 3 (Order & Client Info) are correctly reflected in Tab 4 (Execution & Accounting) documents.

**Last Updated:** 2025-12-11

---

## 🧪 Manual Testing Checklist

### Setup: Create Complete Test Order in Tab 3

#### 1. Client Information (Section 5)
- [ ] **Company Details**
  - [ ] Set "Existing Client"
  - [ ] Enter company name: "Test Company ABC"
  - [ ] Enter PO Number: "PO-2025-001"

- [ ] **Multiple Contacts** (test new feature)
  - [ ] Add primary contact with all 4 fields (name, email, phone, role)
  - [ ] Add billing contact with different role
  - [ ] Test "Remove" button functionality
  - [ ] Verify minimum 1 contact enforced

- [ ] **Addresses**
  - [ ] Enter complete billing address
  - [ ] Enter different shipping address
  - [ ] Test drop shipping = "Yes" with details

- [ ] **Dates & Submission**
  - [ ] Set Client In-Hands Date
  - [ ] Enter Order Submitted By name
  - [ ] Enter Cost Submitted By name
  - [ ] Verify dates auto-populate

#### 2. Products (Section 1)
- [ ] **Regular Products**
  - [ ] Add at least 2 different products
  - [ ] Set different quantities (test >1)
  - [ ] Adjust markup percentages
  - [ ] Enable customization on one product
    - [ ] Add customization description
    - [ ] Set setup fee
    - [ ] Set per-unit cost
    - [ ] Test minimum quantity

- [ ] **Custom Line Item**
  - [ ] Add custom service/product
  - [ ] Enter custom description
  - [ ] Set custom price

#### 3. Order Settings (Section 3)
- [ ] **Pricing Settings**
  - [ ] Enter Partner Shipping Cost ($45)
  - [ ] Enter Client Shipping Price ($75)
  - [ ] Apply 5% NGO discount
  - [ ] Enable $0.50 rounding (new feature)
  - [ ] Enable marketing rounding
  - [ ] Add Sales Tax amount (new feature)

- [ ] **Kitting Section** (new feature)
  - [ ] Enter Kitting PBP Cost ($80)
  - [ ] Enter Kitting Client Price ($150)

- [ ] **Payment Terms**
  - [ ] Select "Net 15" (new option)
  - [ ] Test "Custom" option with text input
  - [ ] Enter custom payment terms text

#### 4. Order Notes (Section - improved UX)
- [ ] Fill all 5 note categories:
  - [ ] Kitting Specifications
  - [ ] Client Requests
  - [ ] Add-on Samples
  - [ ] Artwork Attachments
  - [ ] General Notes
- [ ] Test with long text in each field
- [ ] Verify word counts display

---

## 📋 Tab 4 Verification Checklist

### Navigate to Tab 4 - Execution & Accounting

#### 1. Review & Edit Order Information
- [ ] **Verify all fields populated:**
  - [ ] Company name appears
  - [ ] All contacts listed (expandable cards)
  - [ ] Billing address complete
  - [ ] Shipping address complete
  - [ ] PO number correct
  - [ ] Drop ship details shown
  - [ ] Payment timeline shows "Net 15" or custom
  - [ ] All submission info present

- [ ] **Test Edit Functionality:**
  - [ ] Edit a field and verify it persists
  - [ ] Check callbacks work (no data loss on edit)

#### 2. Edit Product Descriptions (new feature)
- [ ] Expand "Edit Product Descriptions"
- [ ] Verify all products listed
- [ ] Test editing descriptions
- [ ] Verify placeholders show defaults
- [ ] Check custom line items use custom_description

#### 3. Edit Order Settings
- [ ] **Verify all settings transferred:**
  - [ ] Partner shipping cost
  - [ ] Client shipping price
  - [ ] Discount percentage
  - [ ] Sales tax amount
  - [ ] Kitting costs (both)
  - [ ] Credit card fee
  - [ ] Rounding options

#### 4. Invoice/PO Generation
- [ ] Click "Generate Invoice & Purchase Order"
- [ ] **Verify Table 1: Client/Company Information**
  - [ ] Company name
  - [ ] Multiple contacts shown
  - [ ] Addresses correct

- [ ] **Verify Table 2: Partners + POCs**
  - [ ] All partners listed
  - [ ] Contact info populated

- [ ] **Verify Table 3: Order Details**
  - [ ] In-hands date
  - [ ] Ship method
  - [ ] Payment terms (Net 15 or custom)
  - [ ] Submission details

- [ ] **Verify Table 4: Invoice Items**
  - [ ] Products use edited descriptions
  - [ ] Customization as separate line items
  - [ ] Tariffs calculated and shown
  - [ ] Sales tax line present
  - [ ] Kitting costs line present
  - [ ] Shipping costs (both PBP and client)
  - [ ] Totals accurate

- [ ] **Verify Notes Section**
  - [ ] All 5 note categories displayed
  - [ ] Content matches Tab 3 input

---

## 💾 Export Testing

### CSV Export
- [ ] Download CSV file
- [ ] Open in spreadsheet application
- [ ] **Verify includes:**
  - [ ] All client information
  - [ ] Multiple contacts
  - [ ] Product details with edited descriptions
  - [ ] Customization details
  - [ ] All pricing columns (PBP and client)
  - [ ] Sales tax
  - [ ] Kitting costs
  - [ ] All notes

### HTML Export
- [ ] Download HTML file
- [ ] Open in browser
- [ ] **Verify formatting:**
  - [ ] Tables display correctly
  - [ ] Line breaks preserved in descriptions
  - [ ] All data present
  - [ ] Print-friendly layout
  - [ ] Custom payment terms shown

---

## 🔄 Persistence Testing

### Save and Load
- [ ] Save order with name "Test Order Complete"
- [ ] Clear session (Reset Current Session)
- [ ] Load saved order
- [ ] **Verify all fields restored:**
  - [ ] Client info (including multiple contacts)
  - [ ] All products with customization
  - [ ] Order settings
  - [ ] Sales tax
  - [ ] Kitting costs
  - [ ] Custom payment terms
  - [ ] All 5 note categories
  - [ ] Edited product descriptions

---

## 🎯 Edge Cases Testing

### Special Scenarios
- [ ] **Empty Fields**
  - [ ] Leave some optional fields empty
  - [ ] Verify no errors in Tab 4

- [ ] **Special Characters**
  - [ ] Use quotes, commas, ampersands in descriptions
  - [ ] Use special characters in notes
  - [ ] Verify proper escaping in CSV/HTML

- [ ] **Maximum Values**
  - [ ] Add maximum contacts (test up to 5)
  - [ ] Very long descriptions (500+ chars)
  - [ ] Large quantities (1000+)
  - [ ] High percentages (999%)

- [ ] **Zero Values**
  - [ ] Zero quantity (should prevent)
  - [ ] Zero markup
  - [ ] Zero shipping
  - [ ] Zero sales tax

- [ ] **Custom Payment Terms**
  - [ ] Very long custom terms
  - [ ] Special formatting (e.g., "2/10 Net 30")
  - [ ] Switch between standard and custom

---

## ✅ Test Results Summary

**Date Tested:** _________________

**Tester:** _________________

### Results:
- [ ] All client info transfers correctly
- [ ] All order settings preserved
- [ ] All 5 note categories transfer
- [ ] Product details complete
- [ ] Customization details correct
- [ ] Sales tax included
- [ ] Kitting costs included
- [ ] Payment terms (including custom) work
- [ ] Multiple contacts supported
- [ ] Edited descriptions used in invoice
- [ ] CSV export complete
- [ ] HTML export formatted correctly
- [ ] Save/load preserves all data

### Issues Found:
_________________________________
_________________________________
_________________________________

### Notes:
_________________________________
_________________________________
_________________________________

---

## 🚀 Automated Test Script

Run comprehensive automated test:
```bash
cd pricing-data-solution-pbp
python scripts/test_tab3_to_tab4_data_flow.py
```

This tests session state initialization and data structure validation.