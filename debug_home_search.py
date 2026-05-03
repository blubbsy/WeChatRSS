import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_home_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        print("Navigating to Home...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        # Manual search trigger
        print(f"Typing '{name}'...")
        # Use CSS selector from previous successful class list
        search_input = await page.wait_for_selector(".wr_index_page_search_bar_input")
        await search_input.fill(name)
        await page.keyboard.press("Enter")
        print("Search submitted.")
        
        await asyncio.sleep(5)
        await page.screenshot(path="debug_home_search_results.png")
        
        # Check if we are on the results page
        print("URL after search:", page.url)
        
        # Find any links with 'mp'
        links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => ({ text: a.innerText, href: a.href }))''')
        for l in links:
            if "mp" in l['href']:
                print(f"✅ FOUND LINK: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_home_search())
