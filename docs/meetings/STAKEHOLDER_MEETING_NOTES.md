# Stakeholder Meeting Notes

**Date:** November 30, 2025 (Sunday)
**Attendees:** Executive Stakeholders
**Meeting Type:** Executive Stakeholder Review
**Raw Notes:** See [RAW_MEETING_NOTES_113024.md](RAW_MEETING_NOTES_113024.md)

---

## Organized Action Items

### 🔴 CRITICAL - Data Loss & Save Issues
These must be fixed immediately as they can cause users to lose work:

1. **Fix "Clear Data" destroying saved orders** (Tab 3)
   - Current behavior: "Clear Data" button deletes saved orders from database
   - Expected: Should only clear current session, NOT saved data
   - Impact: Users can accidentally delete all saved work

2. **Fix client info deletion on order edit** (Tab 4)
   - Current behavior: Client info gets deleted when user confirms order then clicks "Edit Order"
   - Expected: All data should persist when editing
   - Impact: Users lose entered data and must re-enter

3. **Improve Save UX for Proposals** (Tab 1)
   - Move "Save Proposal" button to bottom of Tab 1 (after full workflow)
   - Add "Saved Proposals" to sidebar for quick access
   - Ensure proposals persist across sessions

4. **Improve Save UX for Orders** (Tab 3)
   - Critical: Most orders won't be completed in one session
   - Need prominent, easy-to-find save functionality
   - Must clearly indicate when data is saved/unsaved

### 🟠 HIGH PRIORITY - Missing Core Features

#### Spreadsheet Updates
1. **Add shipping cost columns**
   - Add "Shipping Cost (PBP)" column to master spreadsheet
   - Rename existing "Shipping" to "Shipping Price (Client)"
   - Fix Mi Eelo shipping cost data
   - Connect to Tab 3 "Shipping Cost from Partner ($)" field

#### Tab 1 - Proposal Generator
1. **Add product search bar** - Reduce scrolling in large catalog
2. **Bidirectional price editing** - Allow editing Client Price to auto-calculate Markup % (currently only Markup % → Price)
3. **Add exit button for match change** - Users get stuck in "Change" window without making selection
4. **Add $0.50 rounding option** - Default to selected (in addition to marketing rounding)

#### Tab 3 - Order & Client Info
1. **Update Pricing Breakdown table** (Section 2)
   - Add "Units" column between "Per Unit" and "Total"
   - Split "Total" into "PBP Cost" and "Client Price" columns
   - Add product name header like "Item: [Product Name]"

2. **Update Order Summary table** (Section 4)
   - Show customization costs after products subtotal (products → subtotal → customization → subtotal)
   - Split "Total" into "PBP Cost" and "Client Price" columns
   - Add product name headers

3. **Add Sales Tax field** - Simple number input in Order Settings
4. **Add Kitting Pricing** - Gift set packaging costs (PBP Cost + Client Price)
5. **Improve Order Notes UX** - Make more prominent (currently hidden in dropdown)
6. **Add multiple contacts** - Allow Contact 1, Contact 2, etc. (unlimited)
7. **Add "Net 15" payment option** + custom configuration

#### Tab 4 - Execution & Accounting
1. **Make product descriptions editable** - "Item + Specs" column needs better descriptions for bookkeeper/client

### 🟡 MEDIUM PRIORITY - Testing & Validation

1. **Test client discount functionality** - Ensure all discount calculations work correctly
2. **Test "All Natural Salve" PowerPoint generation** - Known edge case
3. **Comprehensive table generation testing** - Test all product combinations
4. **Fix client details not transferring** - Tab 3 Section 5 → Tab 4 Section 1 data transfer issue
5. **Verify markup % calculations** - Ensure always accurate
6. **Investigate session state issues** - General stability improvements

### 🔵 DISCUSSION NEEDED

1. **Tab 2 - Client Order Form Generator**
   - Consider moving to Google Forms or cloud-based solution
   - Current HTML system feels clunky
   - Need separate dropshipping form with clear return package cost warnings
   - Requires team discussion before implementation

### 🟢 FUTURE ENHANCEMENTS (Low Priority)

1. **Custom product creation** - Allow creating custom products and adding to master spreadsheet
2. **Sample handling** - Add functionality for executive samples (billed to company, hidden from client)
3. **User-replaceable PowerPoint template** - Cloud-based or upload new template
4. **Sophisticated sales tax calculation** - Needs discussion before implementation

---

## Implementation Plan

### Phase 1: Critical Fixes (Immediate)
- [ ] Fix "Clear Data" issue
- [ ] Fix client info deletion bug
- [ ] Implement proper save functionality for proposals/orders

### Phase 2: Core Features (This Week)
- [ ] Update spreadsheet structure
- [ ] Add missing input fields (sales tax, kitting, contacts)
- [ ] Fix table layouts (split PBP Cost/Client Price)
- [ ] Add search and rounding features

### Phase 3: Testing & Validation (Next Week)
- [ ] Run comprehensive testing suite
- [ ] Fix markup calculations
- [ ] Resolve session state issues

### Phase 4: Discussion & Planning
- [ ] Schedule meeting about Tab 2 redesign
- [ ] Discuss future enhancements prioritization

---

## Next Steps

1. **Immediate:** Start with Phase 1 critical fixes to prevent data loss
2. **This week:** Work through Phase 2 core features
3. **Schedule:** Team meeting to discuss Tab 2 cloud-based alternatives
4. **Document:** Create test cases for Phase 3 validation

---

## Technical Notes

### Issues Summary Count
- **Critical (Data Loss):** 4 issues
- **High Priority (Features):** 14 issues
- **Testing Required:** 6 issues
- **Discussion Items:** 1 major item
- **Future Enhancements:** 4 items

### Key Areas Affected
- **Spreadsheet Structure:** Shipping cost columns
- **Tab 1:** Search, pricing, UI improvements
- **Tab 2:** Complete redesign discussion needed
- **Tab 3:** Table structure, new fields, UX improvements
- **Tab 4:** Editable descriptions, data persistence
- **Global:** Save/load functionality, session management