import asyncio
from playwright.async_api import async_playwright
import re

async def get_biz_id(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Loading {url}...")
        await page.goto(url)
        content = await page.content()
        
        # Look for var biz = "..."
        match = re.search(r'var biz = "([^"]+)"', content)
        if match:
            biz = match.group(1)
            # Find account name
            name_match = re.search(r'var nickname = "([^"]+)"', content)
            name = name_match.group(1) if name_match else "Unknown"
            print(f"\nAccount Name: {name}")
            print(f"Account ID (__biz): {biz}")
        else:
            print("\nCould not find __biz ID in page source.")
            
        await browser.close()

if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/zkiNHp8cfsojGcOwWpI5Ng"
    asyncio.run(get_biz_id(url))
