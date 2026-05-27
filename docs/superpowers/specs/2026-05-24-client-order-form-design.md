# Client Order Form - In-App Design Spec

**Date:** 2026-05-24
**Status:** COMPLETE (shipped v8.4.0, 2026-05-27)
**Replaces:** Google Forms workflow (kept as legacy fallback)

---

## Problem Statement

The current Google Forms-based client order form has three blocking issues:

1. **Google sign-in required for file uploads** -- many B2B clients don't have Google accounts, and we need file uploads for dropshipping address spreadsheets
2. **Product list maintenance** -- product options must be manually updated in the Google Form whenever the catalog changes; no way to tie the form to a specific proposal
3. **No file upload for dropshipping addresses** -- can't collect address spreadsheets without requiring Google sign-in

## Solution

Build a client-facing form page within the existing Streamlit app, accessed via a unique shareable link. The form pulls live product data from a saved proposal, supports file uploads without sign-in, and allows clients to save progress and return later.

## Architecture

### Routing

At the top of `app.py`, check for query parameters before rendering the normal 4-tab app:

```python
params = st.query_params
if "client_form" in params:
    render_client_form(params["client_form"], params.get("session"))
    st.stop()
```

When `client_form` is present, the app renders a clean, single-page form with no sidebar, no tabs, and no internal tools visible. `st.stop()` prevents the rest of `app.py` from executing.

### URL Format

```
https://pricing-data-solution-pbp.onrender.com/?client_form=PROP_20260524_143022&session=abc123
```

- `client_form` = proposal ID (from `saved_proposals` sheet)
- `session` = unique token generated per link, enables multiple clients per proposal

### Data Flow

```
Exec (Tab 2)                    Client (form page)                  Exec (Tab 3)
     |                                |                                  |
     |-- Generate Link -------------->|                                  |
     |   (saves client info           |                                  |
     |    to draft sheet)             |                                  |
     |                                |-- Opens link                     |
     |                                |-- Loads proposal products        |
     |                                |-- Loads draft (if exists)        |
     |                                |-- Fills form                     |
     |                                |-- Save Progress (optional)       |
     |                                |   (writes to drafts sheet)       |
     |                                |-- Submit Order                   |
     |                                |   (writes to Form Responses 1)  |
     |                                |                                  |
     |                                |                                  |-- Load Responses
     |                                |                                  |-- Import (same as today)
```

## Form Sections (Client View)

The form mirrors the existing Google Form fields exactly.

### Header
- Title: "PBP Client Order Form"
- Proposal name displayed
- Draft save status indicator ("Draft saved 2 min ago")

### Section 1: Client Information (pre-filled, editable)
- Client Type
- Company Name *
- Contact Name *
- Contact Email *
- Contact Phone

Pre-filled from what the exec entered in Tab 2. Client can edit if needed.

### Section 2: Products & Quantities
- Product cards pulled live from the saved proposal (not a dropdown)
- Each card shows: product name, partner name
- Editable fields per product: Quantity *, Customization Notes
- No product limit (shows all products in the proposal)
- No pricing information visible (no costs, markup, or MSRP)

### Section 3: Shipping & Delivery
- Shipping Address *
- Billing Address (if different)
- Drop-shipping? * (Yes/No)
- Drop-shipping Instructions (text, conditional on Yes)
- Drop-shipping Address File upload (accepts .xlsx, .csv -- no sign-in required)
- In-Hands Date *

### Section 4: Payment & Preferences
- Impact Cards? (Yes/No)
- Impact Card Selection (conditional on Yes)
- Payment Preference * (Net 30, Net 60, etc.)
- Payment Method * (Credit Card, ACH, Check)

### Section 5: Additional Notes
- Special Requests, Notes, or Questions (free text)

### Action Buttons
- **Save Progress** -- persists all current form data to drafts sheet
- **Submit Order** -- validates required fields, writes to response sheet, shows confirmation

## Data Storage

### Google Sheets

**Existing (no changes):**
- `saved_proposals` -- read by client form to load products
- `Form Responses 1` -- where final submissions are written (same destination as Google Form)

**New:**
- `client_form_drafts` -- stores in-progress form data

