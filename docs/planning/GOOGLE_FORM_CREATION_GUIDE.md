# Google Form Creation Guide for Gemini AI

**Purpose:** Create a Google Form for Peace by Piece International client order collection
**Form Name:** PBP Client Order Form - Master
**Date:** 2026-01-20

---

## Instructions for Gemini

Please help me create a Google Form with the exact structure specified below. I need this form to collect client order information where executives will pre-fill some fields (client info, products) and clients will complete the remaining fields (shipping, payment).

---

## Form Configuration

**Form Title:** PBP Client Order Form - Master

**Form Description:**
```
Welcome! This order form has been customized for you by Peace by Piece International.

Some information has been pre-filled based on our conversation. Please review the pre-filled information and complete the remaining sections.

Required fields are marked with an asterisk (*).
```

**Settings to Configure:**
- ✅ Collect email addresses
- ✅ Allow response editing (respondents can edit after submit)
- ✅ Show progress bar
- ✅ Limit to 1 response (per email)
- ❌ Require sign-in (keep public)
- ✅ Show link to submit another response (in confirmation message)

**Confirmation Message:**
```
Thank you for submitting your order!

Your Peace by Piece International team will review your order and contact you shortly to confirm details and provide next steps.

If you need to make changes, you can edit your response using the link sent to your email.

Questions? Contact your PBP representative.
```

---

## Form Structure

### SECTION 1: Client Information

**Section Title:** Client Information
**Section Description:** Pre-filled by your PBP representative. Please verify this information is correct.

---

**Question 1:**
- **Type:** Multiple choice (dropdown)
- **Question Text:** Client Type *
- **Options:**
  - New
  - Existing
- **Required:** Yes
- **Help Text:** Are you a new client or returning client?

---

**Question 2:**
- **Type:** Short answer
- **Question Text:** Company Name *
- **Required:** Yes
- **Validation:** None
- **Help Text:** Your organization or business name

---

**Question 3:**
- **Type:** Short answer
- **Question Text:** Contact Name *
- **Required:** Yes
- **Validation:** None
- **Help Text:** Primary contact person for this order

---

**Question 4:**
- **Type:** Short answer
- **Question Text:** Contact Email *
- **Required:** Yes
- **Validation:** Email
- **Help Text:** We'll send order confirmations to this email

---

**Question 5:**
- **Type:** Short answer
- **Question Text:** Contact Phone
- **Required:** No
- **Validation:** None
- **Help Text:** Optional - for urgent order updates

---

### SECTION 2: Order Details

**Section Title:** Order Details
**Section Description:** Products pre-selected based on our discussion. You may adjust quantities or add additional products from the dropdown.

**Important:** For each product line below, there are 3 fields:
1. Product Name (dropdown)
2. Quantity (number)
3. Customization Notes (optional text)

If a product line is pre-filled, please verify the quantity. If you don't need a line, leave it blank.

---

#### Product Line 1

**Question 6:**
- **Type:** Dropdown
- **Question Text:** Product Line 1 - Product Name
- **Options:** [SEE PRODUCT LIST BELOW - Insert all 133 products]
- **Required:** No
- **Help Text:** Select a product or leave blank if not needed

**Question 7:**
- **Type:** Short answer
- **Question Text:** Product Line 1 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1
- **Help Text:** Minimum order quantities may apply

**Question 8:**
- **Type:** Paragraph (long answer)
- **Question Text:** Product Line 1 - Customization Notes
- **Required:** No
- **Help Text:** Optional: Custom branding, packaging, label text, etc.

---

#### Product Line 2

**Question 9:**
- **Type:** Dropdown
- **Question Text:** Product Line 2 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 10:**
- **Type:** Short answer
- **Question Text:** Product Line 2 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 11:**
- **Type:** Paragraph
- **Question Text:** Product Line 2 - Customization Notes
- **Required:** No

---

#### Product Line 3

**Question 12:**
- **Type:** Dropdown
- **Question Text:** Product Line 3 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 13:**
- **Type:** Short answer
- **Question Text:** Product Line 3 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 14:**
- **Type:** Paragraph
- **Question Text:** Product Line 3 - Customization Notes
- **Required:** No

---

#### Product Line 4

**Question 15:**
- **Type:** Dropdown
- **Question Text:** Product Line 4 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 16:**
- **Type:** Short answer
- **Question Text:** Product Line 4 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 17:**
- **Type:** Paragraph
- **Question Text:** Product Line 4 - Customization Notes
- **Required:** No

