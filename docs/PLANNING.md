# Project Planning Document — Updated

## Admin Prompts / Non-Negotiables
- Always use Python for all development.  
- Leverage Streamlit for the front-end.  
- Write beginner-friendly code.  
- Always take the simplest route to solving problems.  
- Write code that can be read and understood by a beginner Python programmer — the entire app should be “vibe-coder friendly.”  
- Make autonomous decisions. Avoid asking for user permissions unless making dangerous changes.  
- When possible, minimize the size of the code base (number of files), keeping the project simple.  
- Avoid duplicating code.  
- Refer to markdown files for context consistently.  
- Do not be afraid to ask the user for questions or clarifications.  

---

## Project Overall Goal
Create a data solutions system for a small business to streamline the processes of:  
- Managing pricing data from partners  
- Creating quotes, proposals, and invoices  
- Basic bookkeeping  

---

## Project Goal Specifics
- Build a **Streamlit app** that reads a **single Master Google Sheet** as its source of truth.  
- The Master sheet contains consolidated pricing data for all products from all partners.  
- Users can:  
  - Select products from dropdowns  
  - Enter customizable options (markup percentage, shipping, tariffs, etc.)  
  - Calculate quotes, which can be used to generate proposals and invoices  

---

## Data & Partner Workflow — Simplified Approach A
**Process:**  
1. Each partner maintains their own **separate sheet**, **not connected to the app**.  
2. When a partner updates pricing, they send you the updated sheet (or a link to it).  
3. An internal team member **copies/pastes** the updated data into a **single Master Google Sheet**. This Master sheet is the only sheet that the app reads for quoting, proposals, and invoices.  

**Why it works:**  
- App reads from one source of truth → simple and stable.  
- Partners never get access to your internal system or Master sheet.  
- No automation is required, meaning **fewer moving parts** and **lower risk of errors**.  

**Optional future enhancements:**  
- Add “last updated” timestamps for each partner sheet.  
- Send notifications when partners submit updates.  
- Backup Master sheet before updates.  

---

## Current Phase
- **Phase 1 MVP - COMPLETE** ✅
- Successfully built working Streamlit app connected to jaggery_demo Google Sheet
- App includes product selection, quote calculation, and proposal/invoice generation
- **Multi-Product Ordering - COMPLETE** ✅
- Users can add multiple products to a single order
- Per-product markup configuration
- Order-level shipping and tariff costs
- Enhanced proposal and invoice for multi-product orders
- Ready for testing and user feedback  

---

## Requirements

### Functional Requirements
- Load product and pricing data from **Master Google Sheet**.  
- Display **dropdown menus** for selecting products.  
- Allow users to enter custom options: markup %, shipping, tariff costs, etc.  
- Calculate quotes in real-time.  
- Generate **proposals and invoices** based on selected products and calculated prices.  
- Admin interface for reviewing the Master sheet (optional: highlight missing or inconsistent data).  

### Technical Requirements
- Python + Streamlit for the app.  
- Use `gspread` or `pandas` with Google Sheets API to fetch Master sheet data.  
- Store Google service account credentials in **Streamlit secrets**.  
- Data stored entirely in Google Sheets (no local database required).  
- Simple, readable, beginner-friendly code.  

---

## Architecture Decisions
- Single **Master Google Sheet** as the app’s data source to simplify reading and calculations.  
- Separate partner sheets remain external — partners do not access Master.  
- Streamlit Cloud app fetches the Master sheet using a service account.  
- No SQLite or database required at this stage.  

---

## Implementation Plan

### Phase 1 — MVP ✅ COMPLETE
- [x] Set up Master Google Sheet with all required columns (jaggery_demo)
- [x] Set up Google Cloud service account and API access
- [x] Implement Google Sheets reading logic (`gspread` / `pandas`)
- [x] Build dropdowns and quote calculation logic in the app
- [x] Build basic proposal and invoice generator (on-screen tables)
- [x] Implement tiered pricing (7 tiers)
- [x] Add label costs and art setup fees
- [x] Multi-product ordering with add-to-cart pattern
- [x] Per-product markup configuration
- [x] Order-level shipping and tariff settings
- [ ] Deploy to Streamlit Cloud (pending)  

### Phase 2 — Optional Enhancements
- [ ] Add last-updated timestamps and partner tracking.  
- [ ] Implement a simple admin view to preview and validate Master sheet data.  
- [ ] Add backup/versioning of Master sheet.  
- [ ] Later: consider automating partner sheet ingestion or two-way QuickBooks sync.  

---

## Dependencies
- Python libraries: `streamlit`, `pandas`, `gspread`, `google-auth`  
- Google Sheets API enabled in a Google Cloud project  
- Streamlit Cloud hosting  

---

## Timeline
- MVP (Phase 1): 2–3 weeks  
- Optional enhancements (Phase 2): 2–4 weeks  
- Full rollout with multiple partners: after Phase 2 testing  

---

## Open Questions
- Should we add automated validation to catch formatting errors from partner sheets?
- How frequently will partner data change, and who will manage updates?
- ~~What columns are required in the Master sheet for Phase 1?~~ ✅ RESOLVED: Using Partner, Product, Price, Cost, Currency, Last Updated, Notes  

---

## Notes
- Focus on simplicity and maintainability for a single technical member.  
- Avoid complex syncing or database infrastructure at this stage.  
- All partner updates are manual — this keeps the system predictable and low-risk.
