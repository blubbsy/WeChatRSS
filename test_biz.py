import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_mp_discovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # This ID was previously extracted from the user's link
        biz_id = 'Mzk4ODUyMTE4Ng=='
        
        # Test Case: Does WeRead allow direct MP navigation by biz?
        # Many tools use: https://weread.qq.com/web/reader/mp/{biz}
        test_url = f"https://weread.qq.com/web/reader/mp/{biz_id}"
        
        print(f"Testing WeRead MP path: {test_url}")
        await page.goto(test_url, wait_until="load")
        await asyncio.sleep(5)
        
        # Check if we see content or a 404
        content = await page.content()
        if "404" in content or "Not Found" in content:
            print("❌ direct /reader/mp/ path is NOT supported or blocked.")
        else:
            print("✅ direct /reader/mp/ path SHOWS content.")
            
        await page.screenshot(path="debug_biz_test.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_mp_discovery())
