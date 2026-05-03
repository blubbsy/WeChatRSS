import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_sogou():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = '小木易仿真'
        url = f"https://weixin.sogou.com/weixin?type=1&query={name}"
        
        print(f"Navigating to Sogou: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                href: a.href
            }));
        }''')
        
        print(f"Found {len(links)} links.")
        for l in [l for l in links if "account" in l['href'] or "gzh" in l['href'] or name in l['text']]:
            print(f"- {l['text']} -> {l['href']}")
            
        await page.screenshot(path="debug_sogou.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sogou())
