# Proposal Requirements

## Purpose

This document defines the required information and format for generating proposals from the pricing app.

## Current Format Specification

**Status:** Active (Implemented 2025-10-06)

The proposal section generates a **separate table for each product** with the following structure.

**Download Options:** Each product table includes a download button to export as CSV for easy copying into proposal documents.

### Per-Product Table Format

Each product gets its own 4-column table:

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

## Calculation Logic

### MOQ Handling
- Read from "Minimum Qty" column in data
- If value is NA, empty, or invalid → default to 5
- Display as integer in table

### Price Ea (@ Qty MOQ)
1. Determine which pricing tier the MOQ falls into
2. Get base price for that tier
3. Add per-unit costs:
   - Label cost per unit (if labels selected)
   - Art setup fee amortized per MOQ unit
4. Apply markup to product cost only
5. Result = per-unit price at MOQ quantity

### Discount Price
- Apply order-level discount percentage to "Price Ea"
- Format: `Price Ea × (1 - discount%/100)`
- Column header shows discount description (e.g., "5% NGO Discount")

### Artwork Fees Row
- Shows one-time and per-unit customization costs
- Format: "Artwork Set-Up: $[art_setup]; [Type]: $[cost] per unit"
- If no customization: Display "No additional customization fees"

---

## Future Enhancement Ideas (Not Currently Implemented)

### 1. Company Information
What should we include?
- Company name
- Contact person
- Email address
- Phone number
- Company address
- Logo (future enhancement)

### 2. Client Information
What should we include?
- Client company name
- Contact person name
- Date of proposal
- Proposal reference number (optional)

### 3. Proposal Summary
What should we highlight?
- Brief description of the offering
- Total order value
- Key benefits or unique selling points
- Delivery timeline estimate

### 4. Product/Service Details Table
What information should each line item show?

| Column | Current Invoice Format | Should Proposals Include? |
|--------|----------------------|---------------------------|
| Product/Service Name | Yes | ? |
| Description | Product Ref + Partner | ? |
| Quantity | Yes | ? |
| Pricing Tier | Yes (for transparency) | ? |
| Price (Per-Unit) | Yes | ? |
| Total (Per-Item) | Yes | ? |

**Questions:**
- Should proposals show the same level of detail as invoices?
- Should we show pricing tier ranges to justify volume pricing?
- Should we include product reference numbers in proposals?
- Do we want to show per-unit pricing or just totals?

### 5. Pricing Breakdown
What cost components should be visible?

**Current Invoice Format:**
- Subtotal (sum of all line items)
- Shipping (separate line)
- Tariff (separate line)
- Final Total

**Questions:**
- Should proposals break down costs the same way as invoices?
- Should we show markup percentage?
- Should we explain what's included in each cost?
- Do we want to show discounts as a separate line item?

### 6. Optional Costs & Services
How should we present optional add-ons?

**Current Options in App:**
- Custom labels (with minimum quantity requirements)
- Art setup fee (conditional on labels)
- Custom line items

**Questions:**
- Should proposals list optional services separately?
- Should we show "included" vs "optional" costs?
- How should we present label minimums and requirements?

### 7. Terms & Conditions
What terms should we specify?

**Potential Items:**
- Payment terms (e.g., "Net 30", "50% deposit")
- Proposal validity period (e.g., "Valid for 30 days")
- Estimated delivery timeline
- Cancellation policy
- Warranty information
- Returns/refunds policy

**Questions:**
- What are your standard payment terms?
- How long should proposals remain valid?
- What delivery timeline should we promise?

### 8. Next Steps / Call to Action
How should we guide clients toward acceptance?

**Potential Elements:**
- Acceptance instructions
- Contact information for questions
- Signature block (for formal acceptance)
- Link to order/payment (future enhancement)

**Questions:**
- What's your preferred acceptance process?
- Do you need formal signatures on proposals?
- Should we include a deadline for response?

## Proposal vs Invoice: Key Differences

| Aspect | Proposal | Invoice |
|--------|----------|---------|
| **Purpose** | Persuade & inform | Request payment |
| **Timing** | Before order confirmation | After delivery/completion |
| **Tone** | Marketing/sales | Transactional |
| **Detail Level** | ? (to discuss) | Detailed breakdown |
| **Required Elements** | ? (to discuss) | Standardized format |
| **Flexibility** | More room for customization | Rigid structure |

## Current App Status

**Status:** Needs definition

The current Proposal section in the app may show similar information to invoices, but proposals typically serve a different purpose and may require:
- More persuasive language
- Marketing-focused descriptions
- Terms and conditions
- Validity/expiration dates
- Formal acceptance mechanism

## Next Steps

1. Review and answer the questions in each section above
2. Define exactly what information should be included in proposals
3. Determine proposal table format and column structure
4. Specify any additional sections needed
5. Update app to generate proposals according to this specification

## Notes

- Proposals should be client-facing and professional
- Consider what information helps close deals vs what clutters the proposal
- Balance transparency with simplicity
- Think about what questions clients typically ask
- Consider industry standards for B2B proposals
