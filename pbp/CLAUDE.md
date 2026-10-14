# pbp/ - shared core package

Phase 0 of the Streamlit migration moved the pricing engine, helpers, PowerPoint
generator, slide matcher, forms helper/config, manual-match storage (`pbp/core/`)
and photo storage (`pbp/sheets/`) here so the Streamlit app and the future
FastAPI app can both import them. Phase 0 only moved files and changed imports.

## Layout

- `pbp/settings.py`: environment-driven configuration (spreadsheet IDs with env overrides, `CLIENT_FORM_BASE_URL`, credentials lookup).
- `pbp/sheets/gateway.py`: the one Google Sheets connection, cached worksheet handles, quota back-off. Both apps use it.
- `pbp/sheets/client_form.py`: client order form logic (drafts, submit, backup-then-sync). Framework-free since phase 1.
- `pbp/sheets/order_manager.py`, `proposal_manager.py`: save/load/delete orders and proposals (moved from `src/` in phase 2, no Streamlit).
- `pbp/sheets/catalog.py`: the master_pricing catalog as DataFrames, cached five minutes per process (the web app's version of `src/data_loader.load_pricing_data`).
- `pbp/services/order.py`: order building and pricing arithmetic (Tab 3) on the saved-order dict; `pbp/services/invoice.py`: the invoice/PO tables, CSV and HTML (Tab 4).
- `pbp/web/`: the FastAPI + HTMX app. `app.py` serves the client order form (phase 1); `staff.py` the login, order editor, client form responses and accounting screens (phase 2). Working orders are held in process memory per staff session (`state.py`).

## Known remaining Streamlit coupling

- `pbp/core/slide_matcher.py` imports `get_confirmed_match` from
  `src.match_memory` (which imports streamlit) inside `find_match`. If that
  lookup fails it logs a warning and falls back to manual/automatic matching.
  Phase 3 moves confirmed-match storage into `pbp/sheets/`.
