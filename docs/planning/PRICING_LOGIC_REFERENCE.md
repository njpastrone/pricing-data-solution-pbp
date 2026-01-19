# Pricing Logic Reference

Last Updated: January 19, 2026

---

## Overview

This document explains the MOQ (Minimum Order Quantity) and MOV (Minimum Order Value) calculation logic used throughout the Peace by Piece International pricing application.

### What is MOQ?
**MOQ (Minimum Order Quantity)** is the smallest number of units that must be ordered for a product. It ensures orders meet both partner requirements and PBP's business minimums.

### What is MOV?
**MOV (Minimum Order Value)** is the minimum dollar amount that must be spent on an order. It's converted to a quantity based on the product's unit price.

### Why Both?
Different partners and PBP have different constraints:
- Some partners require a minimum quantity (e.g., "50 units minimum")
- Others require a minimum dollar value (e.g., "$2,000 minimum order")
- PBP may have its own minimums separate from partners
- The final MOQ is the **maximum** of all these constraints

---

## The Four Columns

### 4a. MOQ (Partner)
- **Type:** Number (whole units)
- **Definition:** Partner's minimum order quantity requirement
- **Example:** 50 units
- **When to use:** Partner specifies quantity minimums

### 4b. MOV (Partner)
- **Type:** Currency (dollar amount)
- **Definition:** Partner's minimum order value requirement
- **Example:** $1,500
- **When to use:** Partner specifies dollar minimums
- **Conversion:** `MOQ = ceil(MOV / unit_price)`

### 4c. MOQ (PBP)
- **Type:** Number (whole units)
- **Definition:** PBP's minimum order quantity (internal policy)
- **Example:** 75 units
- **When to use:** PBP sets quantity minimums for operational reasons

### 4d. MOV (PBP)
- **Type:** Currency (dollar amount)
- **Definition:** PBP's minimum order value (internal policy)
- **Example:** $2,000
- **When to use:** PBP sets dollar minimums for profitability
- **Conversion:** `MOQ = ceil(MOV / unit_price)`

---

## Calculation Rules

### Priority Order (Fallback Chain)
The system checks columns in this order:
1. **MOV (PBP)** - Convert to quantity if present
2. **MOQ (PBP)** - Use directly if present
3. **MOV (Partner)** - Convert to quantity if present
4. **MOQ (Partner)** - Use directly if present (with fallback to old "MOQ" column)
5. **Fallback** - Calculate `ceil(1000 / unit_price)` if no spreadsheet data

### MOV to MOQ Conversion Formula
```python
MOQ = math.ceil(MOV / unit_price)
```

**Example:**
- MOV = $2,000
- Unit Price = $30
- MOQ = ceil(2000 / 30) = ceil(66.67) = 67 units

### Final MOQ Calculation
```python
final_moq = max(
    moq_pbp_qty,      # MOQ (PBP) or 0
    mov_pbp_qty,      # MOV (PBP) converted to qty or 0
    moq_partner_qty,  # MOQ (Partner) or 0
    mov_partner_qty   # MOV (Partner) converted to qty or 0
)
```

**The highest value wins** - this ensures all constraints are met.

---

## Display Guidelines

### Where to Show Detailed Breakdown
**Tab 1 Product Catalog:**
```
Est. Cost & Price at MOQ: 80 units (PBP MOV: $2000 = 80 units | Also: PBP MOQ: 75, Partner MOV: $1500 = 60, Partner MOQ: 50): $25.00/unit cost → $50.00/unit client price
```

**Tab 1 Proposal Tables:**
```
MOQ: 80 units (PBP MOV: $2000 = 80 units | Also: PBP MOQ: 75, Partner MOV: $1500 = 60, Partner MOQ: 50)
```

### Where to Show Simple MOQ Only
**PowerPoint Presentations:**
```
MOQ: 80 units
```

**CSV Exports:**
```
MOQ: 80
```

**Invoices/POs:**
```
Minimum Order Quantity: 80 units
```

---

## Real-World Examples

### Example 1: All 4 Fields Present
**Spreadsheet Data:**
- MOQ (Partner) = 50 units
- MOV (Partner) = $1,500
- MOQ (PBP) = 75 units
- MOV (PBP) = $2,000
- Unit Price = $25

**Calculation:**
1. MOQ (Partner) = 50 units
2. MOV (Partner) = $1,500 / $25 = 60 units
3. MOQ (PBP) = 75 units
4. MOV (PBP) = $2,000 / $25 = 80 units

**Result:** MOQ = 80 units (from MOV PBP)

**Display:** "MOQ: 80 units (PBP MOV: $2000 = 80 units | Also: PBP MOQ: 75, Partner MOV: $1500 = 60, Partner MOQ: 50)"

---

