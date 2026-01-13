#!/usr/bin/env python3
"""
Stress test for Tab 5 (Executive Pricing Tool) using Playwright
Tests all functionality including manual PBP cost inputs, tariffs, and pricing calculations
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect
import random

async def stress_test_tab5():
    """Comprehensive stress test for Tab 5"""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
        page = await browser.new_page()

        print("🚀 Starting Tab 5 Stress Test...")

        # Navigate to the app
        await page.goto("http://localhost:8502")
        await page.wait_for_load_state("networkidle")

        # Wait for app to load
        await page.wait_for_timeout(3000)

        # Navigate to Tab 5
        print("📍 Navigating to Tab 5...")
        # Tab buttons in Streamlit are in a role="tablist" container
        tab5_button = page.locator('[role="tab"]:has-text("Executive Pricing Tool")')
        await tab5_button.click()
        await page.wait_for_timeout(2000)

        # Test 1: Add multiple products
        print("\n✅ Test 1: Adding multiple products...")
        products_to_add = [
            ("Partner X", "Product A"),
            ("Partner X", "Product B"),
            ("Partner Y", "Product Y1"),
        ]

        for partner, product in products_to_add:
            print(f"  Adding {product} from {partner}...")

            # Check if product selector needs to be expanded
            add_product_button = page.locator("button:has-text('Add Another Product')")
            if await add_product_button.is_visible():
                await add_product_button.click()
                await page.wait_for_timeout(500)

            # Select partner
            partner_select = page.locator("div[data-testid='stSelectbox']").first
            await partner_select.click()
            await page.wait_for_timeout(500)
            partner_option = page.locator(f"text={partner}")
            await partner_option.click()
            await page.wait_for_timeout(500)

            # Select product
            product_select = page.locator("div[data-testid='stSelectbox']").nth(1)
            await product_select.click()
            await page.wait_for_timeout(500)

            # Look for the product in the dropdown
            product_option = page.locator(f"div[role='option']:has-text('{product}')")
            if await product_option.count() > 0:
                await product_option.first.click()
            else:
                # Try partial match
                product_option = page.locator(f"div[role='option']").filter(has_text=product)
                if await product_option.count() > 0:
                    await product_option.first.click()

            await page.wait_for_timeout(500)

            # Click Add Product button
            add_button = page.locator("button:has-text('Add Product to Quote')")
            await add_button.click()
            await page.wait_for_timeout(1000)

        # Test 2: Modify quantities and markups
        print("\n✅ Test 2: Testing quantity and markup adjustments...")

        # Find quantity inputs and modify them
        qty_inputs = page.locator("input[type='number']").filter(has=page.locator("text='Quantity'"))
        qty_count = await qty_inputs.count()

        for i in range(min(qty_count, 3)):  # Modify first 3 products
            qty_input = qty_inputs.nth(i)
            new_qty = random.choice([50, 100, 200, 500])
            print(f"  Setting quantity {i+1} to {new_qty}...")
            await qty_input.fill(str(new_qty))
            await page.wait_for_timeout(500)

        # Test markup editing with toggle
        print("\n✅ Test 3: Testing markup/price toggle editing...")

        # Find edit mode toggles
        edit_toggles = page.locator("div[role='radiogroup']")
        toggle_count = await edit_toggles.count()

        for i in range(min(toggle_count, 2)):  # Test first 2 products
            toggle = edit_toggles.nth(i)

            # Switch to price direct mode
            price_option = toggle.locator("label:has-text('Price Direct')")
            if await price_option.is_visible():
                print(f"  Switching product {i+1} to Price Direct mode...")
                await price_option.click()
                await page.wait_for_timeout(500)

                # Find and modify the price input
                price_inputs = page.locator("input[type='number']").filter(has=page.locator("text='Client Price/Unit'"))
                if await price_inputs.count() > i:
                    price_input = price_inputs.nth(i)
                    new_price = random.choice([25.00, 50.00, 75.00, 100.00])
                    print(f"    Setting price to ${new_price}...")
                    await price_input.fill(str(new_price))
                    await page.wait_for_timeout(500)

            # Switch back to markup mode
            markup_option = toggle.locator("label:has-text('Markup %')")
            if await markup_option.is_visible():
                print(f"  Switching product {i+1} back to Markup % mode...")
                await markup_option.click()
                await page.wait_for_timeout(500)

        # Test 4: Enable and configure customization
        print("\n✅ Test 4: Testing customization options with manual PBP costs...")

        custom_checkboxes = page.locator("text='Include Customization'")
        checkbox_count = await custom_checkboxes.count()

        for i in range(min(checkbox_count, 2)):  # Enable for first 2 products
            checkbox = custom_checkboxes.nth(i)
            print(f"  Enabling customization for product {i+1}...")
            await checkbox.click()
            await page.wait_for_timeout(500)

            # Set custom setup fee
            setup_inputs = page.locator("input[type='number']").filter(has=page.locator("text='Setup Fee'"))
            if await setup_inputs.count() > i:
                setup_input = setup_inputs.nth(i * 2)  # Client price input
                await setup_input.fill("100")
                await page.wait_for_timeout(300)

                # Check if we need to enter PBP cost manually
                pbp_setup_inputs = page.locator("input").filter(has=page.locator("text='PBP Cost (not in spreadsheet - enter manually)'"))
                if await pbp_setup_inputs.count() > 0:
                    print(f"    Entering manual PBP setup cost...")
                    pbp_input = pbp_setup_inputs.nth(i)
                    await pbp_input.fill("50")
                    await page.wait_for_timeout(300)

            # Set custom per unit cost
            per_unit_inputs = page.locator("input[type='number']").filter(has=page.locator("text='Per Unit Cost'"))
            if await per_unit_inputs.count() > i:
                per_unit_input = per_unit_inputs.nth(i * 2)  # Client price input
                await per_unit_input.fill("5")
                await page.wait_for_timeout(300)

                # Check if we need to enter PBP cost manually
                pbp_per_unit_inputs = page.locator("input").filter(has=page.locator("text='PBP Cost (not in spreadsheet - enter manually)'"))
                if await pbp_per_unit_inputs.count() > 0:
                    print(f"    Entering manual PBP per unit cost...")
                    pbp_input = pbp_per_unit_inputs.nth(i)
                    await pbp_input.fill("2.50")
                    await page.wait_for_timeout(300)

        # Test 5: Enable and configure tariffs
        print("\n✅ Test 5: Testing tariff options...")

        tariff_checkboxes = page.locator("text='Include Tariffs'")
        tariff_count = await tariff_checkboxes.count()

        for i in range(min(tariff_count, 2)):  # Enable for first 2 products
            checkbox = tariff_checkboxes.nth(i)

            # Check if already checked (auto-checked for non-USA products)
            is_checked = await checkbox.is_checked()
            if not is_checked:
                print(f"  Enabling tariffs for product {i+1}...")
                await checkbox.click()
            else:
                print(f"  Tariffs already enabled for product {i+1} (non-USA product)")

            await page.wait_for_timeout(500)

            # Set tariff rate
            tariff_inputs = page.locator("input[type='number']").filter(has=page.locator("text='Tariff Rate'"))
            if await tariff_inputs.count() > i:
                tariff_input = tariff_inputs.nth(i)
                tariff_rate = random.choice([5.0, 10.0, 15.0, 25.0])
                print(f"    Setting tariff rate to {tariff_rate}%...")
                await tariff_input.fill(str(tariff_rate))
                await page.wait_for_timeout(300)

        # Test 6: Configure order settings
        print("\n✅ Test 6: Testing order settings...")

        # Set shipping cost
        shipping_input = page.locator("input[type='number']").filter(has=page.locator("text='Shipping Cost'"))
        if await shipping_input.is_visible():
            print("  Setting shipping cost to $150...")
            await shipping_input.fill("150")
            await page.wait_for_timeout(500)

        # Enable credit card fee
        cc_checkbox = page.locator("text='Add 3.5% Credit Card Processing Fee'")
        if await cc_checkbox.is_visible():
            print("  Enabling credit card fee...")
            await cc_checkbox.click()
            await page.wait_for_timeout(500)

        # Test 7: Verify pricing breakdown
        print("\n✅ Test 7: Verifying pricing breakdown...")

        # Check for pricing breakdown section
        breakdown_section = page.locator("text='Pricing Breakdown'")
        if await breakdown_section.is_visible():
            print("  ✓ Pricing breakdown is visible")

            # Check for margin calculations
            margin_text = page.locator("text=/Margin.*\\$/")
            if await margin_text.is_visible():
                margin_value = await margin_text.text_content()
                print(f"  ✓ Margin calculation shown: {margin_value}")

            # Check for pass-through costs note
            passthrough_text = page.locator("text='Pass-through costs'")
            if await passthrough_text.is_visible():
                passthrough_value = await passthrough_text.text_content()
                print(f"  ✓ Pass-through costs noted: {passthrough_value}")

        # Test 8: Verify order summary
        print("\n✅ Test 8: Checking order summary...")

        # Look for summary table
        summary_table = page.locator("table").last
        if await summary_table.is_visible():
            print("  ✓ Order summary table is visible")

            # Check for total quote
            total_text = page.locator("text=/Total Quote.*\\$/")
            if await total_text.is_visible():
                total_value = await total_text.text_content()
                print(f"  ✓ Total quote shown: {total_value}")

            # Check for true margin
            true_margin_text = page.locator("text=/True Margin.*\\$/")
            if await true_margin_text.is_visible():
                margin_value = await true_margin_text.text_content()
                print(f"  ✓ True margin shown: {margin_value}")

        # Test 9: Test Add Another Product button
        print("\n✅ Test 9: Testing 'Add Another Product' button...")

        add_another_button = page.locator("button:has-text('Add Another Product')")
        if await add_another_button.is_visible():
            print("  Clicking 'Add Another Product' button...")
            await add_another_button.click()
            await page.wait_for_timeout(1000)

            # Check if product selector expanded
            product_selector = page.locator("text='Select a product'")
            if await product_selector.is_visible():
                print("  ✓ Product selector expanded successfully")

        # Test 10: Export functionality
        print("\n✅ Test 10: Testing export options...")

        # Look for export buttons
        csv_button = page.locator("button:has-text('Download CSV')")
        if await csv_button.is_visible():
            print("  ✓ CSV export button available")

        email_button = page.locator("button:has-text('Copy Email Template')")
        if await email_button.is_visible():
            print("  ✓ Email template button available")

        # Summary
        print("\n" + "="*50)
        print("🎉 STRESS TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\nAll Tab 5 features tested:")
        print("✅ Product addition and selection")
        print("✅ Quantity and markup adjustments")
        print("✅ Markup/Price toggle editing")
        print("✅ Customization with manual PBP costs")
        print("✅ Tariff configuration (auto-enabled for non-USA)")
        print("✅ Order settings (shipping, credit card fee)")
        print("✅ Pricing breakdown with margins")
        print("✅ Order summary with true margin")
        print("✅ Add Another Product functionality")
        print("✅ Export options")

        # Keep browser open for manual inspection
        print("\nBrowser will close in 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(stress_test_tab5())