import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_account():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        # Method: Direct Search result check
        print(f"SEARCHING FOR '{name}' via direct analysis URL...")
        url = f"https://weread.qq.com/web/search/analysis?keyword={name}"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Take screenshot of the specific search result area
        await page.screenshot(path="debug_search_final_final.png")
        
        # Print all visible text
        body_text = await page.inner_text("body")
        print(f"Body text contains '公众号'? {'公众号' in body_text}")
        print(f"Body text contains name? {name in body_text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_account())
