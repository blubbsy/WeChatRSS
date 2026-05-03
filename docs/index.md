# Welcome to WeChatRSS

WeChatRSS is a modern, lightweight solution for bringing WeChat Official Account content into your professional workflow (RSS Readers, MS Teams, Slack).

## 🌟 Philosophy

WeChat is a notoriously closed ecosystem. Most scrapers fail because they rely on fragile private APIs or guest links that are frequently blocked. 

WeChatRSS takes a different approach: **The Mimic-Human Model**.
By using persistent browser profiles and real-user sessions, the system looks exactly like a human reader to Tencent's security layers.

## 🗺️ Documentation Map

*   **[Installation](installation.md):** Get the system running on your server.
*   **[Authentication](authentication.md):** How to "prime" the browser profiles for bypass.
*   **[Scraping & MS Teams](scraping.md):** Detailed look at discovery, extraction, and feed integration.
*   **[Architecture](architecture.md):** Deep dive into the tech stack and security.

## 🚀 Quick Setup

If you have Python 3.13+ installed:

1.  **Install:** `pip install -r requirements.txt`
2.  **Auth:** `python auth_ultimate.py` (Scan QR + Solve CAPTCHA)
3.  **Run:** `python main.py`
4.  **Enjoy:** Go to `http://localhost:8000`

---

*Last Updated: May 2026*
