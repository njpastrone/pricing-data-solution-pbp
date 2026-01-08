# Chrome Integration Testing Guide for Pricing Solution

## Overview

This guide explains how to use Claude Code's Chrome integration to automatically test the Pricing Data Solution PBP Streamlit application. With Chrome integration, Claude can test your web app directly in the browser, debug issues, verify UI functionality, and automate repetitive testing tasks.

### Key Benefits for Your Project
- **Automated Testing**: Test all 4 tabs without manual clicking
- **Live Debugging**: Claude reads console errors and fixes code immediately
- **Regression Testing**: Run comprehensive tests before each deployment
- **Visual Documentation**: Record GIFs of features for stakeholders
- **Form Validation**: Test HTML order forms and data imports
- **Pricing Verification**: Ensure calculations match business logic

## Prerequisites

Before setting up Chrome integration, ensure you have:

1. **Google Chrome browser** (required - not Brave, Arc, or other Chromium browsers)
2. **Claude in Chrome extension** v1.0.36+
   - Install from: https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn
3. **Claude Code CLI** v2.0.73+
   - Check version: `claude --version`
   - Update if needed: `claude update`
4. **Paid Claude plan** (Pro, Team, or Enterprise)

## Setup Instructions

### Step 1: Install Chrome Extension
1. Open Google Chrome
2. Go to Chrome Web Store and search for "Claude"
3. Install the official Claude extension by Anthropic
4. Ensure it's version 1.0.36 or higher

### Step 2: Update Claude Code
```bash
# Check current version
claude --version

# Update to latest (if needed)
claude update
```

### Step 3: Start Claude Code with Chrome
```bash
# Start with Chrome integration enabled
claude --chrome

# Or start normally and enable later with /chrome command
claude
# Then type: /chrome
```

### Step 4: Verify Connection
Once Claude Code is running, verify the Chrome connection:
```
/chrome
```
You should see:
- Connection status: Connected
- Extension version
- Available browser tools

## Testing Your Streamlit App

### Starting Your App for Testing
```bash
# In one terminal, start your Streamlit app
streamlit run app.py

# In Claude Code with Chrome enabled
claude --chrome
```

## Test Cases for Each Tab

### Tab 1: Proposal Generator Testing

#### Test Product Catalog Loading
```
Open localhost:8501 and verify:
1. Product catalog loads with all 19 demo products
2. Filter by Partner X shows correct products
3. Price filter (Client Budget) works correctly
4. Country of origin filter displays properly
```

#### Test Product Addition and Pricing
```
Test the proposal generation workflow:
1. Open localhost:8501
2. Add "Strawberry Jam - 8oz" from Partner X
3. Set markup to 150%
4. Verify client price updates correctly
5. Add "Olive Oil" with MSRP pricing enabled
6. Check that MSRP markup is auto-calculated
7. Generate proposal CSV and verify all pricing matches
```

#### Test Bulk Operations
```
Test bulk product addition:
1. Go to Tab 1 and expand Bulk Actions
2. Select Partner X and Partner Y
3. Click Add All Products
4. Verify success message shows correct count
5. Check that duplicates are prevented
6. Verify all products appear in proposal table
```

#### Test PowerPoint Generation
```
Test PowerPoint proposal generation:
1. Add 5 products to proposal
2. Click Generate PowerPoint Proposal
3. Review fuzzy matches and confirm
4. Check that presentation generates without errors
5. Verify download button appears
6. Check console for any errors
```

### Tab 2: Client Order Form Generator Testing

#### Test Form Generation
```
Test order form creation:
1. Go to Tab 2
2. Fill in client details:
   - Client Type: Company
   - Company Name: Test Corp
   - Contact: John Doe
   - Email: john@test.com
3. Click Update Order Form
4. Verify all fields appear in the HTML form
5. Download HTML and verify it opens correctly
```

#### Test Form Customization
```
Test template customization:
1. In Tab 2, go to Form Template Customization
2. Select "Dropshipping Instructions" from dropdown
3. Enter custom text: "Ship directly to our warehouse"
4. Update the form
5. Verify custom text appears in generated HTML
6. Test all 8 customizable fields
```

### Tab 3: Order & Client Info Testing

#### Test HTML Import (Option A)
```
Test importing completed order forms:
1. Go to Tab 3
2. Upload a completed HTML order form
3. Verify client info extraction shows all 11 fields
4. Check product extraction and matching
5. Click "Add Selected Products"
6. Verify products appear with correct settings
```

