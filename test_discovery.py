import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to Shelf...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Method: Follow the link from the shelf if subscribed
        print("Looking for subscription link...")
        # In current WeRead Web, subscriptions are often under a specific tab or '订阅'
        try:
            # Click the tab that contains the text '订阅' or '公众号'
            await page.click("text=公众号", timeout=3000)
            print("Clicked '公众号' tab.")
            await asyncio.sleep(2)
        except:
            print("'公众号' tab not found.")

        # Find all accounts
        acc_links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            })).filter(l => l.href.includes('web/reader/mp/'));
        }''')
        
        print(f"Found {len(acc_links)} followed accounts.")
        for l in acc_links:
            print(f"✅ Found account: {l['text'].strip()} -> {l['href']}")
                
        await page.screenshot(path="debug_followed_final.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())
