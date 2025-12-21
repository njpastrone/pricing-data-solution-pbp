# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /templates
Purpose: PowerPoint templates and reference documents for automated generation

---

## Quick Context
- **Primary responsibility**: Template files for PowerPoint generation and invoice formatting
- **Key dependencies**: None (template files only)
- **Used by**: src/pptx_generator.py, src/template_loader.py
- **Technology stack**: PowerPoint (.pptx), Excel (.xlsx), PDF/Markdown references

---

## Detailed Overview

The `templates/` directory contains all template files used by the application for automated document generation. The most important file is the 43MB PowerPoint template with 339 slides, which is downloaded from Google Drive on-demand for production deployment.

This directory serves as:
1. **PowerPoint template source** - Master slide deck for proposals
2. **Reference documents** - Invoice/PO format specifications
3. **Configuration data** - Partner-specific settings (Impact Slide Reference Guide)

**Important:** In production (Render), the PowerPoint template is downloaded from Google Drive to save disk space and reduce deployment size. Locally, it's stored here for faster access.

---

## Important Files

### PowerPoint Templates

#### November All Slides.pptx (44.8MB)
**Purpose:** Master PowerPoint template with all product slides

**Contents:**
- 339 slides total
- Product slides for ~133 products
- Partner-specific impact slides
- Intro/outro slides
- Multiple pricing table formats (2×3, 2×4, 3×4)

**Usage:**
```python
from src.template_loader import get_template_path

template_path = get_template_path()
# Returns: /path/to/templates/November All Slides.pptx
# Or downloads from Google Drive if not found
```

**Notes:**
- **File size:** 43MB (too large for Render deployment)
- **Solution:** Cloud-hosted on Google Drive (v6.16)
- **Download:** On-demand when needed
- **Caching:** Session-based (downloads once per session)
- **Local dev:** Keep file here for faster access
- **Production:** Downloaded automatically

**Slide Organization:**
- **Product slides:** One per product (some products share slides for variants)
- **Impact slides:** Partner-specific slides (customizable text)
- **Intro slide:** First slide (auto-generated cover with client name)
- **Outro slides:** Final slides (Peace by Piece branding)

**Table Formats:**
- **2×3:** 2 columns, 3 rows (MOQ, Price @ MOQ, Price @ 100 | Product info)
- **2×4:** 2 columns, 4 rows (adds Delivery row)
- **3×4:** 3 columns, 4 rows (multi-variant products)

**Font:** 15pt throughout (must be preserved when updating)

---

#### Intro_Outro_Slides_PbP_Proposals.pptx (2.7MB)
**Purpose:** Standalone intro/outro slides for proposals

**Contents:**
- Professional cover slide template
- Peace by Piece branding slides
- Closing slides

**Usage:**
- Reference for cover slide design
- Can be merged with generated presentations
- Currently: Auto-generated cover slide in pptx_generator.py

**Notes:**
- Not actively used in current workflow
- Kept for reference and manual merging if needed

---

### Reference Documents

#### Impact Slide Reference Guide Nov 5 2025.xlsx (52KB)
**Purpose:** Partner-specific impact slide configuration

**Contents:**
- Impact slide titles per partner
- Slide numbers in template
- Customization options (dropdowns)
- Partner-specific text

**Usage:**
- Reference when adding new partners
- Guide for impact slide customization
- Maps partners to their impact slides

**Structure:**
```
Partner | Impact Slide Title | Slide Number | Customization Options
--------|-------------------|--------------|----------------------
Partner X | "Partner X Impact" | 45 | Option 1, Option 2, Option 3
Partner Y | "Partner Y Impact" | 67 | Option A, Option B
```

**Notes:**
- Updated November 5, 2025 (future date in filename is typo - should be 2024)
- Used by `src/pptx_generator.py` for impact slide customization

---

#### Partner Specific Pricing Template.xlsx (138KB)
**Purpose:** Original partner-specific pricing data template

**Status:** Legacy reference only

**Notes:**
- Data now in Google Sheets (master_pricing_template_10_14)
- Kept for historical reference
- Not used by application

---

#### TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md (2.1KB)
**Purpose:** Invoice/PO format specification (Markdown)

**Contents:**
- 4-table invoice structure
- Required fields per table
- Bookkeeper requirements
- Field descriptions

**Usage:**
- Reference for Tab 4 invoice generation
- Defines expected format for bookkeeper
- Source for INVOICE_AND_PROPOSAL_SPEC.md

---

#### TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf (147KB)
**Purpose:** Invoice/PO format specification (PDF)

**Contents:**
- Same as .md version
- Visual reference format
- Bookkeeper-provided template

**Usage:**
- Visual reference when implementing invoice generation
- Shows exact formatting expected
- Human-readable format for stakeholders

---

## Code Patterns & Conventions

### Template Loading Pattern
```python
from src.template_loader import get_template_path

# Get template (downloads if needed)
template_path = get_template_path()

# Use template
from pptx import Presentation
prs = Presentation(template_path)
```

### Memory Optimization
```python
# In production (Render) - download on-demand
if not os.path.exists(local_path):
    download_from_google_drive()

# Session caching prevents duplicate downloads
if 'template_path' not in st.session_state:
    st.session_state.template_path = get_template_path()
```

