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
- `pbp/sheets/match_memory.py`: confirmed product-to-slide matches (moved from `src/` in phase 3, no Streamlit); `pbp/sheets/templates.py`: PowerPoint templates from Drive, downloaded once per process, plus the impact slide mapping.
- `pbp/services/order.py`: order building and pricing arithmetic (Tab 3) on the saved-order dict; `pbp/services/invoice.py`: the invoice/PO tables, CSV and HTML (Tab 4).
- `pbp/services/proposal.py`: catalog filtering, proposal lines and MOQ tables (Tab 1); `pbp/services/pptx_jobs.py`: slide matching, review state and the background PowerPoint generation job.
- `pbp/web/`: the FastAPI + HTMX app. `app.py` serves the client order form (phase 1); `staff.py` the login, order editor, client form responses and accounting screens (phase 2); `proposals.py` the proposal editor, PowerPoint review and client form link (phase 3). Working orders and proposals are held in process memory per staff session (`state.py`).

## Streamlit coupling

None left in `pbp/`. The `src/` modules that remain (`data_loader.py`, `template_loader.py`) serve only the Streamlit app and go with it in phase 5.
