# Templates & Reference Documents

This directory contains PowerPoint templates and reference documents for automated document generation.

**Last Updated:** 2024-12-20
**Total Files:** 7

---

## Overview

The templates directory houses all source files needed for automated proposal and invoice generation. The primary asset is a 43MB PowerPoint template with 339 slides that is downloaded from Google Drive on-demand in production.

---

## Files

### PowerPoint Templates

#### November All Slides.pptx (44.8MB)
**Purpose:** Master PowerPoint template for automated proposal generation

**Key Features:**
- 339 slides (product slides + impact slides + intro/outro)
- Multiple pricing table formats (2×3, 2×4, 3×4)
- Partner-specific impact slides
- Professional formatting with 15pt font

**Usage:**
- Downloaded from Google Drive in production (Render)
- Stored locally for development
- Session-cached to prevent duplicate downloads

**Deployment:**
- **Local:** Use file directly from this directory
- **Production:** Auto-downloaded from Google Drive via `src/template_loader.py`

---

#### Intro_Outro_Slides_PbP_Proposals.pptx (2.7MB)
**Purpose:** Standalone intro/outro slides

**Usage:**
- Reference for cover slide design
- Manual merging if needed
- Currently: Auto-generated in code

---

### Configuration

#### Impact Slide Reference Guide Nov 5 2025.xlsx (52KB)
**Purpose:** Partner-specific impact slide configuration

**Contents:**
- Partner-to-slide mapping
- Slide numbers in template
- Customization options
- Partner-specific text

**Usage:**
- Reference when customizing impact slides
- Guide for adding new partners
- Maps partners to their slides

---

### Reference Documents

#### Partner Specific Pricing Template.xlsx (138KB)
**Status:** Legacy reference only

**Notes:**
- Original pricing template
- Data now in Google Sheets
- Kept for historical reference

---

#### TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md (2.1KB)
**Purpose:** Invoice/PO format specification (Markdown)

**Contents:**
- 4-table invoice structure
- Required fields
- Bookkeeper requirements

**Usage:**
- Reference for Tab 4 invoice generation
- Defines expected format

---

#### TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.pdf (147KB)
**Purpose:** Invoice/PO format specification (PDF)

**Usage:**
- Visual reference for invoice format
- Shows exact formatting expected
- Human-readable stakeholder document

---

## Usage Examples

### Loading PowerPoint Template
```python
from src.template_loader import get_template_path
from pptx import Presentation

# Get template (downloads if needed)
template_path = get_template_path()

# Load and modify
prs = Presentation(template_path)
# ... make changes
prs.save("output.pptx")
```

### Referencing Invoice Format
```python
# See TEMPLATE INVOICE AND PURCHASE ORDER REQUEST FORM-SHARED.md
# for required fields and structure

# Implementation in app.py (Tab 4)
# Generates 4-table CSV/HTML export matching template
```

---

## Important Notes

### Cloud Template Hosting
The PowerPoint template is **hosted on Google Drive** for production:
- **Why:** 43MB file too large for Render deployment
- **How:** `src/template_loader.py` downloads on-demand
- **Caching:** Session-based (downloads once per session)
- **Local dev:** Use file from this directory for faster access

### Template Modifications
When updating `November All Slides.pptx`:
1. Make changes locally
2. Test thoroughly with `scripts/features/test_*` scripts
3. Upload to Google Drive (production)
4. Update `Impact Slide Reference Guide` if needed
5. Document changes in commit message

### Font Preservation
**Critical:** Template uses 15pt font throughout
- Always preserve font size when updating cells
- Code enforces this in `src/pptx_generator.py`

### Slide Numbering
- Reference guide uses 1-indexed slide numbers
- Python pptx library uses 0-indexed arrays
- Always subtract 1: `slide_index = slide_number - 1`

---

## File Size Considerations

### Local Development
- All files stored in this directory (~50MB total)
- Instant access, no download delays

### Production (Render)
- PowerPoint template downloaded from Google Drive
- Other files deployed with app
- First-time download: ~3-5 seconds
- Subsequent uses: Instant (cached)

---

## Related Documentation

- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) - Comprehensive AI context
- **PowerPoint Phase 2:** [../docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md](../docs/powerpoint/PHASE_2_COMPLETION_SUMMARY.md)
- **Invoice Spec:** [../docs/planning/INVOICE_AND_PROPOSAL_SPEC.md](../docs/planning/INVOICE_AND_PROPOSAL_SPEC.md)
- **Template Loader:** [../src/template_loader.py](../src/template_loader.py)
- **PPTX Generator:** [../src/pptx_generator.py](../src/pptx_generator.py)

---

## Maintenance

### Regular Tasks
- None (templates are stable)

### Occasional Tasks
- Update impact slides when adding new partners
- Add product slides for new products
- Update reference guide when modifying template

### Version Control
- No formal versioning currently
- Consider version suffix for major changes (e.g., `v2`)
- Document changes in git commits
