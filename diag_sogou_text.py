import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def diag_sogou_text():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        url = f"https://weixin.sogou.com/weixin?type=2&query={name}"
        print(f"Opening Sogou: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Get all info for the first few items
        items = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.news-list li')).map(li => ({
                title: li.querySelector('h3 a')?.innerText.trim(),
                account: li.querySelector('.account')?.innerText.trim(),
                href: li.querySelector('h3 a')?.href
            }));
        }''')
        
        print(f"Found {len(items)} items on page.")
        for i in items:
            print(f"- TITLE: {i['title']}")
            print(f"  ACCOUNT: '{i['account']}'")
            print(f"  HREF: {i['href'][:50]}...")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diag_sogou_text())
