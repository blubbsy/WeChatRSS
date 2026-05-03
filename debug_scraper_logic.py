import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_scrape():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_PATH)
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Target WeRead aggregator
        account_id = 'Mzk4ODUyMTE4Ng=='
        account_url = f"https://weread.qq.com/web/reader/mp/{account_id}"
        
        print(f"Navigating to {account_url}...")
        await page.goto(account_url, wait_until="load")
        
        # Inspect iframes
        iframes = page.frames
        print(f"Found {len(iframes)} frames.")
        for i, frame in enumerate(iframes):
            print(f"Frame {i} URL: {frame.url}")
            # Try to find links in this frame
            try:
                links = await frame.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => a.href)''')
                print(f"Frame {i} found {len(links)} links.")
                for l in [l for l in links if "mp.weixin.qq.com" in l][:2]:
                    print(f"  - {l}")
            except:
                pass
                
        await page.screenshot(path="debug_frames.png")
        print("Screenshot saved as debug_frames.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scrape())
