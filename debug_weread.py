import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_weread_behavior():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Method 1: The MP reader link
        # Some accounts use different formats
        account_id = 'Mzk4ODUyMTE4Ng=='
        
        print("Checking WeRead Search for the account...")
        # Searching for the account name might trigger the right view
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        search_input = await page.query_selector(".index_search_input")
        if search_input:
            await search_input.fill("小木易仿真")
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)
            await page.screenshot(path="debug_search.png")
            print("Search screenshot saved.")
        
        # Try direct navigation to an article to see if it loads
        test_article = "https://mp.weixin.qq.com/s/zkiNHp8cfsojGcOwWpI5Ng"
        print(f"Navigating to direct article: {test_article}")
        await page.goto(test_article, wait_until="networkidle")
        await asyncio.sleep(3)
        title = await page.title()
        print(f"Article Title: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_weread_behavior())
