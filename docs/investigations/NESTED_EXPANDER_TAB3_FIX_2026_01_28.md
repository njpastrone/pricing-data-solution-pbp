# Fixed: Nested Expander in Tab 3 Proposal Import

**Date:** 2026-01-28
**Issue:** `StreamlitAPIException: Expanders may not be nested inside other expanders` at line 5465
**Location:** Tab 3, inside "Import Products from Proposal" expander
**Status:** ✅ FIXED

---

## Problem

When we moved the proposal import section into a collapsed expander (line 5413), it created a nested expander situation:

```python
with st.expander("**Import Products from Proposal (Tab 1)**", expanded=False):  # Outer
    # ... content ...
    with st.expander("Select Individual Products from Proposal", expanded=False):  # NESTED! ❌
        # ... individual selection UI ...
```

This caused the app to crash when users tried to use the proposal import feature in Tab 3.

---

## Solution

Replaced the nested expander with a checkbox toggle:

**Before:**
```python
with st.expander("Select Individual Products from Proposal", expanded=False):
    st.markdown("Select specific products...")
    # ... product selection checkboxes ...
```

**After:**
```python
st.markdown("---")
st.markdown("**Select Individual Products**")
show_individual = st.checkbox("Show individual product selection", key="show_individual_proposal_select")

if show_individual:
    st.markdown("Select specific products...")
    # ... product selection checkboxes ...
```

---

## User Experience

**Before:**
- Click to expand outer "Import Products from Proposal" expander
- See "Import All" button
- See nested expander "Select Individual Products from Proposal"
- Click to expand nested expander → **CRASH**

**After:**
- Click to expand "Import Products from Proposal" expander
- See "Import All" button
- See checkbox "Show individual product selection"
- Check the box to reveal individual selection UI ✅

---

## Files Modified

1. **app.py**
   - Line 5465-5467: Replaced nested expander with checkbox toggle
   - Lines 5469-5530: Properly indented content inside if block

---

## Technical Changes

### Structure Before (Nested - BROKEN):
```
with st.expander("Import Products from Proposal"):      # Level 1
    [Import All button]
    with st.expander("Select Individual"):              # Level 2 - NESTED! ❌
        [Individual selection UI]
```

### Structure After (Checkbox - FIXED):
```
with st.expander("Import Products from Proposal"):      # Level 1
    [Import All button]
    if st.checkbox("Show individual selection"):        # Checkbox toggle ✅
        [Individual selection UI]
```

---

## Testing Checklist

- [x] No syntax errors
- [ ] Tab 3: Load page with proposal products
- [ ] Expand "Import Products from Proposal" expander
- [ ] Verify "Import All" button visible
- [ ] Verify checkbox "Show individual product selection" visible
- [ ] Check the checkbox
- [ ] Verify individual product selection UI appears
- [ ] Select some products and add to order
- [ ] Verify functionality works correctly

---

## Related Fixes

This is the third nested expander fix in this session:

1. **Tab 2 HTML Form Preview** (line 4348) - Fixed earlier
2. **Tab 3 HTML Upload** (line 5141) - Fixed earlier
3. **Tab 3 Proposal Individual Selection** (line 5465) - Fixed now ✅

All nested expanders have now been eliminated from the app.

---

## Root Cause

When we reorganized Tab 3 to hide secondary features in expanders (proposal import, HTML form import), we accidentally created nested expander situations. Streamlit doesn't support nested expanders, so any nested expanders must be replaced with alternative UI patterns like:

- Checkbox toggles
- Radio buttons
- Markdown headers with dividers
- Tabs (st.tabs)

---

**Status:** ✅ COMPLETE - No syntax errors, ready for testing
**Date:** 2026-01-28
**Implemented by:** Claude Code Agent
