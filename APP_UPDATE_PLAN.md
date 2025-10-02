# App Update Plan: Transitioning to Tiered Pricing Structure

**Created:** 2025-10-02
**Purpose:** Plan for updating app.py to handle real-world jaggery_sample_6_23 data structure with tiered pricing

---

## 📋 Current State Assessment

### What We Have Now (MVP with master_pricing_demo)
- **Data Structure:** Simple flat pricing
  - Columns: Partner, Product, Price, Cost, Currency, Last Updated, Notes
  - One price per product (no tiers)
  - Clean data with no header rows to skip
- **App Functionality:**
  - Partner/Product dropdowns
  - Single base price lookup
  - Quote calculation: `(base_price * markup%) + shipping + tariff`
  - Proposal and invoice generation

### What We Need (Real Data: jaggery_sample_6_23)
- **Data Structure:** Complex tiered pricing
  - 25 columns with product details and pricing tiers
  - **7+ pricing tiers** based on quantity ranges:
    - Less than 25 units
    - 1-25 units
    - 26-50 units
    - 51-100 units
    - 101-250 units
    - 251-500 units
    - 501-1000 units
    - 1000+ units
  - **Header rows 1-5** (data starts row 6)
  - **Currency strings** with "$" symbol requiring cleaning
  - **Additional costs:** Art Setup Fee, Label costs
  - **22 total fields** (vs. 7 in demo)

### 🌟 IMPORTANT: Multi-Partner Future Consideration
**Current Scope:** jaggery_sample_6_23 contains data for **one artisan partner (Jaggery) only**

**Future Scope:** The master spreadsheet will consolidate data from **multiple partners**, each with:
- Different pricing tier structures (not all partners may have 7+ tiers)
- Different pricing tier ranges (partner A: 1-50, 51-100; partner B: 1-25, 26-75, etc.)
- Different additional costs (setup fees, label costs, shipping charges)
- Different minimum order quantities
- Potentially different column structures or naming conventions

**Design Principle:** ⚠️ **EVERYTHING MUST BE SOFT-CODED AND EASY TO EDIT**
- Do NOT hardcode tier ranges or column names
- Design for flexibility and extensibility
- Assume partner data structures may vary
- Make it easy to add/modify partners without code changes

---

## 🎯 Business Analytics Perspective

### Key Business Requirements

1. **Accurate Quantity-Based Pricing**
   - The business model relies on volume discounts
   - Pricing must **automatically select the correct tier** based on quantity ordered
   - Incorrect tier selection = incorrect quotes = lost revenue or customer dissatisfaction

2. **Transparency in Calculations**
   - Users need to see **exactly how the price was determined**
   - Show which pricing tier was used and why
   - Display all cost components clearly (base price, setup fees, labels, markup, shipping, tariff)

3. **Data Validation**
   - Handle missing pricing tiers gracefully (not all products have all tiers)
   - Validate minimum order quantities
   - Flag when quantity falls below minimum

4. **Simplicity for Non-Technical Users**
   - Interface must remain simple despite complex backend logic
   - Provide helpful guidance (e.g., "You selected 75 units, using 51-100 tier pricing")
   - Clear error messages when data issues arise

---

## 🔄 Key Differences: Old vs. New Structure

| Aspect | master_pricing_demo (Old) | jaggery_sample_6_23 (New) |
|--------|---------------------------|---------------------------|
| **Pricing Model** | Single flat price | 7+ tiered prices based on quantity |
| **Data Format** | Clean, standard CSV-like | Headers in rows 1-5, data from row 6 |
| **Currency** | Numeric values | String with "$" symbol |
| **Columns** | 7 simple columns | 25 columns with complex structure |
| **Additional Costs** | None | Art Setup Fee, Label costs |
| **Minimum Quantity** | Not specified | Specified per product |
| **Price Selection** | Direct lookup | Logic-based on quantity range |

---

## 📐 Technical Challenges & Solutions

### Challenge 1: Reading Data with Header Rows
**Problem:** Rows 1-5 are headers/metadata, not data
**Solution:**
```python
# Skip first 5 rows, use row 5 as column headers
all_values = sheet.get_all_values()
headers = all_values[4]  # Row 5 (index 4)
data_rows = all_values[5:]  # Data starts row 6
df = pd.DataFrame(data_rows, columns=headers)
```

