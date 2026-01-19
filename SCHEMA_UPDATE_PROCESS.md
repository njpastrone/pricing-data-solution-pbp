# Schema Update Process

## Purpose
This document provides a systematic process for updating the data model/schema in the pricing-data-solution-pbp project. Follow this process whenever columns are renamed, added, removed, or modified in the Google Sheets data source.

---

## Process Overview

### Phase 1: Context Gathering
1. **Review Core Documentation:**
   - Read [CLAUDE.md](CLAUDE.md) - Project rules and current status
   - Read [README.md](README.md) - Project overview and architecture
   - Read [CHANGELOG.md](CHANGELOG.md) - Recent schema changes and patterns
   - Read [schema_reference.md](schema_reference.md) - Current canonical schema
   - Read [docs/planning/RESTRUCTURE_CONTEXT.md](docs/planning/RESTRUCTURE_CONTEXT.md) - Data structure details

2. **Understand Current Schema:**
   - Identify all column names in use (old and new canonical names)
   - Review `get_column_value()` helper function in `src/helpers.py`
   - Check backward compatibility mappings
   - Note any deprecated column names still supported

### Phase 2: Schema Change Analysis
1. **Document the Change:**
   - What is being changed? (rename, add, remove, modify)
   - Old column name(s) → New column name(s)
   - Data type changes (if any)
   - Default values (if adding new column)
   - Backward compatibility requirements

2. **Impact Assessment:**
   - Which modules will be affected?
   - Are there any calculated fields that depend on this column?
   - Will this break existing saved proposals/orders?
   - Does this affect CSV exports or downloads?

### Phase 3: Code Search & Discovery
**Use systematic search to find all references:**

1. **Search for Direct Column References:**
   ```bash
   # Search for column name in all Python files
   grep -r "old_column_name" --include="*.py" .

   # Search in markdown documentation
   grep -r "old_column_name" --include="*.md" .
   ```

2. **Search for Related Logic:**
   - Search for functions that use this column
   - Search for calculations involving this field
   - Search for UI elements displaying this data
   - Search for CSV/export logic using this column

3. **Key Files to Check (in priority order):**
   - `app.py` - Main application (all tabs)
   - `src/data_loader.py` - Data loading from Google Sheets
   - `src/helpers.py` - Utility functions and column mappings
   - `src/pricing_engine.py` - Pricing calculations
   - `src/pptx_generator.py` - PowerPoint generation
   - `schema_reference.md` - Schema documentation
   - `README.md` - Documentation
   - `CLAUDE.md` - Project context

4. **Search Patterns to Use:**
   - Exact column name in quotes: `"Old Column Name"`
   - Variable names derived from column: `old_column_name`, `oldColumnName`
   - Dictionary access: `['Old Column Name']`, `.get('Old Column Name')`
   - Comments referencing the column

### Phase 4: Planning
**Create a comprehensive update plan:**

1. **List All Changes Required:**
   - File path: specific change needed
   - Line numbers (approximate)
   - Type of change (rename, add logic, update default, etc.)

2. **Prioritize Updates:**
   - **Critical (must update):**
     - Column name references in `get_column_value()` mappings
     - Direct column access in core logic
     - Schema documentation
   - **Important (should update):**
     - Comments and docstrings
     - UI labels and display text
     - CSV export headers
   - **Nice to have:**
     - Variable names for consistency
     - Debug messages and logging

3. **Backward Compatibility Strategy:**
   - Add old column name to `get_column_value()` fallbacks
   - Update priority order (new canonical name first)
   - Test with old spreadsheet format
   - Document migration path

4. **Testing Plan:**
   - Test data loading with new schema
   - Test backward compatibility with old schema
   - Test all affected calculations
   - Test UI displays
   - Test CSV exports
   - Test saved proposals/orders (if applicable)

### Phase 5: Implementation
**Make changes systematically:**

1. **Start with Core Helpers:**
   - Update `get_column_value()` in `src/helpers.py` first
   - Add new canonical name
   - Add old name to fallback list
   - Update docstrings

2. **Update Schema Documentation:**
   - Update `schema_reference.md` with new column details
   - Mark old column names as deprecated (if applicable)
   - Update examples

3. **Update Application Logic:**
   - Work through files in priority order
   - Update one file at a time
   - Test after each major change
   - Keep backward compatibility intact

4. **Update Documentation:**
   - Update CHANGELOG.md with schema changes
   - Update README.md if user-facing impact
   - Update CLAUDE.md if significant change
   - Update any other affected .md files

### Phase 6: Testing & Validation
1. **Unit Tests:**
   - Test `get_column_value()` with new and old names
   - Test pricing calculations
   - Test data loading

