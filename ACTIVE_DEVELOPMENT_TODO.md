# Active Development TODO List

**Last Updated:** 2025-12-11
**Status:** Active Development
**Related Docs:**
- [STAKEHOLDER_MEETING_NOTES.md](STAKEHOLDER_MEETING_NOTES.md) - Full context and details
- [RAW_MEETING_NOTES_113024.md](RAW_MEETING_NOTES_113024.md) - Original meeting notes

---

## ✅ COMPLETED FIXES

### Clear Data Bug ✅ FIXED (2025-12-02)
- [X] **ISSUE:** "Clear Data" appeared to delete saved orders (was UX issue, not actual deletion)
- [X] Renamed button to "Reset Current Session" for clarity
- [X] Updated warning to explicitly state saved data is preserved
- [X] Moved saved proposals/orders to sidebar for constant visibility
- **Solution:** Reorganized UI to make saved work always visible in sidebar
- **Result:** Users now clearly see saved work is separate from current session

### Save UX Improvements ✅ COMPLETE (2025-12-04)
- [X] Moved saved proposals to sidebar (always visible)
- [X] Moved saved orders to sidebar (always visible)
- [X] Added save button at bottom of Tab 1
- [X] Added quick save at top of Tab 3 and bottom of Tab 3
- [X] Add unsaved changes indicator - Shows ⚠️ in sidebar and save sections
- [X] Add auto-save status - Shows "Saved X minutes ago" in sidebar and tabs
- **Implementation:**
  - Added hash-based change detection for proposals and orders
  - Track save timestamps and display relative time
  - Visual indicators in sidebar, Tab 1, and Tab 3
  - Updates automatically after successful saves
- **Result:** Users always know when they have unsaved changes and when last saved

### Client Info Persistence Bug ✅ FIXED (2025-12-04)
- [X] **ISSUE:** Client info deleted when editing confirmed orders
- [X] Store client info in session state before confirmation
- [X] Restore client info when "Edit Order" clicked
- **File:** app.py (Tab 4 section)
- **Test:** Confirm order → Edit → Verify data persists
- **Solution:** Added callback functions to all 12 input fields in "Edit Order Information" section using on_change parameter
- **Result:** Client info now persists across page reruns and when transitioning between confirmed/edit states

---

## 🔴 CRITICAL FIXES - REMAINING (0 left - ALL COMPLETE)
*All critical data loss issues have been resolved*

---

## 🟠 HIGH PRIORITY FEATURES - TODO

### Spreadsheet Structure Changes ✅ COMPLETE (2025-12-04)
- [X] Add "Shipping Cost (PBP)" column to master spreadsheet (completed by user)
- [X] Rename "Shipping" → "Shipping Price (Client)" (completed by user)
- [X] Fix Mi Eelo shipping cost data (completed by user)
- [X] Update data_loader.py to read new columns
- [X] Connect to Tab 3 "Shipping Cost from Partner ($)"
- **Files:** Google Sheets, src/data_loader.py, app.py
- **Implementation:** Added helper functions in helpers.py to handle both column structures
- **Result:** Backward compatible with demo dataset, auto-populates partner_shipping field

### Tab 1: Search & Pricing
- [X] Add search bar above product catalog ✅ COMPLETE (2025-12-04)
  - Filter products by name/partner/description
  - Use st.text_input with real-time filtering
- [x] Add bidirectional price editing in proposal table
  - Currently: Markup % → Price
  - Need: Price → Markup % calculation
  - ✅ COMPLETED (2025-12-10): Client Price column now editable, automatically updates Markup %
- [x] Add "Cancel" button to match change window
  - ✅ COMPLETED (2025-12-10): Added Cancel buttons to both alternatives and search modes
- [x] Add $0.50 rounding option (make default)
  - Add to both Tab 1 and Tab 3
  - ✅ COMPLETED (2025-12-10): Added round_to_nearest_fifty_cents() function and checkboxes in all tabs
  - Default enabled, applied before marketing rounding
- **File:** app.py (Tab 1)

### Tab 3: Table Restructuring ✅ COMPLETE (2025-12-10)
- [X] **Pricing Breakdown Table Changes:**
  - [X] Add "Units" column between "Per Unit" and "Total"
  - [X] Split "Total" → "PBP Cost" | "Client Price" columns
  - [X] Add product name as table header
- [X] **Order Summary Table Changes:**
  - [X] Reorder: Products → Subtotal → Customization → Subtotal
  - [X] Split "Total" → "PBP Cost" | "Client Price" columns
  - [X] Add product name headers
- **Implementation:**
  - New column order: Description | Units | PBP Cost (Per Unit) | PBP Cost | Client Price (Per Unit) | Client Price
  - Added helper functions in helpers.py for split calculations
  - Product descriptions now show "Base Product: [Product Name]"
  - Clear differentiation between PBP costs and client prices
