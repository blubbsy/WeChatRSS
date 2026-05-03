import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_sogou_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        url = f"https://weixin.sogou.com/weixin?type=1&query={name}"
        
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Look for the 'latest article' link in the results
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href,
                id: a.id
            }));
        }''')
        
        print(f"Found {len(links)} links on Sogou.")
        for l in links:
            # The 'latest article' link usually has an ID or specific text
            if "mp.weixin.qq.com" in l['href'] or l['text'].strip():
                 # Filter for useful ones
                 if "weixin" in l['href'] or "mp.weixin" in l['href']:
                     print(f"LINK: [{l['text'][:20]}] -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sogou_links())
