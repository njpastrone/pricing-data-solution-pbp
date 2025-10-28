# UI Restructure Continuation Prompt

**Copy this entire prompt into a new Claude Code session to continue the UI restructure.**

---

## Context

I'm continuing the UI restructure of the Peace by Piece Order Management System. The project is a Python/Streamlit app that helps create quotes, proposals, invoices, and purchase orders for artisan products.

### What's Been Completed

**Phase 1 is DONE and TESTED ✅**
- Created 3-tab structure: Proposals, Order & Client Info, Execution & Accounting
- ALL existing functionality moved into Tab 2 (1675 lines properly indented)
- Tabs 1 and 3 have placeholder content
- Full backward compatibility maintained
- User has tested and confirmed everything works

### Current State

```
app.py structure:
├── Imports and configuration
├── Session state initialization
├── Header
├── Sidebar (instructions, recent orders, data status, downloads)
├── Data loading (Google Sheets)
└── TAB STRUCTURE
    ├── Tab 1: Proposals (PLACEHOLDER - needs Phase 2)
    ├── Tab 2: Order & Client Info (COMPLETE - all 10 sections working)
    └── Tab 3: Execution & Accounting (PLACEHOLDER - needs Phase 3)
```

### Important Files to Reference

**CRITICAL - Read these first:**
1. `docs/UI_RESTRUCTURE_PROGRESS.md` - Complete progress log with all changes made
2. `docs/UI_RESTRUCTURE_PLAN.md` - Original detailed plan (for reference)
3. `CLAUDE.md` - Project rules and guidelines (NON-NEGOTIABLE)
4. `app.py` - Main application (currently at Phase 1 completion)

**Backups available:**
- `backups/app_2025_10_28_1pm_backup.py` - Pre-restructure backup
- Git commits: `8f1d075` (initial backup), `baea97a` (Phase 1 complete)

### Project Rules (from CLAUDE.md)

**NON-NEGOTIABLE:**
1. Always use Python for all development
2. Leverage Streamlit for the front-end
3. Write beginner-friendly code
4. Always take the simplest route
5. Make autonomous decisions - avoid asking permissions
6. Minimize code base size
7. Avoid duplicating code
8. **NEVER use emojis in the app** (unprofessional)
9. Keep everything in app.py (single file, well-organized)

### Implementation Strategy

**Option B - Incremental Phased Approach:**
- Phase 1: Basic tab structure ✅ DONE
- Phase 2: Extract Proposals to Tab 1 ⏭️ NEXT
- Phase 3: Extract Execution to Tab 3
- Phase 4: Sidebar enhancements
- Phase 5: Final polish

Each phase must be testable before proceeding to the next.

---

## Your Task: Implement Phase 2

**Goal:** Move product browsing, filtering, and proposal generation from Tab 2 into Tab 1.

### What Needs to Move from Tab 2 to Tab 1

Look for these sections in Tab 2 (`with tab2:` block):

1. **Section 2: Select Products** (lines ~517-564)
   - Partner dropdown
   - Product dropdown
   - Product details display
   - Marketing description expander
   - Pricing tier info expander

2. **Section 9: Proposal Generation** (lines ~1527-1699)
   - Per-product proposal tables (MOQ pricing)
   - Customization fees display
   - Tariff information
   - Download buttons for proposals

### Phase 2 Implementation Plan

**Step 1: Create Tab 1 Structure**

In `with tab1:` block (currently placeholder), create:

```python
with tab1:
    st.header("Proposals - Product Catalog & Proposal Generation")
    st.caption("Browse products, configure proposals, and generate client quotes")
    st.divider()

    # Section 1: Filters
    st.subheader("1. Filter Products")
    # Price range filters
    # Partner multiselect
    # Country multiselect

    # Section 2: Product Catalog
    st.subheader("2. Product Catalog")
    # Display filtered products in expanders
    # "Add to Proposal" button for each

    # Section 3: Configure Product (when "Add to Proposal" clicked)
    # Quantity, markup, MSRP, customization inputs
    # "Add" and "Cancel" buttons

    # Section 4: Proposal Preview
    st.subheader("3. Proposal Preview")
    # List of products added to proposal
    # Edit/Remove buttons
    # Marketing rounding checkbox

    # Section 5: Proposal Generation
    st.subheader("4. Generate Proposal Tables")
    # MOQ-based pricing tables per product
    # Customization fees shown separately
    # Download buttons

    # Section 6: Terms & Conditions
    st.subheader("5. Terms & Conditions")
    # Load from config/terms_conditions.txt
    # Editable text area

    # Section 7: Client Order Form
    st.subheader("6. Client Order Form")
    # Pre-formatted text form for clients
    # Download button
```

**Step 2: Session State for Proposals**

Add these if not already present (check session state initialization section):

```python
# Proposal-specific session state
if 'proposal_products' not in st.session_state:
    st.session_state.proposal_products = []

if 'proposal_marketing_rounding' not in st.session_state:
    st.session_state.proposal_marketing_rounding = False

if 'configuring_product' not in st.session_state:
    st.session_state.configuring_product = None
```

**Step 3: Extract Product Browsing Logic**

From Tab 2 Section 2, extract:
- Partner/product dropdowns → Move to Tab 1 catalog display
- Product data fetching → Reuse in Tab 1
- Keep in Tab 2 for actual order building (different workflow)

**Step 4: Create Proposal Workflow**

Tab 1 workflow should be:
1. Filter products by price/partner/country
2. Browse catalog (all filtered products in expanders)
3. Click "Add to Proposal" → Opens configuration UI
4. Configure quantity, markup, customization
5. Add to proposal_products list
6. Preview all proposal products
7. Generate MOQ-based proposal tables
8. Download proposal + client order form

