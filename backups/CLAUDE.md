# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /backups
Purpose: Reference backup of pre-modular app.py for rollback capability

---

## Quick Context
- **Primary responsibility**: Emergency rollback capability for major refactoring
- **Key dependencies**: None (backup file only)
- **Used by**: Developers for reference or emergency rollback
- **Technology stack**: Python (Streamlit)

---

## Detailed Overview

The `backups/` directory contains a single critical backup file from before the modular refactoring in October 2024. This backup serves as:

1. **Emergency rollback point** - If modular refactor causes issues
2. **Reference implementation** - Shows how code worked before extraction
3. **Historical documentation** - Preserves working state at specific milestone

**Important:** This is NOT for version control (use git for that). This is a named reference point for a major architectural change.

---

## Important Files

### app_before_modular_refactor_20251027.py (96.7KB)
**Purpose:** Complete working app.py before modular code extraction

**Date:** October 27, 2024 (note: filename has 2025 typo, should be 2024)

**Contents:**
- Entire application in single file
- All helper functions inline
- All pricing calculations inline
- All data loading inline
- All PowerPoint generation inline
- ~2,800 lines of Python code

**Why it exists:**
The modular refactoring (v6.18, November 2024) extracted code into separate modules:
- `src/data_loader.py`
- `src/helpers.py`
- `src/pricing_engine.py`
- `src/slide_matcher.py`
- `src/pptx_generator.py`
- And 5 more modules

This backup preserves the working pre-modular state in case:
- New structure introduces bugs
- Need to compare implementations
- Emergency rollback needed
- Reference for "how it used to work"

**Status:** Working code at time of backup, no longer maintained

**Usage:**
```bash
# Emergency rollback (not recommended)
cp backups/app_before_modular_refactor_20251027.py app.py

# Better: Reference comparison
diff app.py backups/app_before_modular_refactor_20251027.py

# Or just read to understand old implementation
cat backups/app_before_modular_refactor_20251027.py | less
```

---

## Code Patterns & Conventions

### Backup Naming Convention
```
{filename}_before_{change_description}_{YYYYMMDD}.{ext}

Examples:
- app_before_modular_refactor_20251027.py
- app_before_powerpoint_phase2_20241104.py (if we had one)
- helpers_before_cleanup_20241120.py (if we had one)
```

### When to Create Backups
Create named backups for:
- **Major refactoring** (like modular extraction)
- **Breaking changes** (API changes, data structure changes)
- **Risky rewrites** (entire feature reimplementation)

**Don't create backups for:**
- **Normal development** (use git)
- **Bug fixes** (use git)
- **Small features** (use git)

---

## Common Tasks

### To compare current implementation with backup:
```bash
# Full diff
diff app.py backups/app_before_modular_refactor_20251027.py

# Or use visual diff tool
code --diff app.py backups/app_before_modular_refactor_20251027.py
```

### To find how a function used to work:
```bash
# Search in backup
grep -n "function_name" backups/app_before_modular_refactor_20251027.py

# View context around line
sed -n '100,150p' backups/app_before_modular_refactor_20251027.py
```

### To emergency rollback (LAST RESORT):
```bash
# 1. Backup current state first
cp app.py app_broken_$(date +%Y%m%d).py

# 2. Restore backup
cp backups/app_before_modular_refactor_20251027.py app.py

# 3. Restart app
streamlit run app.py

# 4. Investigate what broke
```

**Note:** Emergency rollback loses all improvements since October 27, 2024. Only use if absolutely necessary.

---

## Important Notes

### Not a Substitute for Git
- **Git** - Version control for all changes
- **Backups** - Named reference points for major milestones

Always use git for normal development. Backups are only for major architectural changes.

### Storage vs Git
- Backups are checked into git
- This seems redundant, but serves different purposes:
  - **Git history** - Shows incremental changes
  - **Named backup** - Clear reference point for "before X change"

### File Size
- 96.7KB for single file
- Minimal storage impact
- Worth keeping for reference

### Cleanup Policy
Old backups were removed in v6.18 cleanup:
- Removed 3 of 4 backups
- Kept only most recent major refactoring backup
- Older backups available in git history if needed

---

## Recent Changes

### v6.18 (November 2024)
- Removed 3 older backups:
  - Pre-Phase 1 backups
  - Pre-Phase 2 backups
  - Other intermediate backups
- Kept only `app_before_modular_refactor_20251027.py`
- Reasoning: Git history preserves everything, one recent backup sufficient

---

## Gotchas & Notes

### Modular Code is Better
The backup represents the OLD way (monolithic):
- Harder to maintain
- Harder to test
- Harder to understand
- ~2,800 lines in one file

Current modular structure is superior:
- Easier to maintain (single responsibility)
- Easier to test (isolated functions)
- Easier to understand (clear boundaries)
- Faster to navigate (~360KB app.py + ~200KB in src/)

### Don't Use Backup Code
Backup is for reference only. Don't copy code from backup to current codebase:
- Old patterns (before improvements)
- Missing recent features
- May have bugs that were fixed
- Inconsistent with current architecture

### Date Typo
Filename says "20251027" (2025) but should be "20241027" (2024).
- Typo in backup creation
- Not worth renaming (would break references)
- Just remember: October 27, 2024

---

## Future Enhancements

### Automated Backup System
Could create pre-commit hook for major changes:
```bash
# Before major refactoring
git commit -m "BACKUP: Pre-refactoring state"
# Creates automatic backup with date/description
```

### Backup Rotation
Keep only N most recent major backups:
- Last 3 major refactorings
- Auto-delete older backups
- Reduces clutter

### Backup Metadata
Add README.txt in backups/:
```
app_before_modular_refactor_20251027.py
Date: October 27, 2024
Reason: Before extracting code to src/ modules
Status: Working, all tests passing
Version: 6.0
```

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **Code Simplification:** [../docs/CODE_SIMPLIFICATION_AGENT.md](../docs/CODE_SIMPLIFICATION_AGENT.md)
- **Changelog:** [../CHANGELOG.md](../CHANGELOG.md)
- **Source Code:** [../src/README.md](../src/README.md)

---

## Summary

This directory contains a single backup file from before the modular refactoring. It serves as:
- Emergency rollback capability (last resort only)
- Reference implementation for comparison
- Historical documentation of working pre-modular state

**Key Point:** Use git for normal version control. Use backups only for major architectural changes.
