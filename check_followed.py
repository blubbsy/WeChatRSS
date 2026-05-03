import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_discovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to Shelf to discover accounts...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Method: Check all links on the shelf page
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            }));
        }''')
        
        found = False
        for l in links:
            if "web/reader/mp/" in l['href']:
                print(f"✅ DISCOVERED: {l['text']} -> {l['href']}")
                found = True
        
        if not found:
            print("❌ No followed accounts found on the shelf. Please make sure you have followed them on WeRead!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_discovery())
