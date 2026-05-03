import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def robust_discovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            storage_state=STATE_PATH
        )
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        # Look for the avatar to confirm login
        avatar = await page.query_selector(".wr_avatar")
        if avatar:
            print("✅ LOGIN VERIFIED (Avatar found)")
        else:
            print("❌ NOT LOGGED IN")
            await browser.close()
            return

        # Navigate to Shelf
        print("Opening Shelf...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Take screenshot
        await page.screenshot(path="shelf_final.png", full_page=True)
        
        # Look for the 'MP' or '公众号' section
        # WeRead often stores these in a side menu or a specific div
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        found_mp = False
        for l in links:
            if "mp" in l['href'].lower() or "公众号" in l['text']:
                print(f"Found MP Link: {l['text']} -> {l['href']}")
                found_mp = True
                
        if not found_mp:
            print("Warning: No MP link found on shelf.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(robust_discovery())
