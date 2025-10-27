# Invoice & Purchase Order Restructure Plan

## Purpose

This document outlines the complete restructuring plan for the Invoice and Purchase Order modules to align with the bookkeeper's standardized format defined in `templates/TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md`.

---

## Plan to Restructure App Output for Invoice & Purchase Order

### 1. Field Mapping Summary

| Template Field | Current App Field | Action Needed |
|----------------|-------------------|----------------|
| **HEADER SECTION** | | |
| Company | `client_info['company_name']` | ✅ Exists |
| Contact + Email | `client_info['contact_name']` + `client_info['contact_email']` | ✅ Exists |
| IF NEW Company Billing Address + Email | `client_info['is_new_client']` + `client_info['billing_address']` | ✅ Exists, needs conditional display |
| Client PO # | `client_info['client_po']` | ✅ Exists |
| Partner(s) + POC | N/A | ❌ **ADD** - Need partner list with POC names |
| Client In-Hands Date | N/A | ❌ **ADD** - Target delivery date for client |
| Ship Method | `client_info['shipping_type']` | ⚠️ **MODIFY** - Change to dropdown: Ground/Air/Freight/Other |
| Payment Terms | `client_info['payment_timeline']` | ⚠️ **MODIFY** - Change to dropdown: Net 30/Net 60/Due on Receipt/50% Deposit |
| Payment Method | `client_info['payment_preference']` | ⚠️ **MODIFY** - Change to dropdown: Check/ACH/Credit Card/Wire Transfer |
| Order Submitted by | N/A | ❌ **ADD** - Person submitting (auto-fill from system) |
| Order Submitted Date | `invoice_date` or `po_date` | ✅ Exists (can rename/reuse) |
| Cost Submitted by | N/A | ❌ **ADD** - Person submitting costs |
| Cost Submitted Date | N/A | ❌ **ADD** - Date costs were submitted |
| **ITEMIZED SECTION** | | |
| PARTNER | `item['partner']` | ✅ Exists |
| ITEMS + SPECS | `item['product_name']` + description | ⚠️ **MODIFY** - Combine product name + specs into one field |
| QTY | `item['quantity']` | ✅ Exists |
| IN-HANDS from Partner | N/A | ❌ **ADD** - Partner delivery date (different from client in-hands) |
| COST | `item['base_price']` or partner cost | ⚠️ **MODIFY** - Show PARTNER cost (not sell price) |
| COST VERIFIED? | N/A | ❌ **ADD** - Boolean dropdown: Yes/No/Pending |
| SELL PRICE | `item['total_per_unit']` or total | ✅ Exists (needs clarification: per-unit or total?) |
| **NOTES SECTION** | | |
| Notes | N/A | ❌ **ADD** - Text area for kitting specs, client requests, samples, artwork |

---

### 2. Data Model Updates

#### 2.1 Update `client_info` structure (in session_state)

```python
# CURRENT structure
client_info = {
    'company_name': str,
    'contact_name': str,
    'contact_email': str,
    'billing_address': str,
    'is_new_client': bool,
    'client_po': str,
    'payment_timeline': str,  # Free text
    'payment_preference': str,  # Free text
    'shipping_type': str,  # Free text
    'shipping_address': str
}

# NEW structure (additions/changes marked with # NEW or # MODIFIED)
client_info = {
    'company_name': str,
    'contact_name': str,
    'contact_email': str,
    'billing_address': str,
    'is_new_client': bool,
    'client_po': str,
    'payment_timeline': str,  # MODIFIED: Dropdown options
    'payment_preference': str,  # MODIFIED: Dropdown options
    'shipping_type': str,  # MODIFIED: Dropdown options
    'shipping_address': str,
    'client_in_hands_date': date,  # NEW
    'order_submitted_by': str,  # NEW
    'order_submitted_date': date,  # NEW (auto-filled)
    'cost_submitted_by': str,  # NEW
    'cost_submitted_date': date  # NEW
}
```

#### 2.2 Update `order_items` structure (in session_state)

