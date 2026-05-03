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
        
        # Take home screenshot
        await page.screenshot(path="debug_home.png")
        
        # Manual search trigger
        search_input = await page.wait_for_selector(".wr_index_page_search_bar_input", timeout=5000)
        if search_input:
            await search_input.fill(name)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)
            await page.screenshot(path="debug_search_results.png")
            
            # Check for specific search classes
            classes = await page.evaluate('''() => {
                return Array.from(new Set(Array.from(document.querySelectorAll('*')).flatMap(el => Array.from(el.classList))));
            }''')
            print(f"Result Classes: {classes[:20]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_search())
