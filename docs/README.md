# Documentation Index

**Project:** Peace by Piece International - Order Management System
**Current Version:** 7.3.0
**Last Updated:** 2025-12-20

---

## Quick Start

- **New to the project?** Read [../README.md](../README.md) first, then [planning/PLANNING.md](planning/PLANNING.md)
- **Need pricing logic?** See [planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md)
- **Working on PowerPoint?** Start with [powerpoint/PHASE_2_COMPLETION_SUMMARY.md](powerpoint/PHASE_2_COMPLETION_SUMMARY.md)
- **Client questions?** Check [CLIENT_QUESTIONS.md](CLIENT_QUESTIONS.md)

---

## Folder Structure

```
docs/
├── README.md                    # This file - documentation index
├── CLIENT_QUESTIONS.md          # Unanswered client questions
├── SCROLL_PRESERVATION_PATTERN.md # Scroll preservation implementation
├── SESSION_STATE_AUDIT.md       # Session state management
├── CODE_SIMPLIFICATION_AGENT.md # Code cleanup process documentation
│
├── planning/                    # Core project documentation
│   ├── PLANNING.md             # Project requirements & goals (READ FIRST)
│   ├── METHODOLOGY_LOGIC.md    # Pricing calculations & business rules
│   ├── RESTRUCTURE_CONTEXT.md  # Data structure from master_pricing_template
│   └── INVOICE_AND_PROPOSAL_SPEC.md  # Invoice/PO format specifications
│
├── powerpoint/                  # PowerPoint Automation (Phase 1 & 2)
│   ├── PHASE_2_COMPLETION_SUMMARY.md  # Phase 2 final summary (READ FOR STATUS)
│   └── PHASE_1_COMPLETION_SUMMARY.md  # Phase 1 technical deep dive
│
├── meetings/                    # Stakeholder meetings and notes
│   ├── STAKEHOLDER_MEETING_NOTES.md   # Organized requirements from Nov 30
│   └── RAW_MEETING_NOTES_113024.md    # Original meeting notes (do not edit)
│
├── testing/                     # Testing documentation
│   └── TAB3_TAB4_TESTING_CHECKLIST.md # Tab 3→4 data flow test plan
│
├── investigations/              # Technical investigations and debugging
│   └── PARTNER_POC_INVESTIGATION.md   # Partner contact pipeline debugging
│
└── archive/                     # Historical/deprecated documentation
    ├── powerpoint-planning/     # PowerPoint planning docs (14 files)
    ├── tab2-improvements/       # Tab 2 redesign docs (9 files)
    └── [Other archived documents]
```

---

## Documentation by Topic

### Core Project Documentation

**Always refer to these before starting work:**

1. **[planning/PLANNING.md](planning/PLANNING.md)** - Project requirements, architecture decisions, implementation plans
2. **[planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md)** - Pricing calculations, business rules, partner-specific logic
3. **[planning/RESTRUCTURE_CONTEXT.md](planning/RESTRUCTURE_CONTEXT.md)** - Current data structure from Google Sheets
4. **[planning/INVOICE_AND_PROPOSAL_SPEC.md](planning/INVOICE_AND_PROPOSAL_SPEC.md)** - Invoice/PO format requirements

### PowerPoint Automation

**Phase 2 Complete - Production Ready**

- **[powerpoint/PHASE_2_COMPLETION_SUMMARY.md](powerpoint/PHASE_2_COMPLETION_SUMMARY.md)** - Complete Phase 2 summary
- **[powerpoint/PHASE_1_COMPLETION_SUMMARY.md](powerpoint/PHASE_1_COMPLETION_SUMMARY.md)** - Technical deep dive on matching system
- See [archive/powerpoint-planning/](archive/powerpoint-planning/) for detailed planning docs (14 files)

### Stakeholder Meetings

- **[meetings/STAKEHOLDER_MEETING_NOTES.md](meetings/STAKEHOLDER_MEETING_NOTES.md)** - Organized requirements from Nov 30 meeting
- **[meetings/RAW_MEETING_NOTES_113024.md](meetings/RAW_MEETING_NOTES_113024.md)** - Original meeting notes (do not edit)

### Testing Documentation

- **[testing/TAB3_TAB4_TESTING_CHECKLIST.md](testing/TAB3_TAB4_TESTING_CHECKLIST.md)** - Tab 3→4 data flow testing plan
- See scripts/ directory for 26 test scripts organized by type

### Technical Investigations

- **[investigations/PARTNER_POC_INVESTIGATION.md](investigations/PARTNER_POC_INVESTIGATION.md)** - Partner contact pipeline debugging
- See scripts/investigations/ for debugging scripts

### Development Process

