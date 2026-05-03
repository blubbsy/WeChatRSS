import asyncio
from playwright.async_api import async_playwright
import re

async def check_wechat_id(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        
        # Look for user_name (this is the unique ID, e.g. gh_...)
        user_name = await page.evaluate("window.user_name")
        nickname = await page.evaluate("window.nickname")
        print(f"window.user_name: {user_name}")
        print(f"window.nickname: {nickname}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_wechat_id("https://mp.weixin.qq.com/s/DS0bd4ut52QAT4UO0s0SUQ"))
