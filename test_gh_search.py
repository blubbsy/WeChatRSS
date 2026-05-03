import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os

async def test_gh_search(gh_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = f"https://weixin.sogou.com/weixin?type=1&query={gh_id}"
        print(f"Searching Sogou for ID {gh_id}: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        accounts = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('li')).map(li => ({
                name: li.querySelector('h3')?.innerText.trim(),
                id: li.querySelector('.info label')?.innerText.trim()
            })).filter(a => a.name);
        }''')
        
        print(f"Found {len(accounts)} accounts.")
        for a in accounts:
            print(f"- {a['name']} ({a['id']})")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_gh_search('gh_c04991494361'))
