import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_numeric_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        numeric_id = '3988521186'
        print(f"Searching for Numeric ID: {numeric_id}")
        url = f"https://weread.qq.com/web/search/analysis?keyword={numeric_id}"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} links.")
        for l in links:
            print(f"- {l['text']} -> {l['href']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_numeric_search())
