import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def discover_real_id():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"Navigating to WeRead Home...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        print(f"Typing '{name}' into search box...")
        search_input = await page.wait_for_selector(".index_search_input")
        await search_input.fill(name)
        await page.keyboard.press("Enter")
        
        print("Waiting for results...")
        await asyncio.sleep(5)
        
        # Take a screenshot to see the results
        await page.screenshot(path="search_results_visible.png")
        
        # Extract all links that look like MP links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .map(a => ({ text: a.innerText, href: a.href }));
        }''')
        
        print("Found links:")
        for l in links:
            if "web/reader/mp/" in l['href'] or "mp" in l['href']:
                print(f"✅ CANDIDATE: {l['text']} -> {l['href']}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(discover_real_id())
