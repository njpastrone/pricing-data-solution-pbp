# Debugging "Refresh Data" Issues

If you're not seeing updated data after clicking "Refresh Data", follow these steps:

## Step 1: Verify Your Changes in Google Sheets

1. Open the Google Sheet in your browser
2. Verify your changes are **saved** (not just in edit mode)
3. Check you're editing the correct spreadsheet:
   - **Demo:** master_pricing_template_10_14
   - **Real:** master_pricing (currently selected)
4. Verify changes are in the **"Data" sheet** (not Metadata or Partner-Specific Info)
5. Verify changes are in **row 8 or below** (row 7 is the header)

## Step 2: Check Current App Data

1. In the sidebar, expand **"🔍 Debug: Current Data Details"**
2. Note the following:
   - Products loaded: _____
   - First product: _____
   - Last product: _____
   - Dataset: _____
   - Last manual refresh: _____

## Step 3: Run Debug Script

```bash
streamlit run scripts/debug_refresh_data.py
```

This will:
- Show cached data
- Show session state data
- Read directly from Google Sheets (bypassing cache)
- Compare all three sources
- Identify where the mismatch is

## Step 4: Click "Refresh Data" and Check Output

When you click "Refresh Data", you should see:
1. "🔄 Clearing cache..."
2. "📥 Fetching fresh data from Google Sheets..."
3. "✅ Data refreshed! Products: X → Y"
4. If first product changed: "🔍 First product changed: 'Old' → 'New'"

**If you don't see these messages:**
- The button might be disabled (30-second cooldown)
- Check the cooldown timer below the button

## Step 5: Compare Before/After

**Before refresh:**
- Products: _____
- First product: _____

**After refresh:**
- Products: _____
- First product: _____

**Changed?** Yes / No

## Step 6: Browser Cache

If data still hasn't updated:

1. **Hard refresh:** Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. **Clear browser cache:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Firefox: Settings → Privacy → Clear Data → Cached Web Content
3. **Restart browser** (close all windows)

## Step 7: Check Specific Field

**What field did you change?**
- Column name: _____
- Row number: _____
- Old value: _____
- New value: _____

**Is this column loaded by the app?**

Run debug script and check if your column appears in the data. Some columns might not be loaded.

## Step 8: Check for Errors

**Terminal output:**
- Look for any error messages in the terminal where Streamlit is running
- Check for "Rate limit exceeded" messages
- Check for authentication errors

## Common Issues

### Issue: "Please wait Xs before refreshing again"
**Solution:** Wait for the cooldown timer to reach 0, then click refresh again.

### Issue: Changes show in debug script but not in main app
**Solution:**
1. Clear browser cache (Ctrl+Shift+R)
2. Close and reopen browser
3. Check if you're looking at the right tab

### Issue: Debug script shows same data as session state
**Solution:** This means cache clearing IS working. The issue is either:
- Your change isn't in Google Sheets (check Step 1)
- You're looking at the wrong field/row
- Browser cache is showing old UI (try hard refresh)

### Issue: Row count changed but content didn't
**Solution:**
- Check if you edited an existing row or added/removed rows
- If you edited a cell, check that specific cell in the debug output
- Make sure you saved the sheet (changes auto-save, but check)

## Need More Help?

Run the debug script and share:
1. The output from "Direct Google Sheets Check"
2. The output from "Check Session State"
3. What specific change you made (column, row, old value, new value)
4. Whether the change shows in the debug script

This will help diagnose exactly where the data flow is breaking.
