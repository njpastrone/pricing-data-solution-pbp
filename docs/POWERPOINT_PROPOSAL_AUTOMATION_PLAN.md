# PowerPoint Proposal Automation - Implementation Plan

**Feature:** Automated PowerPoint Proposal Generation from Tab 1
**Date:** 2025-11-04
**Status:** Planning Phase
**Estimated Implementation Time:** 3-4 days

---

## Table of Contents
1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Solution Architecture](#solution-architecture)
4. [Technical Approach](#technical-approach)
5. [Implementation Phases](#implementation-phases)
6. [Code Structure](#code-structure)
7. [Risk Mitigation](#risk-mitigation)
8. [Testing Strategy](#testing-strategy)
9. [User Setup Instructions](#user-setup-instructions)
10. [Success Criteria](#success-criteria)
11. [Future Enhancements](#future-enhancements)

---

## Overview

### Goal
Automate the creation of client-ready PowerPoint proposal decks by:
- Cloning slides from a master "all-slides.pptx" template
- Updating pricing tables with calculated values from the app
- Generating a downloadable .pptx file with only selected products

### Current Workflow (Manual)
1. User configures proposal in Tab 1 (products, quantities, pricing)
2. User copies pricing tables from app
3. User opens "all-slides.pptx" master deck
4. User manually selects relevant slides
5. User manually pastes pricing into each table
6. User saves as new file and emails to client
**Time:** 15-30 minutes per proposal

### Proposed Workflow (Automated)
1. User configures proposal in Tab 1 (products, quantities, pricing)
2. User clicks "Download PowerPoint Proposal" button
3. App generates complete .pptx file with selected products
4. User emails file directly to client
**Time:** 2 minutes per proposal

---

## Problem Statement

### Pain Points
- **Time-consuming:** Manual slide selection and table editing
- **Error-prone:** Copy-paste mistakes, wrong pricing, formatting issues
- **Inconsistent:** Formatting can vary between proposals
- **Multi-tool friction:** Switching between app, PowerPoint, email

### Business Impact
- Slows down sales cycle (15-30 min per proposal)
- Risk of pricing errors affecting margins
- Inconsistent client experience
- Limits number of proposals team can send daily

---

## Solution Architecture

### Core Principle: Clone, Don't Rebuild
**We do NOT reconstruct slides from scratch.** Instead:
1. Clone complete slides from master template (preserves ALL formatting)
2. Update ONLY the pricing table cell values
3. Assemble cloned slides into new presentation

### Why This Approach is Safe
- **Minimal manipulation:** Only text changes, no layout/style changes
- **Format preservation:** Images, fonts, colors stay pixel-perfect
- **Template protection:** Original "all-slides.pptx" never modified (read-only)
- **Error isolation:** If pricing update fails, slide still has all other content
- **Easy testing:** Compare output vs template side-by-side visually

### Technology: Python-PPTX Library
- **Mature library:** Well-documented, widely used
- **Native .pptx support:** No conversion needed
- **Offline operation:** No API dependencies or rate limits
- **Streamlit compatible:** Works in Streamlit Cloud environment

---

## Technical Approach

### Step 1: Load Master Template (Read-Only)
```python
from pptx import Presentation

# Load master deck without modifying original
master_deck = Presentation('templates/November All Slides.pptx')
```

**Template File Status:**
- ✅ File uploaded: `templates/November All Slides.pptx`
- ✅ File size: 43MB (optimized from 834MB - 95% reduction!)
- ✅ Ready for git commit and Streamlit Cloud deployment

**What's loaded:**
- All slides with complete formatting
- Embedded images (product photos, logos)
- Fonts, colors, layouts
- Tables with existing structure

### Step 2: Match Products to Slides
```python
def find_slide_by_product_name(master_deck, product_name):
    """
    Find slide matching product name.
    Strategy:
    1. Check slide title exact match
    2. Check slide title contains product name
    3. Check text shapes for product name
    4. Return None if not found
    """
    for slide in master_deck.slides:
        # Extract title text
        title_text = extract_slide_title(slide)

        # Exact match
        if title_text.strip().upper() == product_name.strip().upper():
            return slide

        # Contains match
        if product_name.upper() in title_text.upper():
            return slide

    return None
```

**Matching Logic:**
- Primary: Match on slide title (e.g., "UPCYCLED EXECUTIVE URBAN BRIEFCASE")
- Fallback: Fuzzy match or user-provided mapping
- Error handling: Skip products with missing slides, log warning

### Step 3: Clone Complete Slide
```python
def clone_slide(source_slide, target_presentation):
    """
    Clone entire slide including:
    - Layout and master slide reference
    - All shapes (images, text boxes, tables)
    - All formatting (colors, fonts, positioning)
    """
    # Create blank slide with same layout
    blank_slide = target_presentation.slides.add_slide(source_slide.slide_layout)

    # Clone each shape from source to target
    for shape in source_slide.shapes:
        clone_shape(shape, blank_slide)

    return blank_slide
```

**What Gets Cloned:**
- ✅ Product image (embedded, stays perfect)
- ✅ Header text + SDG logo
- ✅ All bullet points with formatting
- ✅ Pricing table with structure and styling
- ✅ Footer + PBP logo
- ✅ Background colors/gradients
- ✅ All positioning and alignment

**What Does NOT Happen:**
- ❌ No layout reconstruction
- ❌ No image re-embedding
- ❌ No style reapplication
- ❌ No manual positioning

### Step 4: Update Pricing Table Only
```python
def update_pricing_table(slide, pricing_data):
    """
    Find pricing table and update cell values.
    Preserves all table formatting (borders, colors, fonts).
    """
    for shape in slide.shapes:
        if shape.has_table:
            table = shape.table

            # Verify table structure (4 columns expected)
            if len(table.columns) != 4:
                continue  # Skip non-pricing tables

            # Update data row (row index 1, headers are row 0)
            table.rows[1].cells[0].text = str(pricing_data['moq'])
            table.rows[1].cells[1].text = f"${pricing_data['price_ea']:.2f}"
            table.rows[1].cells[2].text = f"${pricing_data['ngo_price']:.2f}"
            table.rows[1].cells[3].text = pricing_data['delivery']

            return True  # Success

    return False  # No table found
```

**Table Update Strategy:**
- Only modify cell TEXT values, not formatting
- Headers stay untouched ("MOQ", "Price Ea @ Qty 10", etc.)
- Table borders, colors, alignment preserved from template
- If table not found, log warning but continue

### Step 5: Assemble Client Deck
```python
def generate_proposal_pptx(proposal_products, output_path):
    """
    Main function to generate client presentation.
    """
    # Load master template
    master_deck = Presentation('templates/all-slides.pptx')

    # Create new presentation for client
    client_deck = Presentation()

    # For each product in proposal
    for product_item in proposal_products:
        product_name = product_item['product_data']['Product/Service']

        # Find matching slide
        source_slide = find_slide_by_product_name(master_deck, product_name)

        if source_slide is None:
            st.warning(f"Slide not found for: {product_name}")
            continue

        # Clone slide
        cloned_slide = clone_slide(source_slide, client_deck)

        # Calculate pricing (reuse existing logic from Tab 1)
        pricing_data = calculate_proposal_pricing(product_item)

        # Update pricing table
        success = update_pricing_table(cloned_slide, pricing_data)

        if not success:
            st.warning(f"Could not update pricing table for: {product_name}")

    # Save client presentation
    client_deck.save(output_path)
    return output_path
```

---

## Implementation Phases

### Phase 1: Setup & Dependencies (Day 1 Morning)
**Tasks:**
1. Add `python-pptx` to `requirements.txt`
2. Create `/templates/` directory structure
3. User uploads "all-slides.pptx" to `/templates/master_slides.pptx`
4. Create new module: `src/pptx_generator.py`
5. Test basic slide loading and iteration

**Deliverable:** Basic infrastructure in place, can load master deck

### Phase 2: Core Slide Cloning Logic (Day 1 Afternoon - Day 2 Morning)
**Tasks:**
1. Implement `find_slide_by_product_name()` function
2. Implement `clone_slide()` function
3. Test slide cloning with 1-2 sample products
4. Verify all formatting preserved (visual inspection)

**Deliverable:** Can clone complete slides with perfect formatting

### Phase 3: Table Update Logic (Day 2 Afternoon)
**Tasks:**
1. Implement `update_pricing_table()` function
2. Integrate with existing pricing calculation logic from Tab 1
3. Handle edge cases (table not found, wrong structure)
4. Test table updates with various products

**Deliverable:** Can update pricing tables while preserving formatting

### Phase 4: Integration with Tab 1 (Day 3 Morning)
**Tasks:**
1. Add "Download PowerPoint Proposal" button to Tab 1
2. Connect button to `generate_proposal_pptx()` function
3. Add loading indicator during generation
4. Add download button for generated .pptx file

**Deliverable:** Working end-to-end flow in app

### Phase 5: Error Handling & Edge Cases (Day 3 Afternoon)
**Tasks:**
1. Handle missing slides gracefully (skip + warning)
2. Handle missing tables gracefully (skip + warning)
3. Handle malformed table structures
4. Add validation warnings before generation
5. Add success/error messages after generation

**Deliverable:** Robust error handling

### Phase 6: Testing & Refinement (Day 4)
**Tasks:**
1. Test with 5+ different product combinations
2. Test with all products in catalog
3. Compare output vs template for formatting issues
4. Test file download in Streamlit Cloud
5. User acceptance testing
6. Fix any formatting issues discovered

**Deliverable:** Production-ready feature

---

## Code Structure

### New Files
```
src/
  └─ pptx_generator.py          # PowerPoint generation logic

templates/
  └─ master_slides.pptx          # Master slide deck (user-provided)
```

### New Module: `src/pptx_generator.py`
```python
"""
PowerPoint Proposal Generation Module
Generates client-ready .pptx files from proposal data.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
import streamlit as st

def find_slide_by_product_name(master_deck, product_name):
    """Find slide matching product name."""
    pass

def extract_slide_title(slide):
    """Extract title text from slide."""
    pass

def clone_slide(source_slide, target_presentation):
    """Clone entire slide with all formatting."""
    pass

def clone_shape(source_shape, target_slide):
    """Clone individual shape (image, text, table)."""
    pass

def calculate_proposal_pricing(product_item):
    """
    Calculate pricing for product.
    Reuses logic from Tab 1 generate proposal tables section.
    """
    pass

def update_pricing_table(slide, pricing_data):
    """Update pricing table cells with calculated values."""
    pass

def generate_proposal_pptx(proposal_products, output_path):
    """
    Main function: Generate complete client presentation.
    Returns: path to generated .pptx file
    """
    pass
```

### Integration in `app.py` (Tab 1)
```python
# In Tab 1, after "Generate Proposal Tables" section
st.divider()
st.subheader("5. Download PowerPoint Proposal")

if len(st.session_state.proposal_products) == 0:
    st.caption("Add products to generate PowerPoint proposal")
else:
    st.markdown("""
    Generate a complete PowerPoint presentation with:
    - Only the products you've selected
    - Updated pricing tables for this client
    - All original formatting and images preserved
    """)

    if st.button("Generate PowerPoint Proposal", type="primary", use_container_width=True):
        with st.spinner("Generating PowerPoint presentation..."):
            try:
                from src.pptx_generator import generate_proposal_pptx

                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"output/proposal_{timestamp}.pptx"

                # Generate presentation
                result_path = generate_proposal_pptx(
                    st.session_state.proposal_products,
                    output_path
                )

                # Read file for download
                with open(result_path, 'rb') as f:
                    pptx_data = f.read()

                st.success("PowerPoint proposal generated successfully!")

                # Download button
                st.download_button(
                    label="Download PowerPoint Proposal",
                    data=pptx_data,
                    file_name=f"PBP_Proposal_{timestamp}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    type="primary"
                )

            except Exception as e:
                st.error(f"Error generating PowerPoint: {str(e)}")
                st.caption("Please check that master_slides.pptx exists in templates/ directory")
```

---

## Risk Mitigation

### Risk 1: Slide Names Don't Match Product Names
**Probability:** HIGH
**Impact:** HIGH (feature breaks if slides can't be found)

**Mitigation Strategy:**
1. **Primary:** Implement flexible matching (exact, contains, fuzzy)
2. **Fallback:** Create product→slide name mapping file
3. **User Action:** User provides mapping dict in config:
   ```python
   PRODUCT_SLIDE_MAPPING = {
       "Upcycled Executive Urban Briefcase": "UPCYCLED EXECUTIVE URBAN BRIEFCASE",
       "Water Bottle": "SUSTAINABLE WATER BOTTLE - 16OZ",
       # etc...
   }
   ```
4. **UI Feedback:** Show warnings for missing slides, allow user to continue

### Risk 2: Table Structure Varies Between Slides
**Probability:** MEDIUM
**Impact:** MEDIUM (table updates fail for some products)

**Mitigation Strategy:**
1. **Validate table structure** before updating (check column count, row count)
2. **Identify tables by position** (assume pricing table is last table on slide)
3. **Fallback:** Use text replacement instead of table cell update
4. **User Action:** Standardize table structure in master_slides.pptx

### Risk 3: Images Don't Copy Correctly
**Probability:** LOW
**Impact:** HIGH (slides look broken)

**Mitigation Strategy:**
1. **Test thoroughly** with all image types (JPG, PNG, embedded)
2. **Use python-pptx native cloning** (handles images automatically)
3. **Fallback:** Keep images embedded in master template
4. **Validation:** Visual inspection during Phase 6 testing

### Risk 4: Font Compatibility Issues
**Probability:** LOW
**Impact:** LOW (text looks different but readable)

**Mitigation Strategy:**
1. **Use system fonts** (Arial, Calibri, etc.)
2. **Embed fonts** in master template if custom fonts used
3. **Test on different systems** (Mac, Windows, Linux)
4. **Fallback:** Accept minor font differences (not mission-critical)

### Risk 5: File Size Too Large
**Probability:** LOW
**Impact:** LOW (slower downloads, email issues)

**Mitigation Strategy:**
1. **Compress images** in master template before embedding
2. **Limit proposals** to reasonable number of products (10-15 max)
3. **Monitor file sizes** during testing
4. **Optimization:** Remove unused slides/images from master template

### Risk 6: Streamlit Cloud Deployment Issues
**Probability:** MEDIUM
**Impact:** HIGH (feature doesn't work in production)

**Mitigation Strategy:**
1. **Test locally first** before deploying
2. **Check file permissions** on Streamlit Cloud (can write to temp dirs)
3. **Use temp directories** for output files: `tempfile.TemporaryDirectory()`
4. **Fallback:** Use BytesIO in-memory file handling instead of disk writes

---

## Testing Strategy

### Unit Testing
- **Test slide matching** with various product names
- **Test table detection** on slides with multiple tables
- **Test pricing calculations** match Tab 1 output exactly
- **Test edge cases:** empty proposal, single product, 10+ products

### Integration Testing
- **End-to-end flow:** Select products → configure → generate → download
- **File integrity:** Open generated .pptx in PowerPoint, verify formatting
- **Cross-platform:** Test on Mac, Windows, Linux
- **Browser compatibility:** Test in Chrome, Safari, Firefox

### Visual Validation
- **Side-by-side comparison:** Generated slide vs template slide
- **Checklist:**
  - [ ] Product image present and correct
  - [ ] Header formatting matches (fonts, colors)
  - [ ] Bullet points all present
  - [ ] Table formatting matches (borders, colors)
  - [ ] Pricing values correct
  - [ ] Footer and logos present
  - [ ] No overlapping elements
  - [ ] No broken images

### User Acceptance Testing
- **Scenario 1:** 2-product proposal (simple case)
- **Scenario 2:** 8-product proposal (typical case)
- **Scenario 3:** Mixed pricing (NGO discount, custom markup)
- **Scenario 4:** Products with missing slides (error handling)

### Performance Testing
- **Generation time:** Should complete in < 10 seconds for 10 products
- **File size:** Should be < 10MB for 10-slide deck
- **Memory usage:** Should not crash on large proposals

---

## User Setup Instructions

### Before First Use
1. **Prepare Master Slide Deck:**
   - ✅ COMPLETE: "November All Slides.pptx" uploaded to `/templates/`
   - ✅ COMPLETE: File optimized to 43MB (from 834MB - 95% reduction!)
   - TODO: Verify product names in slide titles match app product names
   - TODO: Standardize pricing table structure across all slides

2. **Upload Template:**
   - ✅ COMPLETE: File in `/templates/November All Slides.pptx`
   - ✅ Git ready: 43MB file can be committed to GitHub (under 100MB limit)

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test Connection:**
   - Run app locally
   - Navigate to Tab 1
   - Add 1 product to proposal
   - Click "Generate PowerPoint Proposal"
   - Download and open result in PowerPoint
   - Verify formatting looks correct

### Ongoing Maintenance
- **Update master template:** When adding new products, add slides to master_slides.pptx
- **Update mapping:** If product names change, update mapping dict
- **Refresh template:** Periodically update logos, branding, contact info in master template

---

## Success Criteria

### Must Have (MVP)
- [ ] Can generate .pptx file with selected products
- [ ] Slides clone with all formatting preserved
- [ ] Pricing tables update with correct calculated values
- [ ] Download button works in Streamlit app
- [ ] Generated file opens correctly in PowerPoint/Google Slides
- [ ] Visual formatting matches master template
- [ ] Reduces proposal creation time by 80% (30 min → 5 min)

### Should Have
- [ ] Handles missing slides gracefully (warnings, not errors)
- [ ] Handles missing tables gracefully
- [ ] Works on Streamlit Cloud (production environment)
- [ ] File generation completes in < 10 seconds
- [ ] Clear error messages for common issues

### Nice to Have (Future)
- [ ] Add cover slide with client name, date
- [ ] Add summary slide with total pricing across all products
- [ ] Customize proposal based on client type (NGO vs corporate)
- [ ] Track which proposals were downloaded (analytics)
- [ ] Email integration (send directly from app)

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
1. **Custom Cover Slide:**
   - Auto-generate cover with client name, date, company logo
   - Include table of contents

2. **Summary Slide:**
   - Total pricing across all products
   - Quantity discounts if applicable
   - Payment terms summary

3. **Client Customization:**
   - Different templates for NGO vs corporate clients
   - Client-specific branding (if repeat customer)

4. **Analytics:**
   - Track proposal download frequency
   - Track which products are most proposed
   - Conversion tracking (proposal → order)

5. **Email Integration:**
   - Send proposal directly from app via email
   - Auto-populate email body with personalized message
   - Track email opens/clicks

6. **Version Control:**
   - Save generated proposals to database
   - Allow users to regenerate past proposals
   - Track proposal revisions

---

## Appendix

### Python-PPTX Resources
- Documentation: https://python-pptx.readthedocs.io/
- GitHub: https://github.com/scanny/python-pptx
- Examples: https://python-pptx.readthedocs.io/en/latest/user/quickstart.html

### Related Project Files
- Tab 1 pricing logic: `app.py` lines 750-1000
- Pricing calculations: `src/pricing_engine.py`
- Helper functions: `src/helpers.py`
- Project rules: `CLAUDE.md`

### Key Stakeholders
- **User (Sales Team):** Creates proposals, sends to clients
- **Clients:** Receive PowerPoint decks, make purchase decisions
- **Developer (Me):** Implements and maintains feature

---

## Questions for User

Before implementation begins, please confirm:

1. **Template Access:** Can you provide "all-slides.pptx" or should I wait for you to upload it?
2. **Product Name Matching:** Do slide titles exactly match product names in app, or do we need a mapping?
3. **Table Structure:** Are pricing tables consistent across all slides (4 columns, 2 rows)?
4. **Priority:** Is this high priority for immediate implementation, or planning only for now?
5. **Additional Requirements:** Any other customizations needed (cover slide, summary, branding)?

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Ready for Implementation Approval
