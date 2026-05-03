import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_sogou_articles():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        # Search type 2 = Articles
        url = f"https://weixin.sogou.com/weixin?type=2&query={name}"
        
        print(f"Searching Sogou Articles: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Take screenshot
        await page.screenshot(path="debug_sogou_news.png")
        
        # Try to find news-list
        news = await page.query_selector_all(".news-list li")
        print(f"Found {len(news)} news items.")
        
        for item in news:
            title_el = await item.query_selector("h3 a")
            if title_el:
                title = await title_el.inner_text()
                href = await title_el.get_attribute("href")
                print(f"✅ ARTICLE: {title.strip()} -> {href}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sogou_articles())
