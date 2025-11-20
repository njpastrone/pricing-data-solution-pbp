# Phase 1 Implementation Guide - Matching System

**Approved Plan:** Option C (Matching First)
**Duration:** 3 days
**Goal:** Build and validate intelligent matching system with user confirmation
**Date Started:** 2025-11-04

---

## Overview

This phase focuses ONLY on the matching system (Layer 1). PowerPoint generation (Layer 2) will be implemented later if this phase succeeds.

**Success Criteria:**
- ✅ Match rate improves from 36.8% to 60%+
- ✅ User can confirm all fuzzy matches via intuitive UI
- ✅ System handles partial matches gracefully
- ✅ Ready for Phase 2 decision

---

## Day 1: Core Matching Improvements (4-5 hours)

### Morning Session (2-3 hours): Enhanced Matching Logic

**Goal:** Implement multi-scorer fuzzy matching with keyword boosting

**File to Edit:** `src/slide_matcher.py`

#### Task 1.1: Add Multi-Scorer Function (45 min)

```python
# Add to src/slide_matcher.py

from thefuzz import fuzz, process
from typing import Tuple, List

def find_best_match_multi_scorer(
    query: str,
    choices: List[str],
    limit: int = 3
) -> Tuple[str, int, str, List[Tuple[str, int]]]:
    """
    Use multiple fuzzy matching algorithms and return best result.

    Args:
        query: Product name from Google Sheets
        choices: List of product names from PowerPoint
        limit: Number of alternatives to return

    Returns:
        (best_match_name, best_score, method_used, alternatives)
    """
    scorers = [
        ('token_sort_ratio', fuzz.token_sort_ratio),
        ('token_set_ratio', fuzz.token_set_ratio),
        ('partial_ratio', fuzz.partial_ratio),
    ]

    best_match = None
    best_score = 0
    best_method = None
    all_results = {}

    # Try each scorer
    for method_name, scorer in scorers:
        matches = process.extract(query, choices, scorer=scorer, limit=limit)

        # Store all results
        all_results[method_name] = matches

        # Track best score across all methods
        if matches and matches[0][1] > best_score:
            best_score = matches[0][1]
            best_match = matches[0][0]
            best_method = method_name

    # Get alternatives from best method
    alternatives = []
    if best_method and best_method in all_results:
        alternatives = all_results[best_method][1:]  # Skip first (it's best_match)

    return best_match, best_score, best_method, alternatives
```

**Test:** Run with sample products, verify it returns better scores than single scorer

#### Task 1.2: Add Keyword Category Boosting (45 min)

```python
# Add to src/slide_matcher.py

CATEGORY_KEYWORDS = {
    'bag': ['BAG', 'BRIEFCASE', 'BACKPACK', 'TOTE', 'DUFFLE', 'SLING', 'POUCH'],
    'sleeve': ['SLEEVE', 'CASE', 'COVER'],
    'cutting_board': ['CUTTING', 'BOARD', 'BUTCHER'],
    'wood_product': ['WOOD', 'WOODEN', 'SPATULA', 'SPOON'],
    'textile': ['SCARF', 'APRON', 'THROW', 'QUILT', 'BLANKET'],
    'candle': ['CANDLE', 'HOLDER'],
    'jewelry': ['BRACELET', 'NECKLACE', 'EARRING', 'RING'],
    'writing': ['PEN', 'PENCIL', 'JOURNAL', 'NOTEBOOK'],
}

def detect_category(product_name: str) -> Optional[str]:
    """
    Detect product category based on keywords.
    Returns: category name or None
    """
    product_upper = product_name.upper()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in product_upper for kw in keywords):
            return category

    return None

def boost_score_if_same_category(
    gs_product: str,
    pptx_product: str,
    base_score: int
) -> int:
    """
    Boost score if both products are in same category.

    Args:
        gs_product: Google Sheets product name
        pptx_product: PowerPoint product name
        base_score: Base confidence score (0-100)

    Returns:
        Boosted score (max 100)
    """
    gs_category = detect_category(gs_product)
    pptx_category = detect_category(pptx_product)

    # Both must have a category AND it must match
    if gs_category and pptx_category and gs_category == pptx_category:
        boost = 15  # Add 15 points
        return min(base_score + boost, 100)

    return base_score
```