### Draft Sheet Structure

| Column | Description |
|--------|-------------|
| Proposal_ID | Links to saved proposal |
| Session_ID | Unique per-link token |
| Draft_Data_JSON | All form fields serialized as JSON |
| File_Data_Base64 | Uploaded file stored as base64 (chunked if needed) |
| File_Name | Original filename of uploaded file |
| Created_Date | When draft was first created |
| Updated_Date | Last save timestamp |
| Status | "draft" or "submitted" |

### Response Sheet Integration

When the client clicks Submit, the form data is written to `Form Responses 1` in the same column format that the Google Form uses. This means:

- Tab 3's "Load Form Responses" works without changes
- `parse_form_response()` in `forms_helper.py` works without changes
- `mark_response_imported()` works without changes
- The uploaded file gets an additional column (e.g., "Dropshipping File Name") with a reference to retrieve the file

### File Upload Storage

Uploaded dropshipping address files are stored as base64 in the drafts sheet, using the same chunking pattern as `drive_helper.py` (product photo storage). On import in Tab 3, the exec can download the file.

## Exec-Side Changes

### Tab 2: New Section

Add **"Section 2: Generate Client Order Form Link"** above the existing Google Form section.

UI flow:
1. Product selection (checkboxes + quantity spinners, same as current Google Form section)
2. Client info from Section 1 (same as today)
3. "Generate Client Form Link" button
4. Displays URL in text box with copy button
5. Each click generates a new session token (supports multiple clients per proposal)

The proposal must be saved before generating a link. If unsaved, the app shows a warning: "Please save your proposal first before generating a client form link."

### Tab 2: Google Form Section (Legacy)

Keep the existing Google Form section as-is, below the new section. Can be collapsed in an expander with a note like "Legacy: Google Form (alternative)".

### Tab 3: Import Changes

Minimal changes:
- Response import works as-is (reads from same sheet)
- Add file download button when a response includes an uploaded dropshipping file

## New Module: src/client_form.py

Handles all client form logic, keeping `app.py` focused on UI:

- `load_proposal_for_client(proposal_id)` -- loads proposal data, returns product list (no pricing info)
- `load_draft(proposal_id, session_id)` -- loads saved draft from sheets
- `save_draft(proposal_id, session_id, form_data, file_data)` -- writes/updates draft
- `submit_form(proposal_id, session_id, form_data, file_data)` -- writes to response sheet, marks draft as submitted
- `generate_session_token()` -- creates unique session ID for link
- `store_uploaded_file(file_bytes, filename)` -- converts to base64 for storage
- `retrieve_uploaded_file(proposal_id, session_id)` -- returns file bytes + filename for download

## Security & Edge Cases

| Scenario | Behavior |
|----------|----------|
| Proposal deleted after link sent | Friendly error: "This form is no longer available. Please contact your PBP representative." |
| Proposal products updated | Client sees updated product list (live data) |
| Client submits twice | Each submit creates a new response row. Exec sees both in Tab 3. |
| File upload too large | Streamlit's default 200MB limit enforced |
| Client leaves without saving | Unsaved data lost. "Save Progress" is the safety net. |
| Link shared/forwarded | Works -- anyone with the link can fill it out (same as Google Forms) |
| Two clients, same proposal | Different session tokens = independent drafts and submissions |
| Invalid proposal ID or session | Friendly error message |

**Not in scope (keeping it simple):**
- No authentication or login for clients
- No email notifications on submission
- No real-time collaboration on same link
- No form expiration dates
- No edit-after-submit (client contacts exec)

## Streamlit Configuration (Client Mode)

When in client form mode, hide Streamlit chrome:

```python
st.set_page_config(page_title="PBP Client Order Form", layout="centered")
# Hide sidebar, hamburger menu, footer
st.markdown("""<style>
    [data-testid="stSidebar"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)
```

## Compatibility

- Works on the existing Render deployment (no new services)
- Same Google Sheets credentials and service account
- Same `gspread` library for sheet operations
- Reuses `drive_helper.py` patterns for file storage
- Reuses `proposal_manager.py` for loading proposal data
- Response format compatible with existing Tab 3 import flow
