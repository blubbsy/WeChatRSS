import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json

STATE_PATH = os.path.join('data', 'state.json')

async def intercept_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # Intercept responses
        async def handle_response(response):
            if "search" in response.url.lower():
                print(f"INTERCEPTED: {response.url}")
                try:
                    data = await response.json()
                    # Look for our account in search data
                    records = data.get('records', [])
                    for r in records:
                        book = r.get('book', {})
                        if "木易" in book.get('title', ''):
                            print(f"FOUND ACCOUNT IN JSON: {book.get('title')} -> ID: {book.get('bookId')}")
                except:
                    pass

        page.on("response", handle_response)
        
        name = "小木易仿真"
        print(f"Searching for {name}...")
        url = f"https://weread.qq.com/web/search/analysis?keyword={name}"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(intercept_search())