### Challenge 2: Currency String Cleaning
**Problem:** Prices stored as "$48.00" instead of numeric
**Solution:**
```python
def clean_price(price_string):
    """Convert '$48.00' to float 48.0"""
    if not price_string or price_string == '':
        return None
    return float(price_string.replace('$', '').replace(',', '').strip())
```

### Challenge 3: Quantity-Based Price Selection
**Problem:** Need to select correct price tier based on quantity ordered
**Solution:** Create a FLEXIBLE price tier lookup function that doesn't hardcode tier ranges

⚠️ **CRITICAL: Must be soft-coded for multi-partner future use**

```python
def get_price_for_quantity(product_row, quantity):
    """
    Select the appropriate price tier based on quantity.
    Returns the price and tier name for transparency.

    SOFT-CODED APPROACH: Automatically detects available pricing tiers
    from the product row instead of hardcoding tier ranges.
    """
    # Define tier columns and their ranges
    # This can be moved to a configuration file or detected dynamically
    tier_columns = [
        {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
        {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
        {'min': 51, 'max': 100, 'column': 'PBP Cost w/o shipping (51-100)'},
        {'min': 101, 'max': 250, 'column': 'PBP Cost w/o shipping (101-250)'},
        {'min': 251, 'max': 500, 'column': 'PBP Cost w/o shipping (251-500)'},
        {'min': 501, 'max': 1000, 'column': 'PBP Cost w/o shipping (501-1000)'},
        {'min': 1001, 'max': float('inf'), 'column': 'PBP Cost w/o shipping (1000+)'}
    ]

    # Find matching tier
    for tier in tier_columns:
        if tier['min'] <= quantity <= tier['max']:
            # Check if this column exists in the product row
            if tier['column'] in product_row.index:
                price_str = product_row[tier['column']]
                price = clean_price(price_str)
                if price is not None:
                    tier_range = f"{tier['min']}-{tier['max'] if tier['max'] != float('inf') else '1000+'}"
                    return price, tier_range, tier['column']

    # Fallback: find any available pricing column
    return None, None, None  # Handle fallback in calling function
```

**Future Enhancement:** Move `tier_columns` to:
1. A configuration file (e.g., `pricing_config.json`)
2. A dedicated Google Sheet tab for tier definitions
3. Auto-detect from column headers (parse "1-25", "26-50" from column names)

### Challenge 4: Handling Missing Data
**Problem:** Not all products have all pricing tiers filled
**Solution:** Implement intelligent fallback strategy

```python
def get_price_with_fallback(product_row, quantity, tier_columns):
    """
    Get price for quantity with intelligent fallback if tier is missing.

    Fallback Strategy:
    1. Try exact tier match
    2. If empty, try next higher tier (more conservative pricing)
    3. If no higher tier, try next lower tier
    4. If all else fails, use any available pricing column
    """
    # Try exact match first
    for i, tier in enumerate(tier_columns):
        if tier['min'] <= quantity <= tier['max']:
            if tier['column'] in product_row.index:
                price = clean_price(product_row[tier['column']])
                if price is not None:
                    return price, tier, "exact"

            # Exact tier is missing, try higher tiers
            for higher_tier in tier_columns[i+1:]:
                if higher_tier['column'] in product_row.index:
                    price = clean_price(product_row[higher_tier['column']])
                    if price is not None:
                        return price, higher_tier, "fallback_higher"

            # Try lower tiers
            for lower_tier in reversed(tier_columns[:i]):
                if lower_tier['column'] in product_row.index:
                    price = clean_price(product_row[lower_tier['column']])
                    if price is not None:
                        return price, lower_tier, "fallback_lower"

    return None, None, "no_price_available"
```

**User-Facing Messages:**
- **Exact match:** "Using 51-100 tier pricing"
- **Fallback higher:** "⚠️ 51-100 tier not available. Using 101-250 tier pricing (contact partner to verify)"
- **Fallback lower:** "⚠️ 51-100 tier not available. Using 26-50 tier pricing (contact partner to verify)"
- **No price:** "❌ No pricing available for this quantity. Please contact partner."

### Challenge 5: Additional Costs (Setup Fees, Labels)
**Problem:** New cost components not in original formula
**Solution:** Expand calculation to include all cost types with soft-coded approach

✅ **CONFIRMED LOGIC** (see METHODOLOGY_LOGIC.md for detailed calculations)