### Garbage Collection
```python
# After heavy operations
import gc
prs.save(output_path)
del prs
gc.collect()
```

---

## Common Tasks

### To use PowerPoint template in code:
```python
from src.template_loader import get_template_path
from pptx import Presentation

template_path = get_template_path()
prs = Presentation(template_path)

# Modify slides
# ...

# Save
prs.save("output.pptx")
```

### To add new product slide:
1. Open `November All Slides.pptx`
2. Add new slide with product information
3. Create pricing table (2×3, 2×4, or 3×4 format)
4. Save template
5. Upload to Google Drive (production)
6. Update slide matching in `src/slide_matcher.py` if needed

### To update impact slides:
1. Check `Impact Slide Reference Guide Nov 5 2025.xlsx`
2. Find partner's impact slide number
3. Open `November All Slides.pptx`
4. Navigate to slide number
5. Update text/customization options
6. Save and upload to Google Drive

### To add new partner:
1. Add partner to Google Sheets data
2. Add partner contact to Partner-Specific Info sheet
3. Create impact slide in PowerPoint template
4. Update `Impact Slide Reference Guide Nov 5 2025.xlsx`
5. Update `src/pptx_generator.py` if custom logic needed

---

## Important Notes

### Cloud Template Hosting (v6.16)
- **Why:** 43MB file too large for Render deployment
- **Solution:** Google Drive hosting with on-demand download
- **Benefits:** Faster deployments, lower disk usage
- **Tradeoff:** First-time download delay (~3-5 seconds)

### Template Versioning
- No formal version control for PowerPoint template
- Changes are manual and require re-upload to Google Drive
- Consider versioning if template changes frequently

### Font Preservation
**Critical:** PowerPoint template uses 15pt font
- Always preserve font size when updating cells
- Code enforces this in `pptx_generator.py`
```python
run.font.size = Pt(15)  # Always restore
```

### Slide Numbering
- Slide numbers in Impact Slide Reference Guide are 1-indexed
- Python pptx library uses 0-indexed arrays
- Always subtract 1: `slide_index = slide_number - 1`

### Template Modification Best Practices
1. **Always backup** before major changes
2. **Test locally** before uploading to Google Drive
3. **Update reference docs** (Impact Slide Reference Guide)
4. **Notify team** of template changes
5. **Version in filename** if making major changes (e.g., `November All Slides v2.pptx`)

---

## Performance Considerations

### Template Download Time
- **Local:** Instant (file already exists)
- **Production (first time):** ~3-5 seconds (downloads from Google Drive)
- **Production (cached):** Instant (session-based cache)

### Memory Usage
- Loading template: ~50-100MB RAM
- Modifying slides: +50MB per presentation
- Multiple generations: Memory leaks possible
- **Solution:** Garbage collection after each generation

### File Size Impact
- **43MB template** would add significantly to Render deployment
- **Cloud hosting** keeps deployment size minimal
- **Tradeoff:** First-time download delay acceptable

---

## Gotchas & Notes

### PowerPoint Repair Warning
Sometimes PowerPoint shows "repair" warning when opening generated files:
- This is normal for programmatically generated files
- No data loss occurs
- Files open correctly after "repair"
- Does not affect client usage

### Font Size Issues
If pricing table fonts look wrong:
- Check `pptx_generator.py` font preservation code
- Verify 15pt is applied after text updates
- Test with sample product

### Slide Order
Template slide order matters:
- Product slides should be consecutive for easier removal
- Impact slides grouped by partner
- Intro/outro slides at beginning/end

### Google Drive Permissions
Template must be:
- Publicly accessible (or service account has access)
- Direct download link format
- Not blocked by corporate firewalls

### Template Lock File
Avoid opening template while app is running:
- PowerPoint creates lock file (`~$November All Slides.pptx`)
- Can cause file access errors
- Close PowerPoint before running tests

---

## Recent Changes

### v6.16 (November 2024)
- Moved PowerPoint template to Google Drive
- Added cloud-based template loading
- Session caching for downloaded template
- Memory optimization with garbage collection

### v6.13 (November 2024)
- Added multi-variant product support
- Updated table formats to handle 3×4 layouts
- Smart variant identifier extraction

### v6.0-6.11 (November 2024)
- PowerPoint automation Phase 1 & 2 complete
- Slide matching system (78.9% accuracy)
- Dynamic pricing table updates
- Impact slide customization

---

## Future Enhancements

### Template Management
- Version control for template changes
- Automated backup before modifications
- Template changelog
- Multiple template support (different brands)

### Impact Slides
- Dynamic impact slide generation from data
- Custom impact metrics per partner
- Multi-language support

### Alternative Formats
- Google Slides export option
- PDF direct generation (skip PowerPoint)
- Interactive HTML presentations

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **PowerPoint Phase 2:** [../docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md](../docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md)
- **PowerPoint Phase 1:** [../docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md](../docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md)
- **Invoice Spec:** [../docs/planning/INVOICE_AND_PROPOSAL_SPEC.md](../docs/planning/INVOICE_AND_PROPOSAL_SPEC.md)
- **Template Loader:** [../src/template_loader.py](../src/template_loader.py)
- **PPTX Generator:** [../src/pptx_generator.py](../src/pptx_generator.py)
