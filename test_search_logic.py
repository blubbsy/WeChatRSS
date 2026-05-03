import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Test searching for the biz string
        biz = 'Mzk4ODUyMTE4Ng=='
        name = '小木易仿真'
        
        for query in [biz, name]:
            print(f"Searching for: {query}")
            url = f"https://weread.qq.com/web/search/analysis?keyword={query}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(3)
            
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText,
                    href: a.href
                }));
            }''')
            
            print(f"  Found {len(links)} links.")
            for l in links:
                if "web/reader/mp/" in l['href']:
                    print(f"  ✅ MATCH: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
