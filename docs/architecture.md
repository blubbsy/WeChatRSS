# System Architecture

WeChatRSS is designed for stability and observability.

## 🏗️ Tech Stack

*   **FastAPI:** High-performance async web framework.
*   **Playwright:** The engine for browser automation and stealth.
*   **aiosqlite:** Non-blocking SQLite access.
*   **APScheduler:** Background job management with random jitter to prevent detection.
*   **Readability-lxml:** Clean text extraction from messy HTML.

## 💾 Data Management

*   **Database:** `data/wechat_rss.db`
    *   `users`: Login and unique RSS hash.
    *   `accounts`: Subscribed channels and health status.
    *   `articles`: Full text, URLs, and pub dates.
    *   `system_logs`: Direct transparency into background worker events.
*   **Media:** `data/media/`
    *   Local mirror of WeChat images.

## 🛡️ Security Layers

### 1. Persistent Browser Profiles
By storing the full Chromium profile folder on disk, we maintain a consistent browser "fingerprint." This includes cache, local storage, and cookies that Tencent's security systems look for to distinguish humans from bots.

### 2. CSRF & Auth
All state-changing API endpoints require a valid CSRF token. Dashboard access is protected by persistent, database-backed sessions.

### 3. Observability (Debug Snapshots)
If the scraper hits a block, it automatically saves:
*   A full-page **Screenshot** (.png)
*   The raw **HTML Source** (.html)
These are stored in `data/debug/` for immediate diagnosis.

## ⚙️ Scheduler Jitter
The background scraper uses **Random Jitter**. If the interval is set to 6 hours, it will add/subtract a random amount of minutes to each run to ensure the request patterns are not perfectly predictable.

---

**Back to:** [Overview](index.md)