```python
# CURRENT item structure
order_item = {
    'product_name': str,
    'partner': str,
    'product_ref': str,
    'quantity': int,
    'tier_range': str,
    'product_subtotal': float,
    'markup_amount': float,
    'product_total': float,
    'total_per_unit': float,
    # ... customization fields
}

# NEW item structure (additions marked with # NEW)
order_item = {
    'product_name': str,
    'partner': str,
    'product_ref': str,
    'quantity': int,
    'tier_range': str,
    'product_subtotal': float,  # This is PARTNER cost
    'markup_amount': float,
    'product_total': float,
    'total_per_unit': float,
    # ... existing customization fields
    'product_specs': str,  # NEW - detailed specifications
    'partner_in_hands_date': date,  # NEW - when partner delivers to PBP
    'partner_cost_per_unit': float,  # NEW - clarify this is PARTNER cost
    'cost_verified': str,  # NEW - "Yes" / "No" / "Pending"
    'sell_price_total': float,  # NEW - clarify this is CLIENT sell price (total)
    'sell_price_per_unit': float  # NEW - clarify this is CLIENT sell price (per unit)
}
```

#### 2.3 Add new `partner_contacts` structure

```python
# NEW: Store partner contact information
# This should be loaded from Google Sheets (Partner-Specific Info sheet)
partner_contacts = {
    'Partner X': {
        'poc_name': 'John Smith',
        'poc_email': 'john@partnerx.com',
        'poc_phone': '555-1234'
    },
    # ... other partners
}
```

#### 2.4 Add `order_notes` structure

```python
# NEW: General notes for the entire order
order_notes = {
    'kitting_specs': str,  # Details about kitting requirements
    'client_requests': str,  # Special client requests
    'addon_samples': str,  # Additional samples to include
    'artwork_attachments': str,  # List of artwork files
    'general_notes': str  # Catch-all for other notes
}
```

---

### 3. Output Template Structure

#### 3.1 Invoice/PO Header Section

```
┌─────────────────────────────────────────────────────────────────┐
│                  INVOICE AND PURCHASE ORDER                     │
│                    REQUEST FORM                                 │
└─────────────────────────────────────────────────────────────────┘

Company: [Existing] / [New]           | Order Submitted by: [Name]
Contact + Email: [Name] ([Email])    | Date: [YYYY-MM-DD]
IF NEW - Billing Address: [Address]  |
Client PO #: [PO-######] or N/A      | Cost Submitted by: [Name]
                                      | Date: [YYYY-MM-DD]

─────────────────────────────────────────────────────────────────

PARTNER(S) + POC:
┌─────────────────────────────────────────────────────────────────┐
│ Partner X - John Smith (john@partnerx.com)                     │
│ Partner Y - Jane Doe (jane@partnery.com)                       │
└─────────────────────────────────────────────────────────────────┘

Client In-Hands Date: [Oct 20, 2025]
Ship Method: [Ground / Air / Freight / Other]
Payment Terms: [Net 30 / Net 60 / Due on Receipt / 50% Deposit]
Payment Method: [Check / ACH / Credit Card / Wire Transfer]
```

#### 3.2 Itemized Table Section

```
INVOICE AND PURCHASE ORDER ITEM DETAILS

This cost-to-sell segment outlines our partners' cost, our sell price
to client, and our partners' requested in-hands date. Our in-hands date
for clients may be later than the in-hands date to Peace by Piece for
kitting purposes.

┌─────────┬──────────────┬─────┬────────────┬──────┬───────────┬──────────┐
│ PARTNER │ ITEMS + SPECS│ QTY │ IN-HANDS   │ COST │   COST    │  SELL    │
│         │              │     │from Partner│      │ VERIFIED? │  PRICE   │
├─────────┼──────────────┼─────┼────────────┼──────┼───────────┼──────────┤
│Partner X│Product A     │ 100 │ Oct 17, 25 │$10.00│    Yes    │$1,500.00 │
│         │ 4oz, Dark    │     │            │      │           │          │
├─────────┼──────────────┼─────┼────────────┼──────┼───────────┼──────────┤
│Partner X│Custom Label  │ 100 │ Oct 17, 25 │ $2.00│    Yes    │  $300.00 │
│         │Setup Fee     │   1 │ Oct 17, 25 │$50.00│    Yes    │   $50.00 │
├─────────┼──────────────┼─────┼────────────┼──────┼───────────┼──────────┤
│Partner Y│Product B     │ 200 │ Oct 18, 25 │ $8.50│  Pending  │$2,550.00 │
└─────────┴──────────────┴─────┴────────────┴──────┴───────────┴──────────┘

                                          Subtotal: $4,400.00
                                          Shipping:   $150.00
                                            Tariff:    $50.00
                                             TOTAL: $4,600.00
```

