import asyncio
from playwright.async_api import async_playwright
import re

async def check_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        
        js_name = await page.evaluate("document.querySelector('#js_name')?.innerText")
        nickname = await page.evaluate("window.nickname")
        biz = await page.evaluate("window.biz")
        
        print(f"URL: {url}")
        print(f"window.nickname: {nickname}")
        print(f"window.biz: {biz}")
        print(f"DOM #js_name: {js_name}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_html("https://mp.weixin.qq.com/s/DS0bd4ut52QAT4UO0s0SUQ"))