#### Test Proposal Import (Option B)
```
Test importing from proposal:
1. Create a proposal in Tab 1 with 3 products
2. Go to Tab 3
3. Click "Import All Products from Proposal"
4. Verify products transfer with markup preserved
5. Edit quantities and verify price updates
```

#### Test Manual Product Selection (Option C)
```
Test manual product addition:
1. In Tab 3, use the product dropdown
2. Enable "Use MSRP pricing"
3. Add a product with MSRP
4. Verify markup auto-calculates to match MSRP
5. Add a product without MSRP
6. Verify it defaults to 100% markup
```

#### Test Order Saving/Loading
```
Test order persistence:
1. Create an order with 3 products
2. Fill in client information
3. Save order as "Test Order v1"
4. Clear the page (refresh)
5. Load "Test Order v1"
6. Verify all data restored correctly
```

### Tab 4: Execution & Accounting Testing

#### Test Invoice Generation
```
Test invoice/PO creation:
1. Complete an order in Tab 3
2. Go to Tab 4
3. Verify all client info displays
4. Check partner POC auto-population
5. Generate invoice
6. Verify 4-table format is correct
7. Download CSV and HTML versions
```

#### Test Data Validation
```
Test field validation:
1. In Tab 4, leave required fields empty
2. Try to generate invoice
3. Verify warning messages appear
4. Fill in missing fields
5. Verify invoice generates successfully
```

## Automated Test Suites

### Pre-Deployment Checklist
```
Run this complete test before deploying to Render:

1. Start the app at localhost:8501
2. Test Tab 1:
   [ ] Products load correctly
   [ ] Filtering works (price, partner, country)
   [ ] Add individual products
   [ ] Bulk add products
   [ ] MSRP pricing checkbox works
   [ ] Proposal saves successfully
   [ ] PowerPoint generates

3. Test Tab 2:
   [ ] Client info form works
   [ ] Template customization saves
   [ ] HTML form generates
   [ ] Download works

4. Test Tab 3:
   [ ] HTML import extracts all fields
   [ ] Product matching works
   [ ] Proposal import transfers data
   [ ] Manual product add with MSRP
   [ ] Order saves/loads correctly

5. Test Tab 4:
   [ ] Client info displays
   [ ] Partner POC populated
   [ ] Invoice generates
   [ ] CSV export works
   [ ] HTML export works

6. Check console for any errors
7. Record a GIF of the full workflow
```

### Regression Testing After Changes
```
After modifying pricing logic, test:
1. Open localhost:8501
2. Add products with different tier quantities:
   - Qty 1 (minimum)
   - Qty 50 (mid-tier)
   - Qty 500 (high-tier)
3. Verify tier selection is correct
4. Test with 5% non-profit discount
5. Test marketing rounding ($60 -> $59)
6. Check customization calculations
7. Verify tariff calculations
8. Export CSV and verify all totals
```

### Feature-Specific Testing

#### After Updating Pricing Engine
```
Test pricing calculations:
1. Add product "Essential Oil Blend"
2. Set quantity to 100
3. Set markup to 75%
4. Add customization: $50 setup, $2 per unit
5. Apply 5% discount
6. Verify total matches expected calculation
7. Check console for calculation errors
```

#### After Modifying HTML Import
```
Test HTML parser:
1. Create order form with special characters
2. Export HTML from Tab 2
3. Manually edit some fields in the HTML
4. Import in Tab 3
5. Verify parser handles edge cases
6. Check for missing field warnings
```

## Debugging with Chrome Integration

### Reading Console Errors
```
Check for JavaScript errors:
1. Open the app
2. Navigate through all tabs
3. Tell me what errors appear in console
4. Filter for errors only (ignore warnings)
```

### Monitoring Network Requests
```
Check API calls to Google Sheets:
1. Open developer console Network tab
2. Reload the app
3. Tell me which Google Sheets requests are made
4. Check for any failed requests (status != 200)
```

### Testing Error Scenarios
```
Test error handling:
1. Try to generate PowerPoint with no products
2. Try to save order with no name
3. Try to import invalid HTML file
4. Verify appropriate error messages display
```

## Recording Demo GIFs

### Creating Feature Demonstrations
```
Record a GIF showing the new bulk add feature:
1. Start recording
2. Go to Tab 1
3. Show the Bulk Actions section
4. Select multiple partners
5. Add all products
6. Show the success message
7. Stop recording and save as bulk_add_demo.gif
```

