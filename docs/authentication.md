# Authentication & Bypass

WeChatRSS uses a "Persistent Browser Profile" to stay undetected. You must perform a one-time "priming" of this profile.

## 🔑 The "Ultimate Auth" Script

The script `auth_ultimate.py` is the key to the system's stealth capabilities. It performs three critical actions in a single headed browser session.

### How to use:
Run the command in your terminal:
```bash
python auth_ultimate.py
```

### The Three Phases:

1.  **WeChat/WeRead Login:**
    *   A browser window will open at `weread.qq.com`. 
    *   Scan the QR code with your WeChat mobile app.
    *   This establishes a trusted Tencent session that allows the scraper to access full article text.

2.  **Sogou CAPTCHA Bypass:**
    *   The window will automatically navigate to Sogou Search.
    *   If you see a verification code or a puzzle, **solve it immediately**.
    *   This "white-lists" your IP address for article discovery.

3.  **Account Following:**
    *   While the window is open, search for your target Official Accounts and click **Follow** (关注).
    *   This ensures the accounts appear in your private library, which the scraper uses as a high-reliability fallback.

## 🕒 How often is this needed?

*   **One-Time Setup:** Usually, you only need to do this once. The session data is saved to `data/profiles/` and persists across restarts.
*   **Re-Auth:** If you see "RE-AUTH NEEDED" or "Sogou BLOCK" in the dashboard logs, simply run the script again to refresh the tokens.

## 🛡️ Privacy Note
The browser profile is stored **entirely on your machine**. WeChatRSS never sends your cookies or session data to any external server (except for the target sites WeRead/Sogou).

---

**Next Step:** [Scraping & MS Teams Integration](scraping.md)
