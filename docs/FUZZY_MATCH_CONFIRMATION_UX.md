# Fuzzy Match Confirmation - User Experience Design

**Principle:** Never auto-apply fuzzy matches. Always require user confirmation.

**Date:** 2025-11-04
**Status:** Final Design

---

## Core Rule

```
if match_type == "exact" (100% confidence):
    → Auto-apply (no confirmation needed)

if match_type == "fuzzy" (<100% confidence):
    → ALWAYS show to user for confirmation
    → User must explicitly approve or reject
    → Never proceed without user input
```

**Why:** Even high-confidence fuzzy matches (90%+) can be wrong. User knows their products best.

---

## User Flow

### Step 1: User Clicks "Generate PowerPoint Proposal"

App immediately shows **Match Review Screen** (blocking modal/full screen).

### Step 2: Match Review Screen

User sees all products with match status and MUST review before proceeding.

```
┌─────────────────────────────────────────────────────────────────┐
│  Review Product Matches Before Generating                       │
│                                                                  │
│  Please confirm fuzzy matches before generating your proposal.  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Match Summary:                                                 │
│  ✓ 7 Exact matches (auto-confirmed)                             │
│  ~ 4 Fuzzy matches (need your confirmation)                     │
│  ✗ 8 No matches (will be skipped)                               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXACT MATCHES (7) - Auto-confirmed ✓                           │
│  ──────────────────────────────────────────────────────────     │
│                                                                  │
│  1. Upcycled Executive Urban Briefcase                           │
│     ✓ Exact match: UPCYCLED EXECUTIVE URBAN BRIEFCASE           │
│     Status: Confirmed automatically                             │
│                                                                  │
│  2. [6 more exact matches...]                                    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FUZZY MATCHES (4) - Confirm each one below ⚠                   │
│  ──────────────────────────────────────────────────────────     │
│                                                                  │
│  3. Upcycled Day Tripper Backpack (Noir)                         │
│     ~ Excellent match (92%): UPCYCLED DAY TRIPPER BACKPACK      │
│     Is this the correct slide for this product?                 │
│     ( ) Yes, use this slide                                     │
│     ( ) No, show alternatives                                   │
│     ( ) Skip this product                                       │
│                                                                  │
│  4. Candle Holders - Set of 3                                    │
│     ~ Good match (81%): MINIMALIST CANDLE HOLDERS – Set of 3    │
│     Is this the correct slide for this product?                 │
│     (•) Yes, use this slide        ← User selected              │
│     ( ) No, show alternatives                                   │
│     ( ) Skip this product                                       │
│                                                                  │
│  5. Upcycled Laptop Sleeve (Enfold)-MOF                          │
│     ~ Good match (80%): UPCYCLED LAPTOP SLEEVE                  │
│     Is this the correct slide for this product?                 │
│     ( ) Yes, use this slide                                     │
│     (•) No, show alternatives      ← User wants to see options  │
│                                                                  │
│  6. Alabaster + Tigerwood Cutting Board                          │
│     ~ Uncertain match (73%): SELVA CUTTING BOARD                │
│     Is this the correct slide for this product?                 │
│     ( ) Yes, use this slide                                     │
│     ( ) No, show alternatives                                   │
│     (•) Skip this product          ← User rejected              │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  NO MATCHES (8) - Will be skipped                               │
│  ──────────────────────────────────────────────────────────     │
│                                                                  │
│  7. Lavender Shortbread Mix                                      │
│     ✗ No good match found (best: CREAM SCONE MIX, 51%)          │
│     This product will be skipped.                               │
│                                                                  │
│  8. [7 more no-match products...]                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Generation Preview:                                            │
│  • 7 products confirmed (exact matches)                         │
│  • 1 product confirmed (fuzzy match - user approved)            │
│  • 1 product pending (awaiting alternatives selection)          │
│  • 10 products will be skipped                                  │
│                                                                  │
│  ⚠ You must confirm all fuzzy matches before generating.        │
│                                                                  │
│  [Generate PowerPoint (8 products)]  [Cancel]                   │
│  ↑ Disabled until all fuzzy matches confirmed                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Show Alternatives (Expandable)

When user selects "No, show alternatives":

```
┌─────────────────────────────────────────────────────────────────┐
│  Select Best Match: Upcycled Laptop Sleeve (Enfold)-MOF         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Top Matches:                                                   │
│                                                                  │
│  (•) UPCYCLED LAPTOP SLEEVE                      80% ← Suggested│
│                                                                  │
│  ( ) UPCYCLED DENIM SLIM LAPTOP SLEEVE           76%            │
│                                                                  │
│  ( ) UPCYCLED BOUNCY CASTLE LAPTOP SLEEVE        72%            │
│                                                                  │
│  ( ) None of these - Skip this product                          │
│                                                                  │
│  [Confirm Selection]  [Cancel]                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 4: Validation Before Generation

