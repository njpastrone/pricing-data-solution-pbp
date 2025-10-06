# Client Questions

This document tracks unanswered questions about features and requirements to ask the client.

---

## Invoice & Quote Generation

### 1. Invoice Description Column Content
**Question:** What should be included in the description column for invoices?

**Current Implementation:**
- Description shows: `"Product Ref: {ref}, Partner: {partner}"`
- Example: "Product Ref: JA01, Partner: Jaggery"

**Options to Consider:**
- Keep current format (Product Ref + Partner)
- Add product details (e.g., size, flavor, packaging)
- Add custom notes field per product
- Make description customizable/editable

**Status:** Awaiting client feedback

---

## Feature Requests

### 2. Save Quote Feature (Across Sessions)
**Question:** Is a "save quote" feature (across sessions) helpful?

**Current Implementation:**
- Quotes can be saved to "Recent Orders" history
- History is session-based (clears when app restarts)
- Users can load saved quotes within the same session

**Proposed Enhancement:**
- Persist saved quotes across sessions
- Store quotes in Google Sheets or local database
- Allow users to search/filter saved quotes
- Add quote naming/labeling functionality

**Considerations:**
- Where to store persistent quotes (Google Sheets vs database)?
- What metadata to track (date, client name, quote number)?
- How long to retain saved quotes?
- Do we need quote versioning/editing history?

**Status:** Awaiting client feedback

---

## Instructions for Use

**When adding new questions:**
1. Add questions under relevant section headings
2. Include current implementation context
3. List options or considerations if applicable
4. Mark status as "Awaiting client feedback"

**When questions are answered:**
1. Update status to "Answered - [Date]"
2. Document the client's decision
3. Create implementation task if needed
4. Move to "Resolved Questions" section at bottom

---

## Resolved Questions

(None yet)
