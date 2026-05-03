# Audit & Roadmap

To ensure the long-term viability and security of WeChatRSS, the following tasks are proposed for future development.

## 🔴 Security Audit (Priority High)

1.  **Session Management:**
    *   **Task:** Move from in-memory `active_sessions` to a persistent store (Redis or encrypted SQLite table).
    *   **Reason:** Currently, all users are logged out whenever the server restarts.
2.  **CSRF Protection:**
    *   **Task:** Implement CSRF tokens for all state-changing POST/DELETE requests.
    *   **Reason:** Current dashboard forms are vulnerable to Cross-Site Request Forgery.
3.  **Password Policy:**
    *   **Task:** Enforce minimum password complexity and implement rate-limiting on login attempts.

## 🟡 Code Review (Priority Medium)

1.  **Database Connection Pooling:**
    *   **Task:** Implement a proper connection pool or use an ORM like Tortoise-ORM or SQLAlchemy.
    *   **Reason:** Current `get_db()` opens a new connection per request, which is inefficient.
2.  **Error Handling:**
    *   **Task:** Centralize exception handling and provide more user-friendly error messages in the dashboard.
3.  **Testing Suite:**
    *   **Task:** Add unit tests for RSS generation and integration tests for the scraper using mock responses.

## 🔵 Bug Hunt (Priority Medium)

1.  **WeChat Link Expiry:**
    *   **Investigation:** Check if articles fetched via WeRead have temporary URLs that expire, and ensure our local mirroring handles this.
2.  **Memory Leaks:**
    *   **Investigation:** Monitor long-running Playwright instances for memory growth.
3.  **Concurrency:**
    *   **Investigation:** Ensure the APScheduler doesn't spawn overlapping scraper jobs if one takes longer than the interval.

## 🚀 Feature Roadmap

*   **Auto Account Extraction:** Allow users to paste an article link to automatically extract the Account ID and Name for subscription.
*   **OPML Export:** Allow users to export their subscription list.
*   **Search:** Search through the archived articles in the dashboard.
*   **Notification Integration:** Webhook support for pushing new articles to Telegram/Discord/Slack.
*   **Headless Login:** Investigate if QR code can be served via the dashboard for remote setup.
