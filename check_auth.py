import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def check_auth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        
        print("Verifying WeRead auth state...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        # Check for avatar or logout
        is_logged_in = await page.query_selector(".wr_avatar")
        if is_logged_in:
            print("✅ WeRead session is VALID and AUTHENTICATED.")
        else:
            print("❌ WeRead session is NOT authenticated.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_auth())