---

#### Product Line 5

**Question 18:**
- **Type:** Dropdown
- **Question Text:** Product Line 5 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 19:**
- **Type:** Short answer
- **Question Text:** Product Line 5 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 20:**
- **Type:** Paragraph
- **Question Text:** Product Line 5 - Customization Notes
- **Required:** No

---

#### Product Line 6

**Question 21:**
- **Type:** Dropdown
- **Question Text:** Product Line 6 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 22:**
- **Type:** Short answer
- **Question Text:** Product Line 6 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 23:**
- **Type:** Paragraph
- **Question Text:** Product Line 6 - Customization Notes
- **Required:** No

---

#### Product Line 7

**Question 24:**
- **Type:** Dropdown
- **Question Text:** Product Line 7 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 25:**
- **Type:** Short answer
- **Question Text:** Product Line 7 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 26:**
- **Type:** Paragraph
- **Question Text:** Product Line 7 - Customization Notes
- **Required:** No

---

#### Product Line 8

**Question 27:**
- **Type:** Dropdown
- **Question Text:** Product Line 8 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 28:**
- **Type:** Short answer
- **Question Text:** Product Line 8 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 29:**
- **Type:** Paragraph
- **Question Text:** Product Line 8 - Customization Notes
- **Required:** No

---

#### Product Line 9

**Question 30:**
- **Type:** Dropdown
- **Question Text:** Product Line 9 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 31:**
- **Type:** Short answer
- **Question Text:** Product Line 9 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 32:**
- **Type:** Paragraph
- **Question Text:** Product Line 9 - Customization Notes
- **Required:** No

---

#### Product Line 10

**Question 33:**
- **Type:** Dropdown
- **Question Text:** Product Line 10 - Product Name
- **Options:** [SAME PRODUCT LIST]
- **Required:** No

**Question 34:**
- **Type:** Short answer
- **Question Text:** Product Line 10 - Quantity
- **Required:** No
- **Validation:** Number, Must be at least 1

**Question 35:**
- **Type:** Paragraph
- **Question Text:** Product Line 10 - Customization Notes
- **Required:** No

---

### SECTION 3: Shipping & Delivery

**Section Title:** Shipping & Delivery
**Section Description:** Please provide shipping details and your target delivery date.

---

**Question 36:**
- **Type:** Paragraph (long answer)
- **Question Text:** Shipping Address *
- **Required:** Yes
- **Help Text:** Full address including street, city, state, ZIP code
- **Placeholder:** 123 Main Street, Suite 100, San Francisco, CA 94102

---

**Question 37:**
- **Type:** Paragraph
- **Question Text:** Billing Address (if different from shipping)
- **Required:** No
- **Help Text:** Leave blank if same as shipping address
- **Placeholder:** 456 Billing Ave, Los Angeles, CA 90012

---

**Question 38:**
- **Type:** Dropdown
- **Question Text:** Will this order be drop-shipped? *
- **Options:**
  - No - Ship to address above
  - Yes - Ship directly to my customer(s)
- **Required:** Yes
- **Help Text:** Drop-shipping means we ship directly to your customer instead of to you

---

**Question 39:**
- **Type:** Paragraph
- **Question Text:** Drop-Shipping Instructions
- **Required:** No
- **Conditional Logic:** ONLY SHOW if Q38 = "Yes - Ship directly to my customer(s)"
- **Help Text:** Provide customer addresses and any special shipping instructions
- **Placeholder:**
```
Customer 1: Jane Doe, 789 Customer St, Seattle, WA 98101
Customer 2: John Smith, 321 Buyer Rd, Portland, OR 97201
```

---

**Question 40:**
- **Type:** Date
- **Question Text:** In-Hands Date (When do you need this order?) *
- **Required:** Yes
- **Validation:** Date must be at least 7 days in the future
- **Help Text:** Target delivery date - we'll work to meet this timeline

---

### SECTION 4: Impact & Payment

**Section Title:** Impact Cards & Payment Preferences
**Section Description:** Final details about impact cards and payment terms.

---

**Question 41:**
- **Type:** Dropdown
- **Question Text:** Would you like Impact Cards included?
- **Options:**
  - No impact cards needed
  - Yes - Include impact cards for each artisan partner
