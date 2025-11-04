# Improving Match Rate Strategy

**Current Match Rate:** 36.8% (7 of 19 products)
**Target Match Rate:** 80%+ (15+ of 19 products)
**Date:** 2025-11-04

---

## Root Cause Analysis

### Why 12 Products Don't Match

#### Category 1: Products NOT in PowerPoint Yet (7 products - 58% of failures)

**Baking Mixes (4 products):**
- LAVENDER SHORTBREAD MIX
- SAVORY HERB BISCUIT MIX
- CHOCOLATE ROSEMARY BROWNIE MIX
- STRAWBERRY PANCAKE MIX

**Seasonings (3 products):**
- GARDEN HERB SEASON SALT
- ZA'ATAR SEASON SALT
- HERBS DE PROVENCE SEASONING

**Analysis:** These products are in Google Sheets but slides don't exist in PowerPoint yet. No amount of fuzzy matching can fix this - the slides literally don't exist.

**Impact:** Unavoidable mismatches until slides are created.

#### Category 2: Different Product Names (3 products - 25% of failures)

**Wood Products:**
- GS: `Angled Wood Spatula` ↔ PPTX: Maybe exists as something else?
- GS: `Alabaster + Tigerwood Cutting Board` ↔ PPTX: `SELVA CUTTING BOARD` (58% match)

**Other:**
- GS: `Upcycled Gym Duffle (CZI)` ↔ PPTX: No clear match (59% best)

**Analysis:** These might exist in PowerPoint under completely different names, or with custom variant names not in the main deck.

#### Category 3: Test/Placeholder Data (2 products - 17% of failures)

- `Product Y` - Obviously a test placeholder
- `Upcycled Pilot's Everyday Case` - Might be a custom variant

---

## Improvement Strategies

### Strategy 1: Clean Up Google Sheets Data (IMMEDIATE - User Action)

**Impact:** Remove 2 products from "no match" list
**Effort:** 5 minutes
**Match Rate Improvement:** 36.8% → 47.4%

**Actions:**
1. Remove `Product Y` (test data)
2. Verify `Upcycled Pilot's Everyday Case` - is this a real product or test data?

**Benefit:** Clean data = more accurate match rate reporting.

---

### Strategy 2: Add Missing Slides to PowerPoint (HIGH IMPACT - User Action)

**Impact:** Could improve match rate dramatically
**Effort:** Depends on whether products exist in business
**Match Rate Improvement:** Potentially 36.8% → 73.7% (14/19 matches)

**Missing Products That Need Slides:**

**Priority 1: Food Products (7 products)**
- 4 Baking Mixes
- 3 Seasonings

**Questions for User:**
1. Do these products have existing slides that might be named differently?
2. Are these new products that need slides created?
3. Should we create template slides for these?

**If slides exist elsewhere:**
- Add to "November All Slides.pptx"
- Ensure product names match Google Sheets exactly

**If slides don't exist yet:**
- Create basic slide template
- Add product photo + pricing table
- Can be done incrementally (add as needed)

---

### Strategy 3: Better Fuzzy Matching Algorithm (MEDIUM IMPACT - Development)

**Impact:** Improve matching for products with different names
**Effort:** 2-3 hours development
**Match Rate Improvement:** 36.8% → 42-50% (1-3 more matches)

#### Current Algorithm Limitation

Using `token_sort_ratio` which works well for word order differences but struggles with completely different product names.

**Example:**
- `Alabaster + Tigerwood Cutting Board` → `SELVA CUTTING BOARD` (58% - too low!)
- Both are cutting boards, but "Alabaster Tigerwood" vs "Selva" have no word overlap

#### Proposed Improvements

**A. Multi-Scorer Approach**

Instead of just `token_sort_ratio`, use multiple scoring methods and take the best:

```python
def find_match_multi_scorer(gs_product, pptx_products):
    scorers = [
        fuzz.token_sort_ratio,   # Current (good for word order)
        fuzz.token_set_ratio,    # Handles subset/superset
        fuzz.partial_ratio,      # Handles partial string matches
    ]

    best_match = None
    best_score = 0

    for scorer in scorers:
        match = process.extractOne(gs_product, pptx_products, scorer=scorer)
        if match[1] > best_score:
            best_score = match[1]
            best_match = match[0]

    return best_match, best_score
```

