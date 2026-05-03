import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def get_sogou_list(biz):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Searching by biz on Sogou
        url = f"https://weixin.sogou.com/weixin?type=1&query={biz}"
        print(f"Sogou URL: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Look for the account link
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} links on Sogou.")
        for l in links:
            if "weixin" in l['href'] and ("account" in l['href'] or "gzh" in l['href']):
                print(f"✅ Found Account Link: {l['text']} -> {l['href']}")
                
        await browser.close()

if __name__ == "__main__":
    biz = 'Mzk4ODUyMTE4Ng=='
    asyncio.run(get_sogou_list(biz))