- **Files:** app.py (Tab 3, sections 2 and 4), src/helpers.py

### Tab 3: New Fields
- [X] Add "Estimated Sales Tax" field in Order Settings ✅ COMPLETE (2025-12-11)
  - Simple number input like shipping
  - Include in order summary calculations
  - Sales tax only affects client price, not PBP cost
  - Persists through order save/load
- [X] Add "Kitting Pricing" section ✅ COMPLETE (2025-12-11)
  - PBP Cost field
  - Client Price field
  - Include in calculations
  - Added to both Tab 3 and Tab 4
  - Persists through save/load
- [X] Improve Order Notes UX ✅ COMPLETE (2025-12-11)
  - Move from dropdown to always-visible text areas
  - One section per note type
  - Changed from 2 to 5 specific categories
  - 3-2 column layout with word counts
  - Backward compatible with old orders
- [ ] Add multiple contacts support
  - Dynamic "Add Contact" button
  - Contact 1, Contact 2, etc.
- [ ] Add "Net 15" to payment terms dropdown
  - Add custom payment terms option
- **File:** app.py (Tab 3, section 3)

### Tab 4: Editable Descriptions
- [ ] Make "Item + Specs" column editable
- [ ] Add inline text inputs for each product
- [ ] Save edited descriptions to session state
- **File:** app.py (Tab 4)

---

## 🟡 TESTING CHECKLIST

### Calculation Tests
- [ ] Test client discount (5% NGO, custom %)
- [ ] Test "All Natural Salve" PowerPoint edge case
- [ ] Verify markup % calculations accuracy
- [ ] Test tiered pricing at all tier boundaries

### Data Flow Tests
- [ ] Test Tab 3 → Tab 4 client info transfer
- [ ] Test order confirmation → edit → data persistence
- [ ] Test saved proposals/orders across sessions
- [ ] Test dataset switching (demo ↔ real)

### PowerPoint Tests
- [ ] Test multi-variant products
- [ ] Test all table formats (2×3, 2×4, 3×4)
- [ ] Test impact slides for all partners

---

## 🔵 NEEDS DISCUSSION

### Tab 2 Redesign
- [ ] Research Google Forms API integration
- [ ] Design dropshipping-specific form with warnings
- [ ] Consider TypeForm or other alternatives
- [ ] **Action:** Schedule stakeholder meeting

---

## 🟢 FUTURE ENHANCEMENTS (After MVP)
- [ ] Custom product creation
- [ ] Executive samples handling
- [ ] Cloud-based PowerPoint templates
- [ ] Advanced tax calculations

---

## Development Notes

### Session State Keys to Watch
- `proposal_products` - Products in Tab 1 proposal
- `order_items` - Products in Tab 3 order
- `client_info` - Must persist through Tab 4 edit
- `saved_proposals` - Must not be cleared
- `saved_orders` - Must not be cleared

### Testing Commands
```bash
# Test with demo data
streamlit run app.py

# Test connection
streamlit run scripts/test_connection.py

# Check saved data
streamlit run scripts/test_saved_orders.py
```

### Git Commit Pattern
```bash
# Use clear prefixes
git commit -m "FIX: Clear Data no longer deletes saved orders"
git commit -m "FEAT: Add product search bar to Tab 1"
git commit -m "TEST: Verify markup calculations"
```

---

## Progress Tracking

### Completed
- ✅ Organized stakeholder feedback
- ✅ Created prioritized task list
- ✅ All critical fixes (4 items - COMPLETE)
- ✅ Spreadsheet structure changes (shipping columns)
- ✅ Tab 1 search bar and pricing improvements (bidirectional editing, cancel button, $0.50 rounding)
- ✅ Tab 3 table restructuring (PBP Cost vs Client Price columns)
- ✅ Tab 3 sales tax field (estimated sales tax input and calculations)
- ✅ Tab 3 kitting pricing section (separate PBP and client costs)
- ✅ Tab 3 order notes UX improvements (5 always-visible fields)

### Current Sprint (Week 1)
- ✅ Critical fixes (4 items - ALL COMPLETE)
- 🟠 High-priority features (10 of 14 complete)

### Next Sprint (Week 2)
- Complete high-priority features
- Run testing suite
- Schedule Tab 2 discussion

---

## Quick Context for AI Assistant

When you lose context, reference these files in order:
1. **CLAUDE.md** - Project rules and current state
2. **This file (ACTIVE_DEVELOPMENT_TODO.md)** - Current tasks
3. **STAKEHOLDER_MEETING_NOTES.md** - Detailed requirements
4. **app.py** - Main application code
5. **src/** - Modular helpers

Key project rules:
- Python/Streamlit only
- Beginner-friendly code
- Always simplest solution
- No emojis in app
- Make autonomous decisions