# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /scripts
Purpose: Testing, investigation, and debugging utilities organized by function

---

## Quick Context
- **Primary responsibility**: Automated testing, data investigation, and system debugging
- **Key dependencies**: src/ modules, Google Sheets API, pandas, streamlit
- **Used by**: Developers for testing and debugging (not part of production app)
- **Technology stack**: Python test scripts, Streamlit test apps

---

## Detailed Overview

The `scripts/` directory contains all testing and debugging utilities, organized into three clear categories:

1. **core/** - Essential system tests (connection, data loading)
2. **features/** - Feature-specific validation tests (19 scripts)
3. **investigations/** - Debugging and data structure analysis (7 scripts)

This organization was implemented in **v7.3.0 (December 2024)** as part of the directory reorganization effort, making it easier to find the right test for any given task.

All scripts are standalone and can be run independently. They serve as:
- **Regression tests** - Verify features still work after code changes
- **Integration tests** - Test multi-component workflows
- **Investigation tools** - Inspect data structures and debug issues
- **Documentation** - Show how features are meant to work

---

## Important Files

### Core Tests (scripts/core/)

#### `test_connection.py` (2.3KB)
**Purpose:** Verify Google Sheets API connection and authentication

**What it tests:**
- Service account credentials validity
- API connection establishment
- Spreadsheet access permissions
- Data retrieval from all 3 sheets

**When to run:**
- First-time setup
- After credential changes
- When seeing connection errors in app
- Before deploying to new environment

**Usage:**
```bash
streamlit run scripts/core/test_connection.py
```

**Success criteria:**
- All 3 sheets load without errors
- Data displays in Streamlit interface
- No authentication failures

---

#### `investigate_data.py` (7.5KB)
**Purpose:** Inspect raw data structure from Google Sheets

**What it shows:**
- All column names and data types
- Sample rows for each sheet
- Header row detection validation
- Tier structure parsing
- Missing value identification

**When to run:**
- Debugging pricing calculations
- Understanding data format
- Investigating missing fields
- Before adding new features that rely on data

**Usage:**
```bash
streamlit run scripts/core/investigate_data.py
```

**Features:**
- Interactive DataFrame viewer
- Column-by-column analysis
- Tier range visualization
- Partner-specific data filtering

---

### Feature Tests (scripts/features/)

#### New Features (v7.0-7.3.0)

**`test_bidirectional_pricing.py` (5.0KB)**
- Tests markup % ↔ client price calculations
- Verifies bidirectional editing in Tab 1 and Tab 3
- Validates rounding and precision
- Added: v7.3.0

**`test_cancel_button.py` (5.1KB)**
- Tests PowerPoint match change cancellation
- Verifies state restoration
- Checks UI feedback
- Added: v7.0.0

**`test_search_bar.py` (5.8KB) + `test_search_bar_refined.py` (4.1KB)**
- Tests product search functionality in Tab 1
- Validates fuzzy matching
- Checks filter integration
- Added: v7.0.0

**`test_fifty_cent_rounding.py` (6.7KB)**
- Tests $0.50 rounding option across all tabs
- Validates accuracy ($47.32 → $47.50)
- Checks interaction with marketing rounding
- Added: v7.0.0

**`test_table_restructure.py` (7.1KB)**
- Tests PBP Cost vs Client Price column structure in Tab 3
- Validates calculation accuracy
- Checks CSV export consistency
- Added: v7.0.0

**`test_shipping_columns.py` (6.8KB)**
- Tests shipping column structure in spreadsheet
- Validates Tab 3 and Tab 4 display
- Checks invoice generation
- Added: v7.0.0

#### Order Management & Client Info (v7.1-7.2.0)

**`test_tab3_to_tab4_data_flow.py` (20.3KB) - COMPREHENSIVE**
- Tests complete Tab 3 → Tab 4 workflow
- Validates all data persistence
- Checks calculation accuracy
- Tests 12 client info fields
- Verifies invoice generation
- Added: v7.2.0

**`test_editable_descriptions.py` (9.3KB)**
- Tests "Item + Specs" column editing in Tab 4
- Validates persistence across saves
- Checks CSV/HTML export
- Added: v7.1.0

**`test_payment_terms.py` (8.4KB)**
- Tests Net 15 and custom payment terms
- Validates dropdown options
- Checks invoice display
- Added: v7.1.0

**`test_kitting.py` (3.3KB)**
- Tests PBP vs client kitting cost separation
- Validates calculation accuracy
- Checks invoice line items
- Added: v7.1.0

**`test_order_notes.py` (3.3KB)**
- Tests 5 always-visible note categories
- Validates persistence
- Checks invoice display
- Added: v7.1.0

**`test_sales_tax.py` (2.3KB)**
- Tests sales tax percentage input
- Validates calculation
- Checks order summary
- Added: v7.1.0

**`test_multiple_contacts.py` (3.6KB)**
- Tests dynamic add/remove POC functionality
- Validates partner POC auto-population
- Checks Tab 4 display (all contacts)
- Added: v7.2.0

#### Data Persistence (v6.6-6.9)

**`test_saved_proposals.py` (3.6KB)**
- Tests save/load/delete proposal functionality
- Validates Google Sheets storage
- Checks auto-versioning (v2, v3)
- Tests dataset mismatch warnings
- Added: v6.6

**`test_saved_orders.py` (4.4KB)**
- Tests save/load/delete order functionality
- Validates client info preservation
- Checks date serialization
- Tests dataset validation
- Added: v6.7

**`test_match_memory.py` (9.7KB)**
- Tests confirmed match storage system
- Validates cloud persistence
- Checks dataset-specific storage
- Tests priority: Confirmed > Manual > Fuzzy
- Added: v6.9

**`test_units_per_package.py` (3.3KB)**
- Tests "Units per Package" column support
- Validates package → per-unit normalization
- Checks MSRP markup calculation
- Tests edge cases (missing values, invalid input)
- Added: v6.8

---

### Investigation Scripts (scripts/investigations/)

#### Partner POC Pipeline (v7.2.0)

**`test_partner_poc_pipeline.py` (11.7KB) - PRIMARY**
- Comprehensive POC extraction testing
- Debug logging at each step
- Tests both demo and real datasets
- Validates header row detection

**`check_partner_info.py` (3.9KB)**
- Inspects Partner-Specific Info sheet structure
- Shows all columns and sample data
- Validates POC field presence

**`check_real_dataset_pocs.py` (2.5KB)**
- Specifically tests real dataset POC extraction
- Validates all 4 partners
- Shows POC details

**`check_sheet_structure.py` (2.2KB)**
- Displays raw sheet structure
- Shows header row location
- Validates column names

**`check_raw_sheet.py` (1.6KB)**
- Raw data viewer (no processing)
- Shows exactly what API returns
- Debug header row issues

#### Data Structure (Older)

**`check_columns.py` (886 bytes)**
- Quick column name checker
- Validates expected columns exist
- Shows data types

---

## Code Patterns & Conventions

### Test Script Structure
All feature tests follow this pattern:
```python
import streamlit as st
from src.module_name import function_name

st.title("Test: Feature Name")

# 1. Setup section
st.header("1. Test Configuration")
# ... test inputs

# 2. Execution section
st.header("2. Run Test")
if st.button("Run Test"):
    # ... execute test

# 3. Results section
st.header("3. Results")
# ... display results with pass/fail indicators

# 4. Expected vs Actual comparison
st.header("4. Validation")
# ... show expected behavior vs actual
```

### Investigation Script Structure
Investigation scripts are simpler:
```python
import streamlit as st
from src.data_loader import load_pricing_data

st.title("Investigation: Data Structure")

# Load data
df_template, df_metadata, df_partner_info = load_pricing_data()

# Show raw data
st.subheader("Raw Data")
st.dataframe(df_template)

# Show analysis
st.subheader("Analysis")
st.write(df_template.dtypes)
```

### Running Tests

**Streamlit-based tests:**
```bash
streamlit run scripts/features/test_name.py
```

**Python script tests:**
```bash
python scripts/features/test_name.py
```

**All tests from root:**
```bash
# Run specific test
streamlit run scripts/core/test_connection.py

# Or with full path
streamlit run /Users/.../pricing-data-solution-pbp/scripts/features/test_bidirectional_pricing.py
```

---

## Common Tasks

### To test a new feature:
1. Create test script in `scripts/features/`
2. Follow standard structure (Setup → Execute → Results → Validation)
3. Include both success and failure cases
4. Add to this documentation
5. Update `scripts/README.md`

### To investigate data issues:
1. Start with `scripts/core/investigate_data.py`
2. Look at raw data structure
3. Check column names and types
4. Verify expected values exist
5. Create specific investigation script if needed

### To debug pricing calculations:
1. Run `scripts/features/test_bidirectional_pricing.py`
2. Test with known quantities (1, 25, 50, 100, etc.)
3. Compare expected vs actual prices
4. Check tier boundary conditions
5. Verify rounding logic

### To verify data persistence:
1. Test proposals: `scripts/features/test_saved_proposals.py`
2. Test orders: `scripts/features/test_saved_orders.py`
3. Test matches: `scripts/features/test_match_memory.py`
4. Check Google Sheets directly for stored data

### To validate Tab 3 → Tab 4 workflow:
Run comprehensive test:
```bash
python scripts/features/test_tab3_to_tab4_data_flow.py
```
This tests:
- Product data flow
- Client info persistence
- Settings preservation
- Calculation accuracy
- Invoice generation

---

## Important Notes

### Dataset Testing
Always test with both datasets:
- **Demo dataset:** `master_pricing_template_10_14` (19 products)
- **Real dataset:** `master_pricing` (133 products)

Switch dataset in sidebar of test scripts when available.

### Test Independence
Each test script should:
- Be runnable standalone
- Not depend on other tests
- Clean up after itself
- Not modify production data

### Google Sheets Rate Limits
When running many tests:
- Google Sheets API: 100 requests/100 seconds
- Spread out test runs if hitting limits
- Use caching where possible
- Consider testing with local data for rapid iteration

### State Management
Test scripts sometimes need to clear state:
```python
# Clear session state between tests
for key in list(st.session_state.keys()):
    del st.session_state[key]
```

### Known Test Issues
None currently. All 28 test scripts passing as of v7.3.0.

---

## Recent Changes (v7.3.0)

### Directory Reorganization
- Moved all tests into organized subdirectories
- `scripts/core/` - Essential tests (2 scripts)
- `scripts/features/` - Feature tests (19 scripts)
- `scripts/investigations/` - Debug tools (7 scripts)

### New Tests Added
- `test_bidirectional_pricing.py` - Markup ↔ price editing
- Updated all tests to v7.3.0 compatibility

### Deprecated/Removed
Removed 13 obsolete test scripts in v6.18:
- Old jaggery_demo scripts
- Deprecated investigation tools
- Duplicate test files
- Pre-modular refactor tests

---

## Testing Coverage

### By Category
- **Core functionality:** 2 scripts (100% coverage)
- **Data persistence:** 3 scripts (proposals, orders, matches)
- **Pricing calculations:** 5 scripts (bidirectional, rounding, tables, etc.)
- **PowerPoint:** 2 scripts (matching, generation)
- **Order workflow:** 8 scripts (Tab 3→4, client info, settings)
- **Investigations:** 7 scripts (data structure, POCs, debugging)

### By Feature
- ✅ Google Sheets connection
- ✅ Data loading and caching
- ✅ Tiered pricing
- ✅ Flat-rate pricing
- ✅ Customization costs
- ✅ MSRP markup
- ✅ Units per package
- ✅ Bidirectional pricing (NEW v7.3.0)
- ✅ Marketing rounding
- ✅ $0.50 rounding
- ✅ Discounts (Non-profit, custom)
- ✅ Sales tax
- ✅ Kitting costs
- ✅ Tariffs
- ✅ Credit card fees
- ✅ Saved proposals
- ✅ Saved orders
- ✅ PowerPoint matching
- ✅ PowerPoint generation
- ✅ Match memory
- ✅ Tab 3 → Tab 4 data flow
- ✅ Payment terms
- ✅ Multiple contacts
- ✅ Editable descriptions
- ✅ Order notes
- ✅ Search bar
- ✅ Cancel button

### Gaps (Not Yet Tested)
- Customization Add-On feature (Week 2 sprint, in progress)
- Date format changes (MM/DD/YY)
- New/Existing client checkbox

---

## Performance Considerations

### Test Runtime
- **Quick tests** (<5 sec): Connection, simple calculations
- **Medium tests** (5-30 sec): Feature tests, data loading
- **Long tests** (30+ sec): Comprehensive workflows, PowerPoint generation

### Memory Usage
- Test scripts use same memory as main app (~500-800MB)
- PowerPoint tests download 43MB template
- Multiple Streamlit instances can run simultaneously (different ports)

### Parallel Testing
Can run multiple tests at once:
```bash
# Terminal 1
streamlit run scripts/features/test1.py  # Port 8501

# Terminal 2
streamlit run scripts/features/test2.py  # Port 8502

# Terminal 3
streamlit run scripts/features/test3.py  # Port 8503
```

---

## Gotchas & Notes

### Port Conflicts
If you see "Port 8501 is in use":
- Close other Streamlit instances
- Or specify different port: `streamlit run script.py --server.port 8502`
- Check for zombie processes: `lsof -i :8501`

### Cache Persistence
Streamlit caches persist between test runs:
- Can cause stale data issues
- Clear with "Rerun" or "Clear cache" in menu
- Or programmatically: `st.cache_data.clear()`

### Dataset Mismatch
Tests may fail if:
- App is using Real dataset
- Test expects Demo dataset structure
- Solution: Check `st.session_state.selected_dataset`

### Google Sheets Credentials
Tests require valid credentials:
- Local: `.streamlit/secrets.toml`
- Render: Environment variable `GOOGLE_CREDENTIALS_JSON`
- Tests will fail immediately if credentials invalid

### Float Precision
Price comparisons should use epsilon:
```python
# Bad
assert actual == expected

# Good
assert abs(actual - expected) < 0.01
```

---

## Future Enhancements

### Planned Tests (Week 2 Sprint)
- Customization Add-On feature test
- Date format validation (MM/DD/YY)
- New/Existing client checkbox test

### Automation Ideas
- Automated regression test suite
- CI/CD integration (GitHub Actions)
- Test result dashboard
- Performance benchmarking

### Coverage Improvements
- Edge case testing (boundary values)
- Error handling validation
- Security testing (input validation)
- Load testing (large datasets)

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **Documentation:** [../docs/README.md](../docs/README.md)
- **Source Code:** [../src/README.md](../src/README.md)
- **Active Development:** [../ACTIVE_DEVELOPMENT_TODO.md](../ACTIVE_DEVELOPMENT_TODO.md)
- **Testing Checklist:** [../docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md](../docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md)
