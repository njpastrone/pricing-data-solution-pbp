---
name: schema-update
description: Systematic 7-phase process for updating database schema (column renames, additions, removals). Ensures backward compatibility and complete documentation.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Schema Update Skill

## Purpose
Guides you through a systematic 7-phase process for updating the pricing data schema. Ensures backward compatibility, maintains documentation, and follows established patterns from SCHEMA_UPDATE_PROCESS.md.

## When to Use This Skill

Invoke `/schema-update` when you need to:
- Rename columns in Google Sheets schema
- Add new columns to the data model
- Remove or deprecate columns
- Change data types or formats
- Update the canonical schema definition

## Process Overview

This skill follows the documented 7-phase approach:
1. **Context Gathering** - Review documentation
2. **Schema Change Analysis** - Document what's changing
3. **Code Search & Discovery** - Find all references
4. **Planning** - Create implementation plan
5. **Implementation** - Make changes systematically
6. **Testing & Validation** - Test thoroughly
7. **Documentation & Commit** - Update docs and commit

## Instructions

### Phase 1: Context Gathering

Read project documentation to understand current state:

1. Read `SCHEMA_UPDATE_PROCESS.md` for complete process details
2. Read `CLAUDE.md` - Project rules and current status
3. Read `schema_reference.md` - Current canonical schema
4. Read `CHANGELOG.md` - Recent schema changes and patterns
5. Read `docs/planning/RESTRUCTURE_CONTEXT.md` - Data structure details

Ask the user to confirm the schema change they want to make.

### Phase 2: Schema Change Analysis

Document the specific change by asking:

1. **What is changing?** (e.g., "MSRP" → "Vendor Published MSRP")
2. **Type of change:** (rename, add, remove, modify)
3. **Data type changes:** (if any)
4. **Default values:** (if adding new column)
5. **Backward compatibility required?** (usually yes)

Create impact assessment:
- Which modules are affected?
- Are there calculated fields depending on this column?
- Will this break existing saved proposals/orders?
- Does it affect CSV exports or PowerPoint generation?

### Phase 3: Code Search & Discovery

Use Grep tool to systematically find all references:

**Search for direct column references:**
```
Pattern: old_column_name
Type: files_with_matches (then read each file)
```

**Key files to check (in priority order):**
- `app.py` - Main application (all 4 tabs)
- `src/data_loader.py` - Google Sheets data loading
- `src/helpers.py` - Utility functions and `get_column_value()` mapping
- `src/pricing_engine.py` - Pricing calculations
- `src/pptx_generator.py` - PowerPoint generation
- `schema_reference.md` - Schema documentation
- `README.md` - Project documentation
- `CLAUDE.md` - Project context

**Search patterns to try:**
- Exact column name in quotes: `"Old Column Name"`
- Variable names: `old_column_name`, `oldColumnName`
- Dictionary access: `['Old Column Name']`, `.get('Old Column Name')`
- Comments referencing the column

Create a list of all files that need updates.

### Phase 4: Planning

Create comprehensive update plan listing:

**For each file requiring changes:**
- File path
- Specific changes needed
- Type of change (rename, add logic, update default, etc.)

**Prioritize by impact:**
- **Critical:** Column mappings in `get_column_value()`, schema docs
- **Important:** Direct column access, UI labels, CSV headers
- **Nice to have:** Variable names, comments, debug messages

**Backward compatibility strategy:**
- Add old column name to `get_column_value()` fallbacks
- Update priority order (new canonical name first)
- Test with both old and new spreadsheet formats

**Testing plan:**
- Test data loading with new schema
- Test backward compatibility with old schema
- Test all affected calculations
- Test UI displays and CSV exports

Present the plan to the user for approval before proceeding.

### Phase 5: Implementation

Make changes systematically (AFTER user approval):

**Step 1: Update Core Helper First**

Read and update `src/helpers.py` - modify `get_column_value()` function:
- Add new canonical name at top of priority list
- Add old name to fallback list
- Update docstrings

Example structure:
```python
def get_column_value(row, canonical_name, default=None):
    """
    Get column value with backward compatibility.

    Priority order (top to bottom):
    1. New canonical name (2026)
    2. Old name (2025)
    3. Legacy name (2024)
    4. Default value
    """
    column_mappings = {
        'new_canonical_name': [
            'New Canonical Name',        # Priority 1
            'Old Name',                  # Priority 2 (backward compat)
        ],
        # ... other mappings
    }
```

**Step 2: Update Schema Documentation**

Update `schema_reference.md`:
- Add new column details
- Mark old column names as deprecated (if applicable)
- Update examples

**Step 3: Update Application Logic**

Work through files in priority order:
- Update one file at a time
- Use Edit tool for changes
- Test after each major change
- Keep backward compatibility intact

**Step 4: Update Project Documentation**

Update documentation files:
- `CHANGELOG.md` - Add schema change entry
- `README.md` - If user-facing impact
- `CLAUDE.md` - If significant change
- Any other affected .md files

### Phase 6: Testing & Validation

Guide user through testing:

**Manual Tests:**
- Test data loading with new schema
- Test backward compatibility with old schema
- Test full workflow (Tab 1 → Tab 4)
- Test CSV exports
- Test PowerPoint generation (if applicable)

**Edge Cases:**
- Missing column in old spreadsheets
- Empty/null values in new column
- Data type mismatches

Ask user to confirm tests pass before committing.

### Phase 7: Documentation & Commit

**Update CHANGELOG.md with clear entry:**
```markdown
## [Version] - Date
### Schema Changes
- **[Change Type]:** "Old Name" → "New Name"
  - Updated references in [files]
  - Maintained backward compatibility via get_column_value()
  - Updated schema_reference.md
```

**Prepare commit message:**
```
SCHEMA: [Brief description of change]

- [Specific change detail 1]
- [Specific change detail 2]
- Maintained backward compatibility
- Updated documentation

Files changed:
- src/helpers.py (column mapping)
- app.py (display logic)
- schema_reference.md (documentation)
```

Ask user if they want to commit now or review changes first.

## Key Principles

- **Always maintain backward compatibility** - Old spreadsheets should still work
- **Update `get_column_value()` first** - Ensures all code using the helper works immediately
- **Test thoroughly** - Schema changes have wide-reaching effects
- **Document clearly** - Update CHANGELOG.md and schema_reference.md
- **Use semantic commits** - `SCHEMA:` prefix for schema changes

## Checklist

After completing all phases, verify:

- [ ] Phase 1: Read all documentation
- [ ] Phase 2: Documented what's changing
- [ ] Phase 3: Found all affected code locations
- [ ] Phase 4: Created and approved implementation plan
- [ ] Phase 5: Implemented all changes
- [ ] Phase 6: Tested thoroughly (new + old schema + edge cases)
- [ ] Phase 7: Updated CHANGELOG.md and prepared commit

## Reference

For complete details, see:
- [SCHEMA_UPDATE_PROCESS.md](../../../SCHEMA_UPDATE_PROCESS.md) - Full process documentation
- [schema_reference.md](../../../schema_reference.md) - Current canonical schema
- [CHANGELOG.md](../../../CHANGELOG.md) - Recent schema change patterns

## Usage

Invoke this skill:
```
/schema-update
```

Or ask Claude:
```
I need to rename the 'MSRP' column to 'Vendor Published MSRP'
```

Claude will guide you through all 7 phases systematically.
