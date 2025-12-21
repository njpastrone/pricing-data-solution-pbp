# Data Storage

Local file system storage for manual product-to-slide matches.

**Last Updated:** 2024-12-20
**Files:** 1

---

## Overview

This directory stores local data files used by the application. Currently contains only manual product-to-slide match overrides.

---

## Files

### manual_matches.json (301 bytes)
**Purpose:** Store manual product-to-slide match overrides

**Structure:**
```json
{
  "demo": {
    "product_name": "slide_title"
  },
  "real": {
    "product_name": "slide_title"
  }
}
```

**Usage:**
- PowerPoint slide matching system
- Manual overrides for fuzzy matches
- Admin-defined exact matches

**Managed by:**
- `src/match_manager.py` - Read/write operations
- Tab 1 UI - User can set overrides

---

## Match Priority

When matching products to PowerPoint slides:
1. **Confirmed matches** (Google Sheets) - User-confirmed fuzzy matches
2. **Manual matches** (this file) - Admin overrides
3. **Fuzzy matches** (calculated) - Auto-matching algorithm

---

## Usage

### Load Matches
```python
from src.match_manager import load_manual_matches

matches = load_manual_matches()
demo_matches = matches.get('demo', {})
```

### Save Matches
```python
from src.match_manager import save_manual_matches

matches['demo']['Product Name'] = 'Slide Title'
save_manual_matches(matches)
```

---

## Important Notes

### Local vs Cloud
- **This file:** Local storage, user-specific
- **Google Sheets:** Cloud storage, shared across users

### Dataset Separation
- Matches are dataset-specific (demo vs real)
- Prevents cross-contamination

### File Maintenance
- Auto-created if missing
- Safe to delete (will be recreated)
- Version controlled in git

---

## Links

- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) - AI context
- **Match Manager:** [../src/match_manager.py](../src/match_manager.py)
- **Match Memory:** [../src/match_memory.py](../src/match_memory.py)
- **PowerPoint Docs:** [../docs/powerpoint/](../docs/powerpoint/)