- **Required:** No
- **Help Text:** Impact cards tell the story of the artisan partners who made your products

---

**Question 42:**
- **Type:** Checkboxes (multiple selection)
- **Question Text:** Impact Card Selection
- **Options:**
  - Partner A Impact Cards
  - Partner B Impact Cards
  - Partner C Impact Cards
  - Partner D Impact Cards
  - All Partners
- **Required:** No
- **Conditional Logic:** ONLY SHOW if Q41 = "Yes - Include impact cards for each artisan partner"
- **Help Text:** Select which partner stories you'd like to include

---

**Question 43:**
- **Type:** Dropdown
- **Question Text:** Payment Preference *
- **Options:**
  - Net 30 (Payment due 30 days after invoice)
  - Net 60 (Payment due 60 days after invoice)
  - Net 15 (Payment due 15 days after invoice)
  - Due on Receipt (Payment due immediately)
  - 50% Deposit + 50% on Delivery
  - Other (specify in notes below)
- **Required:** Yes
- **Help Text:** Standard payment terms

---

**Question 44:**
- **Type:** Dropdown
- **Question Text:** Payment Method *
- **Options:**
  - Check
  - ACH / Bank Transfer
  - Credit Card
  - Wire Transfer
  - Other (specify in notes below)
- **Required:** Yes
- **Help Text:** How will you be paying for this order?

---

### SECTION 5: Additional Information

**Section Title:** Additional Notes & Special Requests
**Section Description:** Any other information we should know about this order?

---

**Question 45:**
- **Type:** Paragraph (long answer)
- **Question Text:** Special Requests, Notes, or Questions
- **Required:** No
- **Help Text:** Examples: rush delivery needed, specific packaging requirements, artwork specifications, sample requests, etc.
- **Placeholder:**
```
- Need rush delivery for event on March 15th
- Please include 5 extra samples for sales team
- Custom logo artwork attached separately via email
```

---

## Product List for All Dropdowns

**Instructions:** Use this exact list for ALL "Product Name" dropdown questions (Questions 6, 9, 12, 15, 18, 21, 24, 27, 30, 33)

**Important:** Products should be listed alphabetically in the dropdown for easy searching.

### Complete Product List (Insert into ALL Product Name dropdowns):

```
(Leave blank - no product for this line)
9 oz Creamed Honey
9 oz Elderberry Honey
9 oz Hot Honey
9 oz Rosemary Honey
'Warsh' Bar
BAY RUM ESSENCE
BOTANICAL BODY OIL
Bath Bomb
CINNAMON PUMPKIN LIP BALM
CITRUS VANILLA LIP BALM
Da' Balm- Beard Salve
Dem' Lips Moisturizer
Detox Face Mask
Face Mask Bundle
HAIR & BEARD OIL
HAND SALVE (1 oz)
HAND SALVE (4 oz)
Hon's Healing Ointment
Hon's Lotion Bar
Honey Sampler (3oz)
HONEY SHEA LOTION
Hydrate Face Mask
LAVENDER BATH TEA 4 PK
LAVENDER ESSENCE
LAVENDER LOTION
LAVENDER MINT LIP BALM
Large Beeswax Candle
Medium Beeswax Candle
Mountain Blanket
Product Y
Raw, Local Honey (16oz)
Rectangular Cosmetics Bag (Cotton Canvas)
Rectangular Cosmetics Bag (Traditional Guatemalan Textile)
ROSEMARY MINT LOTION
Shuga' Scrub
Small Beeswax Candle (New Design!)
SOOTHING FLORAL BATH TEA 4 PK
Specialty Honey Flight
SWEET PEA LOTION
THERAPEUTIC BATH TEA 4 PK
Tote Bag (Muslin Fabric)
Tote Bag (Palacio Fabric)
TRIBLEND LS HOODED TEE
TRIBLEND LS TEE
TRIBLEND SHORT SLEEVE
TRIBLEND V NECK
UNISEX 50/50 FLEECE HOOD
UNISEX 80/20 FLEECE HOOD
UNISEX RIB BEANIE
VANILLA SUGAR LOTION
WILD VERBENA LOTION
```

**Total Products:** 51 products (alphabetically sorted from master_pricing dataset)

**Note:** This is the actual product list from the master_pricing spreadsheet (real dataset) as of January 2026.

---

## After Creating the Form

