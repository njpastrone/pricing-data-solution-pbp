# Active Development TODO

**Last Updated:** December 20, 2024
**Current Version:** 7.3.0
**Sprint:** Week 2 - New Feature Implementation

---

## 🔴 ACTIVE WORK (Week 2 Sprint)

### Currently Implementing (3 of 6 features complete)

#### ✅ Completed Today
1. **Direct client price editing in Tab 3** - Bidirectional pricing like Tab 1
2. **NGO → Non-profit terminology** - Updated throughout app
3. **Directory reorganization** - Cleaner structure

#### 📝 Remaining
4. **Tab 3 Option B toast notification** ✅ COMPLETED
   - [x] Add success message adding to order directly from Tab 3 Option B; will match the behavior from Tab 1 "Add to Proposal"
   - **Location:** app.py (Tab 3, Option B section)
   - **Completed:** Added toast notifications for:
     - "Import All Products from Proposal" button (line 4541)
     - Individual product selection from proposal (line 4598)
     - Manual "Add to Order" button (line 4710)

5. **Execution form updates**
   - [ ] Change New/Existing client to checkbox format
   - [ ] Update date format from YYYY-MM-DD to MM/DD/YY app-wide
   - **Location:** app.py (Tab 4, all date fields)

6. **Customization Add-On feature**
   - [ ] Add within "Include Customization" section
   - [ ] Allow multiple add-ons (2nd color, special wood, etc.)
   - [ ] Display as separate line items in invoice
   - [ ] Easier than using Custom Line Items
   - **Location:** app.py (Tab 3, Section 2 - Product editing)

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