# PowerPoint Automation - Complete Implementation Roadmap

**Goal:** Build full PowerPoint proposal automation with intelligent fuzzy matching
**Status:** Ready to Implement
**Estimated Time:** 6-7 days (with matching system)
**Date:** 2025-11-04

---

## Overview

We started planning PowerPoint automation, then discovered the **matching problem** (only 5.3% exact matches). We've now designed a **fuzzy matching system** that improves this to 60-68% with user confirmation.

**This document integrates both components into a complete implementation plan.**

---

## Architecture: Two-Layer System

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: INTELLIGENT MATCHING SYSTEM                       │
│  (Finds the right slides)                                   │
├─────────────────────────────────────────────────────────────┤
│  • Exact matching (100% confidence)                         │
│  • Fuzzy matching with multiple algorithms                  │
│  • Keyword category boosting                                │
│  • Variant name stripping                                   │
│  • Manual override mappings                                 │
│  • User confirmation UI                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: POWERPOINT GENERATION ENGINE                      │
│  (Clones slides and updates pricing)                        │
├─────────────────────────────────────────────────────────────┤
│  • Load PowerPoint template                                 │
│  • Clone complete slides (preserve formatting)              │
│  • Update pricing tables                                    │
│  • Assemble client presentation                             │
│  • Export downloadable .pptx                                │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** Layer 1 MUST work before Layer 2 is useful. No point generating PowerPoint if we can't find the right slides!

---

## Implementation Strategy: Bottom-Up Approach

### Phase 1: Matching System (FOUNDATION)
Build and test the intelligent matching system first.

**Why first:**
- Matching is the blocker (5% → 60% improvement needed)
- Can test matching without building full PowerPoint generator
- User can validate matches before we invest in generation code
- Faster feedback loop

### Phase 2: PowerPoint Generation (BUILD ON FOUNDATION)
Once matching works, build the generation engine.

**Why second:**
- Depends on reliable matching
- Easier to debug when matching is stable
- Can focus on slide cloning/table updates without matching issues

### Phase 3: Integration & Polish
Connect both layers with excellent UX.

---

## Detailed Implementation Plan

### PHASE 1: Intelligent Matching System (Days 1-3)

#### Day 1: Core Matching Logic (4-5 hours)

**Morning (2-3 hours): Multi-Scorer Fuzzy Matching**

```python
# src/slide_matcher.py - Update existing class

class SlideMatcher:
    def find_match(self, gs_product_name: str) -> SlideMatchResult:
        # STEP 1: Check manual mappings (NEW)
        if gs_product_name in MANUAL_PRODUCT_MAPPINGS:
            return manual_override_result()

        # STEP 2: Normalize name - strip variants (NEW)
        normalized = normalize_product_name(gs_product_name)

        # STEP 3: Try exact match on normalized name
        exact_match = try_exact_match(normalized)
        if exact_match:
            return SlideMatchResult(100%, exact_match)

        # STEP 4: Multi-scorer fuzzy matching (NEW)
        best_match, base_score = find_best_match_multi_scorer(
            normalized,
            self.pptx_products,
            scorers=[token_sort_ratio, token_set_ratio, partial_ratio]
        )

        # STEP 5: Apply keyword boosting (NEW)
        boosted_score = boost_score_if_same_category(
            gs_product_name,
            best_match,
            base_score
        )

        return SlideMatchResult(boosted_score, best_match, alternatives)
```

**Tasks:**
1. ✅ Update `SlideMatcher` class with multi-scorer logic
2. ✅ Implement `find_best_match_multi_scorer()` function
3. ✅ Add `CATEGORY_KEYWORDS` dictionary
4. ✅ Implement `boost_score_if_same_category()` function
5. ✅ Implement `normalize_product_name()` for variant stripping
6. ✅ Add `MANUAL_PRODUCT_MAPPINGS` dictionary
7. ⚠️ Test with all 19 Google Sheets products

**Deliverable:** Enhanced `src/slide_matcher.py` with 60-68% match rate

