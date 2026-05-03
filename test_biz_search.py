import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_biz_search(biz):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Method: Search by biz in Sogou
        # Sometimes query='__biz=...' works
        url = f"https://weixin.sogou.com/weixin?type=2&query={biz}"
        print(f"Searching Sogou for biz {biz}: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.news-list li')).map(li => ({
                title: li.querySelector('h3 a')?.innerText,
                account: li.querySelector('.all-time-y2, .account, .s-p')?.innerText
            }));
        }''')
        
        print(f"Found {len(links)} links.")
        for l in links:
            print(f"- {l['title']} ({l['account']})")
            
        await browser.close()

if __name__ == "__main__":
    # SysPro biz
    asyncio.run(test_biz_search('Mzg3MjE3MTYyOA=='))
