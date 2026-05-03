import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # 1. Search for Account
        name = "小木易仿真"
        print(f"SEARCHING FOR '{name}'...")
        await page.goto(f"https://weread.qq.com/", wait_until="networkidle")
        search_input = await page.wait_for_selector(".wr_index_page_search_bar_input")
        await search_input.fill(name)
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        
        # Log all links in results
        results = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({ text: a.innerText, href: a.href }));
        }''')
        
        print(f"FOUND {len(results)} LINKS IN SEARCH.")
        for r in results:
            if "mp" in r['href'] or "reader" in r['href']:
                print(f"LINK: '{r['text']}' -> {r['href']}")

        await page.screenshot(path="diag_search_v3.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_all())
