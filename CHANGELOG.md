# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased] - 2026-10-09

### Added (2026-10-23, real-app checks of the earlier form and order fixes)
- **App Tests for Fixes #33-#40:** `tests/test_app_earlier_fixes.py` re-checks each fix from the 2026-10-16 feedback round in the real app (AppTest), clicking through like a person: two clients submitting get their own Form Responses rows and an import marks only that row's tracking columns (#34); the client form asks for no drop-ship file, needs words for "Other" shipping and an accounting email or platform (#35); every form answer reaches the Tab 3 order and Tab 3 and Tab 4 show and edit the same values and notes (#36); Tab 3 has one Save & Finalize Order button at the bottom (#38); the Submitted Order Forms tab lists (newest first, including orders still waiting to sync), searches, filters, shows details and imports (#39); a product photo attaches once and stays with the order through re-saves and reloads in a new browser (#33, #40). All six fixes work; no app code changed
- The Form Responses stand-in in these tests behaves like the live tab (a Sheets Table), where `append_row` kept landing on row 8, so going back to `append_row` fails the #34 test
- `start_app()` in `tests/test_app_order_flow.py` opens a second logged-in session on the same fake sheets (a staff member in a new browser)

### Added (2026-10-19, client order form without a proposal)
- **Start a Client Order Form With No Proposal:** Tab 2 "Generate Client Form Link" no longer requires a saved proposal. With no proposal loaded, the PBP rep first picks the products discussed with the client (for example on the kickoff call) from a searchable catalog list in Tab 2, with a quantity, customization notes and the price for each. Generating the link pre-fills the form with those products and the client information from Section 1, so the client opens it to confirm them and add the rest of their details (the rep can also open the link and press Save Progress to update the form before sending it). Each click of Generate creates a link with its own unguessable ID (`?client_form=catalog_<dataset>_<random>`) and records it in the `client_form_drafts` tab; the form page rejects any catalog link it has no record of with the usual "This form is no longer available" page. On the form the client can change those products or add more from the whole product catalog of the dataset in use, and each chosen item shows its price per unit and line total for the quantity entered (the same pricing as the Tab 1 catalog, before customization, shipping and taxes), next to the editable quantity and customization notes. A product whose price cannot be worked out shows "your PBP representative will confirm the price" instead of an error. Links from a saved proposal work as before (proposal products only, no prices). Saving, submitting, the background copy to Form Responses and the Submitted Order Forms import are unchanged
- New helpers in `src/client_form.py`: `catalog_form_id()`, `catalog_products()`, `load_catalog_for_client()`, `client_unit_price()`
- Tests: `tests/test_client_form.py` (fake sheets and pricing data: catalog list, unique link IDs, dataset from the link, unknown or guessed links rejected, errors hidden from the client, price matches catalog pricing)
- Updated 2026-10-22 after team feedback on the PR: the rep now chooses products before sending, instead of the client starting from an empty catalog form
- App tests (`tests/test_app_order_flow.py`): the whole no-proposal flow in the real app (rep picks products in Tab 2, client changes a quantity, adds a product and submits, staff import it from Submitted Order Forms), checking that products, quantities, customization notes, prices and client info carry into the Tab 3 order; a guessed catalog link shows only the friendly page. The Sheets stand-in gained `batch_update` (used to mark a response imported)

### Added (2026-10-22, tests that drive the real app)
- **Google Sheets Stand-In for Tests:** Setting `PBP_FAKE_SHEETS=1` makes `connect_to_sheets()` return an in-memory fake (`tests/fake_sheets.py`) instead of Google. The pricing spreadsheet serves a fixed snapshot of invented products, partners and contacts (`tests/fixtures/sheets/*.csv`, covering the 4 pricing methods, tiers and Per Case); every other spreadsheet starts empty. The app and its tests run with no Google credentials. Production never sets the variable, so the live Sheets path is unchanged
- **AppTest Suite for the Order Flow:** `tests/test_app_order_flow.py` runs the real `app.py` headless (`streamlit.testing.v1.AppTest`): adds products in Tab 3, sets quantities, $0.50 and marketing rounding, a typed client price override and per-product kitting, then checks the Order Summary total and the Tab 4 invoice/PO lines and total. How to run and extend it: `tests/README.md`
- A strict expected-failure test records a bug found this way: raising a tiered product's quantity into a cheaper tier keeps the old client price (the price box keeps its value and the markup is recalculated from it), so the tier discount never reaches the client. Fixed 2026-10-22 (editable PBP Cost work below); the test now passes normally
- `FakeSheet` moved from `tests/test_client_form.py` to `tests/fake_sheets.py` (shared by both)
- **Tests Run on Every Pull Request:** New GitHub Actions workflow (`.github/workflows/tests.yml`) runs `pytest tests/` on pull requests with the Sheets stand-in, so no credentials are needed. `tests/test_impact_slide_mapping.py` is skipped there because it reads the live sheet

### Fixed (2026-10-22, invoice/PO prices and kitting)
- **Rounded PbP MSRP Now Reaches the Invoice/PO:** Tab 3 showed the price rounded to the nearest $0.50 (e.g. 3 oz Honey $7.00, Tea Tin $16.50), but the Tab 4 invoice/PO recalculated each price from the spreadsheet without rounding ($7.06, $16.35) and also ignored PbP MSRP edits unless "Manual override" was on. Tab 4 now uses the same cost and price as the Tab 3 Order Summary through the new `get_item_client_unit_price()` (`src/helpers.py`), which `calculate_split_totals()` also uses. The invoice/PO "Subtotal" line now matches the Tab 3 subtotal (it was the unrounded product total)
- **Kitting Now Reaches the Invoice/PO:** Tab 4's "Edit Order Settings" has its own copies of the order settings (shipping, sales tax, rounding, credit card fee, custom discount %, kitting). Each copy kept its own old value and overwrote the Tab 3 value on every run, so sale-wide kitting entered in Tab 3 was $0 by the time the invoice/PO was built, and the $0.50 rounding setting was turned off. Both tabs' fields now use `synced_widget()`, so they always show and save the same value. Turning $0.50 rounding on or off (either tab) also updates each product's PbP MSRP field, so the old price is not taken as a typed one. The invoice/PO totals also list Kitting and Sales Tax, which were already in the TOTAL
- **Sale-wide Kitting Is Per Box:** New "Number of Boxes" field next to the sale-wide Kitting Cost/Price in Tab 3 and Tab 4 (shared value, saved with the order, old orders load as 1). Kitting cost and price are per box and multiplied by the box count in the Tab 3 totals, Order Summary, and the invoice/PO kitting row (QTY = boxes) and TOTAL, e.g. $11.50 x 85 boxes = $977.50 (`calculate_kitting_totals()` in `src/helpers.py`)
- **Sidebar "Download Order (CSV)" Matches the Order Form:** It used unrounded prices and a TOTAL of products + shipping + tariff only. It now uses the same rounded client prices and the same TOTAL as the Tab 3 Order Summary (discount, customization, sales tax, kitting, credit card fee). The order total math lives in one place, `calculate_order_quote()` (`src/helpers.py`), used by Tab 3, the Tab 4 invoice/PO and the CSV (`build_order_csv()`)
- Tests: `tests/test_order_pricing.py`

### Added (2026-10-22, editable PBP Cost)
- **PBP Cost Can Be Overridden in Tab 3:** The PBP Cost in each product's Quantity & Pricing row is now an input, like the PbP MSRP. A typed cost is kept on the order item (`pbp_cost_override`, saved with the order) and used everywhere the cost is used: client price (cost + markup), totals, tariff base, the Tab 3 summary and the Tab 4 invoice/PO. The spreadsheet cost is shown under an overridden cost; typing it back in removes the override. Done through `get_item_unit_cost()` (`src/pricing_engine.py`)
- A PbP MSRP typed in Tab 3 stays put when the PBP Cost is edited afterwards (the markup is recalculated instead), so cost-then-MSRP and MSRP-then-cost give the same result (`set_item_client_price()` / `set_item_pbp_cost()`). It also stays put when a quantity change moves the product to another price tier (`keep_typed_pbp_msrp()`). Editing the markup releases it. The markup never goes below the markup field's -50% floor (`markup_for_price()`), so a mistyped cost far above the typed price, or a typed price under half the cost, no longer crashes Tab 3; fixing the cost brings the typed price back. A typed price under half the cost is raised to half the cost, and the PbP MSRP field, totals and invoice/PO all show that price with a "Raised to the lowest allowed price" note. The PBP Cost input no longer accepts $0, and the Order Summary MOQ check uses the overridden cost

