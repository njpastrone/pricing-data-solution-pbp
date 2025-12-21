# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /docs
Purpose: Comprehensive project documentation organized by topic

---

## Quick Context
- **Primary responsibility**: Project documentation, planning, and technical specifications
- **Key dependencies**: None (documentation only)
- **Used by**: Developers, AI assistants, stakeholders for project understanding
- **Technology stack**: Markdown documentation

---

## Detailed Overview

The `docs/` directory contains all project documentation organized by topic. This structure was established in **v6.18 (November 2024)** during the documentation cleanup, when 23 completed planning docs were archived to maintain clarity.

Documentation serves multiple purposes:
1. **Project planning** - Requirements, architecture, methodology
2. **Technical specifications** - Invoice formats, pricing logic, data structures
3. **Meeting notes** - Stakeholder feedback and decisions
4. **Feature documentation** - PowerPoint automation, testing checklists
5. **Historical reference** - Archived completed work

All documentation is AI-friendly and human-readable, with clear structure and cross-references.

---

## Directory Structure

```
docs/
├── Root-level documentation (6 files)
│   ├── README.md                        # Documentation index (this level)
│   ├── CLIENT_QUESTIONS.md              # Unanswered client questions
│   ├── CODE_SIMPLIFICATION_AGENT.md     # Cleanup process documentation
│   ├── SCROLL_PRESERVATION_PATTERN.md   # Scroll position implementation
│   ├── SESSION_STATE_AUDIT.md           # Session state management
│   └── SLIDE_MATCHING_NOTES.md          # Partner-specific slide matching
│
├── planning/                            # Core project documentation (4 files)
│   ├── PLANNING.md                      # Project requirements & goals
│   ├── METHODOLOGY_LOGIC.md             # Pricing calculations & business rules
│   ├── RESTRUCTURE_CONTEXT.md           # Data structure reference
│   └── INVOICE_AND_PROPOSAL_SPEC.md     # Invoice/PO format specifications
│
├── meetings/                            # Stakeholder meeting notes (2 files)
│   ├── RAW_MEETING_NOTES_113024.md      # Original notes (Nov 30, 2024)
│   └── STAKEHOLDER_MEETING_NOTES.md     # Organized requirements
│
├── powerpoint/                          # PowerPoint automation docs (2 files)
│   ├── PHASE_1_COMPLETION_SUMMARY.md    # Phase 1 technical deep dive
│   └── PHASE_2_COMPLETION_SUMMARY.md    # Phase 2 production summary
│
├── testing/                             # Testing documentation (1 file)
│   └── TAB3_TAB4_TESTING_CHECKLIST.md   # Comprehensive test checklist
│
├── investigations/                      # Investigation reports (2 files)
│   └── (Partner POC debugging docs)
│
└── archive/                             # Historical documentation (23+ files)
    ├── powerpoint-planning/             # PowerPoint planning (14 files)
    ├── tab2-improvements/               # Tab 2 redesign (9 files)
    └── (Other completed planning docs)
```

---

## Important Files

### Root-Level Documentation

#### README.md (8.8KB)
**Purpose:** Documentation index and navigation guide

**Contents:**
- Quick links to all major docs
- Documentation by category
- Usage guidelines
- Version history

**When to read:** Starting point for finding any documentation

---

#### CLIENT_QUESTIONS.md (1.9KB)
**Purpose:** Track unanswered client questions

**Contents:**
- Outstanding questions needing clarification
- Technical decisions requiring client input
- Feature requests pending discussion

**Last Updated:** October 2024 (mostly resolved)

---

#### CODE_SIMPLIFICATION_AGENT.md (5.3KB)
**Purpose:** Document v6.18 codebase cleanup process

**Contents:**
- Cleanup methodology and decisions
- Files removed (13,649 lines deleted)
- Documentation archived (23 files)
- Lessons learned for future AI-assisted maintenance

**Why it exists:** Reference for future code maintenance and cleanup efforts

---

#### SCROLL_PRESERVATION_PATTERN.md (9.4KB)
**Purpose:** Technical documentation for scroll position preservation

**Contents:**
- JavaScript-based scroll capture system
- sessionStorage implementation
- Button-specific scroll handlers
- MutationObserver for dynamic content
- 95-98% effectiveness metrics

**When to reference:** Implementing similar UI state preservation

---

#### SESSION_STATE_AUDIT.md (11.6KB)
**Purpose:** Complete session state variable inventory

**Contents:**
- All 50+ session state variables documented
- Variable purposes and lifetimes
- Initialization patterns
- Reset conditions
- Cross-tab data flow

**When to reference:** Understanding app state management, debugging state issues

---

#### SLIDE_MATCHING_NOTES.md (2.4KB)
**Purpose:** Partner-specific product-to-slide matching notes

**Contents:**
- Manual override suggestions
- Product name variations
- Slide title quirks
- Category-specific patterns

**When to reference:** Improving PowerPoint matching accuracy

---

### Planning Documentation (planning/)

#### PLANNING.md (6.1KB)
**Purpose:** High-level project requirements and goals

