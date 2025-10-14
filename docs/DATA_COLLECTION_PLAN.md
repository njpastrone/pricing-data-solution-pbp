# 📘 Data Collection and Computation Plan

This document defines **which data points** are required for each deliverable, and specifies **their sources**:
- **Spreadsheet:** Pulled directly from the master workbook (`Partner Specific Pricing Template.xlsx`)
- **App Input:** Entered manually by the internal user via the app interface
- **App Calculation:** Computed dynamically by the app based on inputs and spreadsheet data

---

## 🧾 Invoice / Invoice Details Sheet

| Data Field | Spreadsheet | App Input | App Calculation | Notes |
|-------------|--------------|------------|------------------|-------|
| Product/Service | ✅ |  |  | Pulled from partner/product selection |
| Purchase Description | ✅ |  |  | Product description text |
| Unit Cost (actual sale price) | ✅ | ✅ | ✅ | Depends on pricing tiers and customization |
| Artwork Setup Fee? | ✅ |  |  | From spreadsheet; may be customized per partner |
| Customization Costs | ✅ |  |  | From spreadsheet; per-unit or setup-based |
| Shipping (to client) |  | ✅ |  | Input by user at quote/invoice stage |
| Total Cost (to client) |  |  | ✅ | Calculated based on all components |

---

## 💼 Proposals

| Data Field | Spreadsheet | App Input | App Calculation | Notes |
|-------------|--------------|------------|------------------|-------|
| MOQ (Minimum Order Quantity) |  |  | ✅ | **Calculated based on a minimum total order value of $1,000 per product.** Formula: `MOQ = ceil(1000 / Unit Cost)` |
| Cost at MOQ |  |  | ✅ | Computed as `MOQ × Unit Cost`, ensuring total ≥ $1,000 |

**Logic Notes:**
- The MOQ ensures that each proposal meets the $1,000 minimum order value threshold for each product.
- If a product has tiered pricing, the app should determine which tier applies to the MOQ quantity and price accordingly.

---

## 📦 Purchase Order

| Data Field | Spreadsheet | App Input | App Calculation | Notes |
|-------------|--------------|------------|------------------|-------|
| Quantity Ordered |  | ✅ |  | User-entered quantity |
| Unit Cost (actual sale price) |  |  | ✅ | Derived from pricing tiers and customization |
| Client Name |  | ✅ |  | User-entered client reference |

---

## 🧭 Order Information (Shared for Invoice / IDS)

| Data Field | Spreadsheet | App Input | App Calculation | Notes |
|-------------|--------------|------------|------------------|-------|
| New/Existing Client? |  | ✅ |  | Boolean selector |
| Company Name |  | ✅ |  |  |
| Contact Name |  | ✅ |  |  |
| Contact Email |  | ✅ |  |  |
| Client PO (if available) |  | ✅ |  |  |
| Billing Address |  | ✅ |  |  |
| Shipping Details (one location vs. drop shipping) |  | ✅ |  | Option selector |
| Shipping Address (if one location) |  | ✅ |  |  |
| Payment Timeline |  | ✅ |  | E.g. 50% upfront, 50% on delivery |
| Payment Preference |  | ✅ |  | E.g. Wire, Credit Card, etc. |
| Quantity Ordered |  | ✅ |  |  |
| Unit Cost (actual sale price) |  |  | ✅ | Derived from pricing logic |

---

## ⚙️ Other Considerations (Still Under Review)

| Data Field | Spreadsheet | App Input | App Calculation | Notes |
|-------------|--------------|------------|------------------|-------|
| Tariff Estimates | ✅ |  |  | From spreadsheet, varies by product origin |
| Credit Card Fees |  |  | ✅ | Calculated as % of total if applicable |

---

## 🔍 Summary

This data model supports three main deliverables:
1. **Invoices / Invoice Detail Sheets** — Combine spreadsheet pricing logic with user-entered shipping/customization.
2. **Proposals** — Estimate costs and MOQ-based pricing using the $1,000 minimum order value rule.
3. **Purchase Orders** — Link client and quantity data to compute final sale price.

The app should:
- **Read** static product and pricing data from the spreadsheet.
- **Collect** client and order info from internal users.
- **Compute** dynamic pricing, tariffs, MOQs, and totals.
- **Output** structured deliverables (proposals, POs, invoices) using consistent field names.

---

