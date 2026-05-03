import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_title_discovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        title = "功率器件寄生电感简析"
        url = f"https://weixin.sogou.com/weixin?type=2&query={title}"
        
        print(f"Searching Sogou for title: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .filter(a => a.href.includes('mp.weixin.qq.com'))
                .map(a => ({ text: a.innerText, href: a.href }));
        }''')
        
        print(f"Found {len(links)} article links.")
        for l in links:
            print(f"- {l['text'].strip()[:30]} -> {l['href']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_title_discovery())
