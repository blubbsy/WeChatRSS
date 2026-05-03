import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json

async def diag_account_search(name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        profile_dir = os.path.abspath(os.path.join('data', 'profiles', 'wechat_rss_profile'))
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        # Type 1 = Account Search
        url = f"https://weixin.sogou.com/weixin?type=1&query={name}"
        print(f"Opening Sogou Account Search for '{name}': {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        content = await page.content()
        if "antispider" in content:
            print("❌ SOGOU CAPTCHA DETECTED")
            await context.close()
            return

        # List all matching accounts
        accounts = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('li')).map(li => ({
                name: li.querySelector('.txt-box h3')?.innerText.trim(),
                wechat_id: li.querySelector('.info label')?.innerText.trim(),
                description: li.querySelector('p.dl')?.innerText.trim()
            })).filter(a => a.name);
        }''')
        
        print(f"Found {len(accounts)} accounts.")
        for a in accounts:
            print(f"- NAME: {a['name']}")
            print(f"  ID: {a['wechat_id']}")
            print(f"  DESC: {a['description']}")
            
        await page.screenshot(path=f"debug_account_search_{name}.png")
        await context.close()

if __name__ == "__main__":
    asyncio.run(diag_account_search("SysPro系统工程智库"))
