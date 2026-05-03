import asyncio
from playwright.async_api import async_playwright
import re

async def test_extraction(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Loading {url}...")
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        
        # Method 1: JS Variables
        biz = await page.evaluate("window.biz || ''")
        nickname = await page.evaluate("window.nickname || ''")
        print(f"JS window.biz: {biz}")
        print(f"JS window.nickname: {nickname}")
        
        # Method 2: Regex in Source
        biz_match = re.search(r'var biz = "([^"]+)"', content)
        nick_match = re.search(r'var nickname = "([^"]+)"', content)
        print(f"Regex biz: {biz_match.group(1) if biz_match else 'None'}")
        print(f"Regex nickname: {nick_match.group(1) if nick_match else 'None'}")
        
        # Method 3: DOM elements
        dom_nickname = await page.evaluate('''() => {
            const el = document.querySelector('#js_name') || document.querySelector('.profile_nickname');
            return el ? el.innerText.trim() : '';
        }''')
        print(f"DOM nickname: {dom_nickname}")
        
        await browser.close()

if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/DS0bd4ut52QAT4UO0s0SUQ"
    asyncio.run(test_extraction(url))
