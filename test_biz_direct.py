import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_biz_direct():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # Test direct MP profile access
        # biz: Mzk4ODUyMTE4Ng==
        biz = 'Mzk4ODUyMTE4Ng=='
        url = f"https://weread.qq.com/web/reader/mp/{biz}"
        
        print(f"Navigating to direct MP path: {url}")
        await page.goto(url, wait_until="load")
        await asyncio.sleep(10)
        
        await page.screenshot(path="debug_biz_direct.png")
        
        content = await page.content()
        if "404" in content:
            print("❌ Result: 404")
        else:
            print(f"✅ Result: OK (Length {len(content)})")
            # Look for titles
            titles = await page.evaluate('''() => Array.from(document.querySelectorAll('.mp_article_title, .title')).map(el => el.innerText)''')
            print(f"Found titles: {titles}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_biz_direct())
