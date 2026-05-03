import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_auto_follow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"Searching for {name} to follow...")
        # Search page
        await page.goto(f"https://weread.qq.com/web/search/analysis?keyword={name}", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Look for a "Follow" (关注) button
        follow_btn = await page.query_selector("text=关注")
        if follow_btn:
            print("Found follow button! Clicking...")
            await follow_btn.click()
            await asyncio.sleep(2)
            print("Followed?")
        else:
            print("Follow button not found. Maybe already followed or not found in results.")
            
        await page.screenshot(path="debug_follow_attempt.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_auto_follow())
