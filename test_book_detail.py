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
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Method: Direct profile URL
        # Some accounts use internal IDs
        # biz: Mzk4ODUyMTE4Ng==
        url = "https://weread.qq.com/web/bookDetail/MP_WXS_3988521186"
        
        print(f"Testing WeRead Book Detail: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.screenshot(path="debug_book_detail.png")
        
        content = await page.content()
        if "404" in content:
            print("❌ Result: 404")
        else:
            print(f"✅ Result: OK (Length {len(content)})")
            # Look for article links or "Read" button
            links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => ({ text: a.innerText, href: a.href }))''')
            for l in links:
                if "mp" in l['href'] or "reader" in l['href']:
                    print(f"  FOUND: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_biz_direct())
