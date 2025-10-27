# Archive Directory

This directory contains archived files from previous development phases. Files are kept for historical reference and are not used in the current system.

## Structure

### `archive/docs/`
Archived documentation files that are no longer current:

#### `old_jaggery_demo/`
- Documentation for the deprecated jaggery_demo data source (pre-October 2025)
- **DATA_STRUCTURE.md** - Old tier structure with 7 hardcoded tiers

#### `completed_plans/`
- Implementation plans that have been completed and are now part of the current system
- Kept for historical reference to understand how features were developed

### `archive/scripts/`
Old investigation and testing scripts from earlier development phases:

- **investigate_jaggery_demo.py** - Streamlit tool to explore old jaggery_demo structure
- **check_jaggery_demo.py** - Python script to investigate jaggery_demo data
- **test_new_structure.py** - Testing script (purpose unclear, may be redundant)
- **test_data_loading.py** - Testing script (may be redundant with test_connection.py)

**Note:** Current investigation tool is `scripts/investigate_data.py` (master_pricing_template_10_14)

### `archive/backups/`
Old backup files from before the October 2025 restructuring:

#### `pre_october_2025/`
- **app_mvp_backup.py** - Original MVP version (September 2025)
- **app_before_restructure_20251014_174904.py** - Backup before October 14 restructure

**Note:** Current backup is kept in `backups/app_before_modular_refactor_20251027.py`

## Timeline

- **September 2025:** MVP created with single product quoting
- **Early October 2025:** Multi-product ordering added
- **October 14, 2025:** Migrated from jaggery_demo to master_pricing_template_10_14
- **October 22, 2025:** Restructured Invoice/PO to match bookkeeper template
- **October 27, 2025:** Completed modular code reorganization (this archive created)

## What Changed

### Data Source Migration (October 2025)
**Old System (jaggery_demo):**
- Single sheet with hardcoded 7 pricing tiers
- Columns: "PBP Cost w/o shipping (1-25)", "PBP Cost w/o shipping (26-50)", etc.
- Art Setup Fee and Labels for customization

**Current System (master_pricing_template_10_14):**
- 3-sheet workbook (Template, Metadata, Partner-Specific Info)
- Flexible tier system: products can have 1-6 tiers OR flat pricing
- Dynamic tier parsing from "Pricing Tiers Info" column
- Columns: "PBP Cost: Tier 1", "PBP Cost: Tier 2", OR "PBP Cost (No Tiers)"
- Customization Setup Fee and Per-Unit costs

### Code Organization (October 27, 2025)
**Before:** 2,339-line monolithic app.py

**After:** Modular structure
- `app.py` (~1,500 lines) - UI only
- `src/helpers.py` - Utility functions
- `src/data_loader.py` - Google Sheets integration
- `src/pricing_engine.py` - Pricing calculations

---

**Last Updated:** 2025-10-27
**Status:** Archive - For reference only
