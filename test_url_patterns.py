import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_urls():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Test Account: 小木易仿真
        biz = 'Mzk4ODUyMTE4Ng=='
        
        urls = [
            f"https://weread.qq.com/web/reader/mp/{biz}",
            f"https://weread.qq.com/web/mp/{biz}",
            f"https://weread.qq.com/mp/{biz}",
        ]
        
        for url in urls:
            print(f"Testing URL: {url}")
            try:
                await page.goto(url, wait_until="load", timeout=10000)
                await asyncio.sleep(3)
                content = await page.content()
                title = await page.title()
                print(f"  Title: {title}")
                if "404" in content or "Not Found" in content:
                    print("  Result: 404")
                else:
                    print(f"  Result: OK (Length {len(content)})")
            except Exception as e:
                print(f"  Error: {e}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_urls())
