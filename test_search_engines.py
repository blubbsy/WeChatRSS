import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def test_search_engines(query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Test 1: Bing (Often indexes WeChat articles fast)
        bing_url = f"https://www.bing.com/search?q=site%3Amp.weixin.qq.com+%22{query}%22"
        print(f"Searching Bing: {bing_url}")
        await page.goto(bing_url, wait_until="networkidle")
        await asyncio.sleep(3)
        
        bing_links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => a.href)''')
        wechat_links = [l for l in bing_links if "mp.weixin.qq.com" in l]
        print(f"  Found {len(wechat_links)} WeChat links on Bing.")

        # Test 2: Google
        google_url = f"https://www.google.com/search?q=site%3Amp.weixin.qq.com+%22{query}%22"
        print(f"Searching Google: {google_url}")
        try:
            await page.goto(google_url, wait_until="networkidle", timeout=10000)
            google_links = await page.evaluate('''() => Array.from(document.querySelectorAll('a')).map(a => a.href)''')
            wechat_links_g = [l for l in google_links if "mp.weixin.qq.com" in l]
            print(f"  Found {len(wechat_links_g)} WeChat links on Google.")
        except:
            print("  Google timed out or blocked.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search_engines("小木易仿真"))
