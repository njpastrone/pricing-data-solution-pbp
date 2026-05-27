# Active Development TODO

**Last Updated:** May 27, 2026
**Current Version:** 8.4.0
**Status:** Normal development - client form feature shipped

---

## Completed Work (Jan-May 2026)

### v8.4.0 Client Order Form Link (May 24-27, 2026)
- [x] New `src/client_form.py` module (session tokens, proposal loading, draft save/load, submission)
- [x] Query-param routing in app.py (`?client_form=<id>` renders standalone form)
- [x] Password gate for main app (client forms bypass gate)
- [x] Generate Client Form Link section in Tab 2
- [x] Redesigned client order form UX
- [x] Dropshipping file download in Tab 3 response preview
- [x] Unit tests (`tests/test_client_form.py`)
- [x] Bug fixes: single-date picker, removed Impact Card Selection, query param routing, password gate width

### v8.3.0 Leadership Meeting Fixes (May 23, 2026)
- [x] Current Proposal sidebar widget (scrollable list + remove dropdown)
- [x] Simplified Save Proposal section (removed duplicate Load Proposal UI)
- [x] Cleaned up Data Status sidebar (hid refresh, removed debug details)
- [x] Removed duplicate Client Budget input from Proposal Settings
- [x] Fixed Client Budget Range filter to use MSRP, added transparency message
- [x] Added Clear All Filters button
- [x] Hid Proposal Tables behind debug expander, removed CSV download
- [x] Fixed slide matching (get_slide_title helper)
- [x] Replaced broken tab navigation buttons with text notes
- [x] Google Form URL generation on-demand with Update button
- [x] Promoted Import from Proposal to Option B in Tab 3
- [x] Added PBP In-Hands Date field for Purchase Orders
- [x] Added editable Customization Description field
- [x] Fixed HTML/CSV download stale data bug
- [x] Hid legacy Shipping & Tariffs behind expander
- [x] Added Product Photos upload with HTML export embedding

### v8.2.0 Features (Feb-Apr 2026)
- [x] Template-resilient PowerPoint generation system
- [x] Tab 2 Google Form generation without requiring a proposal
- [x] Custom variant support and "Inquire about variants" handling
- [x] MOQ warnings for orders below minimum quantity
- [x] Volume order discount reminder for orders > $10,000
- [x] Kitting quantity field for per-product kitting
- [x] Tier parsing robustness (space-separated, multi-colon formats)

### v8.1.0 Schema Update (Jan 28, 2026)
- [x] Added "Other Add-On % (of Cost)" column (45 total columns)
- [x] "Package" -> "Case" terminology update
- [x] Fourth pricing method: "MSRP + Other Add-On %"
- [x] Volume Order Discount (5%) option
- [x] Per-product kitting as separate line items
- [x] Refresh Data button fix
- [x] PowerPoint discount/pricing fixes (3 issues)
- [x] All emojis removed from app
- [x] PBP $1,000 baseline MOV enforcement

### v8.0.0 Schema Transition (Jan 22, 2026)
- [x] 3 sophisticated pricing methods implemented
- [x] 33 -> 44 column schema expansion
- [x] Full backward compatibility via get_column_value()

### Earlier Completed
- [x] Google Forms integration (v7.6.0)
- [x] Schema update with backward compatibility (v7.4.0)
- [x] Bidirectional price editing (v7.3.0)
- [x] Production deployment on Render (v7.0)

---

## Needs Discussion

### Google Form Sign-In Issue
- Google Forms requires sign-in when File Upload questions are present
- **Partially resolved:** New Client Form Link (v8.4.0) bypasses Google sign-in entirely
- Google Form workflow kept as legacy fallback
- **Action:** Consider fully deprecating Google Form workflow in favor of Client Form Link

### Customer Setup Form
- Define requirements
- Determine integration points
- Design user experience flow
- **Action:** Gather requirements

---

## Future Enhancements (Post-MVP)
- Custom product creation workflow
- Executive samples handling
- Advanced tax calculations
- Batch order processing
- Email integration for forms

---

## Quick Stats
- **Codebase:** ~19,500 lines of Python
- **Test Scripts:** 55+ organized in scripts/
- **Schema:** v8.1.0 (45 columns, 4 pricing methods)
- **Latest:** v8.4.0 - Client Order Form as shareable link (May 27, 2026)
- **Documentation:** See [CHANGELOG.md](CHANGELOG.md) for full history

---

## Development Guidelines

### Commit Pattern
```bash
git commit -m "FEAT: Brief description"  # New feature
git commit -m "FIX: Brief description"   # Bug fix
git commit -m "TEST: Brief description"  # Test addition
git commit -m "DOC: Brief description"   # Documentation
```

### Testing Commands
```bash
# Core functionality
streamlit run scripts/core/test_connection.py

# Feature tests
python scripts/features/test_bidirectional_pricing.py

# Run app
streamlit run app.py
```

### Key Files
- **app.py** - Main application (~11,100 lines)
- **src/** - 14 modular helpers and engines
- **docs/** - All documentation
- **CHANGELOG.md** - Completed work history

---

## Links
- [Production App](https://pricing-data-solution-pbp.onrender.com)
- [Stakeholder Notes](docs/meetings/STAKEHOLDER_MEETING_NOTES.md)
- [Testing Checklist](docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md)