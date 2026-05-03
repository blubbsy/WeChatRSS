import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def test_proxy_discovery(article_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Wrap the article in WeRead proxy
        proxy_url = f"https://weread.qq.com/wrpage/mp/index.html?link={article_url}"
        print(f"Loading Proxy URL: {proxy_url}")
        
        await page.goto(proxy_url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.screenshot(path="debug_proxy_discovery.png")
        
        # Look for the account name/link in the proxy view
        # WeRead articles usually have a header or footer with the account name
        elements = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a, div, span'))
                .map(el => ({ text: el.innerText, href: (el.tagName === 'A' ? el.href : '') }))
                .filter(el => el.text.length > 0);
        }''')
        
        print("Found elements in Proxy View:")
        for e in elements[:100]:
            if "web/reader/mp/" in e['href'] or "前往" in e['text'] or "关注" in e['text']:
                print(f"  MATCH: '{e['text']}' -> {e['href']}")

        await browser.close()

if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/AD2OAFCfJaKsEzmof3ASg"
    asyncio.run(test_proxy_discovery(url))