### Step 1: Link to Google Sheet

1. In form editor, click "Responses" tab
2. Click the Google Sheets icon (green spreadsheet)
3. Select "Create a new spreadsheet"
4. Name it: "PBP Client Order Responses"
5. Click "Create"

### Step 2: Add Tracking Columns to Response Sheet

Open the newly created response sheet and add these columns at the end (after all the auto-generated columns):

1. Column Header: `Imported?` (leave all rows blank initially)
2. Column Header: `Order ID` (leave all rows blank initially)
3. Column Header: `Imported By` (leave all rows blank initially)
4. Column Header: `Import Date` (leave all rows blank initially)

### Step 3: Get Form URLs

Provide these to your developer:

1. **Form Edit URL:** (the URL you see when editing the form)
2. **Form Public URL:** Click "Send" button → Get shareable link
3. **Response Sheet URL:** (the Google Sheet that was created)

### Step 4: Find Entry IDs

**Option A - Manual Method:**

For EACH question in the form:
1. Open form preview (eye icon)
2. Right-click on the input field → Inspect Element
3. In the HTML, find: `<input name="entry.XXXXXXXXXX">`
4. Record: Question Name → entry.XXXXXXXXXX

**Option B - Automated Method (Recommended):**

1. Open form preview
2. Open browser console (F12 → Console tab)
3. Paste and run this JavaScript:

```javascript
// Extract all entry IDs from Google Form
const entries = {};
document.querySelectorAll('[name^="entry."]').forEach(field => {
    const label = field.closest('[role="listitem"]')?.querySelector('[role="heading"]')?.textContent || 'Unknown';
    entries[label.trim()] = field.name;
});
console.table(entries);
copy(JSON.stringify(entries, null, 2));
```

4. Entry IDs will be copied to clipboard in JSON format
5. Paste into a text file and send to your developer

### Step 5: Share Response Sheet

Share the response Google Sheet with your service account email:
- Email: `your-service-account@your-project.iam.gserviceaccount.com`
- Permission: Editor
- (This is the same service account used for the pricing data)

---

## Testing the Form

Before sending to your developer:

1. **Fill out the form** with test data
2. **Submit** and verify response appears in Sheet
3. **Edit your response** (test the edit functionality)
4. **Check all conditional logic** (Q39 only shows if Q38 = Yes, Q42 only shows if Q41 = Yes)
5. **Verify validation** (email validation, number validation, date validation)

---

## Maintenance Notes

**Monthly Product Updates:**

When new products are added to your catalog:
1. Open form in edit mode
2. Find ALL 10 "Product Name" dropdown questions (Q6, Q9, Q12, Q15, Q18, Q21, Q24, Q27, Q30, Q33)
3. Add new product to EACH dropdown
4. Save form

**Do NOT:**
- ❌ Change question order (will break entry ID mapping)
- ❌ Delete questions (will break entry ID mapping)
- ❌ Change question titles (will break parsing)
- ❌ Change field types (text → dropdown, etc.)

**OK to change:**
- ✅ Add new dropdown options (products)
- ✅ Update help text
- ✅ Update section descriptions
- ✅ Update confirmation message

---

## Summary Checklist

After completing form creation, you should have:

- [ ] Google Form created with 45 questions across 5 sections
- [ ] All product dropdowns populated with full product list
- [ ] Form linked to response Google Sheet
- [ ] Tracking columns added to response sheet (4 columns)
- [ ] Form settings configured (collect email, allow editing, etc.)
- [ ] Form tested with sample submission
- [ ] Form public URL obtained
- [ ] Response sheet URL obtained
- [ ] Entry IDs extracted (all 45 questions)
- [ ] Response sheet shared with service account
- [ ] All URLs and entry IDs documented and ready to send to developer

---

## Questions or Issues?

If Gemini encounters any issues or needs clarification:

1. **Product list:** Use the sample list provided, or ask for actual product catalog
2. **Conditional logic:** Q39 shows only if Q38 = Yes, Q42 shows only if Q41 = Yes
3. **Field validation:** Email format for Q4, number ≥1 for all quantity fields, date must be future for Q40
4. **Required fields:** Q1-Q4, Q36, Q38, Q40, Q43, Q44 are required. All others optional.

---

**End of Instructions**

This comprehensive guide should allow Gemini to create the exact Google Form structure needed for the PBP client order collection system.