### Example 2: Only MOQ Fields (No MOV)
**Spreadsheet Data:**
- MOQ (Partner) = 50 units
- MOV (Partner) = [empty]
- MOQ (PBP) = 75 units
- MOV (PBP) = [empty]

**Calculation:**
1. MOQ (Partner) = 50 units
2. MOQ (PBP) = 75 units

**Result:** MOQ = 75 units (from MOQ PBP)

**Display:** "MOQ: 75 units (PBP MOQ: 75 | Also: Partner MOQ: 50)"

---

### Example 3: Only MOV Fields (No MOQ)
**Spreadsheet Data:**
- MOQ (Partner) = [empty]
- MOV (Partner) = $1,500
- MOQ (PBP) = [empty]
- MOV (PBP) = $2,000
- Unit Price = $30

**Calculation:**
1. MOV (Partner) = $1,500 / $30 = 50 units
2. MOV (PBP) = $2,000 / $30 = 67 units (ceiling)

**Result:** MOQ = 67 units (from MOV PBP)

**Display:** "MOQ: 67 units (PBP MOV: $2000 = 67 units | Also: Partner MOV: $1500 = 50)"

---

### Example 4: Backward Compatibility (Old "MOQ" Column Only)
**Spreadsheet Data:**
- MOQ = 100 units (old column name)
- MOQ (Partner) = [doesn't exist]
- MOV (Partner) = [doesn't exist]
- MOQ (PBP) = [doesn't exist]
- MOV (PBP) = [doesn't exist]

**Calculation:**
1. Check MOQ (Partner) → falls back to old "MOQ" column → 100 units
2. All other fields empty

**Result:** MOQ = 100 units (from old MOQ column via fallback)

**Display:** "MOQ: 100 units (Partner MOQ: 100)"

---

### Example 5: No Spreadsheet Data (Fallback Calculation)
**Spreadsheet Data:**
- All MOQ/MOV fields = [empty]
- Unit Price = $50

**Calculation:**
1. All 4 columns empty
2. Fallback: ceil(1000 / 50) = 20 units

**Result:** MOQ = 20 units (calculated)

**Display:** "MOQ: 20 units (Calculated: $1000 / $50.00)"

---

## Integration Points

### Tab 1: Product Catalog
- **Where:** Product listing display (Section 1)
- **Usage:** Shows estimated MOQ and pricing for each product
- **Display:** Full breakdown with all contributing factors
- **Purpose:** Help users understand minimum order requirements

### Tab 1: Proposal Tables
- **Where:** Proposal preview tables (Section 3)
- **Usage:** Calculates MOQ-based pricing for each proposed product
- **Display:** Full breakdown as caption below table
- **Purpose:** Transparent pricing calculation for proposals

### Tab 1: Proposal CSV Export
- **Where:** Downloaded CSV file
- **Usage:** MOQ used for pricing calculations in export
- **Display:** Simple MOQ value only (no breakdown)
- **Purpose:** Clean export for client-facing proposals

### Tab 3: Order & Client Info
- **Where:** Manual product selection
- **Usage:** Calculates default MOQ when adding products
- **Display:** Simple MOQ value (no breakdown needed)
- **Purpose:** Set initial order quantity defaults

### Tab 4: PowerPoint Generation
- **Where:** Pricing tables in presentation slides
- **Usage:** MOQ-based pricing for slide tables
- **Display:** Simple MOQ value only
- **Purpose:** Professional, clean presentation format

---

## Edge Cases & Error Handling

### Zero or Negative Unit Price
**Scenario:** Unit price is 0 or negative
**Behavior:** MOV conversion returns 0, ignored in max() calculation
**Fallback:** Use MOQ values or calculated fallback

### Zero or Negative MOV
**Scenario:** MOV field contains 0, negative, or invalid value
**Behavior:** `parse_mov_value()` returns None, ignored
**Fallback:** Use other available MOQ/MOV fields

### Empty or Invalid Values
**Scenario:** Field is empty, "NA", or non-numeric
**Behavior:** Parse functions return None, ignored
**Fallback:** Use other available fields or calculated fallback

### String Formats
**Scenario:** MOV = "$2,000.00" (formatted currency)
**Behavior:** `clean_price()` removes $, commas → parses correctly
**Result:** 2000.0

### All Fields Empty
**Scenario:** No MOQ/MOV data in spreadsheet
**Behavior:** Fallback calculation: `ceil(1000 / unit_price)`
**Result:** Ensures every product has a valid MOQ

### MOV Ties
**Scenario:** MOV (Partner) and MOQ (PBP) both equal 75 units
**Behavior:** `max()` returns 75, first matching source wins in display
**Result:** Display shows the first source that matched the max

---

## Return Value Structure

The `calculate_moq()` function returns a dictionary with three keys:

```python
{
    'moq': 67,  # int - Final calculated MOQ
    'breakdown': {
        'moq_partner': 50,           # Raw value from spreadsheet
        'moq_partner_qty': 50,       # Converted to quantity
        'mov_partner': 1500.0,       # Raw value from spreadsheet
        'mov_partner_qty': 60,       # Converted to quantity
        'moq_pbp': 75,              # Raw value from spreadsheet
        'moq_pbp_qty': 75,          # Converted to quantity
        'mov_pbp': 2000.0,          # Raw value from spreadsheet
        'mov_pbp_qty': 80,          # Converted to quantity (WINNER)
        'source': 'MOV (PBP)',      # Which field determined the final MOQ
        'fallback_used': False      # Whether fallback calculation was used
    },
    'display_text': 'MOQ: 80 units (PBP MOV: $2000 = 80 units | Also: PBP MOQ: 75, Partner MOV: $1500 = 60, Partner MOQ: 50)'
}
```

### Key Explanations

**moq (int):**
- The final minimum order quantity to use for all calculations
- Already rounded up via `math.ceil()` for MOV conversions
- Returns None if unit price is invalid and no spreadsheet data exists

**breakdown (dict):**
- Detailed breakdown of all sources and their contributions
- Useful for debugging and understanding MOQ determination
- Shows which constraint was the binding constraint (highest value)

**display_text (str):**
- Human-readable explanation of MOQ calculation
- Shows winning source first, then other contributors
- Format: "MOQ: {value} units ({winning_source} | Also: {other_sources})"

---

## Implementation Details

### Helper Functions

**1. `parse_moq_value(value)` → int or None**
- Converts spreadsheet MOQ values (string, float, int) to integer
- Returns None for empty/invalid values
- Ensures positive integers only

**2. `parse_mov_value(value)` → float or None**
- Converts spreadsheet MOV values to float (reuses `clean_price()`)
- Handles currency formats: "$2,000.00" → 2000.0
- Returns None for empty/invalid values

**3. `convert_mov_to_moq(mov_value, unit_price)` → int**
- Formula: `math.ceil(mov_value / unit_price)`
- Returns 0 if invalid inputs (zero/negative values)
- Always rounds up to ensure minimum is met

**4. `calculate_moq(unit_price, product_data=None)` → dict**
- Main function orchestrating MOQ calculation
- Checks all 4 columns using `get_column_value()` with fallbacks
- Returns dict with moq, breakdown, display_text

### Column Fallback Pattern

```python
# New column name → Old column name → Default
moq_partner_raw = get_column_value(
    product_data,
    'MOQ (Partner)',  # Try new name first
    'MOQ',            # Fall back to old name
    None              # Default if neither exists
)
```

This ensures backward compatibility with older spreadsheets that only have "MOQ" column.

---

## Testing Checklist

When testing MOQ/MOV functionality:

- [ ] All 4 fields present → verify max wins
- [ ] Only MOQ fields → verify max wins
- [ ] Only MOV fields → verify conversion works
- [ ] Mixed MOQ and MOV → verify conversion and max
- [ ] Old "MOQ" column only → verify backward compatibility
- [ ] All fields empty → verify fallback calculation
- [ ] Zero unit price → verify MOV ignored, MOQ used
- [ ] Negative MOV values → verify treated as None
- [ ] Empty string values → verify treated as None
- [ ] Formatted currency ($2,000.00) → verify parsing works
- [ ] Tab 1 catalog display → verify breakdown shows
- [ ] Tab 1 proposal tables → verify breakdown shows
- [ ] Tab 1 CSV export → verify simple MOQ only
- [ ] PowerPoint generation → verify simple MOQ only
- [ ] Display text accuracy → verify winning source shown first

---

## Related Documentation

- **[schema_reference.md](../../schema_reference.md)** - Data structure definitions
- **[METHODOLOGY_LOGIC.md](METHODOLOGY_LOGIC.md)** - Historical pricing logic
- **[PLANNING.md](PLANNING.md)** - Project requirements and architecture
- **[src/helpers.py](../../src/helpers.py)** - Implementation code
- **[scripts/features/test_moq_mov_calculation.py](../../scripts/features/test_moq_mov_calculation.py)** - Unit tests

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 01/19/2026 | 1.0 | Initial documentation of disaggregated MOQ/MOV logic |

---

## Questions or Issues?

If you encounter unexpected MOQ calculations:

1. Check the `breakdown` dict in the return value
2. Verify which source determined the final MOQ
3. Confirm spreadsheet data is formatted correctly
4. Check unit price is positive and valid
5. Review edge case handling in this document
6. Run unit tests: `streamlit run scripts/features/test_moq_mov_calculation.py`

For questions or clarifications, refer to this document and the related code in `src/helpers.py`.
