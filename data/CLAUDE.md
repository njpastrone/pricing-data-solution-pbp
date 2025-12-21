# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /data
Purpose: Local data storage for manual matches and cached files

---

## Quick Context
- **Primary responsibility**: Local JSON storage for manual product-to-slide matches
- **Key dependencies**: src/match_manager.py
- **Used by**: PowerPoint slide matching system
- **Technology stack**: JSON files

---

## Detailed Overview

The `data/` directory serves as local file system storage for application data that doesn't belong in Google Sheets. Currently, it contains only one file: manual product-to-slide match overrides.

**Purpose:**
1. **Manual match storage** - User-defined product-to-slide mappings
2. **Local caching** - Fast access to frequently used data
3. **Offline capability** - Works without Google Sheets connection

**Design decision:** Confirmed matches are stored in Google Sheets (cloud-persistent), while manual overrides are stored locally (user-specific).

---

## Important Files

### manual_matches.json (301 bytes)
**Purpose:** Store manual product-to-slide match overrides

**Structure:**
```json
{
  "demo": {
    "product_name": "slide_title",
    "another_product": "another_slide"
  },
  "real": {
    "product_name": "slide_title"
  }
}
```

**Dataset separation:**
- `"demo"` - Manual matches for demo dataset
- `"real"` - Manual matches for real dataset
- Prevents cross-contamination of matches

**Usage:**
```python
from src.match_manager import load_manual_matches, save_manual_matches

# Load matches
matches = load_manual_matches()
demo_matches = matches.get('demo', {})

# Save new match
matches['demo']['New Product'] = 'Slide Title'
save_manual_matches(matches)
```

**When modified:**
- User manually overrides fuzzy match in UI
- Admin defines guaranteed exact matches
- Correcting recurring matching errors

**Priority:**
1. **Confirmed matches** (Google Sheets) - User-confirmed fuzzy matches
2. **Manual matches** (this file) - User/admin overrides
3. **Fuzzy matches** (calculated) - Auto-matching algorithm

**Notes:**
- Not synced across users (local only)
- Survives app restarts
- Cleared when dataset switches
- Version controlled in git (shared defaults)

---

## Code Patterns & Conventions

### Loading Manual Matches
```python
from src.match_manager import load_manual_matches

matches = load_manual_matches()
# Returns: {'demo': {...}, 'real': {...}}

# Get dataset-specific matches
dataset = st.session_state.selected_dataset
dataset_matches = matches.get(dataset, {})
```

### Saving Manual Matches
```python
from src.match_manager import save_manual_matches

# Load existing
matches = load_manual_matches()

# Modify
matches['demo']['New Product'] = 'New Slide Title'

# Save
save_manual_matches(matches)
```

### Product Name Normalization
```python
from src.match_manager import normalize_for_storage

# Normalize for consistent storage
normalized_name = normalize_for_storage("Product Name (Variant)")
# Returns: "product name variant" (lowercase, no special chars)

# Use normalized name as key
matches['demo'][normalized_name] = 'Slide Title'
```

---

## Common Tasks

### To add manual match:
1. **Via UI (recommended):**
   - Tab 1 → Section 4 (PowerPoint)
   - Click "Change" on product match
   - Select correct slide from alternatives
   - Match is auto-saved

2. **Via file edit (advanced):**
   ```bash
   # Edit file
   nano data/manual_matches.json

   # Add match
   {
     "demo": {
       "product_name": "slide_title"
     }
   }

   # Test in app
   streamlit run app.py
   ```

### To clear manual matches:
```bash
# Backup first
cp data/manual_matches.json data/manual_matches_backup.json

# Clear
echo '{"demo": {}, "real": {}}' > data/manual_matches.json

# Or delete file (will be recreated)
rm data/manual_matches.json
```

### To migrate matches between datasets:
```python
from src.match_manager import load_manual_matches, save_manual_matches

matches = load_manual_matches()

# Copy demo matches to real
matches['real'] = matches['demo'].copy()

save_manual_matches(matches)
```

---

## Important Notes

### Local vs Cloud Storage
- **Manual matches** (this file) - Local, user-specific, fast
- **Confirmed matches** (Google Sheets) - Cloud, shared, persistent

**Why separate?**
- Manual = Admin overrides, testing, development
- Confirmed = User-validated matches, production use

### Match Priority
When matching products to slides:
1. **Confirmed matches** (Google Sheets) - Highest priority
2. **Manual matches** (this file) - Second priority
3. **Fuzzy matches** (calculated) - Fallback

### Dataset Separation
Matches are dataset-specific to prevent errors:
- Demo product names ≠ Real product names
- Demo slide titles ≠ Real slide titles (usually same, but can differ)
- Prevents incorrect matches when switching datasets

### File Permissions
- Read/write by application
- Check into git (shared defaults)
- Users can modify locally
- Not synced via cloud (intentional)

---

## Performance Considerations

### File Size
- Minimal (~300 bytes currently)
- JSON is fast to parse
- No performance impact

### Caching
Not currently cached, but could be:
```python
@st.cache_data
def load_manual_matches():
    # ... load from file
    return matches
```

**Consideration:** Would need cache invalidation when file is modified.

---

## Gotchas & Notes

### JSON Formatting
- Pretty-printed for readability (not minified)
- Use 2-space indentation
- Ensure valid JSON (quotes, commas, braces)

### Product Name Normalization
Product names are normalized before storage:
- Lowercase
- Special characters removed
- Spaces preserved
- See `src/match_manager.py::normalize_for_storage()`

**Why?** Consistent matching regardless of capitalization or punctuation.

### File Creation
If file doesn't exist:
- Application creates empty structure: `{"demo": {}, "real": {}}`
- No error thrown
- Safe to delete file (auto-recreated)

### Git Conflicts
Multiple users editing same file:
- Can cause merge conflicts
- Resolution: Keep both matches (merge manually)
- Or: Use Google Sheets confirmed matches instead

---

## Future Enhancements

### Sync to Google Sheets
Convert manual matches to cloud storage:
- Sync across users
- Centralized management
- Backup capability

### UI Management
Add admin UI for manual matches:
- View all manual matches
- Edit/delete matches
- Import/export matches
- Migrate to confirmed matches

### Validation
Add match validation:
- Verify slide exists in template
- Check product exists in dataset
- Warn on duplicate matches

### Audit Trail
Track when matches were added:
```json
{
  "demo": {
    "product_name": {
      "slide_title": "Slide Title",
      "added_by": "user@example.com",
      "added_at": "2024-12-20T10:30:00",
      "reason": "Fuzzy match was incorrect"
    }
  }
}
```

---

## Related Files

### In src/
- **match_manager.py** - Read/write manual matches (this file)
- **match_memory.py** - Read/write confirmed matches (Google Sheets)
- **slide_matcher.py** - Use matches during PowerPoint generation

### In scripts/
- **test_match_memory.py** - Test confirmed match system
- (No test for manual matches currently - opportunity for improvement)

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **Match Manager:** [../src/match_manager.py](../src/match_manager.py)
- **Match Memory:** [../src/match_memory.py](../src/match_memory.py)
- **Slide Matcher:** [../src/slide_matcher.py](../src/slide_matcher.py)
- **PowerPoint Phase 1:** [../docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md](../docs/powerpoint/PHASE_1_COMPLETION_SUMMARY.md)

---

## Summary

The `data/` directory contains local JSON storage for manual product-to-slide match overrides. This provides fast, local storage that complements cloud-based confirmed matches.

**Key points:**
- Local storage (not synced)
- Dataset-specific matches
- Second priority (after confirmed matches)
- Admin/testing tool primarily
