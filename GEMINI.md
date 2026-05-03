# WeChatRSS Project Overview (Updated May 2026)

This workspace contains a lightweight, high-reliability WeChat Official Account aggregation and RSS delivery system.

## 1. System Architecture

WeChatRSS uses a **"Mimic-Human"** approach to bypass anti-bot measures, prioritizing public discovery via Sogou and full-text extraction via WeRead.

### Technology Stack
*   **Backend:** FastAPI (Python 3.13+)
*   **Database:** SQLite with `aiosqlite` for non-blocking I/O.
*   **Automation:** Playwright with `playwright-stealth` and **Persistent Browser Profiles**.
*   **Discovery Engine:** Sogou Article Search (Primary) with WeRead internal search (Fallback).
*   **Extraction Engine:** WeRead Proxy Viewer (`/wrpage/mp/`) for clean HTML and asset mirroring.
*   **Frontend:** Bootstrap 5 dashboard with real-time `DEBUG` tracing.

---

## 2. Key Features & Safety Mechanisms

*   **Multi-Engine Discovery:** Automatically searches Sogou by name, resolves redirects, and verifies the unique WeChat `__biz` ID to ensure accuracy even if accounts are renamed.
*   **Persistent Profiles:** Stores real browser metadata in `data/profiles/` to look like a returning human user to Tencent's security systems.
*   **Auto-Account Extraction:** Users paste an article URL; the system extracts the `__biz` ID and nickname automatically using an authenticated session.
*   **Image Mirroring:** Automatically downloads and serves WeChat images from local storage to prevent hotlink protection breakage in RSS readers.
*   **Real-Time Observability:** Dashboard includes a **System Logs** tab and **Statistics Row** for full transparency into background scraper activity.

---

## 3. Operations & Maintenance

### Initial Setup & Auth
1.  **Install Dependencies:** `pip install -r requirements.txt` (Note: `bcrypt<4.0.0` pinned for `passlib` compatibility).
2.  **Ultimate Auth:** Run `python auth.py` to perform a one-time WeChat/Sogou session capture in a headed browser.
3.  **Start Server:** `python main.py`. Access at `http://localhost:8000`.

### Security Hardening
*   **CSRF Protection:** All state-changing requests (Sync, Add Account, Delete) require a valid CSRF token.
*   **Persistent Sessions:** Logins survive server restarts via the SQLite `sessions` table.
*   **Error Snapshots:** Scraper automatically saves screenshots of block pages to `data/debug/` for diagnosis.

### Documentation
A professional **MkDocs** site is available.
*   **View:** `mkdocs serve` -> `http://127.0.0.1:8000`
*   **Config:** `mkdocs.yml`

---

## 4. Development Conventions
*   **Logging:** Always use `add_system_log` in `scraper.py` for user-facing visibility.
*   **Database:** Use `get_db_async()` for all FastAPI endpoints.
*   **Extraction:** Never fetch articles directly from `mp.weixin.qq.com` in background workers; always use the `fetch_full_content` proxy method.
