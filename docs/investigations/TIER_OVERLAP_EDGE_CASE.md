# Tier Overlap Edge Case Analysis

**Date:** 2026-01-26
**Issue:** Tiered pricing parser doesn't correctly handle overlapping tier ranges
**Status:** Bug Confirmed
**Severity:** High - Causes incorrect pricing for products in overlap zones

---

## Problem Statement

When tier ranges overlap in the spreadsheet (e.g., `T2: 448-1107, T3: 1008+`), the tier selection algorithm returns the **wrong tier** for quantities in the overlap zone.

**Example Tier String:**
```
T1: 112-447, T2: 448-1107, T3: 1008+
```

**Overlap Zone:** Units 1008-1107 (100 units) are covered by **both T2 and T3**

---

## Root Cause Analysis

### 1. Data Quality Issue (Primary)

The tier ranges in the spreadsheet have overlapping boundaries:
- T2 ends at **1107**
- T3 starts at **1008**
- Overlap: 1008-1107 (100 units affected)

**Expected:**
- T2 should be: `448-1107`
- T3 should be: `1108+` (not `1008+`)

### 2. Code Issue (Secondary)

The tier selection algorithm in `src/pricing_engine.py::determine_tier_number()` checks tiers **in order** and returns the **first match**:

```python
for tier_num, (min_qty, max_qty) in tier_ranges.items():
    if min_qty <= quantity <= max_qty:
        return tier_num  # Returns first match, stops checking
```

**For quantity 1008:**
1. Check T1 (112-447): `112 <= 1008 <= 447`? **NO**
2. Check T2 (448-1107): `448 <= 1008 <= 1107`? **YES** ← Returns T2 and stops
3. T3 (1008+): Never checked!

**Result:** Quantity 1008 incorrectly returns **T2** when it should return **T3**

---

## Test Results

### Confirmed Failures

| Quantity | Expected | Actual | Status | Notes |
|----------|----------|--------|--------|-------|
| 447 | T1 | T1 | ✓ PASS | Last unit of T1 |
| 448 | T2 | T2 | ✓ PASS | First unit of T2 |
| 1007 | T2 | T2 | ✓ PASS | Last unit before overlap |
| **1008** | **T3** | **T2** | **✗ FAIL** | First unit of T3 |
| **1050** | **T3** | **T2** | **✗ FAIL** | Mid-overlap zone |
| **1107** | **T3** | **T2** | **✗ FAIL** | Last unit of overlap |
| 1108 | T3 | T3 | ✓ PASS | First unit after T2 ends |
| 2000 | T3 | T3 | ✓ PASS | Well into T3 |

**Summary:** 3 failures out of 8 tests (37.5% failure rate in overlap zone)

---

## Impact Analysis

### Business Impact

**Customer Pricing:**
- Customers ordering 1008-1107 units are quoted the **wrong price**
- If T2 price > T3 price: Customers are overcharged
- If T2 price < T3 price: Company loses margin

**Order Processing:**
- Proposals generated with incorrect pricing
- PowerPoint presentations show wrong tier info
- Invoices may have incorrect line items

### Technical Impact

**Affected Components:**
1. `src/pricing_engine.py::determine_tier_number()` - Tier selection
2. `src/pricing_engine.py::get_unit_price_new_system()` - Price lookup
3. `src/helpers.py::calculate_moq()` - MOQ calculation (uses tier boundaries)
4. `src/pptx_generator.py::update_pricing_table()` - PowerPoint table population
5. **Tab 1** - Proposal Generator (pricing tables)
6. **Tab 3** - Order & Client Info (product pricing)
7. **Tab 4** - Execution & Accounting (invoice generation)

**Not Directly Affected (but uses tier data):**
- `src/helpers.py::parse_tier_info()` - Parsing is correct, data is wrong

---

## Real-World Occurrence

**Investigation Results:**
- **Real Dataset:** 0 tiered products found (all flat pricing currently)
- **Demo Dataset:** Column name mismatch (schema transition in progress)

**Conclusion:** This edge case is **hypothetical** for current data but represents a real risk if:
1. Partner data is added with tiered pricing
2. Spreadsheet data is entered incorrectly
3. Tier boundaries are manually updated without validation

---

## Proposed Solutions

### Solution 1: Fix Data (Immediate - Recommended)

**Action:** Update spreadsheet to remove overlaps

**Example Fix:**
```
Before: T1: 112-447, T2: 448-1107, T3: 1008+
After:  T1: 112-447, T2: 448-1107, T3: 1108+
```

**Validation Rule:**
- Each tier must start exactly where the previous tier ends + 1
- T1 ends at X → T2 must start at X+1
- Last tier can be open-ended (e.g., `1108+`)

**Pros:**
- Fixes issue immediately
- No code changes required
- Works with existing logic

**Cons:**
- Requires manual data correction
- Doesn't prevent future errors
- No validation

### Solution 2: Add Overlap Detection (Preventive - Recommended)

**Action:** Add validation to detect overlaps when loading data

**Implementation in `src/helpers.py`:**
```python
def validate_tier_ranges(tier_string, product_name):
    """
    Validate that tier ranges don't overlap.
    Returns list of warnings if overlaps detected.
    """
    tier_dict = parse_tier_info(tier_string)
    warnings = []

    tier_numbers = sorted(tier_dict.keys())
    for i in range(len(tier_numbers) - 1):
        t1_num = tier_numbers[i]
        t2_num = tier_numbers[i + 1]

        t1_min, t1_max = tier_dict[t1_num]
        t2_min, t2_max = tier_dict[t2_num]

        # Check for overlap or gap
        if t1_max != float('inf'):
            if t1_max >= t2_min:
                warnings.append({
                    'product': product_name,
                    'tier1': f'T{t1_num} ({t1_min}-{t1_max})',
                    'tier2': f'T{t2_num} ({t2_min}-{t2_max})',
                    'issue': f'Overlap: {t2_min}-{t1_max}',
                    'severity': 'ERROR'
                })
            elif t1_max + 1 < t2_min:
                warnings.append({
                    'product': product_name,
                    'tier1': f'T{t1_num}',
                    'tier2': f'T{t2_num}',
                    'issue': f'Gap: {t1_max + 1} to {t2_min - 1}',
                    'severity': 'WARNING'
                })

    return warnings
```

