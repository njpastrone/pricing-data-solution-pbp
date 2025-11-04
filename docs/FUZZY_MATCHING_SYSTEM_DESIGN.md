# Fuzzy Matching System Design

**Feature:** Intelligent product name matching with fallback system
**Date:** 2025-11-04
**Status:** Designed & Implemented

---

## Problem Statement

Only **5.3%** of Google Sheets products match exactly with PowerPoint slide names. This would make the PowerPoint generation feature unusable for most products.

**Example mismatches:**
- GS: `Upcycled Laptop Sleeve (Enfold)-MOF` ↔ PPTX: `UPCYCLED LAPTOP SLEEVE`
- GS: `Butcher Block - Large` ↔ PPTX: `BUTCHER BLOCK`
- GS: `Candle Holders - Set of 3` ↔ PPTX: `MINIMALIST CANDLE HOLDERS – Set of 3`

---

## Solution: Smart Matching with Fuzzy Fallback

### Matching Logic

```
if exact_match(product_name):
    return exact_match (100% confidence)
else:
    fuzzy_matches = find_fuzzy_matches(product_name)
    if best_match.confidence >= 70%:
        return best_match (suggest to user for confirmation)
    else:
        return no_match (show warning, skip product)
```

### Confidence Thresholds

| Confidence | Color | Action | User Experience |
|-----------|-------|--------|-----------------|
| **100%** (Exact) | 🟢 Green | Auto-use | "✓ Exact match found" |
| **90-99%** (Excellent fuzzy) | 🟢 Green | Auto-use with note | "✓ Excellent match (95%)" |
| **70-89%** (Good fuzzy) | 🟡 Yellow | Suggest, ask confirmation | "~ Good match (80%) - Confirm?" |
| **50-69%** (Poor fuzzy) | 🔴 Red | Show warning | "? Uncertain match (65%) - Review" |
| **< 50%** (No match) | ⚫ Gray | Skip product | "✗ No match found - Skip" |

---

## Implementation Results

### Test Results (19 Google Sheets Products)

**Before Fuzzy Matching:**
- Exact matches: 1 (5.3%)
- Unusable: 18 (94.7%)

**After Fuzzy Matching:**
- Exact matches: 1 (5.3%)
- Fuzzy matches ≥70%: 6 (31.6%)
- **Total usable: 7 (36.8%)**
- Improvement: **600% increase in usable matches!**

### Successful Fuzzy Matches

| Google Sheets Name | PowerPoint Name | Confidence |
|-------------------|----------------|-----------|
| `Upcycled Day Tripper Backpack (Noir)` | `UPCYCLED DAY TRIPPER BACKPACK` | 92% 🟢 |
| `Candle Holders - Set of 3` | `MINIMALIST CANDLE HOLDERS – Set of 3` | 81% 🟡 |
| `Butcher Block - Large` | `BUTCHER BLOCK` | 81% 🟡 |
| `Upcycled Laptop Sleeve (Enfold)-MOF` | `UPCYCLED LAPTOP SLEEVE` | 80% 🟡 |
| `Butcher Block - Medium` | `BUTCHER BLOCK` | 79% 🟡 |
| `Upcycled Multicompartment Briefcase (hustler)` | `UPCYCLED MULTI-COMPARTMENT BRIEFCASE` | 76% 🟡 |

---

## User Interface Design

### Step 1: Pre-Generation Review Screen

When user clicks "Generate PowerPoint Proposal", show match review screen:

```
┌─────────────────────────────────────────────────────────────┐
│  Review Product Matches Before Generating                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  7 of 8 products matched successfully                       │
│  ██████████████████████████░░  88%                          │
│                                                             │
│  ✓ 1 Exact match                                            │
│  ~ 6 Fuzzy matches (need confirmation)                      │
│  ✗ 1 Product will be skipped                                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRODUCT MATCHES:                                           │
│                                                             │
│  1. Upcycled Executive Urban Briefcase                      │
│     ✓ Exact match: UPCYCLED EXECUTIVE URBAN BRIEFCASE      │
│     [✓ Confirmed]                                           │
│                                                             │
│  2. Upcycled Day Tripper Backpack (Noir)                    │
│     ~ Excellent match (92%): UPCYCLED DAY TRIPPER BACKPACK  │
│     [ ] Use this match   [✓] Show alternatives              │
│                                                             │
│  3. Candle Holders - Set of 3                               │
│     ~ Good match (81%): MINIMALIST CANDLE HOLDERS – Set of 3│
│     [✓] Use this match   [ ] Show alternatives              │
│                                                             │
│  4. Upcycled Laptop Sleeve (Enfold)-MOF                     │
│     ~ Good match (80%): UPCYCLED LAPTOP SLEEVE              │
│     [✓] Use this match   [ ] Show alternatives              │
│                                                             │
│  5. Alabaster + Tigerwood Cutting Board                     │
│     ✗ No good match found (best: SELVA CUTTING BOARD, 58%) │
│     This product will be skipped.                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Generate PowerPoint with 7 products]  [Cancel]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Alternative Matches (Expandable)

When user clicks "Show alternatives":

```
┌─────────────────────────────────────────────────────────────┐
│  Select Best Match for: Upcycled Day Tripper Backpack (Noir)│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ( ) UPCYCLED DAY TRIPPER BACKPACK           92% ← Suggested│
│  ( ) UPCYCLED BOUNCY CASTLE BACKPACK         68%            │
│  ( ) UPCYCLED FOLDAWAY HIP BAG               61%            │
│  ( ) Skip this product                                      │
│                                                             │
│  [Confirm Selection]  [Cancel]                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Generation Progress

