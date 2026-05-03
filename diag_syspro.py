import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json

async def diag_account(name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use persistent profile to see if it's a captcha issue
        profile_dir = os.path.abspath(os.path.join('data', 'profiles', 'wechat_rss_profile'))
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        url = f"https://weixin.sogou.com/weixin?type=2&query={name}"
        print(f"Opening Sogou for '{name}': {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        content = await page.content()
        if "antispider" in content:
            print("❌ SOGOU CAPTCHA DETECTED")
            await page.screenshot(path=f"debug_captcha_{name}.png")
            await context.close()
            return

        # Get all info for the first few items
        items = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.news-list li')).map(li => ({
                title: li.querySelector('h3 a')?.innerText.trim(),
                account: li.querySelector('.all-time-y2, .account, .s-p')?.innerText.trim(),
                href: li.querySelector('h3 a')?.href
            }));
        }''')
        
        print(f"Found {len(items)} items on page.")
        for i in items:
            print(f"- TITLE: {i['title']}")
            print(f"  ACCOUNT: '{i['account']}'")
            match = (name in (i['account'] or '') or (i['account'] or '') in name)
            print(f"  MATCHES '{name}'? {match}")
            
        await page.screenshot(path=f"debug_sogou_{name}.png")
        await context.close()

if __name__ == "__main__":
    asyncio.run(diag_account("SysPro系统工程智库"))