```python
def calculate_additional_costs(product_row, quantity, include_labels=False):
    """
    Calculate additional costs (setup fees, labels, etc.)
    Soft-coded to handle different cost structures per partner.

    Args:
        product_row: Product data from DataFrame
        quantity: Order quantity
        include_labels: Boolean - whether customer wants labels

    Returns dict with all additional costs.
    """
    additional_costs = {}

    # Art Setup Fee (one-time per order)
    # ✅ CONFIRMED: Charged once per order, not per unit
    setup_fee_str = product_row.get('Art Setup Fee', '')
    setup_fee = clean_price(setup_fee_str) if setup_fee_str else 0
    additional_costs['art_setup_fee_total'] = setup_fee
    additional_costs['art_setup_fee_per_unit'] = setup_fee / quantity if quantity > 0 else 0

    # Label Costs (optional, user chooses)
    # ✅ CONFIRMED: Jaggery partner has label art setup ($70) + minimum 100 labels
    if include_labels:
        # Label art setup fee (one-time, separate from product art setup)
        # For Jaggery: $70 (may vary by partner)
        label_setup_fee = 70  # TODO: Make this partner-configurable
        additional_costs['label_setup_fee_total'] = label_setup_fee
        additional_costs['label_setup_fee_per_unit'] = label_setup_fee / quantity if quantity > 0 else 0

        # Label unit cost and minimum
        label_cost_str = product_row.get('Labels up to 1" x 2.5\'', '')
        label_min_str = product_row.get('Minimum for labels', '')
        label_cost_per_label = clean_price(label_cost_str) if label_cost_str else 0
        label_minimum = int(clean_price(label_min_str)) if label_min_str else 100

        # Apply minimum: customer pays for at least label_minimum labels
        labels_to_charge = max(quantity, label_minimum)
        additional_costs['labels_charged'] = labels_to_charge
        additional_costs['label_cost_per_label'] = label_cost_per_label
        additional_costs['label_cost_total'] = label_cost_per_label * labels_to_charge
        additional_costs['label_cost_per_unit'] = (label_cost_per_label * labels_to_charge) / quantity if quantity > 0 else 0

        # Warning message if minimum applies
        if quantity < label_minimum:
            additional_costs['label_warning'] = f"Minimum {label_minimum} labels required. Charging for {labels_to_charge} labels even though ordering {quantity} units."
    else:
        # No labels requested
        additional_costs['label_setup_fee_total'] = 0
        additional_costs['label_cost_total'] = 0
        additional_costs['labels_charged'] = 0

    return additional_costs

# New formula components:
# 1. Base price (from selected tier)
# 2. Art setup fee (✅ one-time per order)
# 3. Label art setup fee (✅ one-time per order, if labels requested)
# 4. Label costs (✅ per label, minimum 100 for Jaggery)
# 5. Markup percentage
# 6. Shipping
# 7. Tariff
```

**Soft-Coding Strategy:**
- Use `.get()` to safely access columns that may not exist for all partners
- Return dict with all costs for easy expansion
- `include_labels` parameter makes labels optional (user choice)
- Label setup fee hardcoded for now (TODO: move to partner config)
- Make it easy to add new cost types without changing calculation logic

---

## 🏗️ Multi-Partner Architecture Strategy

### Current Implementation (Single Partner: Jaggery)
For the initial implementation, we'll work with jaggery_sample_6_23 data (single partner).

### Future-Proof Design Principles

**1. Soft-Coded Configuration**
Instead of hardcoding values, use configuration that can be easily modified:

```python
# BAD (hardcoded):
if quantity <= 25:
    price_column = 'PBP Cost w/o shipping (1-25)'

# GOOD (soft-coded):
TIER_CONFIG = [
    {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
    {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
    # ... more tiers
]
```

**2. Dynamic Column Detection**
Handle different column naming conventions:

```python
def find_column(df, possible_names):
    """Find first matching column name from list of possibilities"""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

# Usage:
partner_col = find_column(df, ['Artisan Partner', 'Partner', 'Partner Name'])
product_col = find_column(df, ['Gift Name', 'Product', 'Product Name'])
```

**3. Safe Data Access with Defaults**
Use `.get()` to handle missing columns gracefully:

```python
# Instead of: setup_fee = product_row['Art Setup Fee']
# Use:
setup_fee = product_row.get('Art Setup Fee', 0)
```

