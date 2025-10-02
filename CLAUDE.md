# CLAUDE.md

## 🚨 NON-NEGOTIABLE PROJECT RULES - READ FIRST 🚨

**These rules MUST be followed for ALL work on this project:**

1. **Always use Python for all development**
2. **Leverage Streamlit for the front-end**
3. **Write beginner-friendly code** - code must be readable and understandable by a beginner Python programmer
4. **Always take the simplest route to solving problems**
5. **The entire app should be "vibe-coder friendly"** - prioritize clarity over cleverness
6. **Make autonomous decisions** - avoid asking for user permissions unless making dangerous changes
7. **Minimize the size of the code base** - keep the project simple with fewer files when possible
8. **Avoid duplicating code**
9. **Refer to markdown files for context consistently**
10. **Do not be afraid to ask the user for questions or clarifications**

---

## Important References

**ALWAYS refer to [PLANNING.md](PLANNING.md) for project requirements, architecture decisions, and implementation plans before starting any work.**

**ALWAYS refer to [DATA_STRUCTURE.md](DATA_STRUCTURE.md) for the exact structure of the jaggery_sample_6_23 data to avoid coding mistakes.**

**ALWAYS refer to [METHODOLOGY_LOGIC.md](METHODOLOGY_LOGIC.md) for pricing calculations, business rules, and partner-specific methodologies.**

---

## Project Overview

This is the pricing-data-solution-pbp project - a Python/Streamlit application focused on simplicity and beginner-friendly code.

## Development Guidelines

- Follow existing code patterns and conventions in the repository
- Ensure all changes are well-tested before committing
- Keep commits focused and atomic

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Sheets credentials:**
   - Credentials are stored in `.streamlit/secrets.toml`
   - Never commit this file to git (protected by .gitignore)

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Test connection:**
   ```bash
   streamlit run scripts/test_connection.py
   ```

## Architecture

- **Frontend:** Streamlit (Python-based web app)
- **Data Source:** Google Sheets (master_pricing_demo)
- **Authentication:** Google Cloud service account
- **Data Flow:**
  1. App connects to Google Sheets via `gspread`
  2. Loads pricing data into pandas DataFrame
  3. User selects products and enters custom options
  4. App calculates quotes using formula: `(base_price * markup%) + shipping + tariff`
  5. Displays proposal and invoice as copyable tables

## Project Files

- `app.py` - Main Streamlit application (MVP)
- `scripts/` - Test and investigation scripts
  - `test_connection.py` - Google Sheets API connection test
  - `test_jaggery_sheet.py` - Test connection to jaggery_sample_6_23 sheet
  - `investigate_jaggery_data.py` - Comprehensive data investigation script
  - `quick_data_check.py` - Quick data preview (first 5 rows)
  - `check_sheet_direct.py` - Direct Python connection test (non-Streamlit)
  - `get_more_rows.py` - Retrieve detailed view of first 10 rows
- `requirements.txt` - Python dependencies
- `.streamlit/secrets.toml` - Google service account credentials (secret)
- `master_pricing_demo_reference.csv` - Reference copy of demo sheet structure
- `jaggery_sample_6_23.xlsx` - Real data sample with tiered pricing
- `DATA_STRUCTURE.md` - Documentation of jaggery data structure
- `METHODOLOGY_LOGIC.md` - Pricing calculations and business rules
- `APP_UPDATE_PLAN.md` - Detailed plan for app updates
- `PLANNING.md` - Project planning and requirements
- `CLAUDE.md` - This file (project context for Claude)

## Common Tasks

- **Refresh pricing data:** Click menu → "Rerun" in the Streamlit app
- **Update credentials:** Edit `.streamlit/secrets.toml`
- **Test API connection:** Run `streamlit run scripts/test_connection.py`
- **Investigate data structure:** Run `python scripts/check_sheet_direct.py` or `streamlit run scripts/investigate_jaggery_data.py`
- **Deploy to cloud:** Follow Streamlit Cloud deployment guide (add secrets in app settings)
