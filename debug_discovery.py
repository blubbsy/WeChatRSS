import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_discovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to WeRead...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        # Look for 'Official Accounts' or 'MP' link
        print("Looking for 'Official Accounts' link...")
        await asyncio.sleep(5)
        
        # Take screenshot
        await page.screenshot(path="debug_home_ui.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_discovery())
