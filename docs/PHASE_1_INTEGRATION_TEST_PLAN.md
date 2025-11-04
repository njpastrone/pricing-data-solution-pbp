# Phase 1 Integration Test Plan

## Date
2025-11-04

## Purpose
Validate complete end-to-end workflow from proposal creation to PowerPoint match review.

---

## Test Scenario: Complete Proposal → PowerPoint Workflow

### Prerequisites
- App running: `streamlit run app.py`
- PowerPoint template exists at `templates/November All Slides.pptx`
- Google Sheets data loaded successfully

### Test Steps

#### Phase 1: Create Proposal (Tab 1, Sections 1-9)

1. **Filter Products (Section 1)**
   - [ ] Apply max price filter (e.g., $100)
   - [ ] Select partner filter (e.g., Partner X)
   - [ ] Verify filtered results display correctly
   - [ ] Clear filters

2. **Browse Product Catalog (Section 2)**
   - [ ] Find "Upcycled Executive Urban Briefcase"
   - [ ] Click "Add to Proposal"
   - [ ] Verify success message appears
   - [ ] Verify product appears in Section 3

3. **Configure Proposal (Section 3)**
   - [ ] Set quantity to 50
   - [ ] Set markup to 150%
   - [ ] Verify pricing updates in real-time
   - [ ] Add 2 more products (e.g., Laptop Sleeve, Butcher Block)

4. **Generate Proposal Tables (Section 4)**
   - [ ] Verify 3 product tables display
   - [ ] Verify MOQ calculations correct
   - [ ] Verify markup applied correctly
   - [ ] Download individual proposal CSV
   - [ ] Download "All Proposal Tables" CSV

5. **Optional: Configure Kitting & Terms (Sections 5-6)**
   - [ ] Skip or review kitting pricing
   - [ ] Review terms & conditions
   - [ ] Copy terms if needed

6. **Optional: Dropshipping Notes (Section 7)**
   - [ ] Review dropshipping instructions
   - [ ] Modify if needed

7. **Optional: Order Details (Section 8)**
   - [ ] Add client info (company name, contact)
   - [ ] Click "Add Info to Order Form"

8. **Optional: Client Order Form (Section 9)**
   - [ ] Download HTML client order form
   - [ ] Verify formatting in browser
   - [ ] Verify product list included

#### Phase 2: PowerPoint Match Review (Tab 1, Section 10)

9. **Trigger Match Review**
   - [ ] Scroll to Section 10
   - [ ] Verify button shows: "Review Matches & Generate PowerPoint"
   - [ ] Click button
   - [ ] Verify spinner shows "Loading PowerPoint slides..."
   - [ ] Verify spinner shows "Matching products to slides..."
   - [ ] Verify success message: "Loaded X product slides from PowerPoint"

10. **Review Match Summary**
    - [ ] Verify match summary displays:
      - X exact matches (auto-confirmed)
      - X fuzzy matches (need your confirmation)
      - X products with no good match (will be skipped)
    - [ ] Verify counts are accurate

11. **Review Exact Matches (if any)**
    - [ ] Verify "Exact Matches" expander is collapsed by default
    - [ ] Expand expander
    - [ ] Verify exact match list displays correctly
    - [ ] Verify format: "Product Name → PPTX PRODUCT NAME"
    - [ ] Collapse expander

12. **Review Fuzzy Matches**
    - [ ] Verify "Fuzzy Matches" section is expanded by default
    - [ ] For each fuzzy match:
      - [ ] Verify product name header displays
      - [ ] Verify suggested match with confidence % displays
      - [ ] Verify confidence color (green ≥90%, orange <90%)
      - [ ] Verify 3 action buttons present

13. **Test Action: Confirm Match**
    - [ ] Click "✓ Yes, use this slide" on first fuzzy match
    - [ ] Verify success message: "✓ Confirmed: PPTX PRODUCT NAME"
    - [ ] Verify status indicator appears below buttons
    - [ ] Verify page reruns and state persists

14. **Test Action: Show Alternatives**
    - [ ] Click "→ Show alternatives" on second fuzzy match
    - [ ] Verify "Alternative Matches" expander appears and is expanded
    - [ ] Verify top 3 alternatives display with confidence scores
    - [ ] Select an alternative by clicking "Use this"
    - [ ] Verify success message for alternative
    - [ ] Verify confirmation status updates