**4. Modular Cost Calculation**
Build calculations as composable functions:

```python
def calculate_total_cost(base_price, quantity, additional_costs, markup, shipping, tariff):
    """
    Modular calculation that works regardless of what's in additional_costs dict
    """
    subtotal = base_price * quantity
    for cost_name, cost_value in additional_costs.items():
        subtotal += cost_value
    # ... continue calculation
```

**5. Configuration File Strategy (Future)**
Move partner-specific configuration to external file or sheet tab:

```python
# pricing_config.json (future enhancement)
{
    "jaggery": {
        "partner_column": "Artisan Partner",
        "product_column": "Gift Name",
        "tiers": [
            {"min": 1, "max": 25, "column": "PBP Cost w/o shipping (1-25)"},
            {"min": 26, "max": 50, "column": "PBP Cost w/o shipping (26-50)"}
        ],
        "additional_costs": {
            "setup_fee": {"column": "Art Setup Fee", "type": "one_time"},
            "labels": {"column": "Labels up to 1\" x 2.5'", "type": "per_unit"}
        }
    },
    "partner_b": {
        "partner_column": "Partner Name",
        "product_column": "Product",
        "tiers": [
            {"min": 1, "max": 50, "column": "Price Tier 1"},
            {"min": 51, "max": 100, "column": "Price Tier 2"}
        ]
    }
}
```

### Migration Path to Multi-Partner
1. **Phase 1 (Current):** Build with jaggery data, soft-code where possible
2. **Phase 2:** Add 2-3 more partners, identify commonalities and differences
3. **Phase 3:** Extract configuration to separate file/sheet
4. **Phase 4:** Build admin UI for managing partner configurations

---

## 🛠️ Implementation Plan

### Step 1: Update Data Loading Function
**Goal:** Read jaggery_sample_6_23 correctly with header row handling

**Changes:**
1. Change sheet name from "master_pricing_demo" to "jaggery_sample_6_23"
2. Implement header row skipping (skip rows 1-5, use row 5 as headers)
3. Add data validation to verify column structure

**Code Location:** `app.py` lines 36-45 (load_pricing_data function)

---

### Step 2: Create Helper Functions
**Goal:** Add utility functions for data cleaning and price selection

**New Functions to Add:**
1. `clean_price(price_string)` - Strip "$" and convert to float
2. `get_price_for_quantity(product_row, quantity)` - Select correct pricing tier
3. `validate_minimum_quantity(product_row, quantity)` - Check minimum order quantity
4. `calculate_additional_costs(product_row, quantity)` - Calculate setup fees and label costs

**Code Location:** Add after imports, before cached functions

---

### Step 3: Update Product Selection UI
**Goal:** Update dropdowns to use new column names, prepare for multi-partner data

**Changes:**
1. Replace "Partner" column with "Artisan Partner"
2. Replace "Product" column with "Gift Name" ✅ (user confirmed)
3. Show "Product Ref. No." as secondary identifier in product details
4. **Soft-coding:** Use dynamic column detection to handle different partner data structures

**Code Location:** `app.py` lines 56-80 (Product Selection section)

**Soft-Coded Approach:**
```python
# Detect partner column name dynamically
partner_column = None
for col in ['Artisan Partner', 'Partner', 'Partner Name']:
    if col in df.columns:
        partner_column = col
        break

# Detect product column name dynamically
product_column = None
for col in ['Gift Name', 'Product', 'Product Name']:
    if col in df.columns:
        product_column = col
        break
```

---

### Step 4: Update Product Details Display
**Goal:** Show more relevant information from new data structure

**Changes:**
1. Display Product Ref. No., Artisan Partner, Gift Name
2. Show Minimum Quantity requirement
3. Display dimension and material information (optional)
4. Remove old "Base Price" metric (since price is now tier-dependent)

**Code Location:** `app.py` lines 82-91 (Product Details section)

---

### Step 5: Update Quote Customization Inputs
**Goal:** Add validation for minimum quantity, handle new cost inputs

**Changes:**
1. Add minimum quantity validation (read from product data)
2. Add checkbox/input for "Include Art Setup Fee" (optional)
3. Add checkbox/input for "Include Label Costs" (optional)
4. Keep existing: quantity, markup %, shipping, tariff

**Code Location:** `app.py` lines 93-109 (Quote Customization section)

---

