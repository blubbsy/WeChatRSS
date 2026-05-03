import asyncio
from playwright.async_api import async_playwright

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a context that allows cookies and logs details
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to dashboard...")
        await page.goto("http://localhost:8000")
        
        print("Attempting login...")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin")
        
        async with page.expect_navigation():
            await page.click('button[type="submit"]')
        
        print(f"Current URL: {page.url}")
        cookies = await context.cookies()
        print(f"Cookies: {[c['name'] for c in cookies]}")
        
        content = await page.content()
        if "Logged in as: admin" in content:
            print("SUCCESS: Dashboard verified.")
        elif "Invalid credentials" in content:
            print("FAIL: Invalid credentials alert shown.")
        else:
            print("FAIL: Neither dashboard nor error message found.")
            # Take a screenshot to see what's happening
            await page.screenshot(path="debug_login.png")
            print("Screenshot saved as debug_login.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())
