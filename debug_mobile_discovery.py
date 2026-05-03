import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_mobile_discovery():
    async with async_playwright() as p:
        iphone = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**iphone, storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead Shelf (Mobile)...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # List all clickable text
        elements = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('div, span, p, a')).map(el => el.innerText.trim()).filter(t => t.length > 1 && t.length < 50);
        }''')
        print(f"Discovered {len(elements)} text elements.")
        for t in list(set(elements))[:50]:
             if "公众号" in t or "订阅" in t or "发现" in t:
                 print(f"INTERESTING TEXT: {t}")

        # Try to find links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({ text: a.innerText, href: a.href }));
        }''')
        for l in links:
            if "/mp/" in l['href']:
                print(f"✅ DISCOVERED ACCOUNT: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_mobile_discovery())