**Test:** Verify "Cutting Board" products get boosted when matched with other cutting boards

#### Task 1.3: Add Variant Stripping (30 min)

```python
# Add to src/slide_matcher.py

import re

VARIANT_PATTERNS = [
    r'\([^)]+\)',           # Parentheses: (Noir), (CZI), (Enfold)
    r'-[A-Z]{2,4}$',        # Suffixes: -MOF, -CZI
    r'\s*-\s*(Large|Medium|Small|XL|L|M|S)',  # Size variants
    r'\s*–\s*Set of \d+',   # Set notation
]

def normalize_product_name(name: str) -> str:
    """
    Strip variant identifiers to get base product name.

    Examples:
        "Upcycled Laptop Sleeve (Enfold)-MOF" -> "Upcycled Laptop Sleeve"
        "Butcher Block - Large" -> "Butcher Block"
        "Candle Holders – Set of 3" -> "Candle Holders"
    """
    normalized = name

    for pattern in VARIANT_PATTERNS:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Clean up extra whitespace
    normalized = ' '.join(normalized.split())

    return normalized.strip()
```

**Test:** Verify variant names get normalized correctly

#### Task 1.4: Add Manual Mappings (15 min)

```python
# Add to src/slide_matcher.py

MANUAL_PRODUCT_MAPPINGS = {
    # Google Sheets Name -> PowerPoint Slide Name
    # Add known mappings here as discovered

    # Example (uncomment if confirmed):
    # "Alabaster + Tigerwood Cutting Board": "SELVA CUTTING BOARD",
}
```

**Test:** Add one test mapping and verify it works

#### Task 1.5: Update SlideMatcher.find_match() (60 min)

```python
# Update existing method in src/slide_matcher.py

class SlideMatcher:
    def find_match(self, gs_product_name: str, num_alternatives: int = 3) -> SlideMatchResult:
        """
        Find best matching PowerPoint slide with all improvements.

        Matching Logic:
        1. Check manual mappings (100% confidence)
        2. Normalize product name (strip variants)
        3. Try exact match on normalized name (100% confidence)
        4. Multi-scorer fuzzy match
        5. Apply keyword category boosting
        6. Return result with alternatives
        """
        # STEP 1: Check manual mappings first
        if gs_product_name in MANUAL_PRODUCT_MAPPINGS:
            mapped_name = MANUAL_PRODUCT_MAPPINGS[gs_product_name]
            if mapped_name in self.pptx_product_names:
                return SlideMatchResult(
                    gs_product_name=gs_product_name,
                    pptx_product_name=mapped_name,
                    match_type='manual',
                    confidence=100,
                    alternatives=[]
                )

        # STEP 2: Normalize product name
        normalized_name = normalize_product_name(gs_product_name)

        # STEP 3: Try exact match on normalized name
        normalized_upper = normalized_name.upper()
        if normalized_upper in self.pptx_upper_map:
            exact_match = self.pptx_upper_map[normalized_upper]
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=exact_match,
                match_type='exact',
                confidence=100,
                alternatives=[]
            )

        # STEP 4: Multi-scorer fuzzy matching
        best_match, base_score, method, alternatives = find_best_match_multi_scorer(
            normalized_name,
            self.pptx_product_names,
            limit=num_alternatives
        )

        if not best_match:
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=None,
                match_type='none',
                confidence=0,
                alternatives=[]
            )

        # STEP 5: Apply keyword category boosting
        boosted_score = boost_score_if_same_category(
            gs_product_name,
            best_match,
            base_score
        )

        return SlideMatchResult(
            gs_product_name=gs_product_name,
            pptx_product_name=best_match,
            match_type='fuzzy',
            confidence=boosted_score,
            alternatives=alternatives
        )
```

**Test:** Run with all 19 Google Sheets products, verify improvements

---

### Afternoon Session (2 hours): Testing & Validation

#### Task 1.6: Create Test Script (30 min)