### Documenting Workflows for Stakeholders
```
Record the complete order workflow:
1. Start recording
2. Create proposal in Tab 1
3. Generate order form in Tab 2
4. Import form in Tab 3
5. Generate invoice in Tab 4
6. Save as complete_workflow.gif
```

## Best Practices

### Writing Effective Test Prompts
1. **Be Specific**: Include exact field names and values
2. **Step-by-Step**: Break complex tests into numbered steps
3. **Verify Results**: Always ask Claude to confirm what it sees
4. **Check Console**: Include "check console for errors" in tests

### Handling Authentication
- Claude uses your browser's session cookies
- Log into Google Sheets before testing
- If authentication required, Claude will pause and ask

### Managing Test Data
```
Create consistent test data:
1. Use "Test Company ABC" for company names
2. Use test@example.com for emails
3. Use quantity 100 for standard testing
4. Use Partner X products for consistency
```

### Performance Testing
```
Test app performance:
1. Open the app and go to Tab 1
2. Time how long it takes to load all products
3. Add 10 products to proposal
4. Time the PowerPoint generation
5. Check if any operations take > 5 seconds
```

## Troubleshooting

### Chrome Extension Not Detected
1. Verify extension is installed and enabled
2. Restart Chrome completely
3. Run `claude --chrome` again
4. Try `/chrome` command and select "Reconnect"

### Browser Not Responding
- Check for JavaScript alerts blocking the page
- Ask Claude to open a new tab
- Restart Chrome if tabs become unresponsive

### Connection Lost During Testing
```
If connection drops:
1. Save your current test state
2. Run /chrome to reconnect
3. Resume testing from saved state
```

### Modal Dialogs Blocking
- Streamlit modals may block automation
- Manually dismiss any popups
- Tell Claude to continue after clearing

## Integration with Development Workflow

### Before Committing Code
```bash
# Run automated tests before commit
claude --chrome

# In Claude:
"Run the pre-deployment checklist on localhost:8501
and tell me if all tests pass"
```

### Testing Production Issues
```
When stakeholders report bugs:
1. Get exact steps to reproduce
2. Have Claude follow those steps
3. Check console for errors
4. Test the fix immediately
```

### Continuous Testing
```
Set up daily smoke tests:
1. Test critical path each morning
2. Verify data loads correctly
3. Test one complete order flow
4. Check for console errors
```

## Advanced Testing Scenarios

### Multi-Partner Order Testing
```
Test complex order with multiple partners:
1. Add products from Partner X, Y, and Z
2. Apply different markups to each
3. Add customization to Partner X products
4. Verify invoice shows all partners correctly
5. Check POC information for each partner
```

### Edge Case Testing
```
Test boundary conditions:
1. Order with quantity 0
2. Order with quantity 10,000
3. Markup of 0%
4. Markup of 1000%
5. Discount greater than total
6. Empty client information
7. Special characters in all fields
```

### Data Validation Testing
```
Test data consistency:
1. Create order in Tab 3
2. Save it
3. Generate invoice in Tab 4
4. Reload page
5. Load saved order
6. Regenerate invoice
7. Verify both invoices match exactly
```

## Quick Reference Commands

### Essential Test Commands
```
# Basic navigation test
"Open localhost:8501 and click through all 4 tabs"

# Quick smoke test
"Add one product and generate an invoice, checking for errors"

# Full regression test
"Run the pre-deployment checklist and report any failures"

# Debug specific issue
"Go to Tab 3, try importing HTML, and show me any console errors"

# Performance check
"Time how long each tab takes to load and report if any > 3 seconds"
```

### Common Fixes Claude Can Apply
```
# If test finds calculation error
"The client price is wrong. Check the pricing_engine.py
calculation and fix the markup formula"

# If UI element missing
"The Save Order button is not showing. Check why it's hidden
and fix the conditional display logic"

# If import fails
"HTML import is failing. Debug the parse_client_order_form_html
function and fix the extraction logic"
```

## Conclusion

Chrome integration transforms your testing workflow by:
- Automating repetitive test scenarios
- Catching bugs before production deployment
- Providing visual proof of features working
- Debugging issues in real-time
- Ensuring consistent quality

Use this guide to establish a robust testing practice that catches issues early and maintains high quality in your pricing solution application.

Remember: Always run the pre-deployment checklist before pushing to Render!