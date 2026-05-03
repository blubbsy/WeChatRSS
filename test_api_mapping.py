import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_api_mapping(biz_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Test 1: Can we find the internal ID via the search API directly?
        print(f"Searching for biz ID: {biz_id}")
        url = f"https://weread.qq.com/web/search/analysis?keyword={biz_id}"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Intercept search result links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .filter(a => a.href.includes('web/reader/mp/'))
                .map(a => a.href);
        }''')
        
        print(f"Found {len(links)} MP links.")
        for l in links:
            print(f"  - {l}")
            
        await browser.close()

if __name__ == "__main__":
    # Test with biz ID: Mzk4ODUyMTE4Ng==
    asyncio.run(test_api_mapping('Mzk4ODUyMTE4Ng=='))
