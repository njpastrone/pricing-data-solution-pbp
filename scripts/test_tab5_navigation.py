#!/usr/bin/env python3
"""
Test that Tab 5 stays active after operations like adding products
"""

import asyncio
from playwright.async_api import async_playwright

async def test_tab5_navigation():
    """Test that Tab 5 remains active after adding products"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Run headless for speed
        page = await browser.new_page()

        print("🚀 Testing Tab 5 Navigation Fix...")

        # Navigate to the app
        await page.goto("http://localhost:8504")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        # Navigate to Tab 5
        print("📍 Navigating to Tab 5...")
        tab5_button = page.locator('[role="tab"]:has-text("Executive Pricing Tool")')
        await tab5_button.click()
        await page.wait_for_timeout(2000)

        # Check that we're on Tab 5 (should have Executive Pricing Tool header)
        header = page.locator("h2:has-text('Executive Pricing Tool')")
        is_visible = await header.is_visible()

        if is_visible:
            print("✅ Successfully navigated to Tab 5")
        else:
            print("❌ Failed to navigate to Tab 5")
            await browser.close()
            return

        # Check URL for tab parameter
        url = page.url
        print(f"📝 Current URL: {url}")

        # Try to add a product
        print("➕ Attempting to add a product...")

        # Select partner
        partner_select = page.locator("div[data-testid='stSelectbox']").first
        try:
            await partner_select.click(timeout=3000)
            await page.wait_for_timeout(500)

            # Click on Partner X
            partner_option = page.locator("text=Partner X").first
            await partner_option.click()
            await page.wait_for_timeout(500)

            # Select product
            product_select = page.locator("div[data-testid='stSelectbox']").nth(1)
            await product_select.click()
            await page.wait_for_timeout(500)

            # Select first product
            product_option = page.locator("div[role='option']").first
            await product_option.click()
            await page.wait_for_timeout(500)

            # Click Add Product button
            add_button = page.locator("button:has-text('Add Product to Quote')")
            await add_button.click()

            print("⏳ Waiting for page to reload after adding product...")
            await page.wait_for_timeout(3000)

            # Check that we're STILL on Tab 5
            header_after = page.locator("h2:has-text('Executive Pricing Tool')")
            still_on_tab5 = await header_after.is_visible()

            # Check URL again
            url_after = page.url
            print(f"📝 URL after adding product: {url_after}")

            if still_on_tab5:
                print("✅ SUCCESS: Tab 5 remains active after adding product!")

                # Check if tab=4 is in the URL
                if "tab=4" in url_after:
                    print("✅ Query parameter 'tab=4' correctly set in URL")
                else:
                    print("⚠️ Query parameter not found in URL (might be using fallback)")

            else:
                print("❌ FAILURE: Returned to Tab 1 after adding product")

                # Check what tab we're on
                proposal_header = page.locator("h3:has-text('Proposal Generator')")
                if await proposal_header.is_visible():
                    print("📍 Currently on Tab 1 (Proposal Generator)")

        except Exception as e:
            print(f"⚠️ Error during test: {e}")

        # Summary
        print("\n" + "="*50)
        if still_on_tab5:
            print("🎉 TAB NAVIGATION FIX VERIFIED!")
            print("Tab 5 correctly stays active after operations")
        else:
            print("❌ TAB NAVIGATION ISSUE STILL PRESENT")
            print("Tab switches back to Tab 1 after operations")
        print("="*50)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_tab5_navigation())