# PowerPoint File Inspection Results

**File:** `templates/November All Slides.pptx`
**Inspected:** 2025-11-04
**Purpose:** Understand structure for automation implementation

---

## File Overview

- **Total Slides:** 339
- **Product Slides (with pricing tables):** 242
- **Section/Intro Slides (no tables):** 97
- **File Size:** 43MB (optimized)
- **Unique Products:** 233

---

## Slide Structure

### Typical Product Slide Layout

1. **Product Name** (text shape, usually first text on slide)
2. **Subtitle/Tagline** (e.g., "Repurposing Waste While Supporting...")
3. **Product Image** (embedded photo)
4. **Specifications** (bullet points)
5. **Pricing Table** (2-3 rows, 3-4 columns)
6. **Customization Note** (often in table row 3)
7. **Logos** (SDG logo, PBP logo)

### Table Structure Variations

**Most common formats:**

**Format A: 2 rows x 3 columns** (simpler pricing)
```
| MOQ | Price Ea (@ Qty X) | Delivery |
|-----|-------------------|----------|
| 10  | $XX.XX            | X weeks  |
```

**Format B: 2 rows x 4 columns** (volume pricing)
```
| MOQ | Price Ea (@ Qty X) | Price Ea (@ Qty Y+) | Delivery |
|-----|-------------------|---------------------|----------|
| 10  | $XX.XX            | $XX.XX              | X weeks  |
```

**Format C: 3 rows x 4 columns** (with customization row)
```
| MOQ | Price Ea (@ Qty X) | Price Ea (@ Qty Y+) | Delivery        |
|-----|-------------------|---------------------|----------------|
| 10  | $XX.XX            | $XX.XX              | X weeks        |
| Artwork set-up: $XX.XX / Branding per piece: $X.XX | | |
```

---

## Example: Upcycled Multi-Compartment Briefcase (Slide 141)

### Slide Content:
- **Product Name:** "UPCYCLED MULTI-COMPARTMENT BRIEFCASE"
- **Tagline:** "Repurposing Waste While Supporting Underserved Women & Men in India"

### Table Structure:
```
Row 0 (Headers):
  - MOQ
  - Price Ea (@ Qty 10)
  - Price Ea (@ Qty 50+)
  - Delivery (after art ✓)

Row 1 (Pricing Data):
  - 10
  - $159.00
  - $143.00
  - 6-8 weeks

Row 2 (Customization):
  - Artwork set-up: $70.00 / Branding per piece: From $1.00
  - (empty)
  - (empty)
  - (empty)
```

**Table Dimensions:** 3 rows × 4 columns

---

## Product Name Samples (First 30 alphabetically)

```
"THE SIDEKICK" UPCYCLED TOTE
'WARSH' BAR
A SIMPLE MOMENT GIFT BOX
AAMINA ATHLETIC TOTE
AFRICAN BAULE POUCH
AFRICAN ELEPHANT ORNAMENT
ALL NATURAL SALVE
ANKLE SOCKS THAT GIVE BACK – 3 Pairs
ATHLETIC rPET HALF-ZIP
Ahhh RELAX
BATH BOMB
BATH TEAS
BEADED BRACELET – LOVE OR CUSTOM
BEADED LUGGAGE TAG
BEAMING RINGS ORNAMENT
BEANIE
BEARD SALVE
BEE WELL TEA
BEESWAX CANDLE
BODY & MIND GIFT BOX
BODY BALM
BODY BUTTER
BODY LOTION
BODY SCRUB
BOTANICAL BODY OIL
BOX OF TEA
BRANDABLE POLO SHIRT
BREAKTHROUGH BRACELET
BUCKET HATS
BUMI CAP
```

**Full list:** See `product_names_from_slides.txt`

---

## Key Findings for Implementation

### ✅ Good News

1. **Consistent Product Identification:**
   - Product name is always the first substantial text on slide
   - Easy to extract programmatically

2. **Table Detection:**
   - All product slides have exactly 1 pricing table
   - Easy to identify: `shape.has_table == True`

3. **Table Structure:**
   - Headers always in Row 0
   - Pricing data always in Row 1
   - Customization info (if present) always in Row 2
   - Columns vary (3-4) but row structure is consistent

4. **Reasonable File Size:**
   - 43MB is manageable for Streamlit Cloud
   - Fast loading expected

### ⚠️ Challenges Identified

1. **Table Column Variations:**
   - Some tables have 3 columns (simple pricing)
   - Some tables have 4 columns (volume pricing)
   - **Solution:** Detect column count and adapt update logic

2. **Header Text Variations:**
   - "Price Ea (@ Qty 10)" vs "Price Ea (@ Qty 15)" vs "Price Ea (@ 25)"
   - Quantity in header varies per product
   - **Solution:** Our app calculates its own MOQ, so we can update header text dynamically

3. **Customization Row Format:**
   - Sometimes in Row 2 of table
   - Sometimes missing entirely
   - **Solution:** Check row count, handle both 2-row and 3-row tables

4. **Product Name Matching:**
   - Need to verify if slide names match Google Sheets product names
   - Some names have special characters (quotes, dashes)
   - **Solution:** Implement fuzzy matching or mapping dictionary

---

## Implementation Recommendations

### Phase 1: Basic Matching (Priority 1)
1. Extract product name from first text shape on each slide
2. Match against app's product list (exact match)
3. Create mapping for mismatches

### Phase 2: Table Updates (Priority 1)
1. Detect table structure (row count, column count)
2. Update Row 1 pricing data (preserve Row 0 headers)
3. Handle Row 2 customization (if present)

### Phase 3: Dynamic Headers (Priority 2)
1. Update header text to reflect app-calculated MOQ
2. Example: "Price Ea (@ Qty 10)" → "Price Ea (@ Qty 15)"

### Phase 4: Error Handling (Priority 1)
1. Skip slides where product not in app's proposal
2. Warn user if product slide not found
3. Continue processing remaining products

---

## Next Steps

1. **Verify Product Name Matching:**
   - Compare `product_names_from_slides.txt` with Google Sheets product list
   - Identify mismatches
   - Create mapping dictionary if needed

2. **Start Implementation:**
   - Begin Phase 1 (setup & dependencies) - COMPLETE ✅
   - Create `src/pptx_generator.py` module
   - Implement slide cloning logic

3. **Testing:**
   - Test with 2-3 products first
   - Verify formatting preservation
   - Validate table updates

---

## Files Generated

- `product_names_from_slides.txt` - Complete list of 233 product names from slides
- This document - Inspection results and recommendations

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Ready for Implementation
