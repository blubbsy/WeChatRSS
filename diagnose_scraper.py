import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def diagnose_account(name, biz):
    async with async_playwright() as p:
        print(f"DIAGNOSING: {name} ({biz})")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None
        )
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        # 1. Test WeRead Home/Search
        print("\n--- 1. WeRead Search ---")
        try:
            url = f"https://weread.qq.com/web/search/analysis?keyword={name}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            await page.screenshot(path="diag_weread_search.png")
            print("Screenshot saved: diag_weread_search.png")
            
            # Check for account link
            target_url = await page.evaluate('''() => {
                const link = Array.from(document.querySelectorAll('a'))
                    .find(a => a.href.includes('web/reader/mp/'));
                return link ? { text: link.innerText, href: link.href } : null;
            }''')
            print(f"Found in search: {target_url}")
        except Exception as e:
            print(f"WeRead Search Error: {e}")

        # 2. Test WeRead Shelf
        print("\n--- 2. WeRead Shelf ---")
        try:
            await page.goto("https://weread.qq.com/web/shelf", wait_until="networkidle")
            await asyncio.sleep(3)
            await page.screenshot(path="diag_weread_shelf.png")
            print("Screenshot saved: diag_weread_shelf.png")
            
            # Count followed accounts
            mp_count = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href.includes('web/reader/mp/')).length;
            }''')
            print(f"MP accounts found on shelf: {mp_count}")
        except Exception as e:
            print(f"WeRead Shelf Error: {e}")

        # 3. Test Sogou Articles
        print("\n--- 3. Sogou Article Search ---")
        try:
            url = f"https://weixin.sogou.com/weixin?type=2&query={name}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            await page.screenshot(path="diag_sogou_articles.png")
            print("Screenshot saved: diag_sogou_articles.png")
            
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href.includes('mp.weixin.qq.com'))
                    .map(a => a.href);
            }''')
            print(f"Article links found on Sogou: {len(links)}")
        except Exception as e:
            print(f"Sogou Error: {e}")

        await browser.close()
        print("\nDIAGNOSIS COMPLETE.")

if __name__ == "__main__":
    asyncio.run(diagnose_account("小木易仿真", "Mzk4ODUyMTE4Ng=="))