### Fixed (2026-10-17, order photos)
- **Re-Saving a Loaded Order No Longer Drops Its Photos:** Loading an order kept its saved photos aside, but every save rebuilt the order without them, so overwriting with no new uploads removed all product photos, and adding a photo kept only the new one. `save_current_order()` (`src/order_manager.py`, used by every Tab 3 save button including Save & Finalize) now keeps the saved photos and uploads only new ones, skipping any already saved (same name and size, as `add_product_photos()` does) and stopping at 5 per product counting saved photos. `save_order()` adds new uploads to the saved photos instead of replacing them. Saving twice in one session no longer uploads the same photo again. Photo metadata now also records each photo's size (photos are stored the same way)
- Tab 3 "Product Photos" counts saved photos toward the 5 remaining slots, lists saved photo names, and includes them in the photo summary. "Clear Entire Order" and the sidebar reset also clear photos, so a new order does not pick up the previous order's photos
- Tab 4 invoice HTML and photo section show a product's saved photos and new uploads together (previously new uploads hid the saved ones). Deleting an order keeps photos another saved order still uses (a saved copy of a loaded order shares its photos)
- Tests: `tests/test_save_current_order.py` (fake sheet and photo store: load then re-save keeps photos, adding one keeps old plus new, the cap counts saved photos, delete keeps photos shared with another order)

### Added (2026-10-17, order email)
- **Team Email When a Client Submits an Order Form:** Once a client order reaches Form Responses, `notify_team_of_order()` (`src/client_form.py`) emails a list of team addresses with the company, contact, number of items, submit time, proposal ID and a link to the staff app. It is sent once per order (once the row is written to Form Responses), including orders that were pending and are copied later by the app's retry. The client's submit never waits on or fails because of the email: a failed send is logged and shown to staff as an "Order email not sent" sidebar warning (kept until the app restarts). With no settings, nothing is sent and the app behaves as before
- **Setup (Render > Environment):** `ORDER_NOTIFY_EMAILS` (comma-separated team addresses), `SMTP_HOST` (e.g. `smtp.gmail.com`), `SMTP_PORT` (optional, default `587`, STARTTLS), `SMTP_USER` (the sending mailbox), `SMTP_PASSWORD` (for Gmail/Google Workspace: an App Password, created under Google Account > Security > 2-Step Verification > App passwords), `SMTP_FROM` (optional, defaults to `SMTP_USER`). Locally the same names can go in `.streamlit/secrets.toml`. The existing Google service account cannot send mail without Workspace domain-wide delegation, so plain SMTP is used
- Tests: `tests/test_client_form.py` (fake mail server: one email per order, none while pending, a mail failure never fails the order, no email when not set up)

### Changed (2026-10-17, Tab 3 save and finalize)
- **One "Save & Finalize Order" Button at the Bottom of Tab 3:** The bottom of Tab 3 had a "Confirm Order" button ("Ready to finalize your order?") and a separate "Save Order" button, and it was not clear which one to use. "Confirm Order" only set an in-session `order_confirmed` flag that nothing else reads (Tab 4 never required it) and was lost unless the order was saved afterwards. They are now one button that saves the order to Saved Orders and marks it finalized in the same click, with helper text explaining what it does and that Tab 4 is next. The "Edit Order" button is gone: the order stays editable and can be saved again (Overwrite updates it in place). The quick save at the top of Tab 3 and the Saved Orders panel still save without changing the finalized flag, so a work-in-progress order can be saved as before. "Clear Entire Order" and the sidebar reset also clear the finalized flag, so a new order never starts out finalized
- All three Tab 3 save buttons now share `save_current_order()` (`src/order_manager.py`) instead of three copies of the same code; the session is only marked finalized once the save succeeds
- Tests: `tests/test_save_current_order.py` (fake `save_order`, no Google Sheets)

### Changed (2026-10-17, client order form)
- **Dropshipping Spreadsheet Is No Longer Expected Up Front:** Choosing "dropshipped to multiple addresses" now shows a short note that a recipient address spreadsheet will be needed before the order ships, plus the dropshipping instructions box. The file upload was removed from the form (a file saved with an older draft is kept, and Tab 3 can still download files already submitted). No template is offered until the team settles on a format
- **"Other" Shipping Option:** The drop-shipping dropdown has an "Other" choice with a text box; the typed answer is required on submit and saved to Form Responses as "Other: <typed text>". Tab 3 import keeps it in the order's internal team notes ("Shipping (client's answer): Other: ...") with Shipping Type One Location, even when the text starts with "Yes" or "No"
- **Required Accounting Email or Platform:** New required field (submit only, not Save Progress) asking where invoices go: an email address or an accounting platform. Saved to the existing Form Responses invoice column ("Is there a specific platform or email address we need to send the invoice to (i.e. BillPay.com)?") as e.g. "Email: ap@client.com", so both the in-app form and the Google Form land in the same place on import: the bookkeeping order note ("Send invoice to: ...")
- Test: `tests/test_client_form.py` (accounting answer and "Other" shipping answer reach Form Responses and the imported order)

