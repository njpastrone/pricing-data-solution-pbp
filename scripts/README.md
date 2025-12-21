# Test Scripts & Investigation Tools

This directory contains automated tests and debugging utilities organized by function.

**Last Updated:** 2024-12-20
**Total Scripts:** 28 (2 core + 19 features + 7 investigations)

---

## Overview

The scripts directory is organized into three categories:

1. **core/** - Essential system tests (connection, data loading)
2. **features/** - Feature-specific validation tests
3. **investigations/** - Debugging and data structure analysis

All scripts are standalone and can be run independently for testing, debugging, or documentation purposes.

---

## Directory Structure

```
scripts/
├── core/                    # Essential tests (2 scripts)
│   ├── test_connection.py           # Google Sheets API connection
│   └── investigate_data.py          # Raw data structure inspection
│
├── features/                # Feature tests (19 scripts)
│   ├── test_bidirectional_pricing.py        # Markup ↔ price editing (v7.3.0)
│   ├── test_cancel_button.py               # PowerPoint match cancellation (v7.0.0)
│   ├── test_editable_descriptions.py       # Tab 4 description editing (v7.1.0)
│   ├── test_fifty_cent_rounding.py         # $0.50 rounding option (v7.0.0)
│   ├── test_kitting.py                     # PBP vs client kitting (v7.1.0)
│   ├── test_match_memory.py                # Confirmed match storage (v6.9)
│   ├── test_multiple_contacts.py           # Dynamic POC management (v7.2.0)
│   ├── test_order_notes.py                 # 5-category notes system (v7.1.0)
│   ├── test_payment_terms.py               # Net 15 + custom terms (v7.1.0)
│   ├── test_sales_tax.py                   # Sales tax percentage (v7.1.0)
│   ├── test_saved_orders.py                # Order save/load/delete (v6.7)
│   ├── test_saved_proposals.py             # Proposal save/load/delete (v6.6)
│   ├── test_search_bar.py                  # Product search (v7.0.0)
│   ├── test_search_bar_refined.py          # Search improvements
│   ├── test_shipping_columns.py            # Shipping column structure (v7.0.0)
│   ├── test_tab3_to_tab4_data_flow.py      # COMPREHENSIVE workflow test (v7.2.0)
│   ├── test_table_restructure.py           # PBP Cost vs Client Price (v7.0.0)
│   └── test_units_per_package.py           # Package normalization (v6.8)
│
└── investigations/          # Debug tools (7 scripts)
    ├── test_partner_poc_pipeline.py     # POC extraction testing (v7.2.0)
    ├── check_partner_info.py            # Partner sheet inspection
    ├── check_real_dataset_pocs.py       # Real dataset POC validation
    ├── check_sheet_structure.py         # Sheet structure viewer
    ├── check_raw_sheet.py               # Raw API data viewer
    └── check_columns.py                 # Column name checker
```

---

## Quick Start

### Running Tests

**Streamlit-based tests:**
```bash
# From repository root
streamlit run scripts/core/test_connection.py
streamlit run scripts/features/test_bidirectional_pricing.py
```

**Python script tests:**
```bash
python scripts/features/test_tab3_to_tab4_data_flow.py
```

**Multiple tests simultaneously:**
```bash
# Terminal 1
streamlit run scripts/features/test1.py  # Port 8501

# Terminal 2
streamlit run scripts/features/test2.py  # Port 8502
```

---

## Core Tests

### test_connection.py
**Purpose:** Verify Google Sheets API connection

**What it tests:**
- Service account credentials
- API connection establishment
- Spreadsheet access
- Data retrieval from all 3 sheets

**When to run:**
- First-time setup
- After credential changes
- Connection error debugging
- Pre-deployment validation

**Usage:**
```bash
streamlit run scripts/core/test_connection.py
```

---

### investigate_data.py
**Purpose:** Inspect raw data structure

**What it shows:**
- Column names and data types
- Sample rows
- Header row validation
- Tier structure
- Missing values

**When to run:**
- Debugging pricing issues
- Understanding data format
- Before adding features
- Investigating missing fields

**Usage:**
```bash
streamlit run scripts/core/investigate_data.py
```

---

## Feature Tests (By Category)

### Pricing Calculations

**test_bidirectional_pricing.py** (v7.3.0)
- Tests markup % ↔ client price calculations
- Validates Tab 1 and Tab 3 editing
- Checks rounding and precision

**test_fifty_cent_rounding.py** (v7.0.0)
- Tests $0.50 rounding across all tabs
- Validates accuracy ($47.32 → $47.50)
- Checks interaction with marketing rounding

**test_table_restructure.py** (v7.0.0)
- Tests PBP Cost vs Client Price columns
- Validates calculation accuracy
- Checks CSV export consistency

**test_units_per_package.py** (v6.8)
- Tests package normalization
- Validates MSRP markup calculation
- Checks edge cases

---

### Data Persistence

**test_saved_proposals.py** (v6.6)
- Tests save/load/delete proposals
- Validates Google Sheets storage
- Checks auto-versioning
- Tests dataset warnings

**test_saved_orders.py** (v6.7)
- Tests save/load/delete orders
- Validates client info preservation
- Checks date serialization
- Tests dataset validation

**test_match_memory.py** (v6.9)
- Tests confirmed match storage
- Validates cloud persistence
- Checks dataset-specific storage
- Tests match priority

---

### Order Workflow

**test_tab3_to_tab4_data_flow.py** (v7.2.0) - COMPREHENSIVE
- Tests complete Tab 3 → Tab 4 workflow
- Validates all data persistence
- Checks calculation accuracy
- Tests 12 client info fields
- Verifies invoice generation
- **20KB script - most thorough test**

**test_editable_descriptions.py** (v7.1.0)
- Tests "Item + Specs" editing
- Validates persistence
- Checks export formats

**test_payment_terms.py** (v7.1.0)
- Tests Net 15 and custom terms
- Validates dropdown options
- Checks invoice display

**test_kitting.py** (v7.1.0)
- Tests kitting cost separation
- Validates calculations
- Checks invoice line items

**test_order_notes.py** (v7.1.0)
- Tests 5-category notes
- Validates persistence
- Checks invoice display

**test_sales_tax.py** (v7.1.0)
- Tests tax percentage input
- Validates calculation
- Checks order summary

**test_multiple_contacts.py** (v7.2.0)
- Tests dynamic POC management
- Validates auto-population
- Checks Tab 4 display

---

### UI Features

**test_search_bar.py** + **test_search_bar_refined.py** (v7.0.0)
- Tests product search in Tab 1
- Validates fuzzy matching
- Checks filter integration

**test_cancel_button.py** (v7.0.0)
- Tests PowerPoint match cancellation
- Verifies state restoration
- Checks UI feedback

**test_shipping_columns.py** (v7.0.0)
- Tests shipping column structure
- Validates Tab 3/4 display
- Checks invoice generation

---

## Investigation Scripts

### Partner POC Investigation (v7.2.0)

**test_partner_poc_pipeline.py** - PRIMARY
- Comprehensive POC extraction testing
- Debug logging at each step
- Tests demo and real datasets
- Validates header detection

**check_partner_info.py**
- Inspects Partner-Specific Info sheet
- Shows columns and sample data
- Validates POC fields

**check_real_dataset_pocs.py**
- Tests real dataset POC extraction
- Validates all 4 partners
- Shows POC details

**check_sheet_structure.py**
- Displays raw sheet structure
- Shows header row location
- Validates column names

**check_raw_sheet.py**
- Raw data viewer (no processing)
- Shows exact API response
- Debug header issues

**check_columns.py**
- Quick column checker
- Validates expected columns
- Shows data types

---

## Testing Best Practices

### Test Isolation
Each test should:
- Run standalone
- Not depend on other tests
- Clean up after itself
- Not modify production data

### Dataset Testing
Always test with both:
- **Demo:** 19 products, 4 partners
- **Real:** 133 products, 4 partners

### State Management
Clear state between tests if needed:
```python
for key in list(st.session_state.keys()):
    del st.session_state[key]
```

### Float Comparisons
Use epsilon for price comparisons:
```python
# Good
assert abs(actual - expected) < 0.01

# Bad
assert actual == expected
```

---

## Common Issues & Solutions

### Port Already in Use
**Error:** "Port 8501 is in use"

**Solutions:**
```bash
# Close other Streamlit instances
# Or use different port
streamlit run script.py --server.port 8502

# Check for zombie processes
lsof -i :8501
```

### Stale Cache
**Problem:** Tests showing old data

**Solutions:**
- Click "Rerun" in Streamlit menu
- Click "Clear cache" in menu
- Programmatically: `st.cache_data.clear()`

### Google Sheets Rate Limits
**Error:** "Quota exceeded"

**Solutions:**
- Spread out test runs
- Wait 100 seconds between batches
- Use local data for rapid iteration

### Credential Errors
**Error:** "Authentication failed"

**Solutions:**
- Check `.streamlit/secrets.toml` exists
- Verify service account JSON is valid
- Check spreadsheet sharing permissions

---

## Testing Coverage

### By Feature (28 scripts)
- ✅ Core functionality (2)
- ✅ Data persistence (3)
- ✅ Pricing calculations (5)
- ✅ PowerPoint (2)
- ✅ Order workflow (8)
- ✅ UI features (3)
- ✅ Investigations (7)

### Not Yet Tested
- Customization Add-On (Week 2 sprint)
- Date format changes (MM/DD/YY)
- New/Existing client checkbox

---

## Performance Notes

### Test Runtime
- **Quick** (<5 sec): Connection, calculations
- **Medium** (5-30 sec): Feature tests, data loading
- **Long** (30+ sec): Workflows, PowerPoint

### Memory Usage
- Same as main app: ~500-800MB
- PowerPoint tests: +43MB template
- Multiple instances: Cumulative

### Parallel Testing
Can run 3-5 tests simultaneously on different ports (8501-8505).

---

## Recent Changes

### v7.3.0 (December 2024)
- Directory reorganization (core/features/investigations)
- Added `test_bidirectional_pricing.py`
- Updated all tests to v7.3.0 compatibility

### v7.2.0 (December 2024)
- Added `test_multiple_contacts.py`
- Added POC investigation scripts (6 scripts)
- Added `test_tab3_to_tab4_data_flow.py` (comprehensive)

### v7.1.0 (December 2024)
- Added `test_payment_terms.py`
- Added `test_editable_descriptions.py`
- Added `test_kitting.py`
- Added `test_order_notes.py`
- Added `test_sales_tax.py`

### v7.0.0 (December 2024)
- Added `test_search_bar.py` + refined version
- Added `test_cancel_button.py`
- Added `test_fifty_cent_rounding.py`
- Added `test_table_restructure.py`
- Added `test_shipping_columns.py`

### v6.18 (November 2024)
- Removed 13 obsolete test scripts
- Cleaned up duplicate/deprecated tests

---

## Future Enhancements

### Automation
- CI/CD integration (GitHub Actions)
- Automated regression suite
- Test result dashboard
- Performance benchmarking

### Coverage
- Edge case testing
- Error handling validation
- Security testing
- Load testing (large datasets)

---

## Links

- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) (AI-friendly context)
- **Main README:** [../README.md](../README.md)
- **Source Code:** [../src/README.md](../src/README.md)
- **Testing Checklist:** [../docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md](../docs/testing/TAB3_TAB4_TESTING_CHECKLIST.md)
