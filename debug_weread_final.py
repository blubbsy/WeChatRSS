import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_weread_final():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Method 3: Try to find the account via the shelf / subscribed list
        print("Navigating to Shelf to find subscribed accounts...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Take a screenshot to see if we see "Subscribed accounts" (公众号)
        await page.screenshot(path="debug_shelf.png")
        print("Shelf screenshot saved.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_weread_final())
