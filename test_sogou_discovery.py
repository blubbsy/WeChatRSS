import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_sogou_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a very specific UA and stealth
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        # Search type 1 is for accounts
        url = f"https://weixin.sogou.com/weixin?type=1&query={name}"
        
        print(f"Searching Sogou: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Take screenshot
        await page.screenshot(path="debug_sogou_search.png")
        
        # Check for CAPTCHA
        content = await page.content()
        if "antispider" in content:
            print("❌ SOGOU BLOCKED US.")
            # Try type 2 (articles)
            print("Trying Sogou Articles (type 2)...")
            await page.goto(f"https://weixin.sogou.com/weixin?type=2&query={name}", wait_until="networkidle")
            await asyncio.sleep(5)
            await page.screenshot(path="debug_sogou_articles.png")
            content = await page.content()
            if "antispider" in content:
                print("❌ SOGOU BLOCKED US AGAIN.")
            else:
                links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => a.href)''')
                mp_links = [l for l in links if "mp.weixin.qq.com" in l]
                print(f"✅ FOUND {len(mp_links)} LINKS ON SOGOU ARTICLES.")
        else:
            print("✅ SOGOU PAGE LOADED.")
            # Look for account link
            links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => ({ text: a.innerText, href: a.href }))''')
            for l in links:
                if "weixin" in l['href'] and ("account" in l['href'] or "gzh" in l['href']):
                    print(f"✅ FOUND ACCOUNT LINK: {l['text']} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sogou_search())
