# PowerPoint Slide Matching Notes

This document tracks issues, observations, and action items related to matching pricing data products to PowerPoint proposal slides.

Last Updated: 2025-11-11

---

## Overview

The PowerPoint proposal generator matches products from our pricing spreadsheet to slides in the PowerPoint deck. This document tracks partner-specific notes about matching accuracy, missing slides, and data cleanup needs.

---

## Partner Notes

### GOEX

**Status:** Needs review

**Issues:**
- Need to confirm which products we carry
- May be able to delete many products that are not carried from the spreadsheet

**Action Items:**
- [ ] Review product list with team to confirm active products
- [ ] Remove discontinued/non-carried products from pricing spreadsheet

**Last Updated:** 2025-11-11

---

### Homeless Garden Project

**Status:** Good

**Issues:**
- None currently identified

**Notes:**
- Units per Package column successfully implemented (v6.8)
- All products sell in 6-packs, pricing normalized correctly

**Last Updated:** 2025-11-11

---

### [Partner Name]

**Status:**

**Issues:**

**Action Items:**

**Notes:**

**Last Updated:**

---

## General Matching Issues

### Common Problems

1. **Product name variations:**
   - Spreadsheet: "TRIBLEND SHORT SLEEVE"
   - PowerPoint: "UNISEX ECO-TRIBLEND SHORT SLEEVE TEE"
   - Solution: Use search feature in alternative matches

2. **Missing slides:**
   - Some products in spreadsheet don't have corresponding slides
   - These products will be skipped in PowerPoint generation

3. **Duplicate slides:**
   - Some products may have multiple slide variations
   - Confirm correct slide when fuzzy matches appear

---

## Improvement Ideas

- [ ] Add bulk edit feature to update product names in spreadsheet to match PowerPoint exactly
- [ ] Create mapping file for common name variations
- [ ] Add ability to create new slides from template for missing products
- [ ] Track most commonly searched terms to improve auto-matching algorithm

---

## Template for New Partner Notes

Copy this template when adding notes for a new partner:

```markdown
### [Partner Name]

**Status:** [Good / Needs Review / Issues]

**Issues:**
- [List specific matching problems]

**Action Items:**
- [ ] [Specific tasks to improve matching]

**Notes:**
- [Any additional context or observations]

**Last Updated:** YYYY-MM-DD
```