**Afternoon (2 hours): Testing & Validation**

```python
# Test script: test_matching_improvements.py

from src.slide_matcher import SlideMatcher
import gspread
# ... load data ...

# Test matching
matcher = SlideMatcher(pptx_product_names)
results = matcher.batch_match(gs_product_names)

# Generate report
summary = matcher.get_match_summary(results)
print(f"Match rate: {summary['usable_pct']:.1f}%")

# Show improvements
for result in results:
    print(f"{result.gs_product_name} → {result.pptx_product_name} ({result.confidence}%)")
```

**Tasks:**
1. Create test script to validate improvements
2. Run against all 19 products
3. Verify expected improvements (36% → 60%+)
4. Document any surprises or edge cases

**Deliverable:** Test report showing match rate improvement

---

#### Day 2: User Confirmation UI (4-5 hours)

**Morning (3 hours): Match Review Screen**

```python
# In app.py Tab 1 - new function

def show_match_review_ui(proposal_products, pptx_products):
    """
    Show match review screen with user confirmation for fuzzy matches.
    Returns: dict of confirmed matches {gs_name: pptx_name}
    """
    st.header("Review Product Matches Before Generating")

    # Get matches
    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match([p['product_data']['Product/Service']
                                   for p in proposal_products])

    # Categorize
    exact_matches = [r for r in results if r.match_type == 'exact']
    fuzzy_matches = [r for r in results if r.match_type == 'fuzzy' and r.confidence >= 70]
    no_matches = [r for r in results if r.confidence < 70]

    # Show summary
    st.info(f"""
    ✓ {len(exact_matches)} Exact matches (auto-confirmed)
    ~ {len(fuzzy_matches)} Fuzzy matches (need confirmation)
    ✗ {len(no_matches)} No matches (will skip)
    """)

    # Section 1: Exact matches (collapsed)
    with st.expander(f"✓ Exact Matches ({len(exact_matches)})", expanded=False):
        for r in exact_matches:
            st.success(f"{r.gs_product_name} → {r.pptx_product_name}")

    # Section 2: Fuzzy matches (MUST confirm)
    st.subheader(f"⚠ Fuzzy Matches ({len(fuzzy_matches)}) - Confirm Each One")

    confirmed_fuzzy = {}
    for result in fuzzy_matches:
        st.markdown(f"**{result.gs_product_name}**")
        st.caption(f"~ {result.confidence}% match: {result.pptx_product_name}")

        decision = st.radio(
            "Is this correct?",
            ["Yes, use this slide", "No, show alternatives", "Skip"],
            key=f"decision_{result.gs_product_name}",
            index=None  # No default
        )

        if decision == "Yes, use this slide":
            confirmed_fuzzy[result.gs_product_name] = result.pptx_product_name
        elif decision == "No, show alternatives":
            # Show alternatives UI (see below)
            pass
        elif decision == "Skip":
            confirmed_fuzzy[result.gs_product_name] = None

    # Section 3: No matches (info only)
    with st.expander(f"✗ No Matches ({len(no_matches)})", expanded=False):
        for r in no_matches:
            st.warning(f"{r.gs_product_name} - will be skipped")

    # Validation: All fuzzy matches confirmed?
    all_confirmed = len(confirmed_fuzzy) == len(fuzzy_matches)

    if not all_confirmed:
        st.warning("⚠ Confirm all fuzzy matches before generating")
        st.button("⚠ Confirm all fuzzy matches first", disabled=True)
        return None

    # Collect all confirmed matches
    confirmed = {r.gs_product_name: r.pptx_product_name for r in exact_matches}
    confirmed.update({k: v for k, v in confirmed_fuzzy.items() if v is not None})

    if st.button(f"Generate PowerPoint ({len(confirmed)} products)", type="primary"):
        return confirmed

    return None
```

