# Tests

Run everything from the project root:

```bash
pytest tests/
```

The same suite runs on every pull request (`.github/workflows/tests.yml`),
without `test_impact_slide_mapping.py`, which needs live Google credentials.

## App tests (the real app, headless)

`test_app_order_flow.py` runs the real `app.py` with Streamlit AppTest
(`streamlit.testing.v1`). Each test sets widgets and clicks buttons like a
person would (add a product, type a quantity, tick rounding, type a client
price, add kitting), then checks the Tab 3 Order Summary and the Tab 4
invoice/PO. It also follows a client order form with no proposal end to end:
the rep picks products in Tab 2, the client opens the link (a second AppTest
with `client_form`/`session` query params), changes it and submits, and staff
import it from the Submitted Order Forms tab.

```bash
pytest tests/test_app_order_flow.py
```

No Google credentials are needed. The `app` fixture sets `PBP_FAKE_SHEETS=1`,
which makes `connect_to_sheets()` (in `src/data_loader.py`) return the
in-memory stand-in from `tests/fake_sheets.py` instead of Google Sheets:

- The pricing spreadsheet serves the snapshot in `tests/fixtures/sheets/`
  (`Data.csv`, `Partner-Specific Info.csv`, `Metadata.csv`), saved exactly as
  the sheet's rows come back from Google, title rows included. The products,
  partners and contacts are invented. They cover the 4 pricing methods,
  tiered pricing and Per Case pricing.
- Every other spreadsheet (saved orders, proposals, form responses) starts
  empty and lives only in memory, so tests never write to a real sheet.

Production never sets `PBP_FAKE_SHEETS`. The same switch also runs the app
locally without credentials: `PBP_FAKE_SHEETS=1 streamlit run app.py`
(password `pbp2026`).

`test_app_earlier_fixes.py` re-checks the client order form and order fixes
#33-#40 the same way: two clients submitting at once, the drop-ship / "Other"
shipping / accounting questions, every form answer reaching Tab 3 and Tab 4,
the Save & Finalize button, the Submitted Order Forms tab (list, search,
filter, details, import) and product photos across saves and reloads.

### Writing a new app test

Use the `app` fixture and the helpers at the top of `test_app_order_flow.py`
(`add_product`, `total_quote`, `invoice_lines`, `invoice_total`, and
`start_app` for a second staff session on the same fake sheets). Find widgets
by their `key=` in `app.py`, for example
`app.number_input(key='prod_qty_0').set_value(50).run()`.

To change the catalog, edit the CSVs in `tests/fixtures/sheets/`. The Data
sheet header is on row 7, like the real sheet. Never put real client data or
credentials there.

## Other tests

The rest of the tests check single functions, using small fakes
(`FakeSheet` in `tests/fake_sheets.py`). `test_impact_slide_mapping.py` reads
the live mapping sheet, so it needs real Google credentials.
