import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def check_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"Searching for {name}...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        search_input = await page.wait_for_selector(".wr_index_page_search_bar_input")
        await search_input.fill(name)
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        
        # Take result screenshot
        await page.screenshot(path="debug_search_results_v2.png")
        
        # Extract all result items
        results = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.wr_search_result_item, a')).map(el => ({
                text: el.innerText,
                href: el.href
            }));
        }''')
        
        for r in results:
            if "web/reader/mp/" in r['href'] or "公众号" in r['text']:
                print(f"✅ FOUND IN DOM: '{r['text'].strip()}' -> {r['href']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_search())
