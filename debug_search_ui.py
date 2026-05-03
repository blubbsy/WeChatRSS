import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_search_tabs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"Searching for {name}...")
        await page.goto(f"https://weread.qq.com/web/search/analysis?keyword={name}", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Take a screenshot to see if there are tabs like "Books", "Official Accounts", etc.
        await page.screenshot(path="debug_search_ui.png")
        
        # List all clickable elements in the search area
        elements = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.search_result_tabs_item, button, a'))
                .map(el => ({ text: el.innerText, class: el.className }));
        }''')
        
        print("Search UI Elements:")
        for e in elements:
            if e['text']:
                print(f"- {e['text']} ({e['class']})")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_search_tabs())
