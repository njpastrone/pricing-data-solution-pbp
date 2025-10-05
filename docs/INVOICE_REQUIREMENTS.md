# Invoice Requirements

## Purpose

This document defines the required information and format for generating invoices from the pricing app.

## Required Invoice Information

An invoice must contain the following information in a table format:

| Column | Description | Example |
|--------|-------------|---------|
| **Product/Service Name** | Full name of the product or service | "Jaggery Organic Dark Chocolate Bar" |
| **Description** | Brief description including product reference number and partner | "Product Ref: JA01, Partner: Jaggery" |
| **Quantity** | Number of units ordered | 100 |
| **Pricing Tier** | The quantity tier range used for pricing | "101-250" |
| **Price (Per-Unit)** | Price per single unit including markup | $45.50 |
| **Total (Per-Item)** | Total cost for this line item (Quantity × Price) | $4,550.00 |

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

## Current App Status

**Status:** Needs refinement

The current Invoice section in the app displays detailed breakdowns but may not present information in the exact table format required for invoice generation. The Invoice section needs to be updated to match this specification.
