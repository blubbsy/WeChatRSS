import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to WeRead search for the test account...")
        query = "小木易仿真"
        await page.goto(f"https://weread.qq.com/web/search/analysis?keyword={query}", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Look for links that might be MP accounts
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} search results.")
        for l in links:
            print(f"- [{l['text']}] -> {l['href']}")
            
        await page.screenshot(path="debug_search_results.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