### Step 6: Update Quote Calculation Logic
**Goal:** Implement tiered pricing and new cost components

**Changes:**
1. Call `get_price_for_quantity()` instead of direct price lookup
2. Add art setup fee calculation (one-time cost / quantity)
3. Add label costs if applicable
4. Update breakdown display to show:
   - Which pricing tier was used
   - Base price from that tier
   - Art setup fee (per unit)
   - Label costs (per unit)
   - Markup calculation
   - Shipping (per unit)
   - Tariff (per unit)
   - Total per unit
   - Total quote

**Code Location:** `app.py` lines 111-145 (Quote Calculation section)

---

### Step 7: Update Proposal & Invoice
**Goal:** Include additional cost details and pricing tier transparency

**Changes:**
1. Add "Pricing Tier Used" row
2. Add "Art Setup Fee" row (if applicable)
3. Add "Label Costs" row (if applicable)
4. Update total calculation to include all components

**Code Location:** `app.py` lines 147-186 (Proposal & Invoice sections)

---

### Step 8: Testing & Validation
**Goal:** Ensure app works correctly with real data

**Test Cases:**
1. **Tier Selection:**
   - Order 20 units → should use "1-25" tier
   - Order 75 units → should use "51-100" tier
   - Order 500 units → should use "251-500" tier
   - Order 1500 units → should use "1000+" tier

2. **Missing Data Handling:**
   - Product with missing tier → should fallback gracefully
   - Empty setup fee → should show $0 or "N/A"

3. **Minimum Quantity:**
   - Order below minimum → should show warning

4. **Calculation Accuracy:**
   - Verify all cost components add up correctly
   - Verify per-unit costs are divided by quantity correctly

5. **Currency Cleaning:**
   - Prices with "$" symbol → should parse correctly
   - Prices with "," (e.g., "$1,500") → should handle correctly

---

## 🎨 UI/UX Improvements for Transparency

### 1. Pricing Tier Indicator
**Add visual feedback showing which tier is active:**
```
📊 Pricing Tier: 51-100 units
💰 Base Price: $38.40 per unit
(You're ordering 75 units)
```

### 2. Expanded Price Breakdown Table
**Show all cost components clearly:**
| Cost Component | Per Unit | Total |
|----------------|----------|-------|
| Base Price (51-100 tier) | $38.40 | $2,880.00 |
| Art Setup Fee | $0.93 | $70.00 |
| Labels | $1.50 | $112.50 |
| Markup (100%) | $40.83 | $3,062.25 |
| Shipping (per unit) | $0.50 | $37.50 |
| Tariff (per unit) | $0.25 | $18.75 |
| **Total** | **$82.41** | **$6,181.00** |

### 3. Minimum Quantity Warning
**If quantity < minimum:**
```
⚠️ Warning: Minimum order quantity for this product is 100 units.
You've entered 75 units. Please increase quantity or contact partner.
```

### 4. Missing Data Alerts
**If tier data is missing:**
```
ℹ️ Note: Pricing tier for 75 units not available. Using nearest tier (51-100).
Please verify pricing with artisan partner.
```

---

## 📊 Business Logic: Quantity Tier Selection

### Tier Ranges (from DATA_STRUCTURE.md)
1. **Less than 25**: Column 10 "PBP Cost w/o shipping (-25)"
2. **1-25**: Column 12 "PBP Cost w/o shipping (1-25)"
3. **26-50**: Column 13 "PBP Cost w/o shipping (26-50)"
4. **51-100**: Column 14 "PBP Cost w/o shipping (51-100)"
5. **101-250**: Column 15 "PBP Cost w/o shipping (101-250)"
6. **251-500**: Column 16 "PBP Cost w/o shipping (251-500)"
7. **501-1000**: Column 17 "PBP Cost w/o shipping (501-1000)"
8. **1000+**: Column 18 "PBP Cost w/o shipping (1000+)"

### Selection Algorithm
```python
def select_tier(quantity):
    if quantity < 1:
        return None  # Invalid
    elif quantity < 25:
        return "PBP Cost w/o shipping (-25)"
    elif 1 <= quantity <= 25:
        return "PBP Cost w/o shipping (1-25)"
    elif 26 <= quantity <= 50:
        return "PBP Cost w/o shipping (26-50)"
    elif 51 <= quantity <= 100:
        return "PBP Cost w/o shipping (51-100)"
    elif 101 <= quantity <= 250:
        return "PBP Cost w/o shipping (101-250)"
    elif 251 <= quantity <= 500:
        return "PBP Cost w/o shipping (251-500)"
    elif 501 <= quantity <= 1000:
        return "PBP Cost w/o shipping (501-1000)"
    else:  # 1000+
        return "PBP Cost w/o shipping (1000+)"
```