```python
# Create new file: test_matching_improvements.py

from src.slide_matcher import SlideMatcher
import gspread
from google.oauth2.service_account import Credentials
import toml

# Load data
secrets = toml.load('.streamlit/secrets.toml')
credentials = Credentials.from_service_account_info(
    secrets['gcp_service_account'],
    scopes=['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive']
)

client = gspread.authorize(credentials)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs"
spreadsheet = client.open_by_url(spreadsheet_url)

# Load Google Sheets products
template_sheet = spreadsheet.worksheet("Template")
template_values = template_sheet.get_all_values()
# ... extract product names ...

# Load PowerPoint products
with open('product_names_from_slides.txt', 'r') as f:
    pptx_products = [line.strip() for line in f if line.strip()]

# Test matching
print("TESTING MATCHING IMPROVEMENTS")
print("=" * 80)

matcher = SlideMatcher(pptx_products)
results = matcher.batch_match(gs_product_names)

# Show results
for result in results:
    icon = "✓" if result.match_type == 'exact' else "~" if result.confidence >= 70 else "✗"
    print(f"{icon} {result.gs_product_name}")
    print(f"   → {result.pptx_product_name} ({result.confidence}%, {result.match_type})")
    print()

# Summary
summary = matcher.get_match_summary(results)
print("=" * 80)
print(f"SUMMARY:")
print(f"  Exact matches: {summary['exact']}")
print(f"  Fuzzy matches (≥70%): {summary['fuzzy']}")
print(f"  Poor matches (<70%): {summary['poor']}")
print(f"  No matches: {summary['none']}")
print(f"  Total usable: {summary['usable']} ({summary['usable_pct']:.1f}%)")
```

**Run:** Execute script and verify 60%+ match rate

#### Task 1.7: Document Results (30 min)

Create report showing:
- Before/after match rates
- Which products improved
- Which products still don't match
- Any surprises or issues

#### Task 1.8: Update requirements.txt (5 min)

Verify all dependencies are listed:
```
streamlit
gspread
pandas
google-auth
python-pptx
thefuzz
python-Levenshtein
```

**Deliverable:** Enhanced matching system achieving 60%+ match rate

---

## Day 2: User Confirmation UI (4-5 hours)

### Morning Session (3 hours): Match Review Screen

**Goal:** Build UI that shows all matches and requires user confirmation for fuzzy matches

**File to Edit:** `app.py` (Tab 1)

#### Task 2.1: Create Match Review Function (2 hours)

