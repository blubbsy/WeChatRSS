# Installation Guide

Follow these steps to set up WeChatRSS on your local machine or server.

## 📋 Prerequisites

*   **Python:** Version 3.13 or higher.
*   **Operating System:** Windows, Linux, or macOS.
*   **Browser:** Playwright (Chromium) will be installed automatically.

## ⚙️ Step-by-Step Setup

### 1. Environment Preparation
It is recommended to use a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Database Initialization
The database is initialized automatically on the first run of the server. However, you can manually trigger a clean state by deleting the `data/` folder if needed.

### 4. Firewall & Ports
The server runs on port **8000** by default. Ensure this port is open if you intend to access the dashboard from another device or expose the RSS feed to MS Teams.

## 🐳 Docker (Optional)
A Dockerfile will be provided in a future update. For now, manual installation is the most reliable way to handle the headed browser required for initial authentication.

---

**Next Step:** [Authentication Guide](authentication.md)
