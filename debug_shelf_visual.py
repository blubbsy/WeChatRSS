import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_shelf():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead Shelf...")
        await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
        
        # Take a screenshot to see what the user sees
        await page.screenshot(path="shelf_debug.png", full_page=True)
        print("Screenshot saved as shelf_debug.png")
        
        # Log all text content to find where MP accounts are
        content = await page.inner_text("body")
        print(f"Body text length: {len(content)}")
        print(f"Snippet: {content[:500]}")
        
        if "书架" in content:
            print("Successfully on the Shelf page.")
        else:
            print("Warning: Might not be on the Shelf page.")
            
        # List all links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} links on page.")
        for l in links:
            if "web/reader/mp/" in l['href'] or "公众号" in l['text']:
                print(f"POTENTIAL MP LINK: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_shelf())