```
┌─────────────────────────────────────────────────────────────┐
│  Generating PowerPoint Proposal...                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✓ Found slide: UPCYCLED EXECUTIVE URBAN BRIEFCASE         │
│  ✓ Found slide: UPCYCLED DAY TRIPPER BACKPACK              │
│  ✓ Found slide: MINIMALIST CANDLE HOLDERS – Set of 3       │
│  ✓ Found slide: UPCYCLED LAPTOP SLEEVE                     │
│  ⏳ Updating pricing tables...                              │
│                                                             │
│  █████████████████░░░░░  75%                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Success with Summary

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ PowerPoint Proposal Generated Successfully               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  7 products included in presentation                        │
│  1 product skipped (no matching slide)                      │
│                                                             │
│  Skipped products:                                          │
│   • Alabaster + Tigerwood Cutting Board                     │
│                                                             │
│  [Download PowerPoint (PBP_Proposal_20251104.pptx)]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Structure

### New Module: `src/slide_matcher.py`

```python
class SlideMatcher:
    """
    Intelligent slide matcher with exact and fuzzy matching.
    """
    def __init__(self, pptx_product_names: List[str])
    def find_match(self, gs_product_name: str) -> SlideMatchResult
    def batch_match(self, gs_product_names: List[str]) -> List[SlideMatchResult]
    def get_match_summary(self, results: List[SlideMatchResult]) -> Dict

class SlideMatchResult:
    """
    Result of matching a product name to a slide.
    """
    gs_product_name: str
    pptx_product_name: Optional[str]
    match_type: str  # 'exact', 'fuzzy', 'none'
    confidence: int  # 0-100
    alternatives: List[Tuple[str, int]]

    def is_usable(self, min_confidence: int = 70) -> bool
```

### Integration in Tab 1

```python
# When user clicks "Generate PowerPoint Proposal"

# Step 1: Load PowerPoint product names
from pptx import Presentation
prs = Presentation('templates/November All Slides.pptx')
pptx_products = extract_product_names_from_slides(prs)

# Step 2: Initialize matcher
from src.slide_matcher import SlideMatcher
matcher = SlideMatcher(pptx_products)

# Step 3: Match proposal products
proposal_product_names = [p['product_data']['Product/Service'] for p in st.session_state.proposal_products]
match_results = matcher.batch_match(proposal_product_names)

# Step 4: Show review UI
show_match_review_ui(match_results)

# Step 5: Generate PowerPoint with confirmed matches
confirmed_matches = get_user_confirmed_matches(match_results)
generate_pptx_with_matches(confirmed_matches)
```

---

## Benefits

### 1. Dramatically Increased Success Rate
- **600% improvement** in usable matches (5.3% → 36.8%)
- Will improve further as more products added to Google Sheets

### 2. User Control & Transparency
- User sees all matches before generation
- Can confirm or override fuzzy matches
- Clear indication of skipped products

### 3. Handles Name Variations
- Parenthetical suffixes: `(Noir)`, `(CZI)`, `(Enfold)`
- Hyphenation differences: `Multi-Compartment` vs `Multicompartment`
- Size variations: `Butcher Block - Large` → `BUTCHER BLOCK`
- Descriptive prefixes: `MINIMALIST` in slide name

### 4. Graceful Degradation
- Products without matches are simply skipped
- User still gets a useful proposal (partial is better than none)
- Clear warnings about what was skipped

---

## Future Enhancements

### Phase 2: Learning System
- Remember user confirmations (mapping cache)
- Auto-apply previously confirmed matches
- Suggest corrections for common mismatches

### Phase 3: Manual Override
- Allow user to manually map products to slides
- Store mapping in session state or database
- Use for future proposals

### Phase 4: Slide Search
- Add search box: "Can't find your product? Search all slides"
- Real-time search as user types
- Preview slide before adding to proposal

---

## Testing Plan

### Test Cases

1. **Exact Match** (100% confidence)
   - Input: `Upcycled Executive Urban Briefcase`
   - Expected: Auto-match to `UPCYCLED EXECUTIVE URBAN BRIEFCASE`

2. **Excellent Fuzzy Match** (≥90% confidence)
   - Input: `Upcycled Day Tripper Backpack (Noir)`
   - Expected: Suggest `UPCYCLED DAY TRIPPER BACKPACK` with high confidence

3. **Good Fuzzy Match** (70-89% confidence)
   - Input: `Candle Holders - Set of 3`
   - Expected: Suggest `MINIMALIST CANDLE HOLDERS – Set of 3`, ask for confirmation

4. **Poor Match** (<70% confidence)
   - Input: `Alabaster + Tigerwood Cutting Board`
   - Expected: Show warning, offer to skip or select alternative

5. **Batch Processing**
   - Input: All 19 Google Sheets products
   - Expected: 7 usable matches, 12 skipped

---

## Dependencies

### New Libraries (Added to requirements.txt)

```
python-pptx        # PowerPoint manipulation
thefuzz            # Fuzzy string matching
python-Levenshtein # Fast string distance (optional, speeds up thefuzz)
```

---

## Rollout Plan

### Phase 1: Testing (This Week)
- ✅ Implement SlideMatcher class
- ✅ Test with actual data (19 products)
- ✅ Verify confidence scores
- ⏳ Create UI mockups in Streamlit

### Phase 2: Integration (Next Week)
- Add match review UI to Tab 1
- Integrate with PowerPoint generator
- Test end-to-end flow

### Phase 3: Refinement (Ongoing)
- Collect user feedback on match quality
- Adjust confidence thresholds if needed
- Add manual override features

---

## Conclusion

The fuzzy matching system transforms an unusable feature (5% match rate) into a highly functional one (37% match rate, improving as data grows). By giving users transparency and control over matches, we build trust and provide value even with incomplete data.

**Key Insight:** Perfect data is not required. The system works with imperfect, growing data and gets better over time naturally.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Complete, Implementation Ready
