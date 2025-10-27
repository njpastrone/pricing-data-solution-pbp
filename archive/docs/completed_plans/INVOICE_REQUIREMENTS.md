# Invoice & Purchase Order Requirements

## Purpose

This document defines the required information and format for generating invoices and purchase orders from the pricing app, aligned with the bookkeeper's standardized template.

## Template Reference

The app now generates combined Invoice & Purchase Order Request Forms based on:
- `templates/TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md`
- `templates/TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf`

See also: `docs/INVOICE_PO_RESTRUCTURE_PLAN.md` for implementation details.

## Required Invoice/PO Information

The combined Invoice & Purchase Order form contains the following sections:

### Header Section

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

### Itemized Table

| Column | Description | Example |
|--------|-------------|---------|
| **PARTNER** | Partner/supplier name | "Partner X" |
| **ITEMS + SPECS** | Product name and specifications | "Chocolate Bar\n4oz, Dark, Organic" |
| **QTY** | Quantity ordered | 100 |
| **IN-HANDS from Partner** | When partner delivers to PBP | "Oct 17, 2025" |
| **COST** | Partner cost per unit (before markup) | "$10.00" |
| **COST VERIFIED?** | Cost verification status | "Yes / No / Pending" |
| **SELL PRICE** | Total sell price to client for this line | "$1,500.00" |

## Invoice Calculation Requirements

### Line Item Total
For each product in the order:
```
Total (Per-Item) = Quantity × Price (Per-Unit)
```

Where **Price (Per-Unit)** includes:
- Base product cost from pricing tier
- Label costs (if applicable)
- Art setup fee (if applicable, amortized per unit)
- Markup percentage applied to product cost only

### Subtotal (Pre-Tax)
```
Subtotal = Sum of all line item totals
```

The subtotal represents the total cost before shipping and tariff costs are added.

### Additional Costs (Not in Subtotal)
These costs are typically shown separately after the subtotal:
- **Shipping**: One-time cost for entire order
- **Tariff**: One-time cost for entire order

### Final Total
```
Final Total = Subtotal + Shipping + Tariff
```

## Invoice Table Example

### Multi-Product Order Invoice

| Product/Service Name | Description | Quantity | Pricing Tier | Price (Per-Unit) | Total (Per-Item) |
|---------------------|-------------|----------|--------------|------------------|------------------|
| Jaggery Organic Dark Chocolate | Product Ref: JA01, Partner: Jaggery | 50 | 26-50 | $87.40 | $4,370.00 |
| Jaggery Milk Chocolate Truffle Box | Product Ref: JA02, Partner: Jaggery | 100 | 101-250 | $77.70 | $7,770.00 |

**Subtotal (Pre-Tax):** $12,140.00
**Shipping:** $300.00
**Tariff:** $150.00

**Final Total:** $12,590.00

## Notes

- The **Pricing Tier** column helps provide transparency about volume discounts
- The **Description** should include product reference number for tracking
- All monetary values should be formatted with 2 decimal places
- The subtotal calculation excludes shipping and tariff (these are added separately)
- Per-unit pricing should reflect the "all-in" cost per unit (after markup and fees are applied)

### Notes Section

The form includes a notes section for:
- **Kitting Specifications**: Box size, packaging requirements, assembly instructions
- **Client Requests**: Rush delivery, special handling, custom messaging
- **Add-on Samples**: Extra units for display, samples for approval
- **Artwork Attachments**: List of artwork files (logo_final.ai, label_design_v3.pdf, etc.)
- **General Notes**: Any other important details

## Current App Status

**Status:** ✅ Implemented (2025-10-22)

The Invoice & Purchase Order section has been completely restructured to match the bookkeeper's standardized template format. The app now:

1. **Combines Invoice & PO**: Single unified form instead of separate sections
2. **Matches Template**: All fields align with `TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED`
3. **Auto-extracts Partner Contacts**: Pulls POC info from Google Sheets Partner-Specific Info
4. **Validates Required Fields**: Warns users if critical data is missing before export
5. **Exports in Template Format**: CSV download includes all required columns and notes

### Key Features:
- Standardized dropdowns for Payment Terms, Payment Method, Ship Method
- Date pickers for Client In-Hands Date, Order/Cost Submitted Dates
- Partner contact auto-population from Google Sheets
- Comprehensive order notes section (5 categories)
- Validation warnings for missing/incomplete data
- Single CSV export with header, line items, totals, and notes

See `docs/INVOICE_PO_RESTRUCTURE_PLAN.md` for complete implementation details.
