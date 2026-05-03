# WeChatRSS

A lightweight, high-reliability WeChat Official Account aggregator and RSS deliverer. Optimized for **MS Teams** integration and anti-bot evasion.

## 🚀 Key Features

*   **Mimic-Human Architecture:** Uses persistent browser profiles and stealth automation to bypass Tencent's security systems.
*   **Dual-Engine Discovery:** Prioritizes **Sogou Article Search** for public updates with a **WeRead internal search** fallback.
*   **Tiered Extraction:** Attempts direct article access first, falling back to a trusted **WeRead Proxy Viewer** only when blocked.
*   **MS Teams Optimized:** Delivers **Full Article Text** with mirrored images using absolute public URLs.
*   **Real-Time Dashboard:** Monitor background scraper activity, view logs, and filter articles by account or title.
*   **Smart Deduplication:** Normalizes WeChat URLs and uses Title+Account locking to prevent feed spam.

## 🛠️ Quick Start

1.  **Clone & Install:**
    ```bash
    git clone https://github.com/blubbsy/WeChatRSS.git
    cd WeChatRSS
    pip install -r requirements.txt
    python -m playwright install chromium
    ```

2.  **Initialize Session:**
    Run the ultimate auth script to capture your "Human" fingerprint:
    ```bash
    python auth.py
    ```
    *   Scan the WeChat QR code to log in to WeRead.
    *   Solve the Sogou CAPTCHA when prompted.
    *   Follow your target accounts in the browser window.

3.  **Start the Server:**
    ```bash
    python main.py
    ```
    Access the dashboard at `http://localhost:8000`. Default credentials: `admin` / `admin`.

## 📖 Detailed Documentation

The full documentation is available in the `/docs` folder or can be served via MkDocs:
```bash
pip install mkdocs-material
mkdocs serve
```

## 🛡️ Security
*   **Persistent Profiles:** Your session is stored locally in `data/profiles/`. Never share this folder.
*   **CSRF Protection:** All state-changing dashboard actions are protected.
*   **Local Database:** All articles and settings are stored in a local SQLite database.

## 📄 License
MIT License. See `LICENSE` for details.
