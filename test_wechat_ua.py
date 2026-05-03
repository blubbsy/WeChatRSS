import asyncio
from playwright.async_api import async_playwright
import re

async def test_wechat_ua():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real WeChat Desktop UA
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/9101"
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()
        
        url = "https://mp.weixin.qq.com/s/AD2OAFCfJaKsEzmof3ASg"
        print(f"Loading {url} with WeChat UA...")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        content = await page.content()
        biz = re.search(r'var biz = "([^"]+)"', content)
        if biz:
            print(f"✅ SUCCESS: Biz={biz.group(1)}")
        else:
            print("❌ Still blocked.")
            await page.screenshot(path="debug_wechat_ua.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wechat_ua())
