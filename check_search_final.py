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
        # Direct URL might work better if we include query params
        # But WeRead encodes keyword. Let's try direct navigation again with wait.
        await page.goto(f"https://weread.qq.com/web/search/analysis?keyword={name}", wait_until="networkidle")
        await asyncio.sleep(10) # Long wait
        
        await page.screenshot(path="debug_search_final_attempt.png")
        
        # Log all links
        links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => a.href)''')
        print(f"Found {len(links)} links on search page.")
        for l in links:
            if "mp" in l:
                print(f"✅ MP LINK FOUND: {l}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_search())
