import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def diag_sogou_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        name = "小木易仿真"
        url = f"https://weixin.sogou.com/weixin?type=2&query={name}"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Check all child elements of the first li to find the account name
        structure = await page.evaluate('''() => {
            const li = document.querySelector('.news-list li');
            if (!li) return "NO LI FOUND";
            return Array.from(li.querySelectorAll('*')).map(el => ({
                tag: el.tagName,
                class: el.className,
                text: el.innerText.trim()
            })).filter(e => e.text.length > 0);
        }''')
        
        print("First Item Structure:")
        import json
        print(json.dumps(structure, indent=2, ensure_ascii=False))
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diag_sogou_structure())