**Expected Improvement:**
- `Alabaster + Tigerwood Cutting Board` → `SELVA CUTTING BOARD`
  - token_sort_ratio: 58%
  - **partial_ratio: 67%** (better!)
  - Could push this over 70% threshold with keyword boosting

**B. Keyword Boosting**

Identify key product category words and boost matches that share them:

```python
CATEGORY_KEYWORDS = {
    'cutting': ['CUTTING', 'BOARD', 'BUTCHER'],
    'spatula': ['SPATULA', 'SPOON', 'UTENSIL'],
    'briefcase': ['BRIEFCASE', 'CASE', 'BAG'],
    # etc...
}

def boost_category_match(gs_product, pptx_product, base_score):
    """
    Boost score if products share category keywords
    """
    gs_upper = gs_product.upper()
    pptx_upper = pptx_product.upper()

    for category, keywords in CATEGORY_KEYWORDS.items():
        gs_match = any(kw in gs_upper for kw in keywords)
        pptx_match = any(kw in pptx_upper for kw in keywords)

        if gs_match and pptx_match:
            # Both in same category - boost score
            return min(base_score + 15, 100)

    return base_score
```

**Example:**
- `Alabaster + Tigerwood Cutting Board` (contains "CUTTING")
- `SELVA CUTTING BOARD` (contains "CUTTING")
- Base score: 58% → Boosted: 73% ✓ (now usable!)

**C. Variant Name Handling**

Recognize and strip common variant patterns:

```python
VARIANT_PATTERNS = [
    r'\(.*?\)',         # Parentheses: (Noir), (CZI), (Enfold)
    r'-MOF$',           # Suffixes: -MOF
    r'- (Large|Medium|Small)',  # Size variants
]

def normalize_product_name(name):
    """Strip variant identifiers before matching"""
    import re
    normalized = name
    for pattern in VARIANT_PATTERNS:
        normalized = re.sub(pattern, '', normalized)
    return normalized.strip()
```

**Example:**
- `Upcycled Laptop Sleeve (Enfold)-MOF` → `Upcycled Laptop Sleeve`
- Now matches `UPCYCLED LAPTOP SLEEVE` at 95%+ instead of 80%

---

### Strategy 4: Manual Product Mapping (LOW EFFORT - User Action)

**Impact:** Fix remaining edge cases
**Effort:** 10 minutes one-time setup
**Match Rate Improvement:** 36.8% → 50%+ (fix specific problem products)

**Create a mapping file for known mismatches:**

```python
# In src/product_name_mappings.py or as session state

MANUAL_PRODUCT_MAPPINGS = {
    # Google Sheets Name → PowerPoint Slide Name
    "Alabaster + Tigerwood Cutting Board": "SELVA CUTTING BOARD",
    "Upcycled Gym Duffle (CZI)": "UPCYCLED CANVAS SLING",  # if this is correct
    "Angled Wood Spatula": "WOODEN SPATULA",  # if this exists
    # Add more as discovered
}
```

**Integration:**

```python
def find_match_with_manual_override(gs_product, pptx_products):
    # Check manual mapping first
    if gs_product in MANUAL_PRODUCT_MAPPINGS:
        mapped_name = MANUAL_PRODUCT_MAPPINGS[gs_product]
        if mapped_name in pptx_products:
            return SlideMatchResult(
                gs_product, mapped_name, 'manual', 100, []
            )

    # Fall back to fuzzy matching
    return fuzzy_match(gs_product, pptx_products)
```

**Benefits:**
- Fixes specific problem cases immediately
- No algorithm changes needed
- User maintains control
- Can be updated anytime

---

### Strategy 5: Interactive Match Learning (FUTURE - Best Long-Term)

**Impact:** Improves automatically over time
**Effort:** 1-2 days development
**Match Rate Improvement:** Accumulates over time, eventually near 100%

**Concept:**

When user confirms a fuzzy match, remember it:

