"""
Authentication module for WeChatRSS.
Handles manual login to WeChat/WeRead via Playwright and saves the session state.
"""

import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run():
    """
    Launches a browser for the user to manually scan the QR code and log in.
    Once logged in, it saves the storage state to 'data/state.json' for the scraper to use.
    """
    async with async_playwright() as p:
        # Ensure the data directory exists for storing state
        if not os.path.exists('data'):
            os.makedirs('data')
            
        print("\n" + "="*50)
        print("LAUNCHING WECHAT AUTHENTICATION")
        print("="*50)
        print("A browser window will open. Please scan the QR code to log in.")
        
        # Launching with headless=False to allow user interaction
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Apply stealth
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # Method: Landing on the direct login portal
        print("Navigating to WeRead Portal...")
        try:
            await page.goto("https://weread.qq.com/", wait_until="networkidle")
            
            # Click login if needed
            login_btn = await page.query_selector(".navBar_link_login, .index_login, button:has-text('登录')")
            if login_btn:
                print("Clicking login button...")
                await login_btn.click()
            
            print("\n" + "-"*50)
            print("ACTION REQUIRED: PLEASE SCAN THE QR CODE ON SCREEN")
            print("After scanning, please search for the accounts you want to track")
            print("and click 'Follow' (关注) inside the browser window!")
            print("-"*50 + "\n")
            
            # Wait for user to follow at least one account or stay active for 2 mins
            print("The window will stay open for 2 minutes to allow you to follow accounts.")
            print("Searching and following accounts MANUALLY now will fix the 404 errors.")
            
            # Wait for successful login first
            await page.wait_for_selector(".navBar_link_active, .wr_avatar", timeout=300000)
            print("\nSUCCESS: Login detected!")
            
            # Stay open for manual interaction
            await asyncio.sleep(120)
            
            # Capture cookies and local storage state
            await context.storage_state(path="data/state.json")
            print(f"Session state saved.")
            
        except Exception as e:
            print(f"\nAuth session ended: {e}")
        
        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(run())