**UI Display in `app.py`:**
```python
# After loading data
st.subheader("Data Quality Check")

all_warnings = []
for idx, row in df_template.iterrows():
    if row['Pricing Tiers (Y/N)'] == 'Y':
        tier_string = row['Tier Range']
        product_name = row['Product/Service']
        warnings = validate_tier_ranges(tier_string, product_name)
        all_warnings.extend(warnings)

if all_warnings:
    st.error(f"⚠️ {len(all_warnings)} tier range issues detected!")
    for warning in all_warnings:
        if warning['severity'] == 'ERROR':
            st.error(f"**{warning['product']}**: {warning['issue']}")
        else:
            st.warning(f"**{warning['product']}**: {warning['issue']}")
```

**Pros:**
- Prevents future errors
- Gives immediate feedback to users
- Helps maintain data quality
- Non-breaking change

**Cons:**
- Doesn't auto-fix issues
- Requires code changes
- May generate false positives

### Solution 3: Smart Tier Selection (Alternative - Not Recommended)

**Action:** Change tier selection to use **highest matching tier** instead of first

**Implementation:**
```python
def determine_tier_number(quantity, tier_info_string, has_tiers):
    # ... existing code ...

    matching_tiers = []
    for tier_num, (min_qty, max_qty) in tier_ranges.items():
        if min_qty <= quantity <= max_qty:
            matching_tiers.append(tier_num)

    if matching_tiers:
        return max(matching_tiers)  # Use highest tier in overlap

    return None
```

**Pros:**
- Handles overlaps automatically
- More forgiving of data errors
- May better match user intent (higher tier = better price)

**Cons:**
- Masks data quality issues
- May not match actual intent
- Could give customers better pricing than intended
- Doesn't address root cause

---

## Recommendations

### Immediate Actions (Priority 1)

1. **Audit Current Data:**
   - Run `scripts/investigations/investigate_tier_overlaps.py` (Streamlit)
   - Or run `scripts/investigations/check_tier_overlaps_simple.py` (Python)
   - Check both demo and real datasets

2. **Fix Any Overlaps Found:**
   - Update spreadsheet tier ranges
   - Ensure each tier starts at previous tier max + 1
   - Document corrections

### Short-Term (Priority 2)

3. **Add Validation (Solution 2):**
   - Implement `validate_tier_ranges()` function
   - Display warnings in sidebar on data load
   - Log warnings for monitoring

4. **Add Test Coverage:**
   - Create regression test: `scripts/features/test_tier_validation.py`
   - Test with known overlap cases
   - Test boundary conditions

### Long-Term (Priority 3)

5. **Spreadsheet Validation:**
   - Add Google Sheets formula validation
   - Highlight tier range cells with issues
   - Create data entry guidelines

6. **Documentation:**
   - Update schema_reference.md with tier rules
   - Add examples of correct tier formatting
   - Document validation rules

---

## Test Scripts Created

1. **`scripts/features/test_tier_overlap_bug.py`**
   - Demonstrates the bug with the specific tier string
   - Shows expected vs actual behavior
   - Includes corrected tier string test

2. **`scripts/investigations/investigate_tier_overlaps.py`** (Streamlit)
   - Interactive overlap detection for real data
   - Shows affected products
   - Provides recommendations

3. **`scripts/investigations/check_tier_overlaps_simple.py`** (Python)
   - Command-line overlap detection
   - Checks both demo and real datasets
   - Outputs detailed report

**Run Tests:**
```bash
# Demonstrate the bug
python scripts/features/test_tier_overlap_bug.py

# Check actual data (Streamlit)
streamlit run scripts/investigations/investigate_tier_overlaps.py

# Check actual data (Python)
python scripts/investigations/check_tier_overlaps_simple.py
```

---

## Related Files

### Code Files
- `src/helpers.py::parse_tier_info()` - Line 501
- `src/pricing_engine.py::determine_tier_number()` - Line 10
- `src/pricing_engine.py::get_unit_price_new_system()` - Line 45

### Documentation
- `schema_reference.md` - Tier Range column definition
- `docs/planning/METHODOLOGY_LOGIC.md` - Pricing logic
- `docs/investigations/TIER_OVERLAP_EDGE_CASE.md` - This document

### Test Scripts
- `scripts/features/test_tier_overlap_bug.py` - Bug demonstration
- `scripts/investigations/investigate_tier_overlaps.py` - Interactive checker
- `scripts/investigations/check_tier_overlaps_simple.py` - CLI checker

---

## Conclusion

This edge case represents a **data quality issue** (overlapping tier ranges) exacerbated by a **code design decision** (first-match tier selection). While not currently affecting production (no tiered products in real dataset), it poses a significant risk for:

1. **New partner onboarding** with tiered pricing
2. **Manual data entry errors** when updating tier ranges
3. **Incorrect customer quotes** if overlaps occur

**Recommended Action:** Implement **Solution 1 + Solution 2**:
- Fix any existing overlaps (Solution 1)
- Add validation to prevent future overlaps (Solution 2)

This provides both immediate resolution and long-term prevention.

---

**Last Updated:** 2026-01-26
**Test Coverage:** 3 test scripts created
**Status:** Ready for implementation
