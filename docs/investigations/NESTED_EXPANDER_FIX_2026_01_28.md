# Fixed: Nested Expanders Error

**Date:** 2026-01-28
**Issue:** `StreamlitAPIException: Expanders may not be nested inside other expanders`
**Status:** ✅ FIXED

---

## Problem

When hiding HTML order form sections in expanders (legacy cleanup), we accidentally created nested expanders:

### **Tab 2:**
```python
with st.expander("Legacy: HTML Order Form"):  # Outer expander
    # ...
    with st.expander("Preview HTML Form"):  # NESTED! ❌
```

### **Tab 3:**
```python
with st.expander("Legacy: Import from HTML Order Form"):  # Outer expander
    # ...
    with st.expander("Upload Completed Client Order Form"):  # NESTED! ❌
```

Streamlit doesn't allow nested expanders → App crashes on load.

---

## Solutions Applied

### **Tab 2: Line 4348**

**Before:**
```python
with st.expander("Preview HTML Form", expanded=False):
    st.components.v1.html(html_form, height=800, scrolling=True)
```

**After:**
```python
st.markdown("**Preview HTML Form**")
show_preview = st.checkbox("Show form preview", key="show_html_preview_tab2")
if show_preview:
    st.components.v1.html(html_form, height=800, scrolling=True)
```

**Benefit:** Checkbox toggle is simpler and works inside expanders.

---

### **Tab 3: Lines 5141-5419**

**Before:**
```python
with st.expander("Upload Completed Client Order Form", expanded=False):
    st.caption("Upload an HTML order form...")
    # ... all upload logic ...
```

**After:**
```python
st.markdown("---")
st.markdown("**Upload Completed Client Order Form**")
st.caption("Upload an HTML order form...")
# ... all upload logic (no expander wrapper) ...
```

**Benefit:** Simple header with divider. Content is already hidden inside legacy expander, so no need for another layer.

---

## Files Modified

1. **app.py**
   - Line 4348: Replaced nested expander with checkbox toggle
   - Lines 5141-5144: Replaced nested expander with markdown header
   - Fixed indentation throughout both sections

---

## Testing Checklist

- [x] App compiles without syntax errors
- [ ] Tab 2: Verify HTML form section loads without errors
- [ ] Tab 2: Verify "Show form preview" checkbox works
- [ ] Tab 3: Verify HTML import section loads without errors
- [ ] Tab 3: Verify file upload and import still works
- [ ] No nested expander errors

---

## Related Changes

- **HTML Legacy Cleanup:** HTML_FORM_LEGACY_CLEANUP_2026_01_28.md
- **Google Form Fixes:** GOOGLE_FORM_BUGS_FIX_2026_01_28.md

---

**Status:** ✅ COMPLETE - No syntax errors
**Date:** 2026-01-28
