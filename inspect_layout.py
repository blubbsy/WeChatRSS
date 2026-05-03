import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def inspect_layout():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        print("Navigating to WeRead...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        # Take screenshot of the whole page
        await page.screenshot(path="debug_layout.png", full_page=True)
        
        # List all classes
        classes = await page.evaluate('''() => {
            return Array.from(new Set(Array.from(document.querySelectorAll('*')).flatMap(el => Array.from(el.classList))));
        }''')
        print(f"Discovered {len(classes)} classes.")
        print(f"Top 20 classes: {classes[:20]}")
        
        # List all text in buttons
        buttons = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('button, a, .navBar_link')).map(el => el.innerText.trim()).filter(t => t.length > 0);
        }''')
        print(f"Button/Link texts: {buttons}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_layout())
