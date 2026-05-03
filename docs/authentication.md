# Authentication

WeChat avoids traditional API access. WeChatRSS uses a "Bridge" approach via **WeRead (微信读书)** to access Official Account content safely.

## The WeRead Bridge

WeRead provides a web-based portal to WeChat Official Account articles at `weread.qq.com`. By authenticating with WeRead, we gain access to a less restricted view of the WeChat ecosystem compared to the direct `mp.weixin.qq.com` domain.

## Manual Initial Login

Authentication requires a one-time manual step to handle the WeChat QR code scan:

1.  Run `python auth.py`.
2.  A non-headless Chromium window will open at `weread.qq.com`.
3.  Scan the QR code with your WeChat app.
4.  Once the login is detected, the script captures the **Storage State**.

## Session Persistence

The captured state is saved to `data/state.json`. It includes:
*   **Cookies:** Authentication tokens and session identifiers.
*   **Local Storage:** Application-specific state.

The background scraper loads this state for every run, allowing it to act as a logged-in user without re-scanning the QR code.

!!! warning "Security Note"
    Never share or commit your `data/state.json` file. It contains your full authentication session.