2. **Integration Tests:**
   - Load data with new schema
   - Load data with old schema (backward compatibility)
   - Test full workflow (Tab 1 → Tab 4)
   - Test CSV exports
   - Test PowerPoint generation (if column affects it)

3. **Edge Cases:**
   - Missing column in old spreadsheets
   - Empty/null values in new column
   - Data type mismatches

### Phase 7: Documentation & Commit
1. **Update CHANGELOG.md:**
   ```markdown
   ## [Version] - Date
   ### Schema Changes
   - **Column Renamed:** "Old Name" → "New Name"
     - Updated all references in app.py, helpers.py, pricing_engine.py
     - Maintained backward compatibility via get_column_value()
     - Updated schema_reference.md
   ```

2. **Commit Message Format:**
   ```
   SCHEMA: [Brief description of change]

   - Renamed column "Old Name" → "New Name"
   - Updated get_column_value() mappings
   - Maintained backward compatibility
   - Updated documentation

   Files changed:
   - src/helpers.py (column mapping)
   - app.py (display logic)
   - schema_reference.md (documentation)
   ```

---

## Common Schema Change Scenarios

### Scenario 1: Column Rename
**Example:** "MSRP" → "Vendor Published MSRP"

**Steps:**
1. Add new canonical name to `get_column_value()` priority list
2. Keep old name as fallback
3. Update schema_reference.md
4. Search and update all direct references (UI labels, comments)
5. Test with both old and new spreadsheet formats

### Scenario 2: New Column Addition
**Example:** Adding "PBP Standard Markup" column

**Steps:**
1. Add column to `get_column_value()` with default fallback value
2. Update schema_reference.md with column details
3. Add logic to use new column (e.g., in pricing calculations)
4. Handle missing column gracefully (use default)
5. Test with spreadsheets that don't have the column

### Scenario 3: Column Removal/Deprecation
**Example:** Removing unused "Legacy Field" column

**Steps:**
1. Search for all references to column
2. Remove direct usage in application logic
3. Keep in `get_column_value()` fallbacks (for old data)
4. Mark as deprecated in schema_reference.md
5. Add note to CHANGELOG.md

### Scenario 4: Data Type Change
**Example:** "Tariff Estimate" from percentage-only to dual format ($ and %)

**Steps:**
1. Update parsing logic in data_loader.py or helpers.py
2. Add type detection/conversion functions
3. Update calculations to handle both formats
4. Test with both old and new data formats
5. Update schema_reference.md with format details

---

## Key Functions to Update

### `get_column_value()` in src/helpers.py
**This is the central function for column name mapping.**

**Update pattern:**
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
    # Add new mapping here
    column_mappings = {
        'new_canonical_name': [
            'New Canonical Name',        # Priority 1
            'Old Name',                  # Priority 2
            'Legacy Name'                # Priority 3
        ],
        # ... other mappings
    }
```

### Column Reference Patterns to Find

**Search for these patterns when finding all references:**

1. **Direct dictionary access:**
   - `row['Column Name']`
   - `row.get('Column Name')`
   - `df['Column Name']`

2. **get_column_value() calls:**
   - `get_column_value(row, 'canonical_name')`
   - `helpers.get_column_value(row, 'canonical_name')`

3. **Column name strings:**
   - `"Column Name"` in any context
   - `'Column Name'` in any context

4. **Variable names:**
   - `column_name` (snake_case derived from column)
   - `columnName` (camelCase derived from column)

---

## Example: Complete Schema Update Walkthrough

### Change: Rename "Customization Setup Fee" → "Client Price: Customization Setup Fee"

#### Step 1: Context Review
- Read schema_reference.md - found old name listed
- Read CHANGELOG.md - saw similar rename pattern in v7.4.0
- Understand this is part of canonical naming standardization

#### Step 2: Impact Analysis
- Used in pricing calculations
- Displayed in UI tables (Tab 1, Tab 3, Tab 4)
- Exported in CSV files
- Used in invoice generation

#### Step 3: Code Search
```bash
# Find all references
grep -r "Customization Setup Fee" --include="*.py" .
grep -r "customization_setup_fee" --include="*.py" .
grep -r "Customization Setup Fee" --include="*.md" docs/
```

**Results found in:**
- app.py (lines 450, 890, 1200, 2100)
- src/pricing_engine.py (lines 120, 340)
- src/helpers.py (line 85)
- schema_reference.md (line 45)
- README.md (line 210)

#### Step 4: Create Plan
1. Update `get_column_value()` mapping in helpers.py
2. Update schema_reference.md documentation
3. Update app.py UI labels (4 locations)
4. Update pricing_engine.py calculations (2 locations)
5. Update README.md example
6. Test backward compatibility

#### Step 5: Implementation
```python
# 1. Update helpers.py - get_column_value()
'customization_setup_fee': [
    'Client Price: Customization Setup Fee',  # NEW canonical
    'Customization Setup Fee',                # OLD fallback
],

