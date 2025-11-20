# Tab 2 Restructure Plan - Edit-After-Add Pattern

**Date:** 2025-10-29
**Status:** Approved - Ready for Implementation

## Problem Statement

Current Tab 2 flow is confusing:
- Users configure product settings (quantity, markup, customization) BEFORE adding to order
- Settings are buried in multiple sections before the product is even in the order
- "Current Order" section feels like an afterthought at the bottom
- Hard to see what's in your order without scrolling

## New Design Philosophy

**"Add first, configure after"**
- Get products into the order basket quickly
- Then edit each product's settings directly in the order list
- All settings always visible (no hidden state)
- Clear visual hierarchy: Order list is primary, settings are inline

---

## New Section Structure

### Section 1: Partner & Product Selection
- Import from proposals button (with success banner if available)
- OR dropdown to select product + simple "Add to Order" button
- No quantity/markup/customization fields here
- Defaults: quantity=1, markup=100%, no customization

### Section 2: Current Order
- **Primary focus of the tab**
- List of all products in order
- Each product shows:
  - Product name, partner, pricing tier info
  - Editable quantity field
  - Editable markup % field
  - Customization checkbox + setup/per-unit fields (if available)
  - Calculated totals (base cost, markup, customer price, product total)
  - Remove button
- Always visible (no expand/collapse)
- Clean 2-column layout where possible

### Section 3: Order Settings
- Shipping method & cost
- Discount options
- Payment terms
- (No changes to this section)

### Section 4: Order Notes
- 5-category notes system
- (No changes to this section)

### Section 5: Order Summary
- Read-only totals
- Completeness check
- Link to Tab 3
- (No changes to this section)

---

## Import from Proposals Behavior

**What Carries Over:**
- Product selection
- Quantity
- Markup %
- Discount % (if set)

**What Does NOT Carry Over:**
- Customization settings (reset to unchecked)
- Rounding preferences (reset to default)
- Tariff settings (reset to default)

**Rationale:** These are the core pricing decisions. Customization details often change between proposal and actual order, so better to reconfigure.

---

## Implementation Details

### Product Addition (Section 1)

**Before:**
```python
# Complex form with:
- Product dropdown
- Quantity input
- Markup input
- Rounding checkbox
- Customization checkbox
- Setup fee input
- Per-unit input
- Tariff checkbox
- "Add to Order" button (at bottom after scrolling)
```

**After:**
```python
# Simple addition:
- Product dropdown
- "Add to Order" button (right next to dropdown)

# Defaults applied:
- quantity = 1
- markup_percent = 100.0
- round_to_five = False
- include_customization = False
- include_tariff = False
```

### Current Order Display (Section 2)

**Structure for each product:**
```
┌─────────────────────────────────────────────────────┐
│ Product Name | Partner Name              [Remove]   │
├─────────────────────────────────────────────────────┤
│ Tier info caption (e.g., "Using tier: 1-50 units") │
│                                                     │
│ ┌─────────────────┬─────────────────┐              │
│ │ Quantity: [__]  │ Markup %: [___] │              │
│ │ Tier: T1-T6     │ Round to $5: □  │              │
│ └─────────────────┴─────────────────┘              │
│                                                     │
│ Customization (if available):                      │
│ □ Include Customization                            │
│   Setup Fee: $___  Per-Unit: $___                  │
│                                                     │
│ Pricing Breakdown:                                 │
│ Base Cost:      $X.XX/unit  ($XXX.XX total)       │
│ Markup (XX%):   $X.XX/unit  ($XXX.XX total)       │
│ Customization:  $X.XX/unit  ($XXX.XX total)       │
│ ─────────────────────────────────────────         │
│ Product Total:  $XXX.XX                            │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Each product is a self-contained card
- All settings editable in-place
- Real-time calculation updates
- Clear visual separation between products
- Remove button prominently placed

### Section Renumbering

```
1. Partner & Product Selection
   ├─ Import from Proposals (if available)
   └─ Manual Product Selection

