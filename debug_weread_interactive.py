import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_weread_behavior():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to WeRead...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        print("\nINSTRUCTIONS:")
        print("1. In the browser that just opened, please search for '小木易仿真'.")
        print("2. Click on the account to follow it (if not already followed).")
        print("3. Then click on the account name to open its article list.")
        print("4. Wait 10 seconds, then close the browser.")
        
        await asyncio.sleep(60) # Give the user time to interact
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_weread_behavior())