# 2. Update all get_column_value() calls to use new canonical name
setup_fee = get_column_value(row, 'customization_setup_fee', 0)

# 3. Update UI labels in app.py
st.number_input("Client Price: Customization Setup Fee", ...)

# 4. Update comments
# Extract customization setup fee (client price)
```

#### Step 6: Testing
- ✅ Loaded data with new column name
- ✅ Loaded data with old column name (backward compatible)
- ✅ Pricing calculations work correctly
- ✅ UI displays new label
- ✅ CSV export uses new header

#### Step 7: Documentation
```markdown
## [7.5.0] - 2026-01-19
### Schema Changes
- **Column Renamed:** "Customization Setup Fee" → "Client Price: Customization Setup Fee"
  - Updated get_column_value() mapping in src/helpers.py
  - Updated UI labels in app.py (4 locations)
  - Updated pricing_engine.py calculations (2 locations)
  - Maintained backward compatibility for old spreadsheets
  - Updated schema_reference.md and README.md
```

---

## Tools & Commands

### Useful grep commands:
```bash
# Search all Python files
grep -rn "search_term" --include="*.py" .

# Search all markdown files
grep -rn "search_term" --include="*.md" .

# Search with context (3 lines before/after)
grep -rn -C 3 "search_term" --include="*.py" .

# Case-insensitive search
grep -rni "search_term" --include="*.py" .

# Search for multiple patterns
grep -rn -e "pattern1" -e "pattern2" --include="*.py" .
```

### Files to always check:
```bash
# Core application files
app.py
src/data_loader.py
src/helpers.py
src/pricing_engine.py

# Documentation files
schema_reference.md
README.md
CLAUDE.md
CHANGELOG.md

# Related to data structure
docs/planning/RESTRUCTURE_CONTEXT.md
docs/planning/METHODOLOGY_LOGIC.md
```

---

## Checklist Template

Use this checklist for every schema update:

- [ ] **Phase 1: Context**
  - [ ] Read CLAUDE.md, README.md, CHANGELOG.md, schema_reference.md
  - [ ] Review current schema and backward compatibility approach

- [ ] **Phase 2: Analysis**
  - [ ] Document what's changing (old → new)
  - [ ] Identify affected modules
  - [ ] Check impact on saved data

- [ ] **Phase 3: Search**
  - [ ] Search for direct column name references (Python)
  - [ ] Search for related logic and functions
  - [ ] Search for documentation mentions
  - [ ] List all files with line numbers

- [ ] **Phase 4: Plan**
  - [ ] List all required changes by file
  - [ ] Prioritize critical vs nice-to-have
  - [ ] Define backward compatibility strategy
  - [ ] Create testing plan

- [ ] **Phase 5: Implement**
  - [ ] Update get_column_value() first
  - [ ] Update schema_reference.md
  - [ ] Update application logic
  - [ ] Update all documentation

- [ ] **Phase 6: Test**
  - [ ] Test with new schema
  - [ ] Test with old schema (backward compatibility)
  - [ ] Test full workflow (all tabs)
  - [ ] Test edge cases

- [ ] **Phase 7: Document**
  - [ ] Update CHANGELOG.md
  - [ ] Write clear commit message
  - [ ] Update any affected markdown files

---

## Notes

- **Always maintain backward compatibility** - old spreadsheets should still work
- **Update get_column_value() first** - this ensures all code using the helper works immediately
- **Test thoroughly** - schema changes can have wide-reaching effects
- **Document clearly** - future you (and AI agents) will thank you
- **Use semantic commit prefixes** - `SCHEMA:` for schema changes
- **Keep CHANGELOG.md updated** - track all schema evolution over time

---

## Questions to Ask Before Starting

1. **What exactly is changing?** (be specific: old name → new name)
2. **Why is it changing?** (standardization, new feature, bug fix)
3. **Will old spreadsheets still work?** (backward compatibility required?)
4. **What breaks if I don't update X?** (understand dependencies)
5. **How do I test this?** (what scenarios to validate)

---

## Getting Help

If you're unsure about a schema change:
1. Review similar changes in CHANGELOG.md (search for "Schema Changes")
2. Check v7.4.0 schema update as reference implementation
3. Look at get_column_value() implementation for patterns
4. Test with both old and new data formats before committing
