import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_mp_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        url = "https://weread.qq.com/web/mp/"
        print(f"Testing WeRead MP base: {url}")
        await page.goto(url, wait_until="networkidle")
        
        await page.screenshot(path="debug_mp_base.png")
        print("Screenshot saved.")
        
        # Check for account links
        content = await page.content()
        print(f"Content length: {len(content)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_mp_url())