**Step 5: Keep Tab 2 Workflow Independent**

Tab 2 should keep:
- Product selection (Sections 2-5) for direct order building
- Order items management (Section 6)
- Order settings (Section 7)
- Order notes (Section 7.5)
- Order summary (Section 8)

Remove from Tab 2:
- Section 9 (Proposals) → Move to Tab 1
- Section 10 stays (Invoice/PO will move to Tab 3 in Phase 3)

**Step 6: Test Phase 2**

After implementation, verify:
- [ ] Tab 1: Can filter products
- [ ] Tab 1: Can browse filtered catalog
- [ ] Tab 1: Can configure and add products to proposal
- [ ] Tab 1: Proposal preview shows all products
- [ ] Tab 1: Can generate MOQ-based proposal tables
- [ ] Tab 1: Can download proposal CSVs
- [ ] Tab 1: Client order form generates correctly
- [ ] Tab 2: Product selection still works for orders
- [ ] Tab 2: Order workflow unchanged
- [ ] Tab 2: Section 10 (Invoice/PO) still works

---

## Key Implementation Notes

### Data Access
- `df_template` - Product/pricing data (loaded before tabs)
- `df_metadata` - Field definitions
- `df_partner_info` - Partner contacts
- All available in session state

### Important Functions (from src/)
- `get_unit_price_new_system(product_data, quantity)` - Get price for quantity
- `calculate_moq(unit_price)` - Calculate MOQ based on $1000 minimum
- `apply_marketing_rounding(price, enabled)` - Charm pricing
- `parse_tariff_rate(tariff_string)` - Extract tariff %
- All imported at top of app.py

### Proposal Products Format
Each item in `st.session_state.proposal_products` should be:
```python
{
    'product_data': product_row,  # Full row from df_template
    'quantity': int,
    'markup_percent': float,
    'msrp_value': float,
    'show_msrp': bool,
    'include_customization': bool,
    'customization_setup_fee': float,
    'customization_per_unit': float
}
```

### Proposal Table Format (4-column MOQ format)
```
| MOQ | Price Ea (@ Qty X) | Price Ea [Discount] | Delivery |
```

---

## Code Organization Guidelines

1. **Section Comments:** Use clear headers like:
   ```python
   # ============================================================
   # SECTION NAME
   # ============================================================
   ```

2. **Indentation:** Everything inside `with tab1:` must be indented 4 spaces

3. **Keep It Simple:** Don't over-engineer - maintain beginner-friendly code

4. **Test Incrementally:** Build section by section, test each piece

5. **Preserve Existing:** Don't break Tab 2 functionality

---

## Progress Tracking

**After completing Phase 2:**

1. Update `docs/UI_RESTRUCTURE_PROGRESS.md`:
   - Mark Phase 2 changes as complete
   - List all changes made
   - Update testing checklist

2. Create git commit:
   ```bash
   git add -A
   git commit -m "Phase 2: Extract proposals to Tab 1

   - Created product filtering UI
   - Implemented catalog browser
   - Added proposal configuration workflow
   - Moved proposal table generation to Tab 1
   - Added client order form generator
   - Removed Section 9 from Tab 2
   - Tested and verified both tabs work independently"
   ```

3. Update session notes in progress doc

---

## Testing Checklist for Phase 2

**Tab 1 - Proposals:**
- [ ] Filters work (price range, partners, countries)
- [ ] Catalog shows filtered products correctly
- [ ] Can click "Add to Proposal" on any product
- [ ] Configuration UI opens with correct defaults
- [ ] Can set quantity, markup, customization
- [ ] "Add to Proposal" button adds to list
- [ ] "Cancel" button closes configuration without adding
- [ ] Proposal preview shows all added products
- [ ] Can edit/remove products from proposal
- [ ] Marketing rounding checkbox works
- [ ] MOQ calculations are correct
- [ ] Proposal tables generate correctly
- [ ] Customization fees shown separately
- [ ] Download buttons work
- [ ] Terms & conditions load from config file
- [ ] Terms & conditions editable
- [ ] Client order form generates
- [ ] Client order form downloadable

**Tab 2 - Order & Client Info:**
- [ ] Product selection (Section 2) still works
- [ ] Can add products to order
- [ ] Order management unchanged
- [ ] Section 9 removed (no errors)
- [ ] Section 10 (Invoice/PO) still works
- [ ] All downloads still work

**General:**
- [ ] No Python errors
- [ ] Can switch between tabs without issues
- [ ] Session state persists across tabs
- [ ] Data loads correctly

---

## Questions to Ask If Unclear

1. Should proposal products be importable into Tab 2 orders? (Not required for Phase 2)
2. Should Tab 1 save proposal history? (Not required for Phase 2)
3. Any specific filter logic beyond price/partner/country? (Use existing filters)

---

## Start Implementation

Begin by reading:
1. `docs/UI_RESTRUCTURE_PROGRESS.md` - See exactly what was done in Phase 1
2. `app.py` lines 320-335 - See Tab 1 placeholder
3. `app.py` lines ~517-564 - Section 2 (product selection) to extract
4. `app.py` lines ~1527-1699 - Section 9 (proposals) to extract

Then implement Phase 2 following the plan above. Use the incremental approach:
- Build filters first, test
- Add catalog, test
- Add configuration, test
- Add proposal preview, test
- Move proposal generation, test
- Add client form, test

Document all changes in `docs/UI_RESTRUCTURE_PROGRESS.md` as you go.

**Good luck! The foundation from Phase 1 is solid, so Phase 2 should be straightforward.**
