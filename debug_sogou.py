import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

STATE_PATH = os.path.join('data', 'state.json')

async def debug_sogou_direct():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a fresh context for Sogou to avoid session side-effects
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        name = "小木易仿真"
        print(f"SEARCHING SOGOU FOR '{name}'...")
        # type=2 is article search
        await page.goto(f"https://weixin.sogou.com/weixin?type=2&query={name}", wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.screenshot(path="debug_sogou_verify.png")
        
        # Check for CAPTCHA text or content
        content = await page.content()
        if "antispider" in content or "验证码" in content:
            print("❌ SOGOU CAPTCHA DETECTED.")
        else:
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href.includes('mp.weixin.qq.com'))
                    .map(a => ({ text: a.innerText, href: a.href }));
            }''')
            print(f"✅ FOUND {len(links)} LINKS ON SOGOU.")
            for l in links[:3]:
                print(f" - {l['text'].strip()} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_sogou_direct())