**Contents:**
- Project overview and objectives
- User workflow
- Technical requirements
- Success criteria

**When to read:** Understanding project vision and goals

---

#### METHODOLOGY_LOGIC.md (13.6KB) - CRITICAL
**Purpose:** Detailed pricing calculations and business rules

**Contents:**
- Tiered pricing logic (6 tiers: T1-T6)
- Flat-rate pricing for non-tiered products
- Customization cost calculations
- Markup application rules
- Discount application (Non-profit, custom)
- Marketing rounding ($60 → $59)
- $0.50 rounding option
- MSRP pricing calculations
- Units per package normalization
- Tariff calculations
- Credit card fee calculations

**When to reference:**
- Implementing any pricing feature
- Debugging calculation issues
- Understanding business rules
- **READ THIS BEFORE WORKING ON PRICING CODE**

---

#### RESTRUCTURE_CONTEXT.md (9.7KB)
**Purpose:** Data structure reference from master_pricing_template_10_14

**Contents:**
- Google Sheets structure (3 sheets)
- Column names and data types
- Header row locations (row 6 for Data, row 2 for Metadata/Partner Info)
- Tier column structure (PBP Cost: Tier 1, Tier 2, etc.)
- Partner-specific data organization

**When to reference:**
- Working with spreadsheet data
- Understanding column names
- Debugging data loading issues

---

#### INVOICE_AND_PROPOSAL_SPEC.md (10.9KB)
**Purpose:** Invoice and Purchase Order format specifications

**Contents:**
- 4-table invoice structure
- Required fields per table
- Table 1: Client/Company Information
- Table 2: Partners + Points of Contact
- Table 3: Order Details
- Table 4: Invoice and PO Item Details
- Line item structure and calculations
- Bookkeeper requirements

**When to reference:**
- Implementing invoice generation
- Modifying Table 4 export formats
- Understanding bookkeeper requirements

---

### Meeting Documentation (meetings/)

#### RAW_MEETING_NOTES_113024.md (6.4KB)
**Purpose:** Original stakeholder meeting notes from November 30, 2024

**Contents:**
- Unedited notes from executive meeting
- Feature requests and feedback
- Critical bugs identified
- Enhancement suggestions

**Important:** DO NOT EDIT - this is the source of truth

---

#### STAKEHOLDER_MEETING_NOTES.md (5.9KB)
**Purpose:** Organized requirements from November 30 meeting

**Contents:**
- Critical fixes (4 items - ALL COMPLETE)
- High-priority features (14 items)
- Testing needed (6 items)
- Discussion points (2 items)
- Prioritized by impact and effort

**When to reference:**
- Planning sprints
- Understanding stakeholder priorities
- Checking feature status

**Status:** Active development guide for v7.x features

---

### PowerPoint Documentation (powerpoint/)

#### PHASE_1_COMPLETION_SUMMARY.md (20.1KB)
**Purpose:** Technical deep dive into PowerPoint Phase 1 (Matching)

**Contents:**
- Matching system architecture
- Multi-scorer fuzzy matching (3 algorithms)
- Keyword category boosting (+15%)
- Variant name normalization
- Test results (78.9% accuracy)
- User confirmation UI
- Technical implementation details

**When to reference:**
- Understanding matching logic
- Improving match accuracy
- Debugging matching issues

**Status:** Complete and production-ready (v6.0-6.11)

---

#### PHASE_2_COMPLETION_SUMMARY.md (9.9KB)
**Purpose:** Production summary of PowerPoint Phase 2 (Generation)

**Contents:**
- Generation workflow
- Pricing table updates (2×3, 2×4, 3×4 formats)
- Multi-variant consolidation (v6.13)
- Font preservation (15pt)
- Impact slide customization
- Cover slide generation
- Performance metrics

**When to reference:**
- Understanding generation process
- Modifying PowerPoint output
- Adding new table formats

**Status:** Complete and production-ready (v6.0-6.17)

---

### Testing Documentation (testing/)

#### TAB3_TAB4_TESTING_CHECKLIST.md (7.2KB)
**Purpose:** Comprehensive testing checklist for Tab 3 → Tab 4 workflow

**Contents:**
- Data flow validation (12 checks)
- Calculation accuracy (8 checks)
- Client information (11 fields)
- Edge cases and error handling
- Invoice generation validation
- Test data examples

**When to reference:**
- Testing Tab 3 → Tab 4 changes
- Regression testing
- Validating data persistence

**Usage:** Follow checklist step-by-step after any Tab 3/Tab 4 changes

---

### Archive Documentation (archive/)

