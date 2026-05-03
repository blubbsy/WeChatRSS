import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_weread_reader():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # This is a known working format for some WeRead MP accounts
        # Note the 'mp' instead of 'reader/mp' or similar variations
        account_id = 'Mzk4ODUyMTE4Ng=='
        url = f"https://weread.qq.com/web/reader/mp/{account_id}"
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="load")
        
        # Wait for the account content to load
        print("Waiting for content to populate...")
        await asyncio.sleep(5)
        
        # Print all visible text to see if we reached the right page
        body_text = await page.inner_text("body")
        print(f"Body text snippet: {body_text[:200]}...")
        
        # Find any links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} links.")
        for l in links:
            if "mp.weixin.qq.com" in l['href'] or l['text']:
                print(f"- [{l['text']}] -> {l['href']}")
        
        await page.screenshot(path="debug_reader.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_weread_reader())