**Tasks:**
1. Implement `show_match_review_ui()` function
2. Add summary section showing match counts
3. Add exact matches section (auto-confirmed, collapsed)
4. Add fuzzy matches section (radio buttons for each)
5. Add no matches section (info only, collapsed)
6. Add validation logic (disable button until all confirmed)
7. Test UX with sample data

**Deliverable:** Working match review UI with user confirmation

**Afternoon (1-2 hours): Alternative Selection UI**

```python
# Add to match review UI

if decision == "No, show alternatives":
    with st.expander("Select alternative match", expanded=True):
        alt_options = [f"{name} ({score}%)"
                      for name, score in result.alternatives]
        alt_options.append("None of these - Skip")

        alt_choice = st.radio(
            "Choose best match:",
            alt_options,
            key=f"alt_{result.gs_product_name}"
        )

        if alt_choice and alt_choice != "None of these - Skip":
            selected = alt_choice.split(" (")[0]
            confirmed_fuzzy[result.gs_product_name] = selected
        elif alt_choice == "None of these - Skip":
            confirmed_fuzzy[result.gs_product_name] = None
```

**Tasks:**
1. Add alternative selection expander
2. Show top 3 alternative matches
3. Allow user to select alternative or skip
4. Update confirmed matches based on selection
5. Test with products that have good alternatives

**Deliverable:** Complete match confirmation UI with alternatives

---

#### Day 3: Testing & Refinement (2-3 hours)

**Tasks:**
1. Test match review UI with all 19 products
2. Test edge cases:
   - All exact matches (no fuzzy)
   - All fuzzy matches (no exact)
   - No matches at all
   - Mix of all three
