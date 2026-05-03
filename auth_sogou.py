"""
Sogou Authentication module for WeChatRSS.
Targeted specifically at triggering the 'Article Search' block.
"""

import asyncio
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

STATE_PATH = os.path.abspath(os.path.join('data', 'sogou_state.json'))

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'):
            os.makedirs('data')
            
        print("\n" + "="*50)
        print("SOGOU SESSION CAPTURE (DEEP DISCOVERY)")
        print("="*50)
        
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # We target the EXACT url the scraper uses to trigger the real block
        target_name = "小木易仿真"
        # We'll try both types to be sure we trigger the challenge
        urls = [
            f"https://weixin.sogou.com/weixin?type=2&query={target_name}",
            f"https://weixin.sogou.com/weixin?type=1&query={target_name}"
        ]

        print(f"\nNavigating to Sogou Article Search to trigger the real block...")
        for url in urls:
            print(f"Opening: {url}")
            await page.goto(url, wait_until="load")
            await asyncio.sleep(3)
            
            # Check for block
            content = await page.content()
            if "antispider" in content or "VerifyCode" in content or "assistance in verifying" in content:
                print("\n" + "!"*50)
                print("BLOCK DETECTED! PLEASE SOLVE THE CAPTCHA NOW.")
                print("Once you see search results, we will save the session.")
                print("!"*50 + "\n")
                
                # Wait for the results to appear (indicates success)
                try:
                    await page.wait_for_selector(".news-list, .results", timeout=180000)
                    print("✅ CAPTCHA PASSED.")
                    break # Success
                except:
                    print("Still waiting for results...")
            else:
                print("No block seen yet. Trying another search...")

        # Warm up: do a few random clicks to establish 'human' cookies
        print("\nWarming up session...")
        await asyncio.sleep(3)
        
        # Save state
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        await context.storage_state(path=STATE_PATH)
        print(f"✅ SOGOU SESSION CAPTURED: {STATE_PATH}")
        
        print("\nClosing in 5 seconds...")
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
