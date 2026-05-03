import asyncio
from playwright.async_api import async_playwright
import re

async def get_globals(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Loading {url}...")
        try:
            await page.goto(url, wait_until="load")
            await asyncio.sleep(5)
            
            # Extract biz from various places
            biz = await page.evaluate('''() => {
                return window.biz || (window.cgiData && window.cgiData.biz) || "";
            }''')
            
            # Extract from HTML source
            content = await page.content()
            m = re.search(r'__biz=([^&"]+)', content)
            biz_source = m.group(1) if m else None
            
            # Extract nickname
            name = await page.evaluate('''() => {
                return window.nickname || (window.cgiData && window.cgiData.nickname) || document.querySelector('.profile_nickname')?.innerText || "";
            }''')
            
            print(f"Result: Biz={biz}, BizSource={biz_source}, Name={name}")
        except Exception as e:
            print(f"Error: {e}")
        await browser.close()

if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/AD2OAFCfJaKsEzmof3ASg"
    asyncio.run(get_globals(url))