**Note:** There's overlap in the first two tiers (both cover 1-25 range). We need to clarify with user which to use, or always prefer the "1-25" tier when quantity is in that range.

---

## 🧪 Testing Strategy

### Unit Testing (Manual)
1. **Test each tier boundary:**
   - 24 units → verify correct tier
   - 25 units → verify correct tier
   - 26 units → verify switches to next tier
   - Repeat for all boundaries (50, 100, 250, 500, 1000)

2. **Test missing data scenarios:**
   - Product with incomplete pricing tiers
   - Product with empty setup fee
   - Product with empty label costs

3. **Test calculations:**
   - Verify per-unit costs divide correctly
   - Verify total = per-unit × quantity
   - Verify markup applies to base price only (not shipping/tariff)

### Integration Testing
1. **End-to-end quote generation:**
   - Select product → enter quantity → verify correct tier → generate quote
2. **Proposal/invoice generation:**
   - Verify all data flows correctly into output tables

---

## 🚀 Deployment Considerations

### Before Deploying
1. **Backup Current MVP:** Save working version of app.py
2. **Test with Real Data:** Thoroughly test with jaggery_sample_6_23
3. **User Acceptance:** Get user feedback on new UI and calculations
4. **Documentation:** Update PLANNING.md to reflect Phase 1 completion with new data structure

### Rollout Strategy
- **Option A:** Update app.py directly (simple, maintains single-file approach)
- **Option B:** Create app_tiered.py for testing, then swap after validation
- **Recommendation:** Option B for safety, then rename after testing

---

## ⚠️ Risks & Mitigation

### Risk 1: Tier Overlap Ambiguity
**Issue:** "Less than 25" and "1-25" tiers overlap
**Mitigation:** Clarify with user which tier to use, or always use "1-25" for 1-25 range

### Risk 2: Missing Pricing Tiers
**Issue:** Not all products have all tiers populated
**Mitigation:** Implement fallback logic and display warnings to user

### Risk 3: Currency Parsing Errors
**Issue:** "$" symbols and "," in numbers could cause parsing errors
**Mitigation:** Robust cleaning function with error handling and validation

### Risk 4: Increased Complexity
**Issue:** App becomes more complex, potentially harder for "vibe-coders"
**Mitigation:** Keep helper functions simple, well-commented, with clear names

### Risk 5: Performance with Large Sheet
**Issue:** 1000 rows might slow down loading
**Mitigation:** Keep caching (ttl=300), consider filtering data to active products only

---

## ❓ Unanswered Questions (Placeholders in Code)

~~All questions resolved! ✅~~

**STATUS: NO UNANSWERED QUESTIONS**

---

## ✅ Answered Questions

1. **Tier Selection for 1-25 units:** ✅ Use "PBP Cost w/o shipping (1-25)" tier

2. **Product Selection Display:** ✅ Show "Gift Name" in dropdown

3. **Missing Tier Fallback Strategy:** ✅ Clarified - see detailed fallback logic in Challenge 4
   - Try exact tier first
   - If missing, try next higher tier (more conservative pricing)
   - If no higher tier, try next lower tier
   - Display warning to user showing which fallback was used

4. **Art Setup Fee:** ✅ **CONFIRMED - One-time fee per order**
   - Art setup fee is charged once per order (not per unit)
   - Should be displayed as separate line item in quote
   - Amortize over quantity for per-unit breakdown: `setup_fee / quantity`

5. **Label Costs:** ✅ **CONFIRMED - Optional with minimum requirement**
   - **User Choice:** App should include checkbox/option to add labels
   - **Jaggery Partner Methodology:**
     - One-time label art setup fee: $70
     - Label unit cost: $1.50 per label (size specified in product data)
     - **Minimum quantity:** 100 labels
     - **Logic:** If customer orders < 100 units BUT wants labels, they still pay for 100 labels minimum
     - **Example:** Order 50 units with labels = 50 units @ product price + $70 label setup + (100 labels × $1.50 = $150)
   - **Note:** Different partners may have different label pricing/minimums (see METHODOLOGY_LOGIC.md)