3. Test alternative selection flow
4. Verify validation works (can't proceed without confirming)
5. Get user feedback on UX
6. Refine based on feedback

**Deliverable:** Production-ready matching system with user confirmation

---

### PHASE 2: PowerPoint Generation Engine (Days 4-5)

**Prerequisites:** Phase 1 complete, matching system working

#### Day 4: Core PowerPoint Logic (4-5 hours)

**Morning (3 hours): Slide Extraction & Cloning**

```python
# src/pptx_generator.py - NEW MODULE

from pptx import Presentation
from pptx.util import Inches
import streamlit as st

def load_master_presentation():
    """Load master PowerPoint template."""
    return Presentation('templates/November All Slides.pptx')

def extract_product_names_from_slides(prs):
    """
    Extract all product names from slides.
    Returns: list of product names
    """
    product_names = []
    for slide in prs.slides:
        # Get first substantial text (product name)
        for shape in slide.shapes:
            if hasattr(shape, 'text') and len(shape.text.strip()) > 5:
                product_names.append(shape.text.strip())
                break
    return product_names

def find_slide_by_name(prs, product_name):
    """
    Find slide with matching product name.
    Returns: slide object or None
    """
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                if shape.text.strip().upper() == product_name.upper():
                    return slide
    return None

def clone_slide(source_slide, target_prs):
    """
    Clone entire slide preserving all formatting.
    Note: python-pptx doesn't have built-in slide cloning,
    so we need to use a workaround.
    """
    # Get slide layout from source
    slide_layout = source_slide.slide_layout

    # Add new slide to target with same layout
    new_slide = target_prs.slides.add_slide(slide_layout)

    # Copy all shapes from source to target
    for shape in source_slide.shapes:
        # Use element cloning (preserves formatting)
        el = shape.element
        newel = deepcopy(el)
        new_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')

    return new_slide
```

**Tasks:**
1. Create `src/pptx_generator.py` module
2. Implement `load_master_presentation()`
3. Implement `extract_product_names_from_slides()`
4. Implement `find_slide_by_name()`
5. Implement `clone_slide()` - research python-pptx slide cloning
6. Test slide cloning with 1-2 sample products
7. Verify formatting preservation (visual inspection)

**Deliverable:** Can clone slides with perfect formatting

**Afternoon (2 hours): Pricing Table Updates**

```python
# Continue src/pptx_generator.py

def update_pricing_table(slide, pricing_data):
    """
    Find pricing table and update cell values.
    Preserves all table formatting.

    pricing_data = {
        'moq': 10,
        'price_ea': 149.00,
        'ngo_price': 141.50,
        'delivery': '6-8 weeks'
    }
    """
    for shape in slide.shapes:
        if shape.has_table:
            table = shape.table

            # Verify it's a pricing table (has 3-4 columns)
            if len(table.columns) < 3:
                continue

            # Update data row (row 1, row 0 is headers)
            if len(table.rows) >= 2:
                # Column 0: MOQ
                table.rows[1].cells[0].text = str(pricing_data['moq'])

                # Column 1: Price Ea
                table.rows[1].cells[1].text = f"${pricing_data['price_ea']:.2f}"

                # Column 2: NGO Price (if exists)
                if len(table.columns) >= 3:
                    table.rows[1].cells[2].text = f"${pricing_data['ngo_price']:.2f}"

                # Column 3: Delivery (if exists)
                if len(table.columns) >= 4:
                    table.rows[1].cells[3].text = pricing_data['delivery']

                return True  # Success

    return False  # No table found
```

**Tasks:**
1. Implement `update_pricing_table()`
2. Handle variable table structures (3 or 4 columns)
3. Preserve cell formatting (fonts, colors, borders)
4. Test with various products
5. Handle edge cases (no table, wrong structure)

**Deliverable:** Can update pricing tables while preserving formatting

---

#### Day 5: Integration & Assembly (4-5 hours)

**Morning (3 hours): Main Generation Function**

```python
# Continue src/pptx_generator.py

def calculate_proposal_pricing_from_item(product_item):
    """
    Calculate pricing for a product item.
    Reuses logic from Tab 1 proposal tables.

    Returns: dict with pricing data
    """
    product_row = product_item['product_data']
    quantity = product_item['quantity']
    markup_percent = product_item['markup_percent']

    # Calculate MOQ
    moq = calculate_moq(...)  # From existing app logic

    # Get base price at MOQ
    base_price, tier, _ = get_unit_price_new_system(product_row, moq)

    # Apply markup
    markup_multiplier = 1 + (markup_percent / 100)
    price_ea = base_price * markup_multiplier

    # Calculate NGO discount (5%)
    ngo_price = price_ea * 0.95

    # Get delivery time from product data
    delivery = product_row.get('Lead Time', '6-8 weeks')

    return {
        'moq': moq,
        'price_ea': price_ea,
        'ngo_price': ngo_price,
        'delivery': delivery
    }

def generate_proposal_pptx(proposal_products, confirmed_matches, output_path):
    """
    Main generation function.

    Args:
        proposal_products: list of product items from st.session_state.proposal_products
        confirmed_matches: dict of {gs_product_name: pptx_product_name}
        output_path: where to save generated .pptx

    Returns:
        output_path if successful, None if failed
    """
    # Load master template
    master_prs = load_master_presentation()

    # Create new presentation for client
    client_prs = Presentation()

    slides_added = 0
    slides_failed = []

    # For each confirmed match
    for gs_product_name, pptx_product_name in confirmed_matches.items():
        # Find product item in proposal
        product_item = next(
            (p for p in proposal_products
             if p['product_data']['Product/Service'] == gs_product_name),
            None
        )

        if not product_item:
            st.warning(f"Product item not found: {gs_product_name}")
            continue

        # Find slide in master deck
        source_slide = find_slide_by_name(master_prs, pptx_product_name)

        if not source_slide:
            st.warning(f"Slide not found: {pptx_product_name}")
            slides_failed.append(gs_product_name)
            continue

        # Clone slide
        try:
            cloned_slide = clone_slide(source_slide, client_prs)
        except Exception as e:
            st.error(f"Failed to clone slide for {gs_product_name}: {e}")
            slides_failed.append(gs_product_name)
            continue

        # Calculate pricing
        pricing_data = calculate_proposal_pricing_from_item(product_item)

        # Update pricing table
        success = update_pricing_table(cloned_slide, pricing_data)

        if not success:
            st.warning(f"Could not update pricing table for {gs_product_name}")
            # Continue anyway - slide is still in deck, just with old pricing

        slides_added += 1

    # Save presentation
    if slides_added > 0:
        client_prs.save(output_path)
        return output_path, slides_added, slides_failed
    else:
        st.error("No slides were added to presentation")
        return None, 0, slides_failed
```

**Tasks:**
1. Implement `calculate_proposal_pricing_from_item()`
2. Implement `generate_proposal_pptx()` main function
3. Add error handling for each step
4. Add progress tracking (for UI)
5. Test end-to-end generation with 2-3 products
6. Verify generated .pptx opens correctly

**Deliverable:** Working PowerPoint generation engine

**Afternoon (2 hours): Integration with Tab 1**

```python
# In app.py Tab 1

st.divider()
st.subheader("5. Generate PowerPoint Proposal")

if len(st.session_state.proposal_products) == 0:
    st.caption("Add products to generate PowerPoint proposal")
else:
    if st.button("Generate PowerPoint Proposal", type="primary", use_container_width=True):
        # STEP 1: Load PowerPoint and extract product names
        from src.pptx_generator import load_master_presentation, extract_product_names_from_slides

        with st.spinner("Loading PowerPoint template..."):
            master_prs = load_master_presentation()
            pptx_products = extract_product_names_from_slides(master_prs)

        # STEP 2: Show match review UI (with user confirmation)
        confirmed_matches = show_match_review_ui(
            st.session_state.proposal_products,
            pptx_products
        )

        if confirmed_matches:
            # STEP 3: Generate PowerPoint with confirmed matches
            from src.pptx_generator import generate_proposal_pptx

            with st.spinner(f"Generating PowerPoint with {len(confirmed_matches)} products..."):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"output/proposal_{timestamp}.pptx"

                result_path, slides_added, slides_failed = generate_proposal_pptx(
                    st.session_state.proposal_products,
                    confirmed_matches,
                    output_path
                )

            # STEP 4: Show success and download button
            if result_path:
                st.success(f"✓ PowerPoint generated with {slides_added} products!")

                if slides_failed:
                    st.warning(f"⚠ {len(slides_failed)} products had issues: {', '.join(slides_failed)}")

                # Download button
                with open(result_path, 'rb') as f:
                    st.download_button(
                        label="Download PowerPoint Proposal",
                        data=f.read(),
                        file_name=f"PBP_Proposal_{timestamp}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary",
                        use_container_width=True
                    )
```

**Tasks:**
1. Add button to Tab 1
2. Connect to match review UI
3. Connect to PowerPoint generator
4. Add download functionality
5. Test complete flow
6. Handle errors gracefully

**Deliverable:** Complete integrated system in Tab 1

---

### PHASE 3: Testing & Polish (Days 6-7)

#### Day 6: Comprehensive Testing (Full day)

**Morning: Functional Testing**
1. Test with "Upcycled Executive Urban Briefcase" (exact match)
2. Test with fuzzy match products (confirm/reject/alternatives)
3. Test with all 19 products (full catalog)
4. Test with no matches (error handling)
5. Test with partial matches (7 products work, 12 skip)

**Afternoon: Edge Case Testing**
1. Empty proposal (no products)
2. Single product
3. 20+ products (performance)
4. Products with special characters in names
5. Products with missing slides
6. Products with malformed tables
7. Network interruptions during generation

**Deliverable:** Bug list and fixes

#### Day 7: Polish & Documentation (Full day)

**Morning: UX Polish**
1. Improve progress indicators
2. Better error messages
3. Add helpful tooltips
4. Improve match review layout
5. Add "Learn more" links

**Afternoon: Documentation**
1. Update user guide
2. Create troubleshooting doc
3. Document known limitations
4. Create demo video (optional)
5. Update CLAUDE.md with new feature

**Deliverable:** Production-ready feature with documentation

---

## Success Metrics

### Must Achieve (MVP)
- [ ] 60%+ match rate with fuzzy matching
- [ ] User can confirm all fuzzy matches before generating
- [ ] Generated .pptx preserves all slide formatting
- [ ] Pricing tables update correctly
- [ ] Complete workflow takes < 5 minutes (vs 20-30 min manual)

### Should Achieve (Quality)
- [ ] Generation completes in < 15 seconds for 10 products
- [ ] Clear error messages for common problems
- [ ] Works in Streamlit Cloud (production)
- [ ] File size < 50MB for typical proposals

### Nice to Have (Polish)
- [ ] Progress bar during generation
- [ ] Preview of matches before confirming
- [ ] Remember user confirmations (learned mappings)

---

## Risk Management

### Top Risks & Mitigation

**Risk 1: Slide cloning doesn't preserve formatting**
- Mitigation: Use python-pptx element cloning, test early
- Fallback: Manual workaround if needed
- Impact: HIGH - core feature broken

**Risk 2: Table update fails for some products**
- Mitigation: Detect table structure, handle variations
- Fallback: Skip table update, keep original pricing (user can edit)
- Impact: MEDIUM - degraded experience

**Risk 3: Matching rate still too low after improvements**
- Mitigation: Already designed to handle partial matches gracefully
- Fallback: Manual mappings for problem products
- Impact: LOW - UX handles this

**Risk 4: Performance issues with large decks**
- Mitigation: Test with 20+ products, optimize if needed
- Fallback: Limit to 15 products per proposal
- Impact: LOW - rare use case

---

## Decision Points

### When to Pause for User Feedback

1. **After Day 1:** Show matching improvements, get feedback on match quality
2. **After Day 2:** Demo match review UI, validate UX approach
3. **After Day 5:** Demo first generated PowerPoint, verify formatting
4. **After Day 6:** Full feature demo, collect feedback

### When to Ship

**Minimum Viable Feature:**
- Matching works (60%+ rate)
- Generation works (preserves formatting)
- User confirmation required
- Download works

**Nice to Have (Can Ship Later):**
- Perfect formatting preservation
- Cover slides
- Summary slides
- Analytics

---

## Next Steps

**Ready to start? Here's what I'll do:**

### Option A: Full Implementation (6-7 days)
Implement everything in sequence as outlined above.

### Option B: Proof of Concept (2-3 days)
Build just enough to demonstrate:
- Day 1: Enhanced matching (prove 60% rate)
- Day 2: Match review UI (prove UX works)
- Day 3: Simple PowerPoint generation (prove concept)

### Option C: Matching First (3 days)
Implement Phase 1 only (matching system), get feedback, then decide on Phase 2.

**My Recommendation: Option C (Matching First)**

**Why:**
- Matching is the foundation - must work first
- Can validate improvements with real data
- Get user feedback on UX before investing in generation
- Lower risk - can pause if matching isn't good enough

**After Phase 1 complete, we'll know:**
- Actual match rate (is 60% achievable?)
- UX is intuitive (users can confirm matches?)
- Any unexpected issues

**Then decide:** Proceed with Phase 2 or iterate on Phase 1?

---

**What would you like to do?**

---

## ✅ DECISION: Option C (Matching First) - APPROVED

**Date Approved:** 2025-11-04
**Rationale:** Build and validate matching system first (foundation), then proceed to PowerPoint generation

### Approved Plan: Phase 1 Only (3 Days)

**Scope:**
- Day 1: Core matching improvements
- Day 2: User confirmation UI
- Day 3: Testing & validation

**After Phase 1:**
- Assess match rate (target: 60%+)
- Validate UX with user
- Decide whether to proceed to Phase 2 (PowerPoint generation)

**Phase 2 (Future):**
- Will be implemented ONLY if Phase 1 succeeds
- Estimated 3-4 additional days
- Depends on Phase 1 results

---

**Document Version:** 1.1
**Last Updated:** 2025-11-04
**Status:** APPROVED - Phase 1 Implementation Starting
