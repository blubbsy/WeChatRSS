import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def get_sogou_biz():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        # Search type 1 = Accounts
        url = f"https://weixin.sogou.com/weixin?type=1&query={name}"
        
        print(f"Searching Sogou for account: {name}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Look for the 'account' link
        # It's usually the main title of the result
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href,
                title: a.title
            }));
        }''')
        
        for l in links:
            # Sogou account links often contain 'openid' or 'gzh'
            if "/gzh?" in l['href'] or name in l['text']:
                print(f"✅ POTENTIAL ACCOUNT: '{l['text']}' -> {l['href']}")
                
        await page.screenshot(path="debug_sogou_results.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_sogou_biz())