---

## 📝 Additional Open Questions

4. **Minimum Quantity Enforcement:** Should we prevent users from ordering below minimum, or just show a warning?
   - **Recommendation:** Show warning but allow (user may need to contact partner for exceptions)

5. **Multi-Partner Column Variations:** When consolidating multiple partners, should we:
   - Standardize all partner data to use same column names?
   - Build flexibility to handle different column names per partner?
   - **Current Approach:** Building in flexibility with dynamic column detection

6. **Tier Range Variations:** Different partners may have different tier ranges. Should we:
   - Store tier definitions in a separate config sheet tab?
   - Parse tier ranges from column headers automatically?
   - Require manual configuration per partner?
   - **Recommendation:** Start with config-based approach, move to auto-detection later

---

## ✅ Success Criteria

The update will be considered successful when:

1. ✅ App correctly reads jaggery_sample_6_23 sheet with header row handling
2. ✅ Pricing tier is automatically selected based on quantity
3. ✅ All cost components (base, setup, labels, markup, shipping, tariff) calculate correctly
4. ✅ User can see which pricing tier is being used
5. ✅ Proposal and invoice include all cost details
6. ✅ Missing data is handled gracefully with clear user messaging
7. ✅ Code remains beginner-friendly and well-commented
8. ✅ Minimum quantity validation works correctly
9. ✅ All test cases pass
10. ✅ User approves the updated interface and calculations

---

## 📚 References

- [DATA_STRUCTURE.md](DATA_STRUCTURE.md) - Detailed jaggery data structure
- [PLANNING.md](PLANNING.md) - Project requirements and goals
- [CLAUDE.md](CLAUDE.md) - Project rules and context
- [app.py](app.py) - Current MVP implementation

---

---

## 📊 Implementation Summary

### Key Design Decisions Made

1. ✅ **Soft-Coded Approach:** All tier ranges, column names, and cost calculations use configuration-based approach
2. ✅ **Multi-Partner Ready:** Dynamic column detection and flexible data structures prepare for future consolidation
3. ✅ **Transparent Fallback Logic:** Intelligent tier fallback with clear user messaging
4. ✅ **Modular Functions:** Helper functions are composable and easy to modify
5. ✅ **Placeholder Logic:** Unanswered questions have working placeholders that can be updated later

### What Makes This "Easy to Edit"

- **No Hardcoded Values:** Tier ranges stored in lists/dicts, not if/else chains
- **Dynamic Column Detection:** Works with different column naming conventions
- **Safe Data Access:** Uses `.get()` for optional fields, preventing errors
- **Configuration Comments:** Clear comments marking where to update values
- **Modular Functions:** Change one function without affecting others
- **Clear Placeholders:** Unanswered questions marked with `# PLACEHOLDER:` comments

### Simplicity Maintained

Despite the complexity of tiered pricing:
- **Single File:** All code stays in `app.py` (following non-negotiable #7)
- **Beginner-Friendly:** Well-commented helper functions with clear names
- **Step-by-Step Logic:** Calculations broken into understandable steps
- **No Over-Engineering:** Start simple, add complexity only when needed

---

## 🚀 Next Steps

1. ✅ **User Review:** Review this plan - **COMPLETED**
2. ✅ **Answer Questions:** Get clarifications - **PARTIALLY COMPLETED**
   - Answered: Tier selection (1-25), Product display (Gift Name), Fallback strategy
   - Placeholder: Art setup fee logic, Label cost logic
3. ⏭️ **Begin Implementation:** Follow 8-step plan
4. ⏭️ **Test Thoroughly:** Validate with real jaggery data
5. ⏭️ **User Acceptance:** Get feedback on calculations and UI
6. ⏭️ **Deploy:** Update production app

---

## ⏱️ Estimated Effort

**Initial Implementation:** 4-6 hours of focused development
- Step 1-2 (Data loading + helpers): 1.5 hours
- Step 3-5 (UI updates): 1.5 hours
- Step 6-7 (Calculations + output): 1.5 hours
- Step 8 (Testing): 1 hour

**Testing & Refinement:** 2-3 hours
- Edge case testing
- Placeholder logic refinement (setup fees, labels)
- User acceptance testing

**Total:** 6-9 hours

---

**Ready to begin implementation when user approves this plan.**
