import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_mobile_shelf():
    async with async_playwright() as p:
        # Use iPhone 12 User Agent
        iphone = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            **iphone,
            storage_state=STATE_PATH
        )
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead Shelf (Mobile)...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Log content
        content = await page.inner_text("body")
        print(f"Mobile Body Snippet: {content[:500]}")
        
        await page.screenshot(path="shelf_mobile.png")
        print("Mobile screenshot saved.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_mobile_shelf())