**Cannot proceed until:**
- ✓ All fuzzy matches have a user decision (approve/alternative/skip)
- ✓ At least 1 product is confirmed (exact or fuzzy)

**Generate button states:**
```
[Generate PowerPoint (8 products)]        ← Enabled, shows count
[⚠ Confirm all fuzzy matches first]       ← Disabled, shows reason
```

### Step 5: Generation with Confirmed Matches

Once all confirmations received:

```
┌─────────────────────────────────────────────────────────────────┐
│  Generating PowerPoint Proposal...                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✓ Cloned slide: UPCYCLED EXECUTIVE URBAN BRIEFCASE            │
│  ✓ Cloned slide: UPCYCLED DAY TRIPPER BACKPACK                 │
│  ✓ Cloned slide: MINIMALIST CANDLE HOLDERS – Set of 3          │
│  ✓ Cloned slide: UPCYCLED LAPTOP SLEEVE                        │
│  ⏳ Updating pricing tables...                                  │
│                                                                  │
│  Progress: ████████████████░░░░  75%                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 6: Success with Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  ✓ PowerPoint Proposal Generated Successfully                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Your proposal includes 8 products.                             │
│  11 products were skipped.                                      │
│                                                                  │
│  Included:                                                      │
│   ✓ 7 exact matches                                             │
│   ✓ 1 fuzzy match (confirmed by you)                            │
│                                                                  │
│  Skipped products:                                              │
│   • Alabaster + Tigerwood Cutting Board (you chose to skip)     │
│   • Lavender Shortbread Mix (no matching slide)                 │
│   • [9 more...]                                                 │
│                                                                  │
│  [Download PowerPoint (PBP_Proposal_20251104.pptx)]             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key UX Principles

### 1. Explicit Confirmation Required

**Never auto-apply fuzzy matches**, even at 99% confidence.

**Rationale:**
- User knows their products better than algorithm
- Wrong match = broken proposal sent to client
- Confirmation takes 2 seconds, error recovery takes 20 minutes

### 2. Clear Visual Hierarchy

**Match Types:**
- ✓ **Green** = Exact match (auto-confirmed)
- ~ **Yellow** = Fuzzy match (needs confirmation)
- ✗ **Gray** = No match (will skip)

**Confidence Indicators:**
- 90-99%: "Excellent match"
- 80-89%: "Very good match"
- 70-79%: "Good match"
- 60-69%: "Uncertain match"
- <60%: Not shown as option

### 3. Progressive Disclosure

**Default view:**
- Show all products in one screen
- Radio buttons for fuzzy matches (inline)
- Expand only when user asks for alternatives

**Why:** Don't overwhelm user with details. Show everything they need to decide, hide extra complexity until requested.

### 4. Action-Oriented Language

**Bad:** "Confidence: 81%"
**Good:** "Is this the correct slide for this product?"

**Bad:** "Match found"
**Good:** "Yes, use this slide"

**Rationale:** User thinks in terms of actions, not technical metrics.

### 5. Safe Defaults

**Pre-selected option:** None (user must choose)

**Not:** Pre-select "Yes, use this slide" (dangerous - user might not notice)

**Rationale:** Require intentional action for fuzzy matches.

---

## Streamlit Implementation

### Code Structure

```python
import streamlit as st
from src.slide_matcher import SlideMatcher, SlideMatchResult