### Added (2026-10-17, submitted order forms view)
- **Submitted Order Forms Tab:** Staff no longer need the spreadsheet to see what clients submitted. A new tab (behind the app password) lists every submitted client order form, newest first, with date, company, contact, item count and status (Not imported, Imported, or Waiting to sync), plus search (company, contact, email, date, product) and an imported filter. Selecting a row shows every answer laid out for reading: products with quantity and customization notes, client and contact, shipping and billing addresses, in-hands date, drop-ship answer and instructions (with a download of the client's address file), payment method and invoice details, impact cards and notes. "Import into Tab 3" runs the same import as before and marks the response imported. Data comes from Form Responses plus the `client_form_drafts` backup tab, so orders whose copy into Form Responses is stuck are still visible; nothing new is stored. Sheets are read only when "Load"/"Refresh" is pressed. A failed Google Sheets read shows an error instead of an empty list (`load_form_responses()` and `load_received_orders()` now raise instead of returning an empty list; unused `retrieve_file_by_proposal()` removed). The Tab 3 Option A response list moved here (`import_form_response()` and `show_submission_details()` in `app.py`, `build_submissions_list()` and `submission_matches_search()` in `src/forms_helper.py`, `load_received_orders()` in `src/client_form.py`)
- Tests: `tests/test_submitted_forms.py` (fake sheets: a Google Form answer, a synced in-app order and a stuck one, listed newest first; search; every answer shown in the details)

### Fixed (2026-10-16, form to order mapping)
- **Client Form Answers Lost on Tab 3 Import:** Form Responses held every answer, but "Import This Response" dropped per-product customization notes, the bottom "Special Requests, Notes, or Questions", drop-ship instructions, impact cards and the invoice platform answer, and mis-read Google Form wording (drop-ship "Yes - Ship directly ..." became One Location, "2/27/2026" dates were dropped, "ACH / Bank Transfer" did not match the payment dropdown). A blank "Billing Address (if different from shipping)" left the order with no billing address. New `form_response_to_order()` (`src/forms_helper.py`) is the one place that maps the form to the order: customization notes become that product's customization description (notes only: "Include Customization" stays unticked and no customization pricing is added). The Tab 3 "Customization Description" box is now always shown, and a non-empty description is printed on the product line of the Tab 4 invoice/PO (HTML and CSV) whether or not the box is ticked; it no longer pre-fills from the catalog's Customization Info, which is still shown as "Available: ...". Notes, impact cards and the invoice platform go into the order notes (added to, never wiping, staff notes via `add_order_notes()`), drop-ship instructions (plus the uploaded address file name) go into a new `drop_shipping_instructions` order field, and billing falls back to the shipping address
- **Legacy HTML Order Form Import:** "Import Client Information" wrote the contact as loose `contact_name`/`contact_email` keys that Tab 3, Tab 4 and the invoice never read, and skipped the billing fallback and drop-ship instructions. It now goes through the same mapping (`html_form_to_order()` in `src/forms_helper.py`)
- **Tab 3 to Tab 4 Carry-Over:** Keyed Streamlit widgets keep their own value and ignore `value=` after the first run, so after an import or an order load several Tab 3 fields (contacts, order notes) wrote stale values back over the order, and Tab 4 showed stale dates, ship method, payment terms/method and contact roles. Tab 3 Section 6 and Tab 4 Section 1 now use one helper (`synced_widget()` in `app.py`) that resets each field from the order data every run and saves edits with `on_change`, so both tabs always show the same values. Contacts, payment terms and order notes editors are shared by both tabs. Per-product widgets are reset when an order is loaded or a form response imported
- **Tab 4 Notes Editable:** The NOTES section at the bottom of Tab 4 now holds the same 4 editable notes as Tab 3 (the hidden copy inside "Edit Order Settings" was removed)
- **Invoice Dropshipping Instructions:** The invoice/PO printed the Tab 2 form-template text ("For drop shipping orders, please provide ...") as dropshipping instructions. It now prints the client's own instructions (HTML and CSV), editable in Tab 3/Tab 4 when Shipping Type is Drop Shipping. Tab 3 no longer clears the shipping address when Drop Shipping is chosen
- Tests: `tests/test_form_to_order.py` (a fully filled form through fake Form Responses, Tab 3 import, save/load, and a Tab 3/Tab 4 widget sync check)

### Fixed (2026-10-16)
- **Client Orders Overwrote Each Other in Form Responses:** Every client form submission was written over row 8 of "Form Responses 1", losing earlier orders. The tab had a Google Sheets Table over rows 1-7 and the sync used `append_row`, which lets Google pick the row. `_sync_backup_row()` (`src/client_form.py`) now writes to the row right after the last filled row, growing the grid and retrying once if Google reports the row is past the grid limit
- **"Mark as Imported" Wrote Into Gift 4/5 Columns:** Tab 3 import tracking (Imported?, Order ID, Imported By, Import Date) went into the Gift 4/5 product columns because cell addresses were built with `chr(64 + col)`, which breaks past column Z. `mark_response_imported()` (`src/forms_helper.py`) now uses `gspread.utils.rowcol_to_a1`
- Tests: `tests/test_client_form.py` (a fake Table sheet whose `append_row` always hits row 8, a full grid, a stale cached row count, and the AX8..BA8 tracking ranges)

### Fixed (2026-10-14)
- **Product Photo Attached 5 Times:** Uploading one photo in Tab 3 "Product Photos" attached it repeatedly (up to the 5-photo cap). Streamlit re-sends the file uploader's value on every rerun and each rerun appended it again. New `add_product_photos()` (`src/helpers.py`) skips photos already attached (same name and size). Test: `tests/test_product_photos.py`
- **Client Form No Longer Asks for Payment Terms:** The "Payment Preference" (Net 30 / Net 60 / Due on Receipt) dropdown was removed from the client order form; payment terms are set by PBP staff in Tab 3/Tab 4. "Payment Method" (ACH, Credit Card, Check, Other) stays. The Form Responses column is left blank and Tab 3 import falls back to Net 30 as before

### Fixed
- **Client Order Form Lost Gift Items:** Submitting the in-app client order form saved client and shipping info but no items. The live response sheet's item columns are named "Gift Item 1 - Product Name" / "Gift 1 Quantity" / "Gift 1 Customization Notes" (not "Product Line 1 - ..."), and the drop-ship and impact-card questions were reworded too; values with no exactly matching column were silently skipped. New `find_response_column()` (`src/forms_config.py`) matches headers tolerantly (case, spaces, `*`, dashes, and item columns by line number) and is used by both submit and the Tab 3 import, so existing Google Form responses now import their items as well
- **No More Silent Submit Failures:** `submit_form()` now saves a full backup copy of the form to the `client_form_drafts` tab (saved_orders spreadsheet) before writing anything (if the drop-ship file is too big for a sheet cell, the copy is saved without it; a form-only save never wipes a previously stored file), and flags any filled-in field that has no column in the response sheet (now a staff alert, not a client error; see Changed below). The client form is capped at 10 items (the sheet's item columns)
- **Client Form Hit Google Sheets Read Quota:** Submitting failed with "429 Quota exceeded ... Read requests per minute". The form page re-read the proposal and draft from Google Sheets on every click (about 6 reads per click, against a 60-reads/minute limit shared with the live app). The proposal and draft are now loaded once per visit, spreadsheets are opened once and reused, draft lookups read only the ID columns, and every Sheets call on the form path waits and retries on a 429 (2/4/8/16s). A 429 means Google rejected the request, so a retried write never duplicates the response row; if the quota never clears, the order stays in the backup tab for a later sync (see Changed below)
- Tests: `tests/test_client_form.py` (mocked sheets, includes a header-mismatch case and a 429-then-success case)

### Changed (2026-10-13)
- **Client Order Form Never Shows a Sheets Error:** Submit now saves the order to the `client_form_drafts` backup tab first (status `pending_sync`, retried for about 1-2 minutes), shows the client "Order received", and copies it into Form Responses on a background thread with retries (10/30/60/120s). The backup tab is the source of truth. If the copy still fails, the main app retries every pending order once per staff session (`retry_pending_syncs()`) and shows a sidebar warning for orders pending more than 10 minutes (e.g. a missing sheet column, which no longer blocks the client). Syncing is idempotent: the submit time is stored in the backup and used as the response Timestamp, and a row already in Form Responses is never written twice. The client only sees an error (with no technical detail) if the backup itself cannot be saved
- **Client Form Review Fixes:** A one-off Sheets error during the backup save no longer drops the drop-ship file (the file is left out only when it is too big for a sheet cell, decided once before retrying). A received order (pending or submitted) is never rewritten, so a second Submit from an old tab cannot add a second Form Responses row. The staff "pending sync" warning now shows the reason (e.g. a missing column) and says to refresh to re-check

## [8.5.5] - 2026-09-04

### Fixed
- **PowerPoint Template Discovery:** The template dropdown now lists the decks in the shared "latest" Drive folder (July2026, June2026, May2026) instead of three stale files. It searched all of Drive for filenames containing "All Slides", but files the service account reaches by *inheriting a folder share* do not appear in a Drive-wide name search -- only the older decks that had been shared file-by-file (April/March/November) came back. `list_available_templates()` now queries the folder by ID. Folder is `TEMPLATE_FOLDER_ID` in `src/template_loader.py`, overridable by an env var of the same name
- **Notes Placement on Invoice/PO:** Internal (PBP team, bookkeeping) and external (partners, clients) notes plus dropshipping instructions now appear at the top of the generated invoice/PO -- directly under the title in the HTML, and as the first rows of the CSV -- instead of at the bottom. Requested by accounting, who read the notes first

### Changed
- Adding a new slide deck no longer needs a per-file Drive share: drop the .pptx in the "latest" folder and click Refresh under the template selector

## [8.5.4] - 2026-07-16

### Fixed
- **Price Range Filter (Tab 1):** The proposal price filter now matches the client price shown next to each product. A team member filtering for "gifts under $30" was getting products that display above $30. The filter used a simpler "Vendor MSRP, or cost x2 at quantity 100" estimate that ignored add-ons (e.g. "MSRP + % of cost" methods) and used a different quantity/tier than the price actually shown, so it consistently under-estimated and let over-budget products through. The filter and the catalog display now share one calculation (`calculate_catalog_client_price`), applying the product's real pricing method at its MOQ quantity, so a product's shown price and its filtered price always agree

### Added
- **`calculate_catalog_client_price()` (`src/pricing_engine.py`):** Single source of truth for the client-facing price shown in the Tab 1 catalog and used by the price-range filter. Test: `scripts/features/test_price_filter_matches_display.py`

## [8.5.3] - 2026-07-10

### Fixed
- **Bulk Add Crash (Tab 1):** Adding all products by partner (or via "Quick Add All Products") no longer crashes with `StreamlitAPIException: Expanders may not be nested inside other expanders` when some products have missing pricing data. The "failed products" list is now shown after the rerun (outside the catalog expander) instead of in a nested expander, listing which products were skipped

## [8.5.2] - 2026-07-10

### Fixed
- **Password Gate First-Click Login:** Logging in now takes effect on the first click. Previously the gate set the auth flag then relied on a JavaScript page reload (via a sandboxed iframe) that often did not fire, leaving users clicking "Log In" repeatedly. Now uses `st.rerun()` so login is immediate
- **Password Gate Browser Persistence:** "Remember this browser" now works. The old localStorage approach depended on a `components.html` iframe navigating the top window, which browsers block (sandboxed iframe without allow-top-navigation) -- so the login was never actually remembered. Switched to the `streamlit-local-storage` component, which returns the saved token to Python directly and auto-logs-in a returning browser

### Added
- **Dependency:** `streamlit-local-storage==0.0.25` (browser localStorage access for the password gate)

## [8.5.1] - 2026-07-10

### Added
- **Partner Shipping Instructions (Tab 4):** New per-partner "Shipping Instructions to PbP" free-text field (how each partner should ship goods to PbP, e.g. carrier and service level). Editable alongside partner contacts and printed as a column in the HTML invoice/PO export. Keeps instructions from getting buried in "Note to Partner"
- **Overwrite on Save (Orders and Proposals):** Save dialogs now include an "Overwrite existing order/proposal with this name" checkbox that updates the saved record in place, keeping its original ID. Added to all save buttons (top quick-save, bottom save, sidebar save)

### Fixed
- **Tab 3 to Tab 4 Carry-Over:** Tab 4 "Edit Order Information" widgets now seed from `client_info` on every run, so values entered in Tab 3 display correctly. Removed the contact direct-return assignment that was clobbering Tab 3 input with stale widget state (real data loss on contacts)
- **Stray $0.03 on Line Totals:** `calculate_markup_from_price()` now keeps full precision (6 decimals) instead of rounding markup to 2, so an entered client price reconstructs exactly (e.g. 83 x $30.00 = $2490.00, not $2490.03)
- **Save "always v2, can't overwrite":** `save_order()` / `save_proposal()` gained an in-place overwrite path; version-name suggestion now strips an existing `(vN)` suffix and increments properly (v2 to v3 to v4). Removed the nested "Save as (vN)" confirm buttons that were dropped on Streamlit rerun (the cause of the perpetual "v2")
- **Proposal Load Forcing "Manual Override":** Loading a saved proposal now clears stale per-row widget state (`override_`, `markup_`, `price_` keys) so a previously shown proposal's checkbox state no longer bleeds onto the newly loaded products

### Notes
- **Blank MSRP fallback (not a code change):** Products with a "MSRP + % of cost" pricing logic but an empty Vendor Published MSRP cell correctly fall back to standard 2x markup. If prices look unexpected, add MSRP values to those spreadsheet rows or switch their Pricing Logic to "Standard markup"

## [8.5.0] - 2026-07-02

### Fixed
- **Rounded Pricing in Order Summary:** $0.50 rounding now applies to per-unit prices in the Order Summary table and totals, matching what's shown in the product editing section
- **Password Gate (Local):** Fixed `st.secrets.get()` returning empty on Streamlit 1.29; switched to bracket access with fallback
- **Shipping Type vs Ship Method Conflict:** Separated `shipping_type` (One Location / Drop Shipping) from `ship_method` (Ground / Air / Freight / Other) into independent session state keys. Previously they shared one field, causing "One Location" to display as "Drop Shipping"
- **Tab 3 to Tab 4 Data Flow:** Client info now carries correctly between tabs (resolved by shipping field separation)

### Added
- **Editable Partner Contacts (Tab 4):** Partner POC name, email, and phone are now editable text fields in Tab 4, pre-filled from the spreadsheet. Edits carry through to HTML invoice export
- **Cost Basis Display (Tab 3):** Products priced per case now show "Priced per case (X units/case)" below the quantity input

### Removed
- **Cost Verified Column (Tab 4):** Removed the "Cost Verified?" column from invoice/PO tables, CSV export, and HTML export (not needed in workflow)

## [8.4.0] - 2026-05-27

### Added
- **Client Order Form as Shareable Link:** Standalone form page accessible via direct URL (`?client_form=<proposal_id>`). Clients can complete order forms without needing app password or Google account. New module: `src/client_form.py` (session tokens, proposal loading, draft save/load, form submission)
- **Password Gate:** Main app now requires password entry. Client form links bypass the gate automatically. Styled container prevents title overflow
- **Generate Client Form Link (Tab 2):** New section for generating shareable client form URLs from saved proposals
- **Dropshipping File Download (Tab 3):** Download button for dropshipping address files in form response preview
- **Unit Tests:** Added `tests/test_client_form.py` for client form module

### Changed
- **In-Hands Date Picker:** Switched from date range picker to single-date picker for clearer UX
- **Google Form Section (Tab 2):** Demoted to legacy fallback; Client Form Link is now the recommended workflow

### Fixed
- **Impact Card Selection:** Removed non-functional Impact Card Selection box from order form
- **Query Param Routing:** Fixed client form routing across multiple Streamlit versions (set_page_config ordering, param detection)
- **Render URL:** Corrected production URL in query param generation
- **Password Gate Width:** Widened container to prevent title text overflow

## [8.3.0] - 2026-05-23

### Added
- **Current Proposal Sidebar Widget:** Scrollable list showing all products in the proposal (most recently added first) with a dropdown to remove products
- **Clear All Filters Button:** One-click reset of all product filters (budget range, partner, country, search) in Tab 1
- **PBP In-Hands Date Field:** Date PBP needs to receive product from partner, shown in Tab 3 (Section 5), Tab 4 (Client & Order Information), and on Purchase Orders (both table display and HTML export)
- **Customization Description Field:** Editable text input for base customization in Tab 3, pre-fills from spreadsheet data, appears on pricing breakdown and invoice/PO line items
- **Per-Product Photo Persistence:** Upload photos per product in Tab 3 (dropdown selector, up to 5 per product, thumbnail grid with summary). Photos persist across sessions via Google Sheets storage (base64 chunked). Tab 4 shows per-product photos with individual download buttons below Invoice/PO downloads. Photos auto-deleted when order is deleted. New module: `src/drive_helper.py` (photo storage)
- **Google Form URL On-Demand Generation:** "Generate Form URL" / "Update Form URL" button replaces auto-generation so users can regenerate after making changes
- **Import from Proposal (Option B):** Promoted from hidden expander to full section in Tab 3 as most commonly used workflow; Manual Product Selection renamed to Option C

### Changed
- **Save Proposal Section Simplified:** Removed duplicate "Load Proposal" UI from Tab 2; loading now only done from sidebar
- **Data Status Sidebar Cleaned Up:** Removed debug data details dropdown, hid refresh button behind "Having data issues?" expander
- **Client Budget Input Removed:** Removed duplicate Client Budget input from Proposal Settings (already set at top when filtering)
- **Client Budget Range Filter:** Now uses MSRP when available instead of cost x2, with transparency message showing MSRP vs estimated price counts
- **Proposal Tables Section:** Replaced with discreet "View raw proposal data (debug)" expander, removed CSV download
- **Tab Navigation Buttons:** Replaced non-functional "Continue to next tab" buttons with simple text notes
- **Shipping & Tariffs Hidden:** Section wrapped in "Legacy" expander/checkbox in both Tab 3 and Tab 4 since costs are now factored into product pricing
- **Section Numbering:** Tab 3 sections renumbered (Product Photos is now Section 5, Client & Order Information is Section 6)

### Fixed
- **Slide Matching:** Added `get_slide_title()` helper that checks PowerPoint title placeholder first, then all shapes on the slide, instead of only looking at shapes[0]
- **HTML/CSV Download Stale Data:** Download buttons in Tab 4 now use dynamic keys based on content hash, ensuring downloaded files always match on-screen data

## [8.2.0] - 2026-05-23

### Added
- **Template-Resilient PowerPoint Generation (Feb 23):** System now handles missing or changed template slides gracefully instead of failing
- **Google Form Without Proposal (Feb 21):** Tab 2 Google Form generation no longer requires a proposal to exist first
- **Custom Variant Support (Feb 7):** "Inquire about variants" handling in Tab 3 for products with custom variant options
- **MOQ Warnings (Feb 7):** Visual alerts when order quantity is below minimum order quantity
- **Volume Order Discount Reminder (Jan 29):** Automatic reminder shown for orders over $10,000 suggesting volume discount
- **Kitting Quantity Field (Jan 29):** Per-product kitting now supports configurable quantities
- **Google Forms Product Name Sync Tools (Jan 28):** Helper scripts for syncing product names between catalog and Google Forms
- **Volume Order Discount (5%) (Jan 28):** New discount option available in Tab 1 (Proposal Generator) and Tab 3 (Order & Client Info)
  - Provides clear distinction between non-profit discounts and volume-based discounts
  - Four discount options now available: None, Non-profit (5%), Volume Order (5%), Custom
  - Better tracking and reporting with distinct labels in order summaries
  - Works identically to Non-profit discount (5% applied to products, not customization)
  - Backward compatible with existing saved proposals and orders
  - Display updates in proposal tables show "5% Volume Order discount" label
  - "Discount Quoted to Client" warning in Tab 3 shows Volume Order discount when applicable

### Changed
- **Variant Functionality Removed from Tab 1 (Jan 27):** Variant handling moved to Tab 3 custom variant support; Tab 1 Proposal Generator simplified
- **Workflow Progress Section Removed (Jan 26):** Sidebar workflow progress tracker removed for cleaner UI
- **All Emojis Removed from App (Jan 23):** Completed emoji removal for professional appearance
- **Per-Product Kitting Display (Jan 28):** Kitting now shown as separate line items instead of merged into product rows
  - **Tab 3 (Order Summary):** Added new "Per-Product Kitting" section after Customization
    - Each product's kitting shows as separate line with "one-time" quantity
    - Displays kitting description (e.g., "Premium gift box", "Repackaging")
    - Shows both PBP cost and client price per line
    - Includes subtotal row for all per-product kitting
  - **Tab 4 (Invoice Generation):** Kitting appears as separate line items with indentation
    - Uses "└" prefix to show hierarchy (product → kitting)
    - Quantity = 1 (one-time charge)
    - Separate COST/UNIT and SELL PRICE/UNIT columns
    - Same format as customization line items
  - **Product Detail Breakdown:** Kitting totals removed from product summary (shown separately in breakdown table)
  - **Rationale:** Following customization pattern for consistency and clarity
  - **Backward Compatible:** No data structure changes, only display logic
  - **Test Coverage:** All 5 tests passing in `scripts/features/test_per_product_kitting.py`

### Fixed
- **Tier Parsing Robustness (Apr 2):** Fixed ValueError when tier strings contain multiple colons or space-separated formats
  - `parse_tier_info()` now handles formats like "1 - 99" (space-separated) and "Tier 1: 1:99" (multiple colons)
- **Double Normalization Bug (Jan 29):** Fixed Per Case products being normalized twice, resulting in incorrect pricing
- **"MSRP + Other Add-On %" Pricing Logic (Jan 28):** Fixed calculation for the fourth pricing method
- **Google Form Bugs (Jan 28):** Multiple fixes for Google Form response import and Tab 2/3 UI cleanup
- **Sidebar Session State (Jan 28):** Corrected session state variable name in sidebar
- **"Loading data..." Sidebar Issue (Jan 26):** Resolved persistent loading indicator in sidebar
- **PBP $1,000 Baseline MOV (Jan 23):** Enforced $1,000 minimum order value per-product in MOQ calculations
- **Schema Column Name Mismatch (CRITICAL, Jan 28):** Fixed KeyError caused by code using old column names from v7.x schema instead of new v8.x names
  - **Root Cause:** Google Sheets updated to v8.1.0 schema (Jan 28, 2026) but some code still referenced old column names
  - **Errors:** `KeyError: "['PBP Cost (No Tiers)'] not in index"` when trying to display or refresh data
  - **Fixed Columns:**
    - `PBP Cost (No Tiers)` → `PBP Cost (No Tiers/Tier 1)` (updated in app.py custom products, debug script)
    - `Units per Package` → `Units per Case` (updated in app.py custom products)
  - **Files Updated:**
    - app.py: Custom product creation now uses new schema column names (lines 5872, 5888, 5894)
    - scripts/debug_refresh_data.py: All display code uses new column names
  - **Backward Compatibility:** `get_column_value()` helper already had mappings, but direct column access bypassed it
  - **Impact:** App now works with v8.1.0 schema; refresh button can fetch and display data without errors
- **"Refresh Data" Button Not Working (CRITICAL):** Fixed sidebar "Refresh Data" button that was returning cached data instead of fetching fresh data from Google Sheets
  - **Root Cause 1:** Button called `load_pricing_data()` without clearing the 5-minute TTL cache first
  - **Root Cause 2:** Tab 3 was calling `load_pricing_data()` directly instead of using session state, which re-cached old data immediately after refresh
  - **Impact:** Users clicking "Refresh Data" got same cached data (no actual refresh unless 5+ minutes had passed)
  - **Solution 1:** Added `load_pricing_data.clear()` before fetching data to force fresh load (app.py:1145)
  - **Solution 2:** Changed Tab 3 to use session state data instead of calling `load_pricing_data()` directly (app.py:4501)
  - **Solution 3:** Added `extract_partner_contacts()` call in refresh button to update partner contacts from fresh data (app.py:1156)
  - **API Protection:** Added 30-second cooldown between manual refreshes to prevent rate limiting
    - Cooldown timer displayed to user ("Please wait Xs before refreshing again")
    - Button disabled during cooldown period
    - Protects against API rate limit (100 requests/100 seconds)
    - Each refresh = 3 API calls (Data, Metadata, Partner-Specific Info sheets)
  - **User Experience:** Button now provides immediate feedback and actually refreshes data as expected across all tabs
  - **Testing:** All tabs (1-5) now use session state data, ensuring consistency after refresh
- **PowerPoint Discount Labels & Prices:** PowerPoint proposal tables now correctly display discount labels AND apply discounts to prices
  - **Issue 1 - Headers:** Fixed headers showing "Price @ Qty 100" instead of discount labels
    - Now shows "Client Price (5% Non-profit discount)" or "Client Price (5% Volume Order discount)" when applicable
    - Applies to all table formats: 2×3, 2×4, 3×4, and multi-row variant tables
    - Updated `update_pricing_table()` to accept `discount_percent` and `discount_type` parameters
    - Updated all 3 presentation generation functions to pass discount information through
  - **Issue 2 - Prices:** Fixed prices not being discounted due to settings_snapshot override
    - Settings snapshot was overriding discount_percent with old value (0%) from when products were added
    - Now uses current discount setting from parameter instead of snapshot
    - Discount is treated as global proposal setting (can be changed after adding products)
    - Rounding settings still use snapshot (per-product configuration)
  - **Issue 3 - Column Logic:** Fixed both columns showing discounted price instead of comparison view
    - Problem: Both Column 1 and Column 2 showed prices WITH discount applied
    - User expectation: Column 1 = undiscounted price, Column 2 = discounted price (show savings)
    - Solution: When discount > 0, Column 1 now uses `base_price` (undiscounted), Column 2 uses `client_price_at_100` (discounted)
    - When discount = 0, both columns show regular prices (no change from original behavior)
    - Applies to both variant tables and single product tables
  - **Result:** PowerPoint tables now show price comparison correctly (undiscounted vs discounted)

---

## [8.1.0] - 2026-01-28

### SCHEMA UPDATE: Add-On Expansion & Terminology Update

This release adds support for non-shipping markup add-ons and updates cost basis terminology from "Package" to "Case".

#### 🔥 Schema Changes

**New Column:**
- **Column 25: "Other Add-On % (of Cost)"** - Captures markup add-ons outside of shipping (e.g., tariffs, handling fees)
  - Type: Percentage (0-100)
  - Default: 0.0 if empty
  - Format: 10 (means 10%)
  - Used in MSRP-based pricing methods

**Renamed Columns:**
- **Column 20:** "Cost Basis (Per Item/Per Package)" → "Cost Basis (Per Item/Per Case)"
- **Column 21:** "Units per Package" → "Units per Case"
- Backward compatibility maintained in code via `get_column_value()` fallbacks

**Total Columns:** 45 (was 44, +1 field)

#### ✨ New Features

**Fourth Pricing Method:**
- Added **"MSRP + Other Add-On % (of Cost)"** as allowed value in Pricing Logic column
- Uses same calculation as "MSRP + % of cost" but indicates Other Add-On % is primary
- Formula: `PBP MSRP = Vendor MSRP + ((Shipping Add-On % + Other Add-On %) × cost)`

**Enhanced Pricing Calculation:**
- Both add-ons (Shipping and Other) are now **summed together** in all MSRP-based pricing methods
- Method 1 ("MSRP + % of cost") updated to include both add-ons
- Method 4 ("MSRP + Other Add-On % (of Cost)") added with identical calculation
- Generally only one add-on will have a value, but both can be used simultaneously

#### 🔧 Code Changes

**Core Logic Files:**
1. **src/helpers.py**
   - Added `get_other_addon_percent()` function (mirrors `get_shipping_addon_percent()`)
   - Updated schema_mappings to include "Other Add-On % (of Cost)" with default 0.0
   - Updated "Cost Basis" mapping to use "Per Case" with "Per Package" fallback
   - Updated `normalize_cost_to_per_item()` to use "Units per Case" with fallback

2. **src/pricing_engine.py**
   - Imported `get_other_addon_percent()` function
   - Updated "MSRP + % of cost" method to sum both add-ons: `(Shipping % + Other %) × cost`
   - Added new pricing logic case for "MSRP + Other Add-On % (of Cost)"
   - Updated `get_unit_price_new_system()` to use "Units per Case" terminology
   - Both methods calculate: `total_addon_pct = shipping_addon_pct + other_addon_pct`

#### 📚 Documentation Updates

**schema_reference.md:**
- Updated header: v8.1.0, 45 columns
- Added column 25 definition with description and rules
- Renamed columns 20-21 with "Case" terminology
- Renumbered columns 26-45 (shifted by 1)
- Added v8.1.0 entry to Schema Change Log
- Added v8.1.0 changes summary section

**docs/planning/METHODOLOGY_LOGIC.md:**
- Updated overview to mention four pricing methods
- Updated Method 1 formula and example to show both add-ons
- Updated Method 3 Cost Basis reference to use "Per Case"
- Added complete Method 4 section with formula, examples, and validation
- Updated Cost Basis Normalization section with "Per Case" terminology
- Added update note: "Updated January 28, 2026"

#### 🔄 Backward Compatibility

**Fully Backward Compatible:**
- Old "Units per Package" column still works (fallback in `get_column_value()`)
- Old "Cost Basis (Per Item/Per Package)" values still recognized
- Products without "Other Add-On %" default to 0.0 (no impact on existing pricing)
- All existing spreadsheets continue to work without modification

**Migration Path:**
- Spreadsheets can be updated to new column names at any time
- Code checks new names first, falls back to old names
- No breaking changes for existing data

#### 📊 Examples

**Example 1: Both Add-Ons Used**
```
Pricing Logic: MSRP + % of cost
Vendor MSRP: $10.00
Shipping Add-On %: 15%
Other Add-On %: 5%
Per-Item Cost: $5.00

Calculation: $10.00 + ((0.15 + 0.05) × $5.00) = $10.00 + $1.00 = $11.00
PBP MSRP: $11.00
```

**Example 2: Only Other Add-On**
```
Pricing Logic: MSRP + Other Add-On % (of Cost)
Vendor MSRP: $12.00
Shipping Add-On %: 0% (default)
Other Add-On %: 10%
Per-Item Cost: $6.00

Calculation: $12.00 + ((0.00 + 0.10) × $6.00) = $12.00 + $0.60 = $12.60
PBP MSRP: $12.60
```

**Example 3: Per Case Normalization**
```
Cost Basis: Per Case
PBP Cost: $48.00
Units per Case: 6

Per-Item Cost: $48.00 ÷ 6 = $8.00
(Used in all subsequent pricing calculations)
```

#### ✅ Testing

**Manual Tests Required:**
- Test product with Shipping Add-On only → should work as before
- Test product with Other Add-On only → should add Other to MSRP
- Test product with BOTH add-ons → should sum and add to MSRP
- Test product with no add-ons → should match vendor MSRP exactly
- Test "Per Case" cost basis → should normalize correctly
- Test backward compatibility with old "Package" column names

#### 📝 Files Changed

- `src/helpers.py` - 4 changes (schema mappings, new function, normalize function, case references)
- `src/pricing_engine.py` - 4 changes (import, Method 1 update, Method 4 addition, case references)
- `schema_reference.md` - Complete update (column table, changelog, summary)
- `docs/planning/METHODOLOGY_LOGIC.md` - Complete update (all methods, examples, case references)
- `CHANGELOG.md` - This entry

---

## [8.0.0] - 2026-01-22

### MAJOR SCHEMA TRANSITION (33 → 44 columns)

This is a major release with a complete schema overhaul introducing sophisticated pricing logic and improved data structure.

#### 🔥 Breaking Changes
- **New Schema:** Transitioned from 33 columns to 44 columns (+11 new fields)
- **Pricing Logic:** Replaced simple markup system with 3 distinct pricing methods
- **Column Renames:** Several columns renamed for clarity (see schema_reference.md)
- **Tier Consolidation:** Combined "PBP Cost (No Tiers)" and "Tier 1" into single column "PBP Cost (No Tiers/Tier 1)"
- **Description Fields:** Separated into Billing Description (invoices), Purchase Description (POs), and Marketing Description (proposals)

#### ✨ New Features

**Three Pricing Methods:**
1. **"MSRP + % of cost"** - Vendor MSRP plus shipping recovery (calculated as: Vendor MSRP + Shipping Add-On % × per-item cost)
2. **"MSRP capped – ship absorbed"** - Use vendor MSRP exactly, shipping costs absorbed by PBP
3. **"Standard markup"** - Traditional cost × (1 + markup%), with diagnostic markup support or 100% default

**Pricing Engine (Phase 1):**
- New `calculate_pbp_msrp()` function with method-specific logic
- Cost basis normalization: explicit "Per Item" vs "Per Package" handling
- Hybrid validation: compares calculated prices against spreadsheet values
- Diagnostic markup calculations for transparency (vendor markup and PBP markup)
- Empty field defaults (100% markup fallback, "Per Item" cost basis default)
- Manual override checkbox for all pricing methods (flexible pricing control)

**UI Updates (Phases 2-4):**
- **Tab 1 (Proposal Generator):**
  - Pricing method column in "Products in Proposal" table
  - Shows: Product → PBP Cost → Vendor MSRP → Pricing Method → PBP MSRP → Markup %
  - Rounding indicators when prices adjusted (shows original unrounded price)
  - Manual override checkbox for custom pricing
  - Pricing notes display (expandable, shows method-specific calculations)
  - Validation warnings for price discrepancies (non-blocking, informational)
  - $0.50 rounding integration (default enabled)
  - MSRP pricing checkbox uses new calculation logic

- **Tab 3 (Order & Client Info):**
  - All 4 entry pathways updated (Google Form, HTML, Proposal import, Manual add)
  - Clean 6-column pricing table matching Tab 1 format
  - Pricing method preserved across imports
  - Manual override checkbox
  - Rounding applied by default with indicators
  - Real-time price recalculation with new methods
  - Quantity & Pricing section redesigned for clarity

- **Tab 4 (Execution & Accounting):**
  - Description field hierarchy for invoices: Billing → Marketing → Product Name
  - Description field hierarchy for POs: Purchase → Billing → Product Name
  - Split "ITEMS + SPECS" into two columns: "DESCRIPTION (Invoice)" and "DESCRIPTION (PO)"
  - Separate invoice and PO descriptions in HTML/CSV exports
  - Clean professional output (pricing notes hidden on invoices)
  - Pricing consistency with Tab 3 using new methods

**New Schema Columns:**
- `Pricing Logic` (column 23) - Defines which pricing method to use (3 allowed values)
- `Cost Basis (Per Item/Per Package)` (column 20) - Explicit cost type declaration
- `Shipping Add-On % (of Cost)` (column 24) - Percentage for "MSRP + % of cost" method
- `PBP Cost (Per-Unit, No Tiers, Calculated)` (column 22) - Normalized per-item cost (calculated)
- `PBP MSRP (Per-Unit, No Tiers, Calculated)` (column 29) - **AUTHORITATIVE PRICE** (calculated)
- `Vendor Markup (No Tiers, Calculated)` (column 27) - Diagnostic vendor markup % (calculated)
- `PBP Markup (Vendor+Add-On, No Tiers)` (column 28) - Diagnostic PBP markup % (calculated)
- `PBP MSRP (Website)` (column 30) - Website-displayed MSRP (reference)
- `Pricing Notes` (column 25) - Pricing assumptions and exceptions (informational)
- `Billing Description (to Client)` (column 6) - Client-facing invoice description
- `Purchase Description (to Partner)` (column 5) - Partner-facing PO description (renamed)
- `Marketing Description (Website)` (column 7) - Website/proposal description (renamed)
- `Data Collection Notes` (column 44) - Data quality and audit trail (governance)

**Backward Compatibility:**
- `get_column_value()` helper supports old and new column names seamlessly
- Graceful handling of empty fields with sensible defaults
- Works with spreadsheets missing new columns (falls back to old names)
- Quiet validation (informs user of missing data, doesn't block functionality)

#### 🧪 Testing (Phase 5)
- Comprehensive test suite created (5 new test scripts)
- All 3 pricing methods validated with real dataset (51 products, 44 columns)
- Pricing method distribution verified: MSRP + % (47.1%), MSRP capped (37.3%), Standard markup (15.7%)
- Empty field handling tested (defaults work correctly)
- Description fallback logic verified (3-level hierarchy per use case)
- Full workflow testing (Tab 1 → Tab 3 → Tab 4)
- Edge case testing (MSRP below cost, missing fields, invalid values)
- Regression testing (existing features preserved - variants, saved proposals/orders)
- Backward compatibility confirmed (old demo dataset still works)
- **Test Results:** 100% success rate, no critical errors, production-ready

**Bugs Fixed During Testing:**
- Fixed pandas NA handling in `get_column_value()` (TypeError with pd.isna())
- Fixed MSRP string conversion in `calculate_pbp_msrp()` (TypeError with clean_price())
- Fixed header row reading for real dataset (row 7 vs row 6)

#### 📚 Documentation (Phase 6)
- Created `schema_update_jan_2026/` workspace with:
  - `MASTER_TRACKING.md` - Complete context, decisions, and implementation tracking
  - 6 phase-specific implementation guides (PHASE1-6_*.md)
  - `RESUME_PROMPTS.md` - Context recovery for new sessions
  - `PHASE5_COMPLETION_SUMMARY.md` - Complete testing results and bug fixes
- Updated `schema_reference.md` - Complete 44-column schema documentation
- Updated `METHODOLOGY_LOGIC.md` - Added new pricing methods section (detailed)
- Updated all README and CLAUDE.md references
- Created deployment checklist for production readiness

#### 🔧 Bug Fixes
- Fixed session state management for new pricing fields
- Fixed manual override persistence across tabs
- Fixed description field fallback logic (3-level hierarchy working correctly)
- Fixed validation warning display conditions (non-blocking, informational only)
- Fixed pricing calculation consistency across all tabs
- Fixed false "price changed" warnings when importing from proposal (rounding mismatch)
- Fixed rounding integration in PowerPoint generation

#### 💡 Technical Improvements
- Modular pricing engine architecture (clean separation of concerns)
- Clear separation of concerns (calculation vs display vs validation)
- Consistent function signatures across tabs (calculate_pbp_msrp used everywhere)
- Improved error handling and validation (graceful degradation)
- Better user feedback (pricing notes, validation warnings, rounding indicators)
- Hybrid validation approach (read spreadsheet + calculate for comparison)
- Cost normalization with explicit basis checks ("Per Item" vs "Per Package")

#### 🚀 Deployment Notes
- Full schema migration completed across all phases (1-6)
- All phases tested and validated (comprehensive test coverage)
- Production-ready as of 2026-01-22
- No backward compatibility issues (clean migration with fallbacks)
- Real dataset verified (51 products, 44 columns, all pricing methods working)
- Demo dataset still works (backward compatibility confirmed)

#### 📖 Documentation References
- **Schema Definition:** `schema_reference.md` (44 columns documented)
- **Transition Context:** `schema_update_jan_2026/MASTER_TRACKING.md` (complete tracking)
- **Implementation Guides:** `schema_update_jan_2026/PHASE[1-6]_*.md` (step-by-step)
- **Pricing Methodology:** `docs/planning/METHODOLOGY_LOGIC.md` (new methods section)
- **Testing Results:** `schema_update_jan_2026/PHASE5_COMPLETION_SUMMARY.md`
- **Deployment Checklist:** `schema_update_jan_2026/DEPLOYMENT_CHECKLIST.md`

#### ⚠️ Migration Notes for Users
- New spreadsheet format required (44 columns - see schema_reference.md)
- Products without pricing logic default to "Standard markup" (100%)
- MSRP-based products calculate markup automatically from vendor MSRP
- Manual override checkbox available on all products for flexible pricing
- Validation warnings inform of price discrepancies (non-blocking, can be ignored)
- Empty fields handled gracefully with sensible defaults
- Old spreadsheets still work (backward compatibility via get_column_value)

#### 🎉 Implementation Statistics
- **Total Phases:** 6 (all complete)
- **Files Modified:** 3 core files (app.py, src/helpers.py, src/pricing_engine.py)
- **Lines Changed:** ~1,000+ lines (new pricing logic, UI updates, validation)
- **Test Scripts Created:** 5 comprehensive test files
- **Documentation Created:** 8 new markdown files
- **Test Coverage:** 100% of critical pricing paths
- **Production Status:** ✅ Ready for deployment

---

## [7.6.0] - 2026-01-20

### Added
- **Google Forms Integration (Tab 2 → Tab 3)** - Modern workflow for client order collection
  - **Tab 2: Form Generation**
    - Pre-fill Google Forms with proposal products and client info
    - Clean UI: Select products from proposal, adjust quantities, generate URL
    - One-click URL generation with copy button and preview link
    - Supports up to 10 product lines per form
  - **Tab 3: Response Import**
    - Load recent form responses from Google Sheets
    - Preview before importing: client info, products, shipping, payment details
    - One-click import populates all client fields and adds products to order
    - Automatic product matching (exact match, case-insensitive)
    - Default settings: quantities from form, 100% markup
    - Tracking columns prevent duplicate imports (Imported?, Order ID, Import Date)
  - **New modules:**
    - `src/forms_config.py` - Form URLs, entry IDs, column mappings (249 lines)
    - `src/forms_helper.py` - URL generation, response parsing, import tracking (~350 lines)
  - **Documentation:**
    - `docs/planning/GOOGLE_FORMS_IMPLEMENTATION_COMPLETE.md` - Complete feature guide with testing checklist
    - `docs/planning/GOOGLE_FORM_CREATION_GUIDE.md` - Step-by-step form creation instructions
  - **Benefits:**
    - Replaces "finnicky HTML" workflow with professional Google Forms
    - 50-70% faster than HTML workflow (45-60 seconds vs 2-3 minutes)
    - Better client experience and data quality
    - Pure Python implementation (no Apps Script)
  - **Bug fixes during testing:**
    - Fixed nested expanders UI issue
    - Fixed product import with proper dict conversion and pricing structure
    - Fixed client_info field mapping (all required fields)
    - Fixed response column mappings (asterisks for required fields)
    - Fixed date parsing (string to date object)
    - Fixed per-unit pricing calculations

- **Custom Product Creation** - Create unique products not in the catalog (Tab 3)
  - **Quick add form:** 3 fields only (Product Name, Partner, Base Cost/Unit)
  - **Partner selection:** Choose real partner for POC tracking, or "Custom/Other"
  - **Inline configuration:** After adding, configure quantity, markup, customization using same controls as catalog products
  - **Country & Tariff fields:** Set country of origin (Made In / Ships From) and tariff estimate for custom products
  - **Full integration:** Works with all existing features (discounts, marketing rounding, kitting, etc.)
  - **Profit visibility:** Base cost + markup % = client price (transparent pricing)
  - **Invoice integration:** Partner POC auto-populates when real partner selected
  - **UX consistency:** Matches catalog product add-to-order flow (add quick, configure inline)
  - **Legacy support:** Old custom line items still work, shown with "(Legacy)" label

### 🚧 In Progress (Week 2 Sprint - Jan 2026)
- Customization Add-On feature for product editing
- Execution form updates (New/Existing checkbox + MM/DD/YY dates)
- Tab 3 Option A (HTML import): Parse variants from client order forms

---

## [7.5.1] - 2026-01-20

### Changed
- **Order Notes reorganization (Breaking Change)** - Restructured from 5 topic-based categories to 4 audience-based categories
  - **Old structure (5 categories):** Kitting Specs, Client Requests, Samples Required, Artwork Details, General Notes
  - **New structure (4 categories):**
    - Internal Notes (For PBP Team) - Team coordination, workflow notes, internal reminders
    - Internal Notes (For Bookkeeping) - Accounting, billing, payment tracking
    - External Notes (For Partners/POs) - Instructions for partners, PO details, shipping requirements
    - External Notes (For Clients/Invoices) - Client-facing information, special requests, delivery instructions
  - **UI improvements:**
    - Tab 3: Clean 2×2 layout (Internal row, External row)
    - Tab 4: All 4 categories displayed with clear section headers
    - Better organization by audience (internal vs external)
  - **Backward compatibility:** Old saved orders with 5-category notes are discarded on load (replaced with fresh 4-category structure)
  - **Test data only:** All existing saved orders contain test data, so no production data is lost

### Updated
- **Documentation** - Updated INVOICE_AND_PROPOSAL_SPEC.md with new order_notes structure
- **Test scripts** - Updated test_tab3_to_tab4_data_flow.py and test_saved_orders.py with new structure

---

## [7.5.0] - 2026-01-20

### Added
- **Product Variant Support** - Full schema update to support product variants (colors, flavors, sizes, etc.)
  - Added 2 new columns to schema: "Has Variants (Y/N)" and "Variant Type" (36 total columns, was 34)
  - **Tab 1 (Proposal Generator):**
    - Variant selector dropdown appears for products with variants
    - Warning shown if variant not selected (but still allows add)
    - Displays products as "Product/Service - Variant" format throughout
  - **Tab 3 (Order & Client Info):**
    - Manual product selection (Option C) includes variant selector
    - Current Order display shows product names with variant suffix
    - Variant data stored with each order item
  - **New helper functions in src/helpers.py:**
    - `has_variants()` - Checks if product has variants (Y/N flag)
    - `parse_variant_types()` - Parses variant list from "(x, y, z)" format
    - `format_product_with_variant()` - Formats display name as "Product - Variant"
- **Schema documentation updated** - Added variant columns to schema_reference.md with format examples
- **Backward compatibility** - Works with spreadsheets that don't have variant columns (defaults to N)

### Changed
- **Product display format** - All product names now show variant when applicable: "9oz Honey - Hot"
- **Variant consolidation support** - Products with same pricing can be consolidated into single row with variant list
  - Example: Instead of 4 separate rows (9oz Hot Honey, 9oz Elderberry Honey, etc.), use 1 row with Variant Type = "(Hot, Elderberry, Rosemary, Creamed)"
- **Proposal items structure** - Now includes `selected_variant` field (None if no variant selected)
- **Order items structure** - Now includes `selected_variant` field (None if no variant selected)

### Fixed
- **Tab 3 Option B:** Variant data now preserved when importing from proposals
- **Tab 4:** Product names in invoice/PO tables now include variant suffix
- **CSV exports:** Variants included in all CSV downloads
- **Saved data:** Proposals and orders automatically save/load variant selections via JSON

### Complete Variant Workflow
- ✅ Tab 1: Select variant and add to proposal
- ✅ Save/load proposals with variants (persisted to Google Sheets)
- ✅ Tab 3 Option B: Import from proposal preserves variants
- ✅ Tab 3 Option C: Manual selection includes variant selector
- ✅ Tab 3: Current Order displays product names with variants
- ✅ Save/load orders with variants (persisted to Google Sheets)
- ✅ Tab 4: Invoice/PO tables show variants in all 4 tables
- ✅ HTML/CSV exports include variants in product names

### Notes
- Future data migration: Will consolidate variant products into single rows with variant lists
- App supports BOTH old format (separate product rows) and new format (variants in one row) simultaneously
- PowerPoint generation already has multi-variant support (v6.13) - will work with new variant format
- Remaining: Tab 3 Option A (HTML import) variant parsing (future enhancement)

---

## [7.4.0] - 2026-01-08

### Added
- **Full schema update with backward compatibility** - Implemented new canonical pricing data schema (30 columns)
- **MOQ field support** - App now uses MOQ from spreadsheet when available, calculates otherwise
- **PBP Standard Markup field** - Partner-specific default markups replace hardcoded 100%
- **Dual tariff format support** - Handles both percentage (%) and dollar ($) tariff estimates
- **Backward compatibility helper** - `get_column_value()` function ensures seamless old→new transitions
- **Comprehensive documentation** - Added schema_reference.md and testing guides

### Changed
- **Column name updates** - All references updated to new canonical names with fallback support:
  - "MSRP" → "Vendor Published MSRP"
  - "Customization Setup Fee" → "Client Price: Customization Setup Fee"
  - "Customization Cost per Unit" → "Client Price: Customization Cost per Unit"
  - "Shipping Cost (PBP)" → "PBP Cost: Shipping Cost per Unit"
  - "Shipping Price (Client)" → "Client Price: Shipping Price per Unit"
  - "Tariff Rate" → "Tariff Estimate (%)" with fallback to "Tariff Estimate ($)"
- **Default markup logic** - Products now use PBP Standard Markup when available instead of hardcoded 100%

### Fixed
- **Critical: Streamlit query_params compatibility** - Fixed AttributeError with older Streamlit versions
- **Critical: pandas Series evaluation error** - Fixed ValueError in calculate_moq with DataFrame rows
- Both errors were blocking app functionality - now resolved

---

## [7.3.0] - 2025-12-20

### Added
- **Bidirectional price editing in Tab 3** - Users can now directly edit client price per unit, not just markup %
- **Directory reorganization** - Cleaner structure with organized docs/ and scripts/ folders

### Changed
- **NGO → Non-profit terminology** - Updated all references throughout the app for better inclusivity

### Fixed
- Critical error in Tab 3 where `new_markup` variable was undefined

---

## [7.2.0] - 2024-12-13

### Added
- **Multiple contacts support** - Dynamic add/remove functionality for multiple POCs
- **Partner POC investigation** - Debug logging and comprehensive test scripts
- **Comprehensive Tab 3→4 test suite** - Automated tests for data flow

### Fixed
- Partner POC pipeline - Corrected header row detection for different datasets
- Multiple contacts now display ALL contacts in Tab 4, not just primary

---

## [7.1.0] - 2024-12-11

### Added
- **Payment terms Net 15** - Added Net 15 and custom payment terms option
- **Editable product descriptions** - Tab 4 "Item + Specs" column now editable
- **Kitting Pricing section** - Separate PBP and client kitting costs
- **Improved Order Notes UX** - 5 always-visible text areas instead of dropdown
- **Sales tax field** - Estimated sales tax percentage input

### Fixed
- Tab 3 to Tab 4 data flow (4 critical issues resolved)
- Client info persistence in Tab 4
- Kitting costs now appear in invoice generation

---

## [7.0.0] - 2024-12-10

### Added
- **Search bar in Tab 1** - Quick product search functionality
- **Bidirectional price editing in Tab 1** - Edit markup or price directly
- **Cancel button for match changes** - Easy cancellation in PowerPoint matching
- **$0.50 rounding option** - All pricing tabs support fifty-cent rounding
- **Table restructuring** - PBP Cost vs Client Price columns in Tab 3

### Fixed
- Shipping columns in spreadsheet structure
- Price calculation accuracy with rounding

---

## [6.18.0] - 2024-11-20

### Added
- **Codebase simplification** - Removed 13,649 lines of obsolete code
- **Documentation cleanup** - Archived 23 completed planning docs
- **Code clarity improvements** - Renamed confusing functions, removed unused imports

### Technical
- Reduced codebase by 49% (now ~14,138 lines)
- Saved 22MB by removing deprecated files
- Improved beginner-friendliness

---

## [6.0.0 - 6.17.0] - 2024-11-05 to 2024-11-19

### Major Features
- **4-Tab Structure** - Split Tab 1 into Proposal Generator and Client Order Form
- **PowerPoint Automation** - Complete Phases 1 & 2 with 78.9% match accuracy
- **Saved Proposals/Orders** - Cloud-persistent save/load functionality
- **HTML Form Import** - Parse completed client forms (11 fields extracted)
- **Multi-variant PowerPoint** - Handle products with multiple variants
- **Units per Package** - Support for package-based pricing
- **Match Memory System** - Remember confirmed product-to-slide matches
- **MSRP Pricing** - Automatic markup calculation to match MSRP
- **Bulk Add Products** - Add all products from selected partners
- **Dataset Selector** - Switch between Demo and Real pricing data
- **Render Deployment** - Successfully deployed to production

### Infrastructure
- Cloud-based PowerPoint template loading
- Environment variable support for Render
- Memory optimization for 2GB RAM tier
- Scroll preservation system (95-98% effective)

---

## Version History

- **v7.x** - December 2024: Stakeholder feedback implementation
- **v6.x** - November 2024: PowerPoint automation & infrastructure
- **v5.x** - October 2024: Core order management
- **v4.x** - September 2024: Pricing engine implementation
- **v3.x** - August 2024: Google Sheets integration
- **v2.x** - July 2024: Basic Streamlit UI
- **v1.x** - June 2024: Initial prototype

---

## Statistics

### Codebase Size
- **Current:** ~14,138 lines of Python
- **Peak:** ~28,000 lines (before cleanup)
- **Reduction:** 49% smaller, more maintainable

### Features Completed
- **Critical Fixes:** 4/4 (100%)
- **High Priority:** 13/13 (100%)
- **Week 1 Sprint:** Complete
- **Week 2 Sprint:** 3/6 (50%)

### Testing Coverage
- **Core Tests:** 2 scripts
- **Feature Tests:** 19 scripts
- **Investigation Scripts:** 7 scripts
- **Total:** 28 test scripts

---

## Contributors
- Human Developer
- Claude AI Assistant (Co-Author)

---

## Links
- [Production App](https://pricing-data-solution-pbp.onrender.com)
- [Documentation](docs/README.md)
- [Active Development](ACTIVE_DEVELOPMENT_TODO.md)