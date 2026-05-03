import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_numeric_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # Test Account: 小木易仿真 (3988521186)
        numeric_id = '3988521186'
        url = f"https://weread.qq.com/web/reader/mp/{numeric_id}"
        
        print(f"Testing WeRead Numeric URL: {url}")
        await page.goto(url, wait_until="load")
        await asyncio.sleep(5)
        
        content = await page.content()
        title = await page.title()
        print(f"  Title: {title}")
        
        if "404" in content or "Not Found" in content:
            print("  Result: 404")
        else:
            print(f"  Result: OK (Length {len(content)})")
            # Look for article links
            links = await page.query_selector_all("a")
            print(f"  Found {len(links)} links.")
            
        await page.screenshot(path="debug_numeric_id.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_numeric_url())