def show_match_review_ui(proposal_products, pptx_products):
    """
    Show match review screen and collect user confirmations.
    Returns: dict of {product_name: confirmed_slide_name}
    """
    st.header("Review Product Matches Before Generating")
    st.caption("Please confirm fuzzy matches before generating your proposal.")

    # Initialize matcher
    matcher = SlideMatcher(pptx_products)

    # Get all matches
    match_results = matcher.batch_match(
        [p['product_data']['Product/Service'] for p in proposal_products]
    )

    # Categorize matches
    exact_matches = [r for r in match_results if r.match_type == 'exact']
    fuzzy_matches = [r for r in match_results if r.match_type == 'fuzzy' and r.confidence >= 70]
    no_matches = [r for r in match_results if r.match_type == 'none' or r.confidence < 70]

    # Show summary
    st.info(f"""
    Match Summary:
    - ✓ {len(exact_matches)} Exact matches (auto-confirmed)
    - ~ {len(fuzzy_matches)} Fuzzy matches (need your confirmation)
    - ✗ {len(no_matches)} No matches (will be skipped)
    """)

    # Section 1: Exact Matches (auto-confirmed)
    if exact_matches:
        with st.expander(f"✓ Exact Matches ({len(exact_matches)}) - Auto-confirmed", expanded=False):
            for result in exact_matches:
                st.success(f"**{result.gs_product_name}**")
                st.caption(f"→ {result.pptx_product_name}")

    # Section 2: Fuzzy Matches (need confirmation)
    st.divider()
    st.subheader(f"⚠ Fuzzy Matches ({len(fuzzy_matches)}) - Confirm each one")

    # Store user decisions in session state
    if 'fuzzy_match_decisions' not in st.session_state:
        st.session_state.fuzzy_match_decisions = {}

    confirmed_count = 0

    for idx, result in enumerate(fuzzy_matches):
        st.markdown(f"**{idx+1}. {result.gs_product_name}**")

        # Confidence badge
        if result.confidence >= 90:
            badge = "🟢 Excellent"
        elif result.confidence >= 80:
            badge = "🟡 Very Good"
        else:
            badge = "🟠 Good"

        st.caption(f"{badge} match ({result.confidence}%): {result.pptx_product_name}")
        st.markdown("**Is this the correct slide for this product?**")

        # Radio button for user decision
        decision_key = f"decision_{result.gs_product_name}"

        decision = st.radio(
            label=f"Decision for {result.gs_product_name}",
            options=["Yes, use this slide", "No, show alternatives", "Skip this product"],
            key=decision_key,
            label_visibility="collapsed",
            index=None  # No default selection (user must choose)
        )

        # Handle "show alternatives"
        if decision == "No, show alternatives":
            with st.expander("View alternative matches", expanded=True):
                st.caption("Select the best match:")
                alt_options = [f"{name} ({score}%)" for name, score in result.alternatives]
                alt_options.append("None of these - Skip this product")

                alt_decision = st.radio(
                    label=f"Alternatives for {result.gs_product_name}",
                    options=alt_options,
                    key=f"alt_{decision_key}",
                    label_visibility="collapsed"
                )

                if alt_decision and alt_decision != "None of these - Skip this product":
                    # Extract slide name from "NAME (XX%)" format
                    selected_slide = alt_decision.split(" (")[0]
                    st.session_state.fuzzy_match_decisions[result.gs_product_name] = selected_slide
                    confirmed_count += 1
                elif alt_decision == "None of these - Skip this product":
                    st.session_state.fuzzy_match_decisions[result.gs_product_name] = None
                    confirmed_count += 1

        elif decision == "Yes, use this slide":
            st.session_state.fuzzy_match_decisions[result.gs_product_name] = result.pptx_product_name
            confirmed_count += 1

        elif decision == "Skip this product":
            st.session_state.fuzzy_match_decisions[result.gs_product_name] = None
            confirmed_count += 1

        st.divider()

    # Section 3: No Matches (will skip)
    if no_matches:
        with st.expander(f"✗ No Matches ({len(no_matches)}) - Will be skipped", expanded=False):
            for result in no_matches:
                st.warning(f"**{result.gs_product_name}**")
                st.caption(f"No good match found (best: {result.pptx_product_name}, {result.confidence}%)")

    # Section 4: Generation Preview & Button
    st.divider()
    st.subheader("Generation Preview")

    total_confirmed = len(exact_matches) + confirmed_count
    total_skipped = len(fuzzy_matches) - confirmed_count + len(no_matches)

    st.info(f"""
    - {len(exact_matches)} products confirmed (exact matches)
    - {confirmed_count} products confirmed (fuzzy matches you approved)
    - {total_skipped} products will be skipped
    """)

    # Validation: All fuzzy matches must have decisions
    all_confirmed = confirmed_count == len(fuzzy_matches)
    has_products = total_confirmed > 0

    if not all_confirmed:
        st.warning(f"⚠ You must confirm all {len(fuzzy_matches)} fuzzy matches before generating.")
        st.button(
            f"⚠ Confirm all fuzzy matches first",
            disabled=True,
            use_container_width=True,
            type="primary"
        )
        return None

    elif not has_products:
        st.error("✗ No products confirmed. Cannot generate empty proposal.")
        return None

    else:
        # Ready to generate!
        if st.button(
            f"Generate PowerPoint ({total_confirmed} products)",
            use_container_width=True,
            type="primary"
        ):
            # Collect all confirmed matches
            confirmed_matches = {}

            # Add exact matches
            for result in exact_matches:
                confirmed_matches[result.gs_product_name] = result.pptx_product_name

            # Add confirmed fuzzy matches
            for gs_name, pptx_name in st.session_state.fuzzy_match_decisions.items():
                if pptx_name is not None:  # Skip if user chose to skip
                    confirmed_matches[gs_name] = pptx_name

            return confirmed_matches

    return None
```

### Integration in Tab 1

```python
# In Tab 1, after "Generate Proposal Tables" section

st.divider()
st.subheader("5. Generate PowerPoint Proposal")

if len(st.session_state.proposal_products) == 0:
    st.caption("Add products to generate PowerPoint proposal")
else:
    if st.button("Generate PowerPoint Proposal", type="primary", use_container_width=True):
        # Show match review UI
        confirmed_matches = show_match_review_ui(
            st.session_state.proposal_products,
            pptx_product_names
        )

        if confirmed_matches:
            # User confirmed matches - proceed with generation
            with st.spinner("Generating PowerPoint presentation..."):
                output_path = generate_pptx_with_confirmed_matches(
                    st.session_state.proposal_products,
                    confirmed_matches
                )

                # Success message
                st.success(f"✓ Proposal generated with {len(confirmed_matches)} products!")

                # Download button
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="Download PowerPoint",
                        data=f.read(),
                        file_name=f"PBP_Proposal_{datetime.now().strftime('%Y%m%d')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary"
                    )
```

---

## Validation Rules

### Before Allowing Generation:

1. ✓ **All fuzzy matches must have decisions**
   - User selected "Yes", "Alternative", or "Skip" for each

2. ✓ **At least 1 product confirmed**
   - Either exact match OR user-approved fuzzy match
   - Cannot generate empty proposal

3. ✓ **Decisions are stored**
   - Saved in session state
   - Persists if user navigates away and returns

---

## Edge Cases

### Case 1: User Refreshes Page During Review

**Behavior:** Lose all decisions, start over

**Solution:** Store decisions in session state, but accept that refresh = restart

**Why:** Implementing persistence across page refreshes adds complexity for rare edge case

### Case 2: User Confirms Wrong Match

**Behavior:** Wrong slide included in generated PowerPoint

**Solution:**
- User downloads .pptx
- Opens it
- Sees wrong slide
- Deletes slide from PowerPoint
- Still faster than manual process

**Prevention:** Clear UI with confidence scores helps user make informed decisions

### Case 3: All Products are Fuzzy Matches

**Behavior:** User must confirm every single product (could be tedious for 20+ products)

**Solution:**
- Group by confidence level
- Allow "Confirm all excellent matches (90%+)" bulk action (future enhancement)
- For MVP: Accept that user must review each (builds trust)

### Case 4: No Products Match

**Behavior:** Show message, disable generation

**Solution:**
```
✗ No matching slides found for any products.

To generate proposals:
1. Add slides to PowerPoint with matching product names, OR
2. Use manual slide selection (future feature)
```

---

## Mobile Considerations

**Challenge:** Match review UI is complex for small screens

**Solution:**
- Use Streamlit's responsive layout
- Stack elements vertically
- Radio buttons work well on mobile
- Scrollable sections
- Test on mobile devices

**Acceptable:** Some horizontal scrolling on very small screens (rare use case)

---

## Accessibility

**Considerations:**
- ✓ Radio buttons are keyboard navigable
- ✓ Screen readers can read match status
- ✓ Color-blind friendly (use icons + text, not just color)
- ✓ Clear focus indicators
- ✓ Semantic HTML from Streamlit

---

## Future Enhancements (Post-MVP)

### 1. Remember Confirmations

Store user confirmations in database:
- "Alabaster Cutting Board → SELVA CUTTING BOARD" confirmed by user
- Next time: Auto-apply this mapping (show as exact match)
- Over time: Fewer confirmations needed

### 2. Bulk Actions

For high-confidence matches:
- "Confirm all excellent matches (90%+)" checkbox
- Reduces clicks for users with many products

### 3. Inline Preview

Show slide thumbnail when user hovers over match:
- Visual confirmation that it's the right slide
- Faster decision making

### 4. Match Explanations

Show why algorithm suggested this match:
- "Both contain keywords: CUTTING, BOARD"
- "87% similar after removing variants"
- Builds trust in suggestions

---

## Conclusion

**Key Principle:** User confirmation is mandatory for fuzzy matches.

**Why:**
- Builds trust in the system
- Prevents wrong slides in client proposals
- User knows their products better than algorithm
- 10 seconds of confirmation saves 30 minutes of error recovery

**Result:** Reliable, trustworthy PowerPoint generation that users can depend on.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Final Design - Ready for Implementation
