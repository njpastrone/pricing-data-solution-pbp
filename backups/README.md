# Backups

Reference backup of app.py before major refactoring.

**Last Updated:** 2024-11-20 (cleanup)
**Files:** 1

---

## Overview

This directory contains a single backup file from October 27, 2024, preserving the complete working application before modular code extraction.

**Purpose:** Emergency rollback capability for major architectural changes

**Not for:** Normal version control (use git for that)

---

## Files

### app_before_modular_refactor_20251027.py (96.7KB)
**Date:** October 27, 2024
**Purpose:** Pre-modular refactoring backup

**What it contains:**
- Complete working app.py (monolithic structure)
- All functions inline (~2,800 lines)
- Working state before extracting to src/ modules

**When to use:**
- **Reference:** Compare old vs new implementation
- **Study:** Understand how features used to work
- **Emergency:** Rollback if modular structure breaks (LAST RESORT)

**Don't use for:**
- Normal development (use git)
- Copying code (old patterns, missing features)
- Production deployment (outdated)

---

## Usage

### Reference Comparison
```bash
# See what changed
diff app.py backups/app_before_modular_refactor_20251027.py

# Visual diff
code --diff app.py backups/app_before_modular_refactor_20251027.py
```

### Find Old Implementation
```bash
# Search for function
grep -n "function_name" backups/app_before_modular_refactor_20251027.py

# View specific lines
sed -n '100,150p' backups/app_before_modular_refactor_20251027.py
```

### Emergency Rollback (NOT RECOMMENDED)
```bash
# 1. Backup current first
cp app.py app_broken_$(date +%Y%m%d).py

# 2. Restore backup
cp backups/app_before_modular_refactor_20251027.py app.py

# 3. Restart
streamlit run app.py
```

**Warning:** Loses all improvements since October 27, 2024. Only use if absolutely necessary.

---

## Important Notes

### Modular Code is Better
The backup represents the OLD monolithic structure:
- ❌ Harder to maintain
- ❌ Harder to test
- ❌ Harder to understand
- ❌ ~2,800 lines in one file

Current modular structure is superior:
- ✅ Single responsibility per module
- ✅ Isolated testing
- ✅ Clear boundaries
- ✅ Maintainable codebase

### Backup Policy
**v6.18 cleanup removed 3 older backups:**
- Only kept most recent major refactoring backup
- Git history preserves everything if needed
- Reduces clutter

### Date Typo
Filename says "20251027" (2025) but means October 27, **2024**.

---

## Related Documentation

- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) - AI context
- **Code Simplification:** [../docs/CODE_SIMPLIFICATION_AGENT.md](../docs/CODE_SIMPLIFICATION_AGENT.md)
- **Changelog:** [../CHANGELOG.md](../CHANGELOG.md)
- **Source Code:** [../src/README.md](../src/README.md)
