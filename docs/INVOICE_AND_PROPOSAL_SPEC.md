# Invoice & Proposal Specifications

**STATUS:** Current - Implemented 2025-10-22
**Last Updated:** 2025-10-27

This document defines the requirements and format for generating invoices, purchase orders, and proposals from the pricing app.

---

## Table of Contents

1. [Invoice & Purchase Order Specification](#invoice--purchase-order-specification)
2. [Proposal Specification](#proposal-specification)
3. [Data Model Requirements](#data-model-requirements)

---

## Invoice & Purchase Order Specification

### Purpose

The app generates combined Invoice & Purchase Order Request Forms aligned with the bookkeeper's standardized template.

### Template Reference

Based on: `templates/TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED`

### Required Information

#### Header Section

| Field | Description | Example |
|-------|-------------|---------|
| **Company** | Client company name (Existing/New) | "Acme Corp (Existing)" |
| **Contact + Email** | Client contact person and email | "John Smith (john@acme.com)" |
| **IF NEW - Billing Address** | Billing address (shown only for new clients) | "123 Main St, City, State ZIP" |
| **Client PO #** | Client purchase order number | "PO-2025-001" or "N/A" |
| **Partner(s) + POC** | List of partners with point of contact | "Partner X - Jane Doe (jane@partnerx.com)" |
| **Client In-Hands Date** | Target delivery date for client | "Oct 20, 2025" |
| **Ship Method** | Shipping method | "Ground / Air / Freight / Other" |
| **Payment Terms** | Payment timeline | "Net 30 / Net 60 / Due on Receipt / 50% Deposit" |
| **Payment Method** | How client will pay | "Check / ACH / Credit Card / Wire Transfer" |
| **Order Submitted by** | Person creating order | "Your Name" |
| **Order Submitted Date** | Date order created | "2025-10-22" (auto-filled) |
| **Cost Submitted by** | Person who verified costs | "Finance Contact" |
| **Cost Submitted Date** | Date costs verified | "2025-10-22" |

#### Itemized Table

| Column | Description | Example |
|--------|-------------|---------|
| **PARTNER** | Partner/supplier name | "Partner X" |
| **ITEMS + SPECS** | Product name and specifications | "Chocolate Bar\n4oz, Dark, Organic" |
| **QTY** | Quantity ordered | 100 |
| **IN-HANDS from Partner** | When partner delivers to PBP | "Oct 17, 2025" |
| **COST** | Partner cost per unit (before markup) | "$10.00" |
| **COST VERIFIED?** | Cost verification status | "Yes / No / Pending" |
| **SELL PRICE** | Total sell price to client for this line | "$1,500.00" |

#### Notes Section

The form includes a notes section for:
- **Kitting Specifications**: Box size, packaging requirements, assembly instructions
- **Client Requests**: Rush delivery, special handling, custom messaging
- **Add-on Samples**: Extra units for display, samples for approval
- **Artwork Attachments**: List of artwork files (logo_final.ai, label_design_v3.pdf, etc.)
- **General Notes**: Any other important details

### Invoice Calculation Requirements

#### Line Item Total
```
Total (Per-Item) = Quantity × Price (Per-Unit)
```

Where **Price (Per-Unit)** includes:
- Base product cost from pricing tier
- Label costs (if applicable)
- Art setup fee (if applicable, amortized per unit)
- Markup percentage applied to product cost only

#### Subtotal (Pre-Tax)
```
Subtotal = Sum of all line item totals
```

#### Additional Costs (Not in Subtotal)
- **Shipping**: One-time cost for entire order
- **Tariff**: One-time cost for entire order

#### Final Total
```
Final Total = Subtotal + Shipping + Tariff
```

### Invoice Table Example

| Product/Service Name | Description | Quantity | Pricing Tier | Price (Per-Unit) | Total (Per-Item) |
|---------------------|-------------|----------|--------------|------------------|------------------|
| Jaggery Organic Dark Chocolate | Product Ref: JA01, Partner: Jaggery | 50 | 26-50 | $87.40 | $4,370.00 |
| Jaggery Milk Chocolate Truffle Box | Product Ref: JA02, Partner: Jaggery | 100 | 101-250 | $77.70 | $7,770.00 |

**Subtotal (Pre-Tax):** $12,140.00
**Shipping:** $300.00
**Tariff:** $150.00

**Final Total:** $12,590.00

### Implementation Status

**Status:** Implemented (2025-10-22)

The app now:
1. **Combines Invoice & PO**: Single unified form instead of separate sections
2. **Matches Template**: All fields align with bookkeeper template
3. **Auto-extracts Partner Contacts**: Pulls POC info from Google Sheets Partner-Specific Info
4. **Validates Required Fields**: Warns users if critical data is missing before export
5. **Exports in Template Format**: CSV download includes all required columns and notes

**Key Features:**
- Standardized dropdowns for Payment Terms, Payment Method, Ship Method
- Date pickers for Client In-Hands Date, Order/Cost Submitted Dates
- Partner contact auto-population from Google Sheets
- Comprehensive order notes section (5 categories)
- Validation warnings for missing/incomplete data
- Single CSV export with header, line items, totals, and notes

---

## Proposal Specification

### Purpose

Generates client-facing proposals with per-product pricing tables for sales and quoting purposes.

### Current Format

**Status:** Active (Implemented 2025-10-06)

The proposal section generates a **separate table for each product** with a 4-column format.

### Per-Product Table Format

| Column | Header Format | Description | Data Source |
|--------|---------------|-------------|-------------|
| **Column 1** | MOQ | Minimum order quantity | "Minimum Qty" from data (default to 5 if NA) |
| **Column 2** | Price Ea (@ Qty [MOQ]) | Per-unit price at MOQ quantity | Base price from appropriate tier + fees |
| **Column 3** | Price Ea [Discount Description] | Per-unit price with discount applied | Column 2 price minus discount % |
| **Column 4** | Delivery | Delivery timeframe | Blank (user fills in manually) |

**Row 1:** Column headers (as specified above)
**Row 2:** Data values for each column
**Row 3:** Artwork/customization fees (displayed as text below the data row)

- Format: "Artwork Set-Up: $[amount]; [Customization Type]: $[cost] per unit"
- Example: "Artwork Set-Up: $70; Embroidery: $5.00 per unit"

### Example Tables

#### Example 1: Product with Labels

**Upcycled Pilot's Everyday Case**

| MOQ | Price Ea (@ Qty 10) | Price Ea 5% NGO Discount | Delivery |
|-----|---------------------|--------------------------|----------|
| 10 | $139.00 | $132.05 | 2-3 weeks |

Artwork Set-Up: $70; Labels: $1.50 per unit

---

#### Example 2: Product without Customization

**Organic Cotton Tote Bag**

| MOQ | Price Ea (@ Qty 25) | Price Ea 5% NGO Discount | Delivery |
|-----|---------------------|--------------------------|----------|
| 25 | $18.50 | $17.58 | 2-3 weeks |

No additional customization fees

---

### Calculation Logic

#### MOQ Handling
- Read from "Minimum Qty" column in data
- If value is NA, empty, or invalid → default to 5
- Display as integer in table

#### Price Ea (@ Qty MOQ)
1. Determine which pricing tier the MOQ falls into
2. Get base price for that tier
3. Add per-unit costs:
   - Label cost per unit (if labels selected)
   - Art setup fee amortized per MOQ unit
4. Apply markup to product cost only
5. Result = per-unit price at MOQ quantity

#### Discount Price
- Apply order-level discount percentage to "Price Ea"
- Format: `Price Ea × (1 - discount%/100)`
- Column header shows discount description (e.g., "5% NGO Discount")

#### Artwork Fees Row
- Shows one-time and per-unit customization costs
- Format: "Artwork Set-Up: $[art_setup]; [Type]: $[cost] per unit"
- If no customization: Display "No additional customization fees"

### Download Options

Each product table includes a download button to export as CSV for easy copying into proposal documents.

---

## Data Model Requirements

### client_info Structure

```python
client_info = {
    'company_name': str,
    'contact_name': str,
    'contact_email': str,
    'billing_address': str,
    'is_new_client': bool,
    'client_po': str,
    'payment_timeline': str,  # Dropdown options
    'payment_preference': str,  # Dropdown options
    'shipping_type': str,  # Dropdown options
    'shipping_address': str,
    'client_in_hands_date': date,
    'order_submitted_by': str,
    'order_submitted_date': date,  # Auto-filled
    'cost_submitted_by': str,
    'cost_submitted_date': date
}
```

### order_items Structure

```python
order_item = {
    'product_name': str,
    'partner': str,
    'product_ref': str,
    'quantity': int,
    'tier_range': str,
    'product_subtotal': float,  # Partner cost
    'markup_amount': float,
    'product_total': float,
    'total_per_unit': float,
    'product_specs': str,
    'partner_in_hands_date': date,
    'partner_cost_per_unit': float,
    'cost_verified': str,  # "Yes" / "No" / "Pending"
    'sell_price_total': float,
    'sell_price_per_unit': float
}
```

### partner_contacts Structure

```python
# Loaded from Google Sheets (Partner-Specific Info sheet)
partner_contacts = {
    'Partner X': {
        'poc_name': 'John Smith',
        'poc_email': 'john@partnerx.com',
        'poc_phone': '555-1234'
    }
}
```

### order_notes Structure

```python
order_notes = {
    'kitting_specs': str,
    'client_requests': str,
    'addon_samples': str,
    'artwork_attachments': str,
    'general_notes': str
}
```

---

## Export Formats

### CSV Export
- Header section with all client and order metadata
- Itemized table with all products
- Totals section (subtotal, shipping, tariff, final total)
- Notes section with all note categories

### JSON Export (Future Enhancement)
```python
{
    'header': {...},  # All header fields
    'line_items': [...],  # All products
    'notes': {...},  # All notes
    'totals': {...}  # Summary totals
}
```

---

## Validation Requirements

### Required Fields Check

Before allowing export, validate that these fields are filled:
- Company name
- Contact email
- Client in-hands date
- Payment terms
- Payment method
- Ship method
- Order submitted by
- Cost submitted by

### Line Item Validation

For each order item, check:
- Cost verified status is set
- Partner in-hands date is specified
- Quantities are valid (> 0)

### Warning System

Display user-friendly warnings for:
- Missing required fields
- Incomplete line items
- Unverified costs
- Missing partner contact information

---

## Notes

- **Pricing Tier** column helps provide transparency about volume discounts
- **Description** should include product reference number for tracking
- All monetary values should be formatted with 2 decimal places
- Subtotal calculation excludes shipping and tariff (these are added separately)
- Per-unit pricing should reflect the "all-in" cost per unit (after markup and fees are applied)
- Proposals are client-facing and should be professional
- Invoices/POs are for internal bookkeeping and partner coordination

---

**End of Specification**
