"""
Ultimate Authentication module for WeChatRSS.
Uses Persistent Browser Contexts to store a full user profile.
This makes the scraper virtually indistinguishable from a real browser.
"""

import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROFILE_DIR = os.path.abspath(os.path.join(BASE_DIR, 'data', 'profiles', 'wechat_rss_profile'))

async def run():
    async with async_playwright() as p:
        if not os.path.exists(PROFILE_DIR):
            os.makedirs(PROFILE_DIR, exist_ok=True)
            
        print("\n" + "="*50)
        print("PERSISTENT SESSION CAPTURE (WEREAD + SOGOU)")
        print("="*50)
        print(f"Profile Directory: {PROFILE_DIR}")
        
        # Use launch_persistent_context to keep a real browser profile
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            slow_mo=300,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = browser_context.pages[0]
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # Phase 1: WeRead Auth
        print("\nStep 1: Authenticating WeRead...")
        print("URL: https://weread.qq.com/#login")
        await page.goto("https://weread.qq.com/#login", wait_until="load")
        print("Please scan the QR code and ensure you are logged in.")
        
        try:
            await page.wait_for_selector(".wr_avatar, .navBar_link_active", timeout=300000)
            print("✅ WeRead Authenticated!")
        except Exception as e:
            print(f"⚠️ WeRead Auth Timeout or Error: {e}")
        
        # Phase 2: Follow Accounts (Crucial for WeRead visibility)
        print("\n" + "-"*50)
        print("STEP 2: FOLLOW ACCOUNTS")
        print("Please search for your accounts in this browser window")
        print("and click 'Follow' (关注). This is mandatory!")
        print("-"*50 + "\n")
        
        # Phase 3: Sogou Auth (Solve CAPTCHA here)
        print("\nStep 3: Solving Sogou CAPTCHA...")
        # Use a specific account to trigger the real block
        test_url = "https://weixin.sogou.com/weixin?type=2&query=小木易仿真"
        print(f"URL: {test_url}")
        await page.goto(test_url, wait_until="load")
        
        print("\n" + "!"*50)
        print("ACTION REQUIRED:")
        print("1. If you see 'VerifyCode', solve it NOW.")
        print("2. Once you see article results, wait for the timer.")
        print("!"*50 + "\n")
        
        try:
            await page.wait_for_selector(".news-list", timeout=300000)
            print("✅ Sogou CAPTCHA Passed!")
        except:
            print("⚠️ Sogou results not detected. Proceeding anyway...")

        # Finalize
        print("\nThe window will stay open for 60 seconds. Use this time to follow your accounts!")
        await asyncio.sleep(60)
        
        print(f"\n✅ PERSISTENT PROFILE UPDATED.")
        await browser_context.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(run())