```python
# Add to app.py

def show_match_review_ui(proposal_products, pptx_products):
    """
    Show match review screen with user confirmation for fuzzy matches.

    Returns:
        dict of confirmed matches {gs_product_name: pptx_product_name}
        OR None if not all fuzzy matches confirmed
    """
    st.header("Review Product Matches Before Generating")
    st.caption("Please confirm fuzzy matches before generating your proposal.")

    # Initialize matcher
    from src.slide_matcher import SlideMatcher
    matcher = SlideMatcher(pptx_products)

    # Get all matches
    product_names = [p['product_data']['Product/Service'] for p in proposal_products]
    match_results = matcher.batch_match(product_names)

    # Categorize matches
    exact_matches = [r for r in match_results if r.match_type in ['exact', 'manual']]
    fuzzy_matches = [r for r in match_results if r.match_type == 'fuzzy' and r.confidence >= 70]
    no_matches = [r for r in match_results if r.match_type == 'none' or r.confidence < 70]

    # Show summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✓ Exact Matches", len(exact_matches))
    with col2:
        st.metric("~ Fuzzy Matches", len(fuzzy_matches))
    with col3:
        st.metric("✗ No Matches", len(no_matches))

    st.divider()

    # Section 1: Exact Matches (auto-confirmed, collapsed)
    if exact_matches:
        with st.expander(f"✓ Exact Matches ({len(exact_matches)}) - Auto-confirmed", expanded=False):
            for result in exact_matches:
                st.success(f"**{result.gs_product_name}**")
                st.caption(f"→ {result.pptx_product_name}")
                st.divider()

    # Section 2: Fuzzy Matches (MUST confirm)
    if fuzzy_matches:
        st.subheader(f"⚠ Fuzzy Matches ({len(fuzzy_matches)}) - Confirm Each One")
        st.caption("Please review and confirm each fuzzy match below.")

        # Initialize session state for decisions
        if 'fuzzy_match_decisions' not in st.session_state:
            st.session_state.fuzzy_match_decisions = {}

        confirmed_count = 0

        for idx, result in enumerate(fuzzy_matches, 1):
            st.markdown(f"### {idx}. {result.gs_product_name}")

            # Show confidence badge
            if result.confidence >= 90:
                badge = "🟢 Excellent"
            elif result.confidence >= 80:
                badge = "🟡 Very Good"
            else:
                badge = "🟠 Good"

            st.caption(f"{badge} match ({result.confidence}%): **{result.pptx_product_name}**")
            st.markdown("**Is this the correct slide for this product?**")

            # Radio button for decision
            decision_key = f"decision_{result.gs_product_name}_{idx}"

            decision = st.radio(
                label=f"Decision for {result.gs_product_name}",
                options=[
                    "Yes, use this slide",
                    "No, show alternatives",
                    "Skip this product"
                ],
                key=decision_key,
                index=None,  # No default - user MUST choose
                label_visibility="collapsed"
            )

            # Handle decision
            if decision == "Yes, use this slide":
                st.session_state.fuzzy_match_decisions[result.gs_product_name] = result.pptx_product_name
                confirmed_count += 1
                st.success("✓ Confirmed")

            elif decision == "Skip this product":
                st.session_state.fuzzy_match_decisions[result.gs_product_name] = None
                confirmed_count += 1
                st.info("Product will be skipped")

            elif decision == "No, show alternatives":
                # Show alternatives (Task 2.2)
                pass

            st.divider()

        # Validation message
        if confirmed_count < len(fuzzy_matches):
            st.warning(f"⚠ You must confirm all {len(fuzzy_matches)} fuzzy matches before generating.")

    # Section 3: No Matches (info only, collapsed)
    if no_matches:
        with st.expander(f"✗ No Matches ({len(no_matches)}) - Will Be Skipped", expanded=False):
            for result in no_matches:
                st.warning(f"**{result.gs_product_name}**")
                st.caption(f"Best match: {result.pptx_product_name} ({result.confidence}%)")
                st.caption("This product will be skipped.")
                st.divider()

    st.divider()

    # Section 4: Generation Preview
    st.subheader("Generation Preview")

    confirmed_fuzzy = sum(1 for v in st.session_state.fuzzy_match_decisions.values() if v is not None)
    total_confirmed = len(exact_matches) + confirmed_fuzzy
    total_skipped = len(no_matches) + len([v for v in st.session_state.fuzzy_match_decisions.values() if v is None])

    st.info(f"""
    **Will be included:** {total_confirmed} products
    - {len(exact_matches)} exact matches
    - {confirmed_fuzzy} fuzzy matches (confirmed by you)

    **Will be skipped:** {total_skipped} products
    """)

    # Validation: All fuzzy matches confirmed?
    all_confirmed = len(st.session_state.fuzzy_match_decisions) == len(fuzzy_matches)

    if not all_confirmed:
        st.button(
            "⚠ Confirm all fuzzy matches first",
            disabled=True,
            type="primary",
            use_container_width=True
        )
        return None

    if total_confirmed == 0:
        st.error("No products confirmed. Cannot generate empty proposal.")
        return None

    # Ready to generate!
    if st.button(
        f"Generate PowerPoint ({total_confirmed} products)",
        type="primary",
        use_container_width=True
    ):
        # Collect all confirmed matches
        confirmed_matches = {}

        # Add exact matches
        for result in exact_matches:
            confirmed_matches[result.gs_product_name] = result.pptx_product_name

        # Add confirmed fuzzy matches
        for gs_name, pptx_name in st.session_state.fuzzy_match_decisions.items():
            if pptx_name is not None:
                confirmed_matches[gs_name] = pptx_name

        return confirmed_matches

    return None
```

**Test:** Run in Streamlit, verify UI looks good and validation works

#### Task 2.2: Add Alternative Selection UI (1 hour)

Update the "No, show alternatives" section:

```python
elif decision == "No, show alternatives":
    with st.expander("Select alternative match", expanded=True):
        st.caption("Choose the best match from the options below:")

        # Build alternative options
        alt_options = []
        for alt_name, alt_score in result.alternatives:
            alt_options.append(f"{alt_name} ({alt_score}%)")
        alt_options.append("None of these - Skip this product")

        # Radio button for alternatives
        alt_key = f"alt_{result.gs_product_name}_{idx}"
        alt_choice = st.radio(
            label=f"Alternatives for {result.gs_product_name}",
            options=alt_options,
            key=alt_key,
            index=0,  # Pre-select first alternative (best)
            label_visibility="collapsed"
        )

        if alt_choice:
            if alt_choice == "None of these - Skip this product":
                st.session_state.fuzzy_match_decisions[result.gs_product_name] = None
                confirmed_count += 1
                st.info("Product will be skipped")
            else:
                # Extract slide name from "NAME (XX%)" format
                selected_slide = alt_choice.split(" (")[0]
                st.session_state.fuzzy_match_decisions[result.gs_product_name] = selected_slide
                confirmed_count += 1
                st.success(f"✓ Confirmed: {selected_slide}")
```

**Test:** Verify alternative selection works

---

### Afternoon Session (1-2 hours): Integration & Testing

#### Task 2.3: Integrate into Tab 1 (30 min)

```python
# In app.py Tab 1, add after "Generate Proposal Tables" section

st.divider()
st.subheader("5. Generate PowerPoint Proposal")

if len(st.session_state.proposal_products) == 0:
    st.caption("Add products to generate PowerPoint proposal")
else:
    st.markdown("""
    Generate a complete PowerPoint presentation with selected products.
    You'll review and confirm all product matches before generating.
    """)

    if st.button("Review Matches & Generate PowerPoint", type="primary", use_container_width=True):
        # Load PowerPoint product names
        from pptx import Presentation

        with st.spinner("Loading PowerPoint template..."):
            prs = Presentation('templates/November All Slides.pptx')

            # Extract product names from slides
            pptx_products = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and len(shape.text.strip()) > 5:
                        pptx_products.append(shape.text.strip())
                        break

        # Show match review UI
        confirmed_matches = show_match_review_ui(
            st.session_state.proposal_products,
            pptx_products
        )

        if confirmed_matches:
            st.success(f"✓ Ready to generate with {len(confirmed_matches)} confirmed products!")
            st.info("Phase 2 (PowerPoint generation) not yet implemented. This is Phase 1 testing.")
```

**Test:** Full workflow from adding products to confirming matches

#### Task 2.4: Test Edge Cases (1 hour)

Test these scenarios:
1. All exact matches (no fuzzy)
2. All fuzzy matches (no exact)
3. No matches at all
4. User rejects all fuzzy matches (skips all)
5. User selects alternatives
6. Empty proposal (no products)

**Deliverable:** Working match review UI with user confirmation

---

## Day 3: Testing & Documentation (2-3 hours)

### Task 3.1: Comprehensive Testing (1.5 hours)

1. Test with all 19 Google Sheets products
2. Verify match rate is 60%+
3. Test user confirmation flow
4. Test alternative selection
5. Verify validation works
6. Test in Streamlit Cloud (if deployed)

### Task 3.2: Create Results Report (1 hour)

Document:
- Final match rate achieved
- Breakdown by match type
- User feedback on UX
- Any issues or limitations discovered
- Recommendations for Phase 2

### Task 3.3: Update Documentation (30 min)

Update these files:
- CLAUDE.md (add Phase 1 completion status)
- README.md (if needed)
- Phase 1 results summary

**Deliverable:** Complete Phase 1 with results report

---

## Success Criteria

### Must Achieve
- [ ] Match rate ≥60% (11+ of 19 products)
- [ ] User can confirm all fuzzy matches
- [ ] UI is intuitive and clear
- [ ] No crashes or major bugs
- [ ] Works on local development

### Should Achieve
- [ ] Match rate ≥65% (12+ of 19 products)
- [ ] Alternative selection works smoothly
- [ ] Clear error messages
- [ ] Good performance (< 3 sec for matching)

### Nice to Have
- [ ] Match rate ≥70% (13+ of 19 products)
- [ ] Works in Streamlit Cloud
- [ ] User feedback is positive

---

## After Phase 1: Decision Point

### If Success (60%+ match rate, good UX):
→ **GREEN LIGHT for Phase 2** (PowerPoint generation)
→ 3-4 more days to complete full feature

### If Needs Iteration (50-59% match rate):
→ **YELLOW LIGHT**
→ 1-2 days more work on Phase 1
→ Then reassess

### If Fundamental Issues (<50% match rate):
→ **RED LIGHT**
→ Reassess approach
→ May need different strategy

---

**Ready to begin Day 1 implementation!**