#### Purpose
Historical reference for completed work. Contains:
- **powerpoint-planning/** (14 files) - PowerPoint feature planning docs
- **tab2-improvements/** (9 files) - Tab 2 UI redesign documentation
- **Other completed planning docs** (5 files)

**Why archived:**
- Work is complete and in production
- Documentation no longer needed for active development
- Preserved for historical reference
- Reduces clutter in active docs

**When to reference:** Historical context, understanding past decisions

---

## Code Patterns & Conventions

### Documentation Style
All docs follow this structure:
```markdown
# Title

**Last Updated:** YYYY-MM-DD
**Status:** Active / Complete / Archived
**Version:** X.X.X (if applicable)

## Overview
[Brief description]

## Contents
[Detailed sections]

## Links
[Related documentation]
```

### Cross-Referencing
Always use relative links:
```markdown
See [METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md) for pricing details.
See [PHASE_1_COMPLETION_SUMMARY.md](powerpoint/PHASE_1_COMPLETION_SUMMARY.md) for matching.
```

### Version History
Include version context for time-sensitive info:
```markdown
**Added in v6.13:** Multi-variant PowerPoint support
**Changed in v7.3.0:** NGO → Non-profit terminology
**Deprecated in v6.18:** Old jaggery_demo scripts
```

---

## Common Tasks

### To understand pricing calculations:
1. Read `planning/METHODOLOGY_LOGIC.md` (comprehensive)
2. Check `src/pricing_engine.py` for implementation
3. Run `scripts/features/test_bidirectional_pricing.py` for examples

### To understand data structure:
1. Read `planning/RESTRUCTURE_CONTEXT.md`
2. Run `scripts/core/investigate_data.py`
3. Check Google Sheets directly

### To understand invoice format:
1. Read `planning/INVOICE_AND_PROPOSAL_SPEC.md`
2. Check Tab 4 in app.py
3. Generate sample invoice in app

### To understand PowerPoint automation:
1. Read `powerpoint/PHASE_2_COMPLETION_SUMMARY.md` (overview)
2. Read `powerpoint/PHASE_1_COMPLETION_SUMMARY.md` (technical details)
3. Check `src/slide_matcher.py` and `src/pptx_generator.py`

### To plan new features:
1. Check `meetings/STAKEHOLDER_MEETING_NOTES.md` for priorities
2. Read relevant planning docs
3. Create test script in `scripts/features/`
4. Update `ACTIVE_DEVELOPMENT_TODO.md` with progress

### To find archived documentation:
1. Check `docs/archive/` directory
2. Look for topic-specific subdirectories
3. Reference for historical context only

---

## Important Notes

### Documentation Maintenance
- Update docs when implementing features
- Keep cross-references current
- Archive completed work
- Version-tag time-sensitive information

### Single Source of Truth
- **Planning**: `planning/METHODOLOGY_LOGIC.md` for pricing
- **Data**: `planning/RESTRUCTURE_CONTEXT.md` for structure
- **Invoices**: `planning/INVOICE_AND_PROPOSAL_SPEC.md` for format
- **Requirements**: `meetings/STAKEHOLDER_MEETING_NOTES.md` for priorities

### Do Not Edit
- `meetings/RAW_MEETING_NOTES_113024.md` - Original notes
- `archive/*` - Historical reference only

### Active vs Archive
- **Active docs** (20 files) - Current development reference
- **Archived docs** (23+ files) - Historical reference
- Move to archive when work is complete and stable

---

## Recent Changes (v7.3.0)

### Documentation Reorganization
- Created `docs/meetings/` subdirectory
- Created `docs/investigations/` subdirectory
- Created `docs/testing/` subdirectory
- Improved navigation and organization

### New Documentation
- `CODE_SIMPLIFICATION_AGENT.md` - Cleanup process reference
- `TAB3_TAB4_TESTING_CHECKLIST.md` - Comprehensive test guide

### Updates
- `README.md` - Updated documentation index
- `STAKEHOLDER_MEETING_NOTES.md` - Updated feature status
- All docs - Version numbers and dates refreshed

---

## Documentation Coverage

### By Topic
- ✅ Planning & Requirements (4 files)
- ✅ Pricing & Calculations (1 comprehensive file)
- ✅ Data Structure (1 file)
- ✅ Invoice Format (1 file)
- ✅ PowerPoint Automation (2 files)
- ✅ Testing (1 checklist)
- ✅ Meeting Notes (2 files)
- ✅ Technical Patterns (2 files)
- ✅ Historical Archive (23+ files)

### By Audience
- **Developers:** All docs are dev-friendly
- **AI Assistants:** CLAUDE.md files provide context
- **Stakeholders:** Meeting notes and planning docs
- **Testers:** Testing checklists and feature docs

---

## Future Enhancements

### Planned Documentation
- Tab 2 redesign specification (when approved)
- Customer Setup Form requirements (when defined)
- Advanced tax calculation guide (if implemented)
- Batch processing workflow (if implemented)

### Documentation Improvements
- API reference for src/ modules
- Architecture diagrams (ASCII or Mermaid)
- Video tutorials (screen recordings)
- FAQ document

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **Active Development:** [../ACTIVE_DEVELOPMENT_TODO.md](../ACTIVE_DEVELOPMENT_TODO.md)
- **Changelog:** [../CHANGELOG.md](../CHANGELOG.md)
- **Source Code:** [../src/README.md](../src/README.md)
- **Test Scripts:** [../scripts/README.md](../scripts/README.md)
- **Production App:** https://pricing-data-solution-pbp.onrender.com
