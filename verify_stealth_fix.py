import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def verify_stealth():
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Applying stealth...")
            # Create Stealth instance and apply it
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            print("Navigating to check webdriver property...")
            await page.goto("https://bot.sannysoft.com/")
            # Check navigator.webdriver
            webdriver = await page.evaluate("navigator.webdriver")
            print(f"navigator.webdriver: {webdriver}")
            
            await browser.close()
            print("SUCCESS: Stealth applied correctly.")
            return True
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(verify_stealth())