#### 3.3 Notes Section

```
─────────────────────────────────────────────────────────────────

NOTES

Enter any specific details, kitting specs, client requests, add-on
samples for Peace by Piece to be added to purchase orders. Remember
to attach titled artwork that matches your purchase order request and
any additional spec sheets for our partners.

┌─────────────────────────────────────────────────────────────────┐
│ Kitting Specs:                                                  │
│ - Box size: 12x8x4 inches                                       │
│ - Include thank you card with each box                          │
│                                                                  │
│ Client Requests:                                                │
│ - Rush delivery for first 50 units                              │
│                                                                  │
│ Add-on Samples:                                                 │
│ - 10 extra units for display purposes                           │
│                                                                  │
│ Artwork Attachments:                                            │
│ - logo_partnerx_final.ai                                        │
│ - label_design_v3.pdf                                           │
│                                                                  │
│ General Notes:                                                  │
│ - Client prefers biodegradable packaging                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4. Automation Integration

#### 4.1 Export Format Options

1. **CSV Export** (Current + Enhanced)
   - Maintain current CSV download functionality
   - Add new fields to CSV headers
   - Include separate "Notes" sheet or section

2. **JSON Export** (NEW)
   ```python
   def export_invoice_json():
       return {
           'header': {...},  # All header fields
           'line_items': [...],  # All products
           'notes': {...},  # All notes
           'totals': {...}  # Summary totals
       }
   ```

3. **Formatted Email Template** (NEW)
   - HTML email template matching printed format
   - Plain text fallback
   - Attachment support for CSV/PDF

#### 4.2 Email Automation Hooks

```python
# NEW function to prepare data for bookkeeper
def prepare_bookkeeper_submission():
    """
    Format data according to bookkeeper template requirements
    Returns structured data ready for email or API submission
    """
    return {
        'invoice_data': {...},
        'po_data': {...},
        'attachments': [...]  # Artwork files, specs, etc.
    }

# NEW function to send to bookkeeper
def send_to_bookkeeper(invoice_data, recipient_email):
    """
    Automated email submission to bookkeeper
    - Formats email body using template
    - Attaches CSV export
    - Sends via SMTP or email API
    """
    pass
```

#### 4.3 Data Validation

```python
# NEW validation function
def validate_invoice_completeness():
    """
    Check if all required fields are filled before submission
    Returns list of missing/invalid fields
    """
    required_fields = [
        'company_name',
        'contact_email',
        'client_in_hands_date',
        'payment_terms',
        'payment_method',
        # ... etc
    ]

    missing = []
    for field in required_fields:
        if not client_info.get(field):
            missing.append(field)

    # Check line items
    for item in order_items:
        if not item.get('cost_verified'):
            missing.append(f"Cost verification for {item['product_name']}")
        if not item.get('partner_in_hands_date'):
            missing.append(f"Partner in-hands date for {item['product_name']}")

    return missing
