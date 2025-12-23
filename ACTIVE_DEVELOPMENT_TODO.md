# Active Development TODO

**Last Updated:** December 20, 2024
**Current Version:** 7.3.0
**Sprint:** Week 2 - New Feature Implementation

---

## 🔴 ACTIVE WORK (Week 2 Sprint)

### ✅ Week 2 Sprint COMPLETE! (6 of 6 features done)

#### ✅ Completed Features
1. **Direct client price editing in Tab 3** - Bidirectional pricing like Tab 1
2. **NGO → Non-profit terminology** - Updated throughout app
3. **Directory reorganization** - Cleaner structure
4. **Tab 3 Option B toast notification** - Added deferred toast pattern for all product additions
5. **Execution form updates** - Checkbox format for New Client? and MM/DD/YY date format
6. **Customization Add-On feature** - Multiple add-ons with separate invoice line items

---

## 🟡 TESTING NEEDED

### Calculation Tests
- [ ] Client discount (5% Non-profit, custom %)
- [ ] Markup % calculations with new bidirectional pricing
- [ ] Tiered pricing at all boundaries
- [ ] Sales tax calculations
- [ ] Kitting cost calculations
- [ ] $0.50 rounding accuracy

### PowerPoint Tests
- [ ] Multi-variant products
- [ ] All table formats (2×3, 2×4, 3×4)
- [ ] Impact slides for all partners

### Integration Tests
- [ ] Tab 3 → Tab 4 data flow with new features
- [ ] Saved proposals/orders with new fields
- [ ] Dataset switching (demo ↔ real)

---

## 🔵 NEEDS DISCUSSION

### Tab 2 Redesign
- Research Google Forms API integration
- Design dropshipping-specific form
- Consider TypeForm alternatives
- **Action:** Schedule stakeholder meeting

### Customer Setup Form (NEW)
- Define requirements
- Determine integration points
- Design user experience flow
- **Action:** Gather requirements

---

## 🟢 FUTURE ENHANCEMENTS (Post-MVP)
- Custom product creation workflow
- Executive samples handling
- Advanced tax calculations
- Batch order processing
- Email integration for forms

---

## 📊 Quick Stats
- **Completed Features:** 16 of 19 (84%)
- **Active Sprint:** Week 2
- **Test Scripts:** 28 organized in scripts/
- **Documentation:** See [CHANGELOG.md](CHANGELOG.md) for history

---

## 🛠️ Development Guidelines

### Commit Pattern
```bash
git commit -m "FEAT: Brief description"  # New feature
git commit -m "FIX: Brief description"   # Bug fix
git commit -m "TEST: Brief description"  # Test addition
git commit -m "DOCS: Brief description"  # Documentation
```

### Testing Commands
```bash
# Core functionality
streamlit run scripts/core/test_connection.py

# Feature tests
python scripts/features/test_bidirectional_pricing.py

# Run app with real data
streamlit run app.py
```

### Key Files
- **app.py** - Main application (359KB)
- **src/** - Modular helpers and engines
- **docs/** - All documentation
- **CHANGELOG.md** - Completed work history

---

## 📝 Notes for Next Session
- Test bidirectional pricing thoroughly
- Consider batching date format changes
- Customization Add-On needs UI/UX design
- Multiple Streamlit instances running (ports 8502, 8503)

---

## Links
- [Production App](https://pricing-data-solution-pbp.onrender.com)
- [Stakeholder Notes](docs/meetings/STAKEHOLDER_MEETING_NOTES.md)
- [Testing Checklist](docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md)