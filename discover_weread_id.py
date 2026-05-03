import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def discover_id():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"Searching for {name} on WeRead...")
        await page.goto("https://weread.qq.com/", wait_until="networkidle")
        
        search_input = await page.query_selector(".index_search_input")
        if search_input:
            await search_input.fill(name)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)
            
            # Find the link that goes to /web/reader/mp/
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href.includes('web/reader/mp/'))
                    .map(a => ({
                        text: a.innerText,
                        href: a.href
                    }));
            }''')
            
            print(f"Discovered WeRead IDs:")
            for l in links:
                wr_id = l['href'].split('/').pop()
                print(f"- {l['text']} -> ID: {wr_id}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(discover_id())