2. Current Order
   └─ (List of products with inline editing)

3. Order Settings
   ├─ Shipping
   ├─ Discounts
   └─ Payment Terms

4. Order Notes
   └─ (5-category notes)

5. Order Summary
   └─ (Read-only totals + completeness check)
```

---

## User Flow Examples

### Flow 1: Import from Proposal
1. User clicks "Import All Products from Proposal"
2. Products appear in Section 2 with proposal quantities and markups
3. User edits quantity for Product 1 (changes 10 → 15)
4. User adds customization to Product 2 (checks box, enters setup fee)
5. User proceeds to Section 3 for shipping/discounts

### Flow 2: Manual Product Addition
1. User selects "Product A" from dropdown
2. Clicks "Add to Order"
3. Product A appears in Section 2 with defaults (qty=1, markup=100%)
4. User changes quantity to 50
5. User selects "Product B" from dropdown
6. Clicks "Add to Order"
7. Product B appears in Section 2
8. User configures both products
9. User proceeds to Section 3

### Flow 3: Mixed Approach
1. User imports 3 products from proposal
2. Edits quantity on Product 1
3. Adds 1 additional product manually
4. Configures customization on new product
5. Proceeds to Section 3

---

## Benefits of New Design

1. **Clearer Mental Model:** "Add to basket, then configure"
2. **Less Scrolling:** No need to scroll past empty sections before adding products
3. **Better Visibility:** See all products and their settings at once
4. **Faster Workflow:** Quick add with defaults, then customize only what needs changing
5. **Consistent with E-commerce Patterns:** Familiar "shopping cart" UX
6. **Easier to Compare:** See all products side-by-side with their settings
7. **Simpler Section 1:** Just product selection, not a complex form

---

## Implementation Checklist

- [ ] Simplify Section 1 to just product dropdown + Add button
- [ ] Move all quantity/markup/customization fields into Section 2
- [ ] Create product card component for Section 2
- [ ] Update add_product logic to use defaults
- [ ] Update import_from_proposal logic to preserve only markup/discounts
- [ ] Add real-time calculation updates when settings change
- [ ] Update section numbering (2→3, 3→4, etc.)
- [ ] Test all workflows (add, edit, import, remove)
- [ ] Update documentation (CLAUDE.md, CHANGELOG.md)

---

## Code Structure Changes

### Session State (No Changes Needed)
```python
st.session_state.order_items = [
    {
        'product_name': str,
        'partner': str,
        'product_data': dict,
        'quantity': int,
        'markup_percent': float,
        'round_to_five': bool,
        'include_customization': bool,
        'customization_setup_fee': float,
        'customization_per_unit': float,
        'include_tariff': bool,
        # ... calculated fields
    }
]
```

### New Helper Function
```python
def add_product_with_defaults(product_data):
    """Add product to order with default settings"""
    return {
        'product_name': product_data.get('Product/Service', 'Unknown'),
        'partner': product_data.get('Partner', 'Unknown'),
        'product_data': product_data,
        'quantity': 1,
        'markup_percent': 100.0,
        'round_to_five': False,
        'include_customization': False,
        'customization_setup_fee': 0.0,
        'customization_per_unit': 0.0,
        'include_tariff': False,
        # Calculated fields populated by pricing engine
    }
```

---

## Risks & Mitigation

**Risk 1:** Users might forget to edit default quantity (1 unit)
- **Mitigation:** Make quantity field visually prominent, use warning color for qty=1

**Risk 2:** Too much vertical space if many products
- **Mitigation:** Keep cards compact with 2-column layouts, consider max-height with scroll

**Risk 3:** Users might not realize they can edit after adding
- **Mitigation:** Use instructional text "Edit settings for each product below"

**Risk 4:** Import from proposals might confuse users (why doesn't customization carry over?)
- **Mitigation:** Add caption explaining what carries over vs what resets

---

## Success Metrics

- Reduced user confusion in Tab 2
- Faster time to complete an order
- Fewer "where do I configure X?" questions
- More intuitive workflow matches user mental model
