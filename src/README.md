# Source Code Modules

This directory contains business logic extracted from app.py for better organization and maintainability.

## Modules

### `helpers.py`
**Purpose:** Utility functions for data processing and calculations

**Functions:**
- `clean_price()` - Convert price strings to floats
- `apply_marketing_rounding()` - Charm pricing ($60 → $59)
- `round_to_nearest_five()` - Round to nearest $5
- `calculate_moq()` - Calculate minimum order quantity
- `calculate_credit_card_fee()` - Calculate CC processing fee
- `extract_partner_contacts()` - Parse partner contact info from DataFrame
- `validate_invoice_completeness()` - Check required fields before export
- `parse_tier_info()` - Parse tier ranges from string
- `parse_tariff_rate()` - Parse tariff percentage
- `calculate_product_tariff()` - Calculate tariff on product cost

**Usage:**
```python
from src.helpers import clean_price, parse_tier_info

price = clean_price("$48.00")  # Returns 48.0
tiers = parse_tier_info("T1: 1-25, T2: 26-50")  # Returns {1: (1, 25), 2: (26, 50)}
```

---

### `data_loader.py`
**Purpose:** Google Sheets integration and data loading

**Functions:**
- `connect_to_sheets()` - Establish Google Sheets API connection (cached)
- `load_pricing_data()` - Load all 3 sheets from master_pricing_template_10_14 (5-min cache)

**Returns:**
- `df_template` - Product pricing data (header at row 6)
- `df_metadata` - Field definitions (header at row 2)
- `df_partner_info` - Partner contacts (header at row 2)

**Usage:**
```python
from src.data_loader import load_pricing_data

df_template, df_metadata, df_partner_info = load_pricing_data()
```

---

### `pricing_engine.py`
**Purpose:** Pricing calculations and quote generation

**Functions:**
- `determine_tier_number()` - Map quantity to tier number (1-6)
- `get_unit_price_new_system()` - Get price based on tier/flat logic (NEW SYSTEM)
- `get_price_for_quantity()` - Get price based on quantity (OLD SYSTEM - deprecated)
- `calculate_customization_costs()` - Calculate setup fees and per-unit costs (NEW SYSTEM)
- `calculate_additional_costs()` - Calculate label/setup costs (OLD SYSTEM - deprecated)
- `calculate_product_quote()` - Complete quote for single product
- `calculate_order_total()` - Multi-product order total with shipping/tariff

**Usage:**
```python
from src.pricing_engine import calculate_product_quote, calculate_order_total

# Calculate quote for single product
quote = calculate_product_quote(
    row=product_row,
    quantity=100,
    markup_percent=50,
    include_customization=True,
    customization_minimum=100
)

# Calculate order total with multiple products
summary = calculate_order_total(
    order_items=[item1, item2],
    shipping=100,
    order_tariff=200,
    discount_percent=5.0
)
```

**Status:** ✅ Complete (7 functions extracted)

---

## Migration Status

**Phase 2 Progress:**
- ✅ helpers.py - Complete (13 functions extracted)
- ✅ data_loader.py - Complete (2 functions extracted)
- ✅ pricing_engine.py - Complete (7 functions extracted)
- ⏳ app.py refactor - In Progress (update imports, remove extracted functions)

**Next Steps:**
1. Extract pricing engine functions from app.py
2. Update app.py to import from src/ modules
3. Remove duplicated functions from app.py
4. Test refactored app to ensure functionality preserved
5. Update documentation with new import patterns

---

## Development Guidelines

**When adding new functions:**
1. Place in appropriate module based on responsibility
2. Add comprehensive docstrings with examples
3. Follow existing naming conventions
4. Keep functions small and focused (single responsibility)
5. Update this README with new function descriptions

**Module Responsibilities:**
- `helpers.py` - Pure utility functions, no business logic
- `data_loader.py` - Data fetching and DataFrame processing only
- `pricing_engine.py` - All pricing calculations and business rules
- `app.py` - UI components and Streamlit interactions only

---

**Last Updated:** 2025-10-27
**Version:** 0.1 (Partial extraction)
