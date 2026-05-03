# Scraping & Safety

WeChat employs advanced anti-bot technologies. WeChatRSS implements several safety mechanisms to remain undetected.

## Anti-Detection Mechanisms

### 1. WeRead Proxy Access
Instead of scraping the main WeChat portal, the system accesses articles through `weread.qq.com/web/reader/mp/{account_id}`. This acts as a natural proxy and utilizes a different set of rate limits.

### 2. Browser Stealth
The system uses the `playwright-stealth` library, which applies patches to Chromium to hide common bot signatures, such as:
*   `navigator.webdriver` flags.
*   Consistent WebGL and Canvas fingerprints.
*   Standardized Chrome-like `navigator` properties.

### 3. Human-like Behavior
The scraper (`scraper.py`) implements:
*   **Randomized Jitter:** Scans are not perfectly periodic. A random delay (default ±30 mins) is added to every scheduled run.
*   **Inter-action Delays:** `asyncio.sleep` with random durations between page loads and interactions.
*   **Natural Scrolling:** Before capturing content, the scraper scrolls down the page at variable speeds to trigger lazy-loaded images and mimic a reading human.

### 4. Custom User-Agents
The system uses a randomized but modern desktop User-Agent to blend in with normal browser traffic.

## Content Extraction

WeChatRSS uses the **Readability** algorithm (similar to "Reader Mode" in browsers) to:
1.  Strip ads, menus, and tracking scripts.
2.  Extract the core article content.
3.  Normalize HTML for RSS compatibility.

## Safety Recommendations

*   **Don't over-fetch:** Keep `fetch_interval_hours` at 6 or higher.
*   **Limit Subscriptions:** Excessive scraping of hundreds of accounts from a single IP may trigger temporary bans.
*   **Use a Residential IP:** If hosting on a VPS, try to use one with a "clean" IP range.
