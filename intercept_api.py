import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json

STATE_PATH = os.path.join('data', 'state.json')

async def intercept_shelf():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        async def log_response(response):
            # Log all JSON responses from weread
            if "weread.qq.com" in response.url and "json" in response.headers.get("content-type", ""):
                print(f"\nINTERCEPTED JSON: {response.url}")
                print(f"  Status: {response.status}")
                try:
                    data = await response.json()
                    print(f"  Keys: {list(data.keys())}")
                    # If it's shelf sync, list books
                    if "books" in data:
                        print(f"  Found {len(data['books'])} books on shelf.")
                        for b in data['books']:
                            if b.get('bookId', '').startswith('MP_WXS_'):
                                print(f"    - MP: {b.get('title')}")
                except:
                    pass

        page.on("response", log_response)
        
        print("Navigating to WeRead Shelf...")
        # Direct navigation to shelf often triggers the sync API
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        await asyncio.sleep(10)
        
        # Take a screenshot to verify we are actually seeing the shelf
        await page.screenshot(path="shelf_intercept.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(intercept_shelf())
