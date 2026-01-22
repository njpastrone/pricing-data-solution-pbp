# Customization Add-Ons: PBP Cost vs Client Price Update

**Date:** 2026-01-19
**Status:** ✅ COMPLETE

## Summary

Updated the "Add Customization Option" feature in Tab 3 to distinguish between:
- **PBP Cost** (what PBP pays to the partner)
- **Client Price** (what PBP charges the client)

This brings the add-ons UI into consistency with the main customization fields.

## Changes Made

### 1. Data Structure (app.py lines 5223-5229)
**Before:**
```python
{
    'name': '',
    'setup_fee': 0.0,        # Ambiguous
    'per_unit_cost': 0.0     # Ambiguous
}
```

**After:**
```python
{
    'name': '',
    'client_setup_fee': 0.0,      # What we charge client
    'client_per_unit_cost': 0.0,  # What we charge client per unit
    'partner_setup_fee': 0.0,     # What we pay partner
    'partner_per_unit_cost': 0.0  # What we pay partner per unit
}
```

### 2. User Interface (app.py lines 5234-5301)
- **Backward compatibility migration** (lines 5235-5242): Automatically converts old add-ons
- **Restructured layout:**
  - Option Name field with remove button
  - **Client Pricing** section (2-column layout)
    - Setup Fee (to Client)
    - Per Unit Cost (to Client)
  - **Partner Cost** section (2-column layout)
    - Setup Fee (from Partner)
    - Per Unit Cost (from Partner)

### 3. Summary Display (app.py lines 5309-5335)
- Shows separate totals in 2-column format:
  - **Client Total:** $X.XX setup + $Y.YY/unit
  - **Partner Total:** $X.XX setup + $Y.YY/unit

### 4. Cost Calculations
- **Client costs** (lines 5357-5362): Includes client add-on fees in total
- **Partner costs** (lines 5381-5385): Includes partner add-on costs in total
- Both calculations include backward compatibility

### 5. Invoice Display - Tab 4 (app.py lines 7513-7548)
- **COST/UNIT & TOTAL COST:** Shows partner costs
- **SELL PRICE/UNIT & TOTAL SELL PRICE:** Shows client prices
- Backward compatibility for old field names

## Benefits

✅ **Complete transparency** - Clear distinction between costs and prices  
✅ **Profit visibility** - Shows markup on add-on customizations  
✅ **Consistency** - Matches existing main customization pattern  
✅ **Backward compatible** - Existing add-ons migrate automatically  
✅ **Invoice accuracy** - Proper cost vs price columns in Tab 4  

## Testing Instructions

1. **Navigate to Tab 3** (Order & Client Info)
2. **Add a product** to the order
3. **Enable customization** for the product
4. **Click "Add Customization Option"**
5. **Verify new UI:**
   - Enter option name (e.g., "Second Color")
   - Enter Client Setup Fee: $100
   - Enter Client Per Unit Cost: $3.00
   - Enter Partner Setup Fee: $50
   - Enter Partner Per Unit Cost: $2.00
6. **Verify summary shows:**
   - Client Total: $100.00 setup + $3.00/unit
   - Partner Total: $50.00 setup + $2.00/unit
7. **Check Tab 3 Section 4** (Order Summary) - verify costs
8. **Navigate to Tab 4** (Execution & Accounting)
9. **Verify invoice** shows:
   - COST columns: Partner costs ($50 setup, $2/unit)
   - SELL PRICE columns: Client prices ($100 setup, $3/unit)

## Migration Notes

**Backward Compatibility:**
- Old add-ons with `setup_fee` and `per_unit_cost` automatically migrate to new format
- Old values become `client_setup_fee` and `client_per_unit_cost`
- Partner fields default to $0.00
- No data loss occurs during migration

## Files Modified

- `app.py` (5 locations):
  - Lines 5223-5229: Add-on initialization
  - Lines 5234-5301: Add-on UI
  - Lines 5309-5335: Add-on summary
  - Lines 5357-5362 & 5381-5385: Cost calculations
  - Lines 7513-7548: Invoice display

## Version

This update is part of the January 2026 improvements addressing the distinction between PBP costs and client prices throughout the application.
