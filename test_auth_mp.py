import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import re

STATE_PATH = os.path.join('data', 'state.json')

async def test_auth_mp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Load WeRead state
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        url = "https://mp.weixin.qq.com/s/AD2OAFCfJaKsEzmof3ASg"
        print(f"Loading {url} with WeRead session...")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Check for biz
        content = await page.content()
        biz = re.search(r'var biz = "([^"]+)"', content)
        if biz:
            print(f"✅ SUCCESS: Biz={biz.group(1)}")
        else:
            print("❌ Still blocked.")
            # Screenshot for proof
            await page.screenshot(path="debug_mp_auth.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_auth_mp())
