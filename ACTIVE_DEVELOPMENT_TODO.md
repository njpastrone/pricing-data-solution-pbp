# Active Development TODO

**Last Updated:** May 23, 2026
**Current Version:** 8.2.0
**Status:** Normal development - post-schema features and maintenance

---

## Completed Work (Jan-Apr 2026)

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
- **Codebase:** ~18,300 lines of Python
- **Test Scripts:** 55+ organized in scripts/
- **Schema:** v8.1.0 (45 columns, 4 pricing methods)
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
- **app.py** - Main application (~10,600 lines)
- **src/** - 12 modular helpers and engines
- **docs/** - All documentation
- **CHANGELOG.md** - Completed work history

---

## Links
- [Production App](https://pricing-data-solution-pbp.onrender.com)
- [Stakeholder Notes](docs/meetings/STAKEHOLDER_MEETING_NOTES.md)
- [Testing Checklist](docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md)