- **[CODE_SIMPLIFICATION_AGENT.md](CODE_SIMPLIFICATION_AGENT.md)** - Autonomous code cleanup process documentation
- **[SCROLL_PRESERVATION_PATTERN.md](SCROLL_PRESERVATION_PATTERN.md)** - Scroll preservation implementation
- **[SESSION_STATE_AUDIT.md](SESSION_STATE_AUDIT.md)** - Session state management

### Client Questions

**[CLIENT_QUESTIONS.md](CLIENT_QUESTIONS.md)** - Unanswered questions requiring client input

---

## Key Concepts

### Data Architecture

**3-Sheet Structure** (from [planning/RESTRUCTURE_CONTEXT.md](planning/RESTRUCTURE_CONTEXT.md)):
1. **Template** - Partner-product pricing data
2. **Metadata** - Deliverable field definitions
3. **Partner-Specific Info** - Partner configuration

### Pricing System

**From [planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md):**
- Tiered pricing (T1-T6) or flat-rate
- Markup applies to product cost only (not customization)
- MOQ calculation: `ceil(1000 / unit_price)`
- Marketing rounding (charm pricing)
- Non-profit discount (5%) and custom discounts

### PowerPoint Automation

**Two-Phase System:**
1. **Phase 1 (Matching)** - 78.9% automatic matching with user confirmation
2. **Phase 2 (Generation)** - Dynamic pricing tables, font preservation, one-click download

**Key Files:**
- `src/slide_matcher.py` - Matching engine
- `src/pptx_generator.py` - Generation engine
- `templates/November All Slides.pptx` - 339-slide template

---

## Recent Updates

### Version 7.3.0 (2025-12-20)
**Week 2 Sprint - 3 of 6 features complete:**
- ✅ Bidirectional price editing in Tab 3 (edit price or markup directly)
- ✅ NGO → Non-profit terminology update (better inclusivity)
- ✅ Directory reorganization (docs/ and scripts/ organized by topic)
- ✅ CHANGELOG.md added (comprehensive version history)

### Version 7.2.0 (2025-12-13)
- ✅ Multiple partner contacts support
- ✅ Partner POC pipeline debugging and fixes
- ✅ Tab 3→4 comprehensive test suite

### Version 7.0-7.1 (2025-12-10)
- ✅ Search bar in Tab 1
- ✅ Bidirectional pricing in Tab 1
- ✅ $0.50 rounding option
- ✅ Tab 3 table restructuring
- ✅ Kitting pricing sections
- ✅ Payment terms Net 15

### Version 6.0-6.18 (2025-11-05 to 2025-11-20)
- ✅ PowerPoint automation complete (Phase 1 & 2)
- ✅ Production deployment on Render
- ✅ Codebase simplification (49% reduction)
- ✅ 4-tab workflow structure
- ✅ Saved proposals/orders (cloud-persistent)
- ✅ HTML form import with product extraction

---

## How to Use This Documentation

### For New Features
1. Read [planning/PLANNING.md](planning/PLANNING.md) for project context
2. Check [planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md) for business rules
3. Review relevant feature docs (e.g., PowerPoint folder)
4. Check [CLIENT_QUESTIONS.md](CLIENT_QUESTIONS.md) for open questions

### For Bug Fixes
1. Search for related feature documentation
2. Check completion summaries for known issues
3. Review test plans for edge cases
4. Update relevant docs after fixing

### For Code Reviews
1. Verify changes follow [planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md)
2. Check against specs in planning folder
3. Update completion summaries if needed

### Adding New Documentation
- **Core specs** → `planning/`
- **Feature docs** → Create new subfolder (like `powerpoint/`)
- **Historical** → `archive/`
- **Client info** → Root `docs/` folder
- **Always update this README** with new files

---

## Contributing Guidelines

When updating documentation:

1. **Keep it current** - Update docs when code changes
2. **Be specific** - Include line numbers, file paths, examples
3. **Be concise** - Beginner-friendly, no jargon
4. **Cross-reference** - Link to related docs
5. **Date stamp** - Include "Last Updated" dates
6. **Update this README** - Keep index current

---

## Documentation Standards

- **Format:** Markdown (.md)
- **Naming:** SCREAMING_SNAKE_CASE for major docs, lowercase for helpers
- **Headers:** Use H1 (#) for title, H2 (##) for major sections
- **Code blocks:** Always specify language (```python, ```bash)
- **File paths:** Use relative paths from project root
- **Status tags:** Use ✅ ⏳ ❌ for clarity

---

## Need Help?

- **Technical questions:** Check [planning/METHODOLOGY_LOGIC.md](planning/METHODOLOGY_LOGIC.md)
- **Architecture questions:** See [planning/PLANNING.md](planning/PLANNING.md)
- **Feature status:** Check relevant completion summary
- **Missing docs:** Create an issue or add to [CLIENT_QUESTIONS.md](CLIENT_QUESTIONS.md)

---

**Maintained by:** Development Team
**Last Review:** 2025-12-20