15. **Test Action: Skip Product**
    - [ ] Click "X Skip this product" on third fuzzy match (if available)
    - [ ] Verify warning message: "Product will be skipped"
    - [ ] Verify skip status indicator appears

16. **Review Poor/No Matches (if any)**
    - [ ] Verify "Products with No Good Match" expander is collapsed
    - [ ] Expand expander
    - [ ] Verify list of poor matches displays
    - [ ] Verify caption: "These products likely don't have slides..."
    - [ ] Collapse expander

17. **Test Validation: Pending Confirmations**
    - [ ] If any fuzzy matches not confirmed/skipped:
      - [ ] Verify warning displays: "Please review X pending fuzzy matches..."
      - [ ] Verify "Pending Confirmations" expander shows list
      - [ ] Verify "Generate PowerPoint Presentation" button disabled or not shown
    - [ ] Confirm all remaining fuzzy matches

18. **Test Validation: Ready to Generate**
    - [ ] After all fuzzy matches confirmed/skipped:
      - [ ] Verify success message: "✓ Ready to generate PowerPoint with X products!"
      - [ ] Verify "Reset Confirmations" button appears
      - [ ] Verify "Generate PowerPoint Presentation" button appears

19. **Test Reset Functionality**
    - [ ] Click "Reset Confirmations" button
    - [ ] Verify all confirmation states cleared
    - [ ] Verify UI returns to initial state (no confirmations)
    - [ ] Re-confirm matches

20. **Test Generation (Phase 2 Placeholder)**
    - [ ] Click "Generate PowerPoint Presentation" button
    - [ ] Verify info message: "PowerPoint generation will be implemented in Phase 2!"
    - [ ] Verify JSON output of confirmed matches displays
    - [ ] Verify format: `{"GS Product Name": "PPTX Product Name", ...}`

#### Phase 3: Edge Case Testing

21. **Test Empty Proposal**
    - [ ] Remove all products from proposal
    - [ ] Verify Section 10 does not appear (only shown when products exist)

22. **Test Missing PowerPoint File**
    - [ ] Temporarily rename `templates/November All Slides.pptx`
    - [ ] Add product to proposal
    - [ ] Click "Review Matches & Generate PowerPoint"
    - [ ] Verify error message: "PowerPoint template not found at..."
    - [ ] Restore file name

23. **Test All Exact Matches**
    - [ ] Create proposal with only exact-match products:
      - Upcycled Executive Urban Briefcase
      - Butcher Block
      - Granola (if available)
    - [ ] Trigger match review
    - [ ] Verify all appear in "Exact Matches" expander
    - [ ] Verify no "Fuzzy Matches" section appears
    - [ ] Verify ready to generate immediately

24. **Test No Good Matches**
    - [ ] Create proposal with products not in PowerPoint:
      - Organic Baking Mixes
      - Salts & Seasonings
    - [ ] Trigger match review
    - [ ] Verify warning: "No usable matches found. Cannot generate..."
    - [ ] Verify generation disabled

---

## Expected Results

### Success Criteria
- ✅ All workflow steps complete without errors
- ✅ Exact matches auto-confirmed, no user action required
- ✅ Fuzzy matches require explicit user confirmation
- ✅ Validation prevents generation until all fuzzy matches addressed
- ✅ Reset functionality clears all confirmations
- ✅ Edge cases handled gracefully (empty, missing file, no matches)
- ✅ UI responsive and intuitive throughout workflow
- ✅ Session state persists correctly across reruns

### Known Limitations (Acceptable)
- PowerPoint loading takes 2-3 seconds (acceptable for Beta)
- Alternative matches limited to 3 (sufficient for most cases)
- Phase 2 generation not yet implemented (expected)

---

## Test Results

### Test Date: _____________
### Tester: _____________

### Overall Status: [ ] PASS  [ ] FAIL  [ ] PARTIAL

### Issues Found:
1. _______________________________________
2. _______________________________________
3. _______________________________________

### Recommendations:
1. _______________________________________
2. _______________________________________
3. _______________________________________

---

## Sign-Off

Phase 1 implementation is ready for:
- [ ] User Acceptance Testing
- [ ] Beta Release
- [ ] Production Release
- [ ] Phase 2 Development

**Approved by:** ___________________  **Date:** ___________
