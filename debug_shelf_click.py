import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_shelf_interaction():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead Shelf...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Log all text for debugging
        all_text = await page.inner_text("body")
        print(f"Page Text Snippet: {all_text[:1000]}")
        
        # Try to find the 'Official Accounts' button
        # It's often a span or div
        try:
            mp_btn = await page.query_selector("text=公众号")
            if mp_btn:
                print("Found '公众号' button. Clicking...")
                await mp_btn.click()
                await asyncio.sleep(5)
                print("Clicked. New URL:", page.url)
                
                # Check for links now
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => ({ text: a.innerText, href: a.href }));
                }''')
                print(f"Found {len(links)} links after click.")
                for l in links:
                    if "/mp/" in l['href']:
                        print(f"✅ ACCOUNT: {l['text']} -> {l['href']}")
            else:
                print("'公众号' button not found.")
        except Exception as e:
            print(f"Error during interaction: {e}")
            
        await page.screenshot(path="shelf_after_click.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_shelf_interaction())