```python
# User confirms: "Alabaster + Tigerwood Cutting Board" → "SELVA CUTTING BOARD"

# Save to learned mappings
st.session_state.learned_mappings["Alabaster + Tigerwood Cutting Board"] = "SELVA CUTTING BOARD"

# Next time, use learned mapping (100% confidence)
# Over time, system learns all the exceptions
```

**Storage Options:**
- Session state (temporary)
- JSON file (persistent, local)
- Database (persistent, multi-user)

**User Experience:**
```
[X] Remember this match for future proposals
```

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (This Week)

**1. Clean up test data** ✅
- Remove `Product Y`
- Verify other suspicious entries

**2. Identify missing slides** ✅
- Review the 7 food products
- Confirm: Do slides exist elsewhere or need creation?

**3. Add manual mappings** (30 min)
- Create `MANUAL_PRODUCT_MAPPINGS` dict
- Add known good matches for problem products
- Test with actual data

**Expected Result:** 36.8% → 50% match rate

### Phase 2: Algorithm Improvements (Next Week)

**4. Implement multi-scorer** (2 hours)
- Add `token_set_ratio` and `partial_ratio`
- Take best score across all methods
- Test with all 19 products

**5. Add keyword boosting** (2 hours)
- Build category keyword dictionary
- Boost scores for category matches
- Should help cutting boards, spatulas, etc.

**Expected Result:** 50% → 60-65% match rate

### Phase 3: Long-Term Solution (Ongoing)

**6. Add missing slides to PowerPoint** (ongoing)
- Create slides for baking mixes (as products are sold)
- Create slides for seasonings
- Incremental improvement

**7. Implement match learning** (future)
- Remember user confirmations
- Build up mapping database over time

**Expected Result:** 65% → 90%+ match rate (as slides added)

---

## Realistic Expectations

### Current Situation (19 Products)

| Category | Count | Can Match? | Why/Why Not |
|----------|-------|-----------|-------------|
| Already matching | 7 | ✓ Yes | Working now |
| Test data | 2 | ✗ No | Need removal |
| Missing slides | 7 | ✗ No | Slides don't exist |
| Name variations | 3 | ⚠ Maybe | With better algorithm |

### Best Case Scenario (All Improvements)

| Improvement | Potential Matches | Match Rate |
|-------------|------------------|------------|
| Current | 7 | 36.8% |
| Remove test data | 7/17 | 41.2% |
| Better algorithm | 10/17 | 58.8% |
| Manual mappings | 10/17 | 58.8% |
| **Add missing slides** | **17/17** | **100%** |

**Key Insight:** The biggest blocker is missing slides, not the algorithm. Even perfect fuzzy matching can't match products to slides that don't exist!

---

## Immediate Action Items for User

1. **Review this list** - which products should have slides?
   - LAVENDER SHORTBREAD MIX
   - SAVORY HERB BISCUIT MIX
   - CHOCOLATE ROSEMARY BROWNIE MIX
   - STRAWBERRY PANCAKE MIX
   - GARDEN HERB SEASON SALT
   - ZA'ATAR SEASON SALT
   - HERBS DE PROVENCE SEASONING

2. **Check if slides exist with different names:**
   - Search PowerPoint for "Cutting Board", "Spatula", "Duffle"
   - If found, provide name mapping

3. **Decide on approach:**
   - **Option A:** Remove products from Google Sheets that don't have slides yet
   - **Option B:** Create basic slides for missing products
   - **Option C:** Accept that not all products will match (partial proposals are OK)

---

## Recommendation

**Short-term (MVP):**
- Implement manual mappings for 2-3 fixable cases
- Improve algorithm with multi-scorer
- **Accept 50-60% match rate** as OK for MVP
- Focus on making the "partial proposal" user experience excellent

**Long-term:**
- Add slides incrementally as products are sold
- Match rate will naturally improve to 80-90%+ over time
- No rush - system works with partial data!

**Why this is OK:**
- Even at 50% match rate, tool saves time vs. fully manual process
- Users get value immediately
- Improves automatically as you add more slides
- Transparent UI shows what's included/skipped

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
