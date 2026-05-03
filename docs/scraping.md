# Scraping & MS Teams

WeChatRSS is built specifically to deliver high-quality, full-text content to enterprise tools like MS Teams.

## 🔍 Discovery Logic

The scraper uses a "Discovery-First" model to find the latest articles without being restricted by your personal library.

1.  **Sogou Search (Primary):** The system searches Sogou Articles by the account's nickname.
2.  **Biz-Lock Verification:** Once links are found, it resolves the unique `__biz` ID of the first article. If it matches the stored ID, the entire search result is trusted. This handles renamed or sub-branded accounts.
3.  **WeRead Shelf (Fallback):** If Sogou is blocked, the scraper looks inside your authenticated WeRead library for updates.

## 📄 Extraction Logic (Full Text)

To ensure the best reading experience in MS Teams, the extraction follows a tiered hierarchy:

1.  **Direct Access:** The system first tries to load the article directly from `mp.weixin.qq.com`. 
2.  **WeRead Proxy Fallback:** If direct access is blocked (common for automated browsers), it uses a hidden WeRead "Proxy Viewer" (`/wrpage/mp/index.html`). This cleans the HTML and bypasses hotlink protection.

## 🖼️ Image Mirroring

WeChat protects its images from being displayed on external sites (Hotlink Protection).
*   **Process:** During extraction, the system downloads all article images to `data/media/`.
*   **RSS Delivery:** The RSS feed rewriter replaces local paths with **Absolute Public URLs** so that MS Teams can fetch and display the images correctly.

## 🤝 MS Teams Integration

1.  Copy your private RSS link from the dashboard: `http://[IP]:8000/rss/[hash]`.
2.  In MS Teams, add the **RSS Connector** to your channel.
3.  Paste the link and set the frequency.
4.  **Result:** Teams will post a rich-text card with the full article content and images for every new update.

---

**Next Step:** [System Architecture](architecture.md)