```

---

### 5. Testing Plan

#### 5.1 Data Population Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| **New client - single product** | Enter new company info + 1 product | All header fields populate correctly, billing address shows |
| **Existing client - multi-product** | Select existing company + 3 products from 2 partners | Partner list shows both partners, line items grouped correctly |
| **Custom line item** | Add custom service with no partner | Shows "Custom" in Partner column, cost verified = N/A |
| **Incomplete data** | Leave required field blank | Validation catches missing field, prevents export |

#### 5.2 Field Mapping Verification

| Template Field | Test Input | App Output Location | Pass/Fail |
|----------------|------------|---------------------|-----------|
| Client In-Hands Date | Oct 20, 2025 | Header section, row 3 | ☐ |
| Partner(s) + POC | Partner X - John Smith | Header section, partners table | ☐ |
| Cost Verified? | "Yes" | Line item column 6 | ☐ |
| IN-HANDS from Partner | Oct 17, 2025 | Line item column 4 | ☐ |
| Notes | "Rush delivery..." | Notes section, formatted text | ☐ |

#### 5.3 Output Format Testing

1. **Visual Comparison**
   - Generate sample invoice with app
   - Print side-by-side with bookkeeper template
   - Verify column alignment, section headers match

2. **CSV Export Test**
   - Download CSV from app
   - Open in Excel/Google Sheets
   - Verify all columns present with correct headers
   - Verify data types (dates as dates, currency as numbers)

3. **Email Template Test**
   - Send test email to internal recipient
   - Verify formatting renders correctly
   - Verify attachments included
   - Test on desktop + mobile email clients

#### 5.4 Cross-Check with Bookkeeper

**Before Production Launch:**
1. Generate 3 sample invoices using app (simple, complex, edge case)
2. Send to bookkeeper for review
3. Collect feedback on:
   - Missing fields
   - Incorrect field mappings
   - Formatting issues
   - Additional requirements
4. Iterate based on feedback

#### 5.5 Integration Testing

| Scenario | Test Steps | Expected Behavior |
|----------|------------|-------------------|
| **Complete order flow** | Start → Add products → Fill all fields → Export | No errors, complete export |
| **Partial completion** | Add products → Leave dates blank → Try export | Validation error, list missing fields |
| **Multi-partner order** | Add products from 3 partners → Export | Partner list complete, items grouped |
| **Save & resume** | Fill half the form → Close app → Reopen | Session state preserved, can continue |

---

### 6. Implementation Phases

#### Phase 1: Data Model Updates (Core Schema)
- Update `client_info` dictionary with new fields
- Update `order_items` dictionary with partner details
- Add `partner_contacts` data structure
- Add `order_notes` data structure
- **Estimated Time:** 2-3 hours

#### Phase 2: UI Input Forms
- Add date pickers for in-hands dates
- Convert payment/shipping to dropdowns
- Add partner contact selector
- Add notes text areas
- Add "Cost Verified?" toggle per item
- **Estimated Time:** 3-4 hours

#### Phase 3: Output Template Redesign
- Restructure invoice header layout
- Rebuild itemized table with new columns
- Add notes section rendering
- Update CSV export structure
- **Estimated Time:** 2-3 hours

#### Phase 4: Validation & Testing
- Implement validation function
- Add warning messages for missing fields
- Test all field mappings
- **Estimated Time:** 1-2 hours

#### Phase 5: Automation & Export
- Build email template
- Add JSON export option
- Create `send_to_bookkeeper()` function
- **Estimated Time:** 3-4 hours

**Total Estimated Time:** 11-16 hours

---

### 7. Key Decisions & Clarifications Needed

| Question | Current Assumption | Needs Confirmation |
|----------|-------------------|-------------------|
| Is "SELL PRICE" per-unit or total? | Assuming **total** per line item | ✓ Clarify with user |
| Should partner contacts be hardcoded or from Sheets? | Load from **Google Sheets** (Partner-Specific Info) | ✓ Confirm data source |
| Do we need separate Invoice vs PO outputs? | **Combined** format per template | ✓ Confirm with bookkeeper |
| Should "Cost Verified?" default to "Pending"? | Default to **"Pending"** | ✓ Confirm workflow |
| What date format? | **YYYY-MM-DD** for system, display as **MMM DD, YYYY** | ✓ Confirm preference |

---

## Next Steps

1. Review this plan with stakeholders
2. Answer clarification questions in Section 7
3. Confirm partner contact data source
4. Begin Phase 1 implementation
5. Test incrementally after each phase

---

**Document Version:** 1.0
**Last Updated:** 2025-10-22
**Status:** Draft - Awaiting Approval